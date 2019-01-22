from copy import deepcopy
from functools import wraps
from itertools import chain
from logging import getLogger
from random import choice
from uuid import uuid1

from game.cell_types import CellType, Drill, PLAYER, GUARD, DRILL_SCENARIO
from game.game_board import LodeRunnerGameBoard
from game.game_participants import get_participant
from game.game_utils import get_lower_cell, get_cell_neighbours
from game.move_types import Move
from utils.map_generation import get_generated_board

logger = getLogger()

GOLD_CELLS_NUMBER = 30
TICK_TIME = .3
GUARD_NAME_PREFIX = "AI_"


AdminCommands = []


def rest_action_decorator(func):
    AdminCommands.append(func.__name__)

    @wraps(func)
    def wrapper(game_session, *args, **kwargs):
        return func(game_session, *args, **kwargs)

    return wrapper


class LodeRunnerGameSession:

    def __init__(self, loop, broadcast):
        self.loop = loop
        self.broadcast = broadcast
        self.artifacts = []
        self.registry = {}
        self.scenarios = {}
        self.is_paused = True
        self.is_started = False

        self.game_board = LodeRunnerGameBoard(get_generated_board())
        self.spawn_gold_cells(GOLD_CELLS_NUMBER)
        self.tick_time = TICK_TIME

    @rest_action_decorator
    def start(self):
        if self.is_paused:
            self.is_paused = False
            if not self.is_started:
                self.is_started = True
                self.tick()
                logger.info('Game session has been started')

    @rest_action_decorator
    def stop(self):
        if not self.is_paused:
            self.is_paused = True
            logger.info('Game session has been started')

    def tick(self):
        if not self.is_paused:
            self.process_gravity()
            self.process_drill_scenario()
            self.broadcast()
            self.allow_participants_action()
        self.loop.call_later(self.tick_time, self.tick)

    @property
    def gold_cells(self):
        return self.artifacts

    @rest_action_decorator
    def spawn_gold_cells(self, number=1):
        self.spawn_artifacts(CellType.Gold, number)

    def register_participant(self, client_id, name, participant_type):
        cell = choice(self._get_free_to_spawn_cells())
        if self._is_participant_id_in_registry(client_id):
            participant_object = self._get_participant_object_by_id(client_id)
            participant_object.re_spawn(cell)
        else:
            participant_object = get_participant(participant_id=client_id,
                                                 participant_type=participant_type,
                                                 cell=cell,
                                                 name=name)
            self.registry.update({client_id: participant_object})
            participant_object = self._get_participant_object_by_id(client_id)

        self._update_participant_board_cell(participant_object)

    def process_action(self, action, player_id):
        player_object = self._get_participant_object_by_id(player_id)
        if not self._is_participant_falling(participant_object=player_object) and player_object.is_allowed_to_act:
            if Move.is_code_valid(action):
                self._process_move(action, player_object)
            elif Drill.is_code_valid(action):
                self._process_drill(action, player_object)
            else:
                logger.info("Unknown command '%s' from client '%s'" % (action, repr(player_object)))

    def _is_participant_falling(self, participant_object):
        lower_cell = get_lower_cell(participant_object.get_cell())
        if self._can_participant_get_into_cell(participant_object=participant_object, move_action=Move.Down,
                                               next_cell=lower_cell) \
                and self._should_participant_fall(participant_object=participant_object, lower_cell=lower_cell):
            return True
        return False

    def _can_participant_get_into_cell(self, participant_object, move_action, next_cell):
        if next_cell not in self.game_board.board_info:
            return False

        if move_action == Move.Up and self.game_board.get_cell_type(participant_object.get_cell()) != CellType.Ladder:
            return False

        if self._is_participant_in_cell(cell=next_cell, participant_type=GUARD):
            return False

        if participant_object.get_type() == PLAYER and self._is_anyone_in_cell(next_cell):
            return False

        if self.game_board.get_cell_type(next_cell) == CellType.UnbreakableBrick:
            return False

        if self.game_board.get_cell_type(next_cell) == CellType.DrillableBrick \
                and not self._is_cell_in_scenarios(next_cell):
            return False

        if self.game_board.get_cell_type(next_cell) == CellType.DrillableBrick \
                and self._scenarios_info[next_cell][-1] in [CellType.Drill, CellType.DrillableBrick]:
            return False

        if self._is_cell_in_scenarios(participant_object.get_cell()) and participant_object.get_type() == GUARD:
            return False

        return True

    def _should_participant_fall(self, participant_object, lower_cell):
        if self.game_board.get_cell_type(participant_object.get_cell()) in [CellType.Ladder, CellType.Pipe]:
            return False

        if self._is_cell_in_scenarios(participant_object.get_cell()) and participant_object.get_type() == GUARD:
            return False

        if self.game_board.get_cell_type(lower_cell) == CellType.Ladder:
            return False

        return True

    def _process_move(self, move_action, participant_object):
        logger.debug("Processing move '{move}' from '{participant}'".format(move=move_action,
                                                                            participant=participant_object.name))
        current_cell = participant_object.get_cell()
        next_cell = get_move_point_cell(current_cell, move_action)
        if move_action in [Move.Left, Move.Right]:
            participant_object.set_direction(move_action)

        if self._can_participant_get_into_cell(participant_object=participant_object, move_action=move_action,
                                               next_cell=next_cell):
            if self._is_participant_in_cell(next_cell, PLAYER):
                victim_player_object = self._get_participant_object_by_cell(next_cell)
                self.register_participant(client_id=victim_player_object.get_id(), name=victim_player_object.get_name(),
                                          participant_type=PLAYER)
                next_cell_type = CellType.HeroDies

            else:
                if next_cell in self.gold_cells:
                    self._process_gold_cell_pickup(player_object=participant_object, cell=next_cell)

                next_cell_type = \
                    self.game_board.get_participant_on_cell_type(cell=next_cell,
                                                                 participant_type=participant_object.get_type(),
                                                                 direction=participant_object.get_direction())

            participant_object.move(next_cell)
            self.game_board.process_move(current_cell=current_cell, next_cell=next_cell, next_cell_type=next_cell_type,
                                         is_cell_in_scenarios=self._is_cell_in_scenarios(current_cell))
        else:
            self._update_participant_board_cell(participant_object)

        participant_object.disallow_action()

    def _process_gold_cell_pickup(self, player_object, cell):
        if player_object.get_type() == PLAYER:
            player_object.pickup_gold()
        self.gold_cells.remove(cell)
        logger.debug("Gold cell %s has been picked up" % str(cell))
        self.spawn_gold_cells()

    def _process_drill(self, drill_action, player_object):
        logger.debug("Processing %s of %s" % (drill_action, vars(player_object)))
        drill_vector = get_drill_vector(drill_action)
        cell = get_modified_cell(player_object.get_cell(), drill_vector)
        if self.game_board.is_cell_drillable(cell) and not self._is_cell_in_scenarios(cell):
            self._add_scenario(cell, player_id=player_object.get_id())
        player_object.disallow_action()

    def _add_scenario(self, cell, player_id):
        scenario = deepcopy(DRILL_SCENARIO)
        scenario.reverse()
        if player_id in self.scenarios:
            self.scenarios[player_id].update({cell: scenario})
        else:
            self.scenarios.update({player_id: {cell: scenario}})

    def process_drill_scenario(self):
        logger.debug("Processing drill scenarios ...")
        for player_id, player_scenarios in self.scenarios.items():
            for cell, scenario in player_scenarios.items():
                scenario_cell_type = scenario.pop()
                if not self._is_anyone_in_cell(cell):
                    self.game_board.update_board(cell, scenario_cell_type)
                else:
                    participant_object = self._get_participant_object_by_cell(cell)

                    if len(scenario) == 1:
                        pits_owner = self._get_player_object_by_pit_cell(cell)
                        if pits_owner and pits_owner != participant_object:
                            pits_owner.trap_participant(participant_object)
                        self.register_participant(client_id=participant_object.get_id(),
                                                  name=participant_object.get_name(),
                                                  participant_type=participant_object.get_type())

                        if participant_object.get_type() == PLAYER:
                            self.game_board.update_board(cell, CellType.HeroDies)

        self._delete_empty_scenarios()

    def _get_player_object_by_pit_cell(self, cell):
        for player_id, player_scenarios in self.scenarios.items():
            if cell in player_scenarios:
                return self._get_participant_object_by_id(player_id)

    def _delete_empty_scenarios(self):
        delete_empty_value_keys(self.scenarios)

        for player_id, player_scenarios in self.scenarios.items():
            delete_empty_value_keys(player_scenarios)

    @property
    def score_info(self):
        return {player_object.name: player_object.score['permanent'] for player_object in self.players}

    @property
    def players(self):
        return sorted([p_obj for p_obj in self._participants if p_obj.get_type() == PLAYER],
                      key=lambda x: x.score['permanent'],
                      reverse=True)

    @property
    def players_cells(self):
        return {player_object.name: player_object.cell for player_object in self.players}

    def is_player_name_in_registry(self, name):
        return name in [player_object.name for player_object in self.players]

    def process_gravity(self):
        logger.debug("Processing Gravity ...")
        for participants_object in self._participants:
            if self._is_participant_falling(participants_object):
                self._process_move(move_action=Move.Down, participant_object=participants_object)

    def _get_participant_direction_by_id(self, participant_id):
        if self._is_participant_id_in_registry(participant_id):
            participant_object = self._get_participant_object_by_id(participant_id)
            return participant_object.get_direction()

    def get_session_info(self, player_id):
        session_info = {}
        cell = self._get_participant_cell_by_id(player_id)
        direction = self._get_participant_direction_by_id(player_id)
        session_info['board'] = self.game_board.get_board_layers(cell=cell, direction=direction)
        session_info['players'] = {'score': self.score_info, 'names': self.players_cells}
        session_info['size'] = self.game_board.size
        return session_info

    @rest_action_decorator
    def info(self):
        return AdminCommands

    def run_admin_command(self, func_name):
        if func_name in AdminCommands:
            func = getattr(self, func_name)
            return func()
        return "Rest action is not available"

    @rest_action_decorator
    def get_board_size(self):
        return self.game_board.size

    @rest_action_decorator
    def check_user_name(self, name):
        return name in [participant.name for _, participant in self.registry.items()]

    def add_ai_objects(self, ai_number, ai_type):
        current_ai_number = self.get_participants_number(ai_type)
        for index in range(int(ai_number)):
            guard_name = "%s%s" % (GUARD_NAME_PREFIX, str(current_ai_number + index))
            self.register_participant(client_id=uuid1(), name=guard_name, participant_type=ai_type)

    def get_participants_number(self, participant_type):
        return len([el for el in self._participants if el.get_type() == participant_type])

    def remove_ai_objects(self, ai_number, ai_type):
        for index in range(int(ai_number)):
            self.unregister_participant(choice([ai_object.get_id() for ai_object in self._participants
                                                if ai_object.get_type() == ai_type]))

    def spawn_artifacts(self, cell_type, number):
        artifacts_info = {}
        free_to_spawn_cells = self._get_free_to_spawn_cells()
        for index in range(int(number)):
            artifact_cell = choice(free_to_spawn_cells)
            artifacts_info[artifact_cell] = cell_type
            self.artifacts.append(artifact_cell)
        self.game_board.board_info.update(artifacts_info)

    @rest_action_decorator
    def set_tick_time(self, tick_time):
        try:
            new_tick_time = float(tick_time)
            self.tick_time = new_tick_time
            return "Tick time has been set to %s sec" % new_tick_time
        except ValueError as e:
            return "Could't set tick time: %s" % str(e)

    @rest_action_decorator
    def regenerate_game_board(self):
        self.pause()
        self.scenarios = {}
        new_board_string = get_generated_board()
        self.game_board.__init__(new_board_string)
        free_cells = self._get_free_to_spawn_cells()
        for participant in self._participants:
            cell = choice(free_cells)
            participant.set_cell(cell)
        self.artifacts = []
        self.spawn_gold_cells(GOLD_CELLS_NUMBER)
        self.resume()

    def _get_free_to_spawn_cells(self):
        empty_cells = self.game_board.get_empty_cells()
        participants_cells = [participant_object.cell for participant_object in self._participants]
        participants_neighbour_cells = list(chain.from_iterable([get_cell_neighbours(cell, self.game_board.board_info)
                                                                 for cell in participants_cells]))
        return list(set(empty_cells) - set(participants_cells + participants_neighbour_cells + self.artifacts))

    @property
    def _participants(self):
        return [participant_object for participant_object in self.registry.values()]

    def _update_participant_board_cell(self, participant_object):
        cell = participant_object.get_cell()
        player_cell_type = self.game_board.get_participant_on_cell_type(cell=cell,
                                                                        participant_type=participant_object.get_type(),
                                                                        direction=participant_object.get_direction())
        self.game_board.update_board(cell=cell, cell_type=player_cell_type)

    def unregister_participant(self, participant_id):
        participant_cell = self._get_participant_cell_by_id(participant_id)
        participant_cell_type = self.game_board.get_cell_type(participant_cell)
        self.game_board.update_board(participant_cell, participant_cell_type)
        participant_obj = self.registry.pop(participant_id)
        logger.info("Unregistered {participant_type} '{name}', id: {id}"
                    .format(participant_type=participant_obj.participant_type,
                            name=participant_obj.name,
                            id=participant_id))

    def _get_participant_cell_by_id(self, participant_id):
        if self._is_participant_id_in_registry(participant_id):
            participant_object = self._get_participant_object_by_id(participant_id)
            return participant_object.get_cell()

    def _get_participant_object_by_id(self, participant_id):
        if participant_id in self.registry:
            return self.registry[participant_id]
        return ''

    def _is_participant_in_cell(self, cell, participant_type):
        return cell in [participant_object.get_cell() for participant_object in self._participants
                        if participant_object.get_type() == participant_type]

    def _is_anyone_in_cell(self, cell):
        return cell in [participant_object.get_cell() for participant_object in self._participants]

    def _is_cell_in_scenarios(self, cell):
        return cell in self._scenarios_info

    @property
    def _scenarios_info(self):
        return dict(chain.from_iterable([player_scenarios.items() for player_scenarios in self.scenarios.values()]))

    def _get_participant_object_by_cell(self, cell):
        for participant_object in self._participants:
            if participant_object.get_cell() == cell:
                return participant_object

    def _is_participant_id_in_registry(self, participant_id):
        return participant_id in self.registry

    def allow_participants_action(self):
        for participant_object in self._participants:
            participant_object.allow_action()

    def get_participant_id_by_name(self, name):
        for participant_object in self._participants:
            if participant_object.get_name() == name:
                return participant_object.get_id()

    def get_cell_by_name(self, name):
        participant_obj = self.registry[self.get_participant_id_by_name(name)]
        return participant_obj.get_cell()

    def get_participant_obj_by_name(self, name):
        for participant_object in self._participants:
            if participant_object.get_name() == name:
                return participant_object


def get_drill_vector(drill_action):
    if drill_action == Drill.DrillLeft:
        return -1, 1
    if drill_action == Drill.DrillRight:
        return 1, 1


def delete_empty_value_keys(info):
    empty_value_keys = []
    for key, value in info.items():
        if not value:
            empty_value_keys.append(key)

    for elem in empty_value_keys:
        info.pop(elem)


def get_move_point_cell(cell, move):
    x_move, y_move = get_move_changes(move)
    return cell[0] + x_move, cell[1] + y_move


def get_move_changes(move):
    move_changes = {
            None:       (0, 0),
            Move.Right: (1, 0),
            Move.Left: (-1, 0),
            Move.Down: (0, 1),
            Move.Up: (0, -1)
        }
    return move_changes[move]


def get_modified_cell(cell, vector):
    return cell[0] + vector[0], cell[1] + vector[1]
