import time
from itertools import chain

import json
from copy import deepcopy
from functools import wraps
from logging import getLogger
from random import choice, shuffle
from uuid import uuid4

from common.utils import (
    PLAYER,
    GUARD,
    SPECTATOR,
    CellType,
    Move,
    get_lower_cell,
    Drill,
    get_next_target_age,
    CellGroups,
)
from game.game_board import LodeRunnerGameBoard
from game.game_participants import get_participant

logger = getLogger()

DEFAULT_GUARDS_NUMBER = 4
TICK_TIME = 0.5
DEFAULT_SESSION_TIMESPAN = 15 * 60
GUARD_DESTROY_TIMEOUT = 1
GUARD_NAME_PREFIX = "AI_"
DRILL_SCENARIO = [
    CellType.Drill,
    CellType.Empty,
    CellType.Empty,
    CellType.Empty,
    CellType.Empty,
    CellType.Empty,
    CellType.PitFill4,
    CellType.PitFill3,
    CellType.PitFill2,
    CellType.PitFill1,
    CellType.PitFilled,
    CellType.DrillableBrick,
]

AdminCommands = []


def admin_command_decorator(func):
    AdminCommands.append(func.__name__)

    @wraps(func)
    def wrapper(game_session, *args, **kwargs):
        func(game_session, *args, **kwargs)
        game_session.broadcast([SPECTATOR, PLAYER])
        game_session.send_admin_info_func()

    return wrapper


