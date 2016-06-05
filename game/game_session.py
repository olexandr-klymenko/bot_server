from logging import getLogger
from random import choice
from copy import deepcopy

from utils.map_generation import get_generated_board
from common.game_session import GameSession
from common.game_utils import *
from common.move_types import Move
from game.game_participants import ParticipantFactory
from game.game_utils import get_drill_vector, delete_empty_value_keys
from game.cell_types import CellType, Drill, PLAYER, GUARD, DRILL_SCENARIO
from game.game_board import LodeRunnerGameBoard
from game_config import GOLD_CELLS_NUMBER, GUARDS_NUMBER, TICK_TIME

logger = getLogger()


class LodeRunnerGameSession(GameSession):
    def __init__(self):
        super().__init__(ParticipantFactory)
        self.game_board = LodeRunnerGameBoard(get_generated_board())
        self.spawn_gold_cells(GOLD_CELLS_NUMBER)
        self.add_guards(GUARDS_NUMBER)
        self.tick_time = TICK_TIME

    @rest_action_decorator
    def add_guards(self, guards_number):
        self.add_ai_objects(ai_number=guards_number, ai_type=GUARD)

    @rest_action_decorator
    def remove_guards(self, guards_number):
        self.remove_ai_objects(ai_number=guards_number, ai_type=GUARD)

    @property
    def gold_cells(self):
        return self.artifacts

    @rest_action_decorator
    def spawn_gold_cells(self, number=1):
        spawned_cells = self.spawn_artifacts(CellType.Gold, number)
        logger.debug("Spawned gold cells %s" % spawned_cells)

    def register_participant(self, client_id, name, participant_type=PLAYER):
        super().register_participant(client_id, name, participant_type)

    def process_action(self, action, player_id):
        player_object = self._get_participant_object_by_id(player_id)
        if not self._is_participant_falling(participant_object=player_object) and player_object.is_allowed_to_act:
            if Move.is_code_valid(action):
                self._process_move(action, player_object)
            elif Drill.is_code_valid(action):
                self._process_drill(action, player_object)
            else:
                logger.info("Unknown command '%s' from client '%s'" % (action, player_object.name))

    def can_process_action(self, player_id, action):
        return not self._is_participant_falling(self._get_participant_object_by_id(player_id))

    def _is_participant_falling(self, participant_object):
        lower_cell = get_lower_cell(participant_object.get_cell())
        if self._can_participant_get_into_cell(participant_object=participant_object, move_action=Move.Down,
                                               next_cell=lower_cell)\
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

        if self.game_board.get_cell_type(next_cell) == CellType.DrillableBrick\
                and not self._is_cell_in_scenarios(next_cell):
            return False

        if self.game_board.get_cell_type(next_cell) == CellType.DrillableBrick\
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
    def scores(self):
        return {player_object.name: player_object.scores['permanent'] for player_object in self.players}

    @property
    def players(self):
        return [participant_object for participant_object in self._participants
                if participant_object.get_type() == PLAYER]

    @property
    def players_cells(self):
        return {player_object.name: player_object.cell for player_object in self.players}

    def is_player_name_in_registry(self, name):
        return name in [player_object.name for player_object in self.players]

    def move_guards(self):
        for guard_object in self._guards:
            if guard_object.is_allowed_to_act:
                move_action = self._get_guard_move_action(guard_object.get_cell())
                self._process_move(move_action, guard_object)

    @property
    def _guards(self):
        return [participant_object for participant_object in self._participants
                if participant_object.get_type() == GUARD]

    def _get_guard_move_action(self, cell):
        if self.players:
            joints_info = self.game_board.joints_info
            wave_age_info = get_wave_age_info(cell, joints_info)
            players_cells = [player_object.cell for player_object in self.players]
            next_cell = get_route(players_cells, wave_age_info, joints_info)

            if next_cell:
                return get_move_action(cell, next_cell)
            elif joints_info[cell]:
                return get_move_action(cell, choice(joints_info[cell]))

        return choice(Move.get_valid_codes())

    def process_gravity(self):
        logger.debug("Processing Gravity ...")
        for participants_object in self._participants:
            if self._is_participant_falling(participants_object):
                self._process_move(move_action=Move.Down, participant_object=participants_object)

    def _get_participant_direction_by_id(self, participant_id):
        if self._is_participant_id_in_registry(participant_id):
            participant_object = self._get_participant_object_by_id(participant_id)
            return participant_object.get_direction()

    def get_board_string(self, player_id):
        cell = self._get_participant_cell_by_id(player_id)
        direction = self._get_participant_direction_by_id(player_id)
        return self.game_board.get_board_string(cell=cell, direction=direction)