class LodeRunnerGameSession:
    clients_info = None
    send_admin_info_func = None

    def __init__(self, loop, game_board: LodeRunnerGameBoard):
        self.loop = loop
        self.game_board = game_board
        self.registry = {}
        self.scenarios = {}
        self.is_paused = False
        self.is_running = False
        self.tick_time = TICK_TIME
        self.session_timespan = DEFAULT_SESSION_TIMESPAN
        self.start_time = None

    def broadcast(self, client_types=(SPECTATOR, PLAYER, GUARD)):
        logger.debug("Broadcasting data for websocket clients ...")
        if self.clients_info:
            for client_id, client in self.clients_info.items():
                if client.client_info["client_type"] in client_types:
                    client.sendMessage(
                        json.dumps(self.get_session_info(client_id)).encode()
                    )

    @admin_command_decorator
    def start(self):
        if not self.is_running:
            self.start_time = time.time()
            self.is_running = True
            self._tick()
            logger.info("Game session has been started")

    @admin_command_decorator
    def stop(self):
        self.is_running = False
        logger.info("Game session has been terminated")

    @admin_command_decorator
    def pause_resume(self):
        self.is_paused = not self.is_paused

    @admin_command_decorator
    def set_session_timespan(self, session_timespan):
        if not self.is_running:
            self.session_timespan = int(session_timespan)
            logger.info(f"Game session timespan has been set to {session_timespan}")

    def _tick(self):
        if not self.is_paused:
            self.move_guards()
            self.process_gravity()
            self.process_drill_scenario()
            self.broadcast()
            self.send_admin_info_func()
            shuffle(self._participants)
            self.allow_participants_action()

        if time.time() - self.start_time < self.session_timespan and self.is_running:
            self.loop.call_later(self.tick_time, self._tick)
        else:
            self.is_running = False
            self.send_admin_info_func()
            logger.info("Game session has been ended")

    @admin_command_decorator
    def update_gold_cells(self, number: int):
        if not self.is_running:
            number = int(number)
            if number != len(self.game_board.gold_cells):
                if self.game_board.gold_cells:
                    self.game_board.empty_gold_cells()

                self.game_board.init_gold_cells(number)

    @admin_command_decorator
    def update_guards_number(self, number=DEFAULT_GUARDS_NUMBER):
        if not self.is_running:
            number = int(number)
            for guard in self.guards:
                self.unregister_participant(guard.participant_id)
            for idx in range(number):
                self.register_participant(uuid4(), f"{GUARD}-{idx}", GUARD)

    def move_guards(self):
        players_cells = list(self.players_cells.values())
        guard_player_data = []
        for guard_id, guard_cell in self.guards_info.items():
            for player_cell in players_cells:
                next_target_distance = get_next_target_age(
                    self.game_board.global_wave_age_info,
                    self.game_board.joints_info,
                    [player_cell],
                    guard_cell,
                )
                if next_target_distance:
                    guard_player_data.append(
                        [guard_id, guard_cell, next_target_distance]
                    )

        guard_player_data = sorted(guard_player_data, key=lambda x: x[2][2])
        selected_guard_ids = []
        selected_players_cells = []
        for (
            guard_id,
            guard_cell,
            (next_cell, target_cell, distance),
        ) in guard_player_data:
            if (
                guard_id not in selected_guard_ids
                and target_cell not in selected_players_cells
            ):
                move_action = Move.get_move_from_start_end_cells(guard_cell, next_cell)
                self.process_action(move_action, guard_id)
                selected_guard_ids.append(guard_id)
                selected_players_cells.append(target_cell)

    @property
    def timer(self):
        if self.is_running:
            return int(self.session_timespan - (time.time() - self.start_time))
        return self.session_timespan

    def spawn_gold_cell(self):
        cell = choice(self.game_board.get_empty_cells_on_bricks())
        self.game_board.gold_cells.append(cell)
        self.game_board.board_info[cell] = CellType.Gold

    def register_participant(self, client_id, name, participant_type):
        cell = choice(self.game_board.get_empty_cells())
        if self._is_participant_id_in_registry(client_id):
            participant_object = self._get_participant_object_by_id(client_id)
            participant_object.re_spawn(cell)
        else:
            participant_object = get_participant(
                participant_id=client_id,
                participant_type=participant_type,
                cell=cell,
                name=name,
            )
            self.registry.update({client_id: participant_object})
            participant_object = self._get_participant_object_by_id(client_id)

        self._update_participant_board_cell(participant_object)

    def process_action(self, action, player_id):
        player_object = self._get_participant_object_by_id(player_id)
        if (
            not self._is_participant_falling(participant_object=player_object)
            and player_object.is_allowed_to_act
        ):
            if Move.is_code_valid(action):
                self._process_move(action, player_object)
            elif Drill.is_code_valid(action):
                self._process_drill(action, player_object)
            else:
                logger.info(
                    "Unknown command '%s' from client '%s'"
                    % (action, repr(player_object))
                )

    def _is_participant_falling(self, participant_object):
        lower_cell_code = self.game_board.board_info.get(
            get_lower_cell(participant_object.cell)
        )
        if lower_cell_code is None:
            return False
        if (
            lower_cell_code != CellType.Pipe
            and lower_cell_code not in CellGroups.EmptyCellTypes
        ):
            return False
        if self.game_board.initial_board_info[participant_object.cell] in [
            CellType.Pipe,
            CellType.Ladder,
        ]:
            return False
        return True

    def _can_participant_get_into_cell(
        self, participant_object, move_action, next_cell
    ):
        if next_cell not in self.game_board.board_info:
            return False

        if (
            move_action == Move.Up
            and self.game_board.get_initial_cell_type(participant_object.cell)
            != CellType.Ladder
        ):
            return False

        if self._is_participant_in_cell(cell=next_cell, participant_type=GUARD):
            return False

        if participant_object.get_type() == PLAYER and self._is_anyone_in_cell(
            next_cell
        ):
            return False

        if (
            self.game_board.get_initial_cell_type(next_cell)
            == CellType.UnbreakableBrick
        ):
            return False

        if self.game_board.get_initial_cell_type(
            next_cell
        ) == CellType.DrillableBrick and not self._is_cell_in_scenarios(next_cell):
            return False

        if self.game_board.get_initial_cell_type(
            next_cell
        ) == CellType.DrillableBrick and self._scenarios_info[next_cell][-1] in [
            CellType.Drill,
            CellType.DrillableBrick,
        ]:
            return False

        if (
            self._is_cell_in_scenarios(participant_object.cell)
            and participant_object.get_type() == GUARD
        ):
            return False

        return True

    def _process_move(self, move_action, participant_object):
        logger.debug(
            "Processing move '{move}' from '{participant}'".format(
                move=move_action, participant=participant_object.name
            )
        )
        current_cell = participant_object.cell
        next_cell = get_move_point_cell(current_cell, move_action)
        if move_action in [Move.Left, Move.Right]:
            participant_object.set_direction(move_action)

        if self._can_participant_get_into_cell(
            participant_object=participant_object,
            move_action=move_action,
            next_cell=next_cell,
        ):
            if self._is_participant_in_cell(next_cell, PLAYER):
                victim_player_object = self._get_participant_object_by_cell(next_cell)
                self.register_participant(
                    client_id=victim_player_object.get_id(),
                    name=victim_player_object.get_name(),
                    participant_type=PLAYER,
                )
                next_cell_type = CellType.HeroDies

            else:
                if next_cell in self.game_board.gold_cells:
                    self._process_gold_cell_pickup(
                        player_object=participant_object, cell=next_cell
                    )

                next_cell_type = self.game_board.get_participant_on_cell_type(
                    cell=next_cell,
                    participant_type=participant_object.get_type(),
                    direction=participant_object.get_direction(),
                )

            participant_object.move(next_cell)
            self.game_board.process_move(
                current_cell=current_cell,
                next_cell=next_cell,
                next_cell_type=next_cell_type,
                is_cell_in_scenarios=self._is_cell_in_scenarios(current_cell),
            )
        else:
            self._update_participant_board_cell(participant_object)

        participant_object.disallow_action()

    def _process_gold_cell_pickup(self, player_object, cell):
        if player_object.get_type() == PLAYER:
            player_object.pickup_gold()
        self.game_board.gold_cells.remove(cell)
        logger.debug("Gold cell %s has been picked up" % str(cell))
        self.spawn_gold_cell()

    def _process_drill(self, drill_action, player_object):
        logger.debug("Processing %s of %s" % (drill_action, vars(player_object)))
        drill_vector = get_drill_vector(drill_action)
        cell = get_modified_cell(player_object.cell, drill_vector)
        if self.game_board.is_cell_drillable(cell) and not self._is_cell_in_scenarios(
            cell
        ):
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
                        self.register_participant(
                            client_id=participant_object.get_id(),
                            name=participant_object.get_name(),
                            participant_type=participant_object.get_type(),
                        )

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
        return {
            player_object.name: player_object.score["permanent"]
            for player_object in self.players
        }

    @property
    def players(self):
        return sorted(
            [p_obj for p_obj in self._participants if p_obj.get_type() == PLAYER],
            key=lambda x: x.score["permanent"],
            reverse=True,
        )

    @property
    def players_cells(self):
        return {
            player_object.name: player_object.cell for player_object in self.players
        }

    @property
    def guards(self):
        return [p_obj for p_obj in self._participants if p_obj.get_type() == GUARD]

    @property
    def guards_info(self):
        return {
            g_obj.participant_id: g_obj.cell
            for g_obj in self._participants
            if g_obj.get_type() == GUARD
        }

    @property
    def player_clients(self):
        return [
            client
            for _, client in self.clients_info.items()
            if client.client_info["client_type"] == PLAYER
        ]

    def is_player_name_in_registry(self, name):
        return name in [player_object.name for player_object in self.players]

    def process_gravity(self):
        logger.debug("Processing Gravity ...")
        for participants_object in self._participants:
            if self._is_participant_falling(participants_object):
                self._process_move(
                    move_action=Move.Down, participant_object=participants_object
                )

    def _get_participant_direction_by_id(self, participant_id):
        if self._is_participant_id_in_registry(participant_id):
            participant_object = self._get_participant_object_by_id(participant_id)
            return participant_object.get_direction()

    def get_session_info(self, player_id=None):
        session_info = {}
        cell = self._get_participant_cell_by_id(player_id)
        direction = self._get_participant_direction_by_id(player_id)
        session_info["board"] = self.game_board.get_board_layers(
            cell=cell, direction=direction
        )
        session_info["players"] = {
            "score": self.score_info,
            "names": self.players_cells,
        }
        session_info["size"] = self.game_board.size
        return session_info

    def run_admin_command(self, func_name, func_args):
        if func_name in AdminCommands:
            func = getattr(self, func_name)
            return func(*func_args)
        return "Command is not available"

    @admin_command_decorator
    def check_user_name(self, name):
        return name in [participant.name for _, participant in self.registry.items()]

    @admin_command_decorator
    def set_tick_time(self, tick_time):
        if not self.is_running:
            try:
                new_tick_time = float(tick_time)
                self.tick_time = new_tick_time
                return "Tick time has been set to %s sec" % new_tick_time
            except ValueError as e:
                return "Could't set tick time: %s" % str(e)

    @admin_command_decorator
    def regenerate_game_board(self, blocks_number=None):
        if not self.is_running:
            try:
                blocks_number = int(blocks_number)
            except ValueError:
                logger.warning(f"Invalid blocks number '{blocks_number}'")
                raise
            else:
                gold_cells_number = len(self.game_board.gold_cells)
                guards_number = len(self.guards)
                self.game_board.empty_gold_cells()
                for guard in self.guards:
                    self.unregister_participant(guard.participant_id)
                for player in self.player_clients:
                    player.sendClose()
                time.sleep(0.1)
                self.game_board = LodeRunnerGameBoard.from_blocks_number(
                    int(blocks_number)
                )
                for idx in range(guards_number):
                    self.register_participant(uuid4(), f"{GUARD}-{idx}", GUARD)
                self.game_board.init_gold_cells(gold_cells_number)

    @property
    def _participants(self):
        return [participant_object for participant_object in self.registry.values()]

    def _update_participant_board_cell(self, participant_obj):
        player_cell_type = self.game_board.get_participant_on_cell_type(
            cell=participant_obj.cell,
            participant_type=participant_obj.get_type(),
            direction=participant_obj.get_direction(),
        )
        self.game_board.update_board(
            cell=participant_obj.cell, cell_type=player_cell_type
        )

    def unregister_participant(self, participant_id):
        participant_cell = self._get_participant_cell_by_id(participant_id)
        participant_cell_type = self.game_board.get_initial_cell_type(participant_cell)
        self.game_board.update_board(participant_cell, participant_cell_type)
        participant_obj = self.registry.pop(participant_id)
        logger.info(
            "Unregistered {participant_type} '{name}', id: {id}".format(
                participant_type=participant_obj.participant_type,
                name=participant_obj.name,
                id=participant_id,
            )
        )

    def _get_participant_cell_by_id(self, participant_id):
        if self._is_participant_id_in_registry(participant_id):
            participant_object = self._get_participant_object_by_id(participant_id)
            return participant_object.cell

    def _get_participant_object_by_id(self, participant_id):
        if participant_id in self.registry:
            return self.registry[participant_id]
        return ""

    def _is_participant_in_cell(self, cell, participant_type):
        return cell in [
            participant_object.cell
            for participant_object in self._participants
            if participant_object.get_type() == participant_type
        ]

    def _is_anyone_in_cell(self, cell):
        return cell in [
            participant_object.cell for participant_object in self._participants
        ]

    def _is_cell_in_scenarios(self, cell):
        return cell in self._scenarios_info

    @property
    def _scenarios_info(self):
        return dict(
            chain.from_iterable(
                [
                    player_scenarios.items()
                    for player_scenarios in self.scenarios.values()
                ]
            )
        )

    def _get_participant_object_by_cell(self, cell):
        for participant_object in self._participants:
            if participant_object.cell == cell:
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
        None: (0, 0),
        Move.Right: (1, 0),
        Move.Left: (-1, 0),
        Move.Down: (0, 1),
        Move.Up: (0, -1),
    }
    return move_changes[move]


def get_modified_cell(cell, vector):
    return cell[0] + vector[0], cell[1] + vector[1]


# TODO: Fix board regeneration
