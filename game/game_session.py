import json
import time
from copy import deepcopy
from functools import wraps
from itertools import chain
from logging import getLogger
from random import choice, shuffle
from typing import Callable, Dict, List, Tuple, Any, Union, Optional
from uuid import uuid4, UUID

from common.utils import (
    PLAYER,
    GUARD,
    SPECTATOR,
    CellType,
    Move,
    Drill,
    get_next_target_age,
)
from game.game_board import GameBoard
from game.game_participants import BaseParticipant, Guard, Player

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
        result = func(game_session, *args, **kwargs)
        game_session.broadcast([SPECTATOR, PLAYER])
        return result

    return wrapper


class LodeRunnerGameSession:
    def __init__(self, loop, game_board: GameBoard):
        self.loop = loop
        self._board: GameBoard = game_board
        self._registry: Dict[UUID, Union[Player, Guard]] = {}
        self._drill_scenarios: Dict[UUID, Dict[Tuple, List]] = {}
        self._die_cells: List[Tuple] = []
        self._is_paused: bool = False
        self._is_running: bool = False
        self._tick_time: float = TICK_TIME
        self._session_timespan: int = DEFAULT_SESSION_TIMESPAN
        self._start_time = None
        self._clients_info = None
        self._send_admin_info_func: Optional[Callable] = None

    def init(self, clients_info: Dict[UUID, Any], send_admin_info_func: Callable):
        self._clients_info = clients_info
        self._send_admin_info_func = send_admin_info_func
        self.update_guards_number()

    def broadcast(self, client_types=(SPECTATOR, PLAYER, GUARD)):
        logger.debug("Broadcasting data for websocket clients ...")
        if self._clients_info:
            for client_id, client in self._clients_info.items():
                if client.client_info["client_type"] in client_types:
                    client.sendMessage(
                        json.dumps(self.get_session_info(client_id)).encode()
                    )
        self._send_admin_info_func()

    def get_admin_info(self) -> Dict[str, Any]:
        return {
            "guards": len(self.guards),
            "gold": len(self._board.gold_cells),
            "players": [player.get_name() for player in self.players],
            "size": self._board.blocks_number,
            "tick": self._tick_time,
            "is_running": self._is_running,
            "is_paused": self._is_paused,
            "timespan": self._session_timespan,
            "timer": self.timer,
        }

    @admin_command_decorator
    def start(self):
        if not self._is_running:
            self._start_time = time.time()
            self._is_running = True
            self._tick()
            logger.info("Game session has been started")

    @admin_command_decorator
    def stop(self):
        self._is_running = False
        logger.info("Game session has been terminated")

    @admin_command_decorator
    def pause_resume(self):
        self._is_paused = not self._is_paused

    @admin_command_decorator
    def set_session_timespan(self, session_timespan):
        if not self._is_running:
            self._session_timespan = int(session_timespan)
            logger.info(f"Game session timespan has been set to {session_timespan}")

    def _tick(self):
        if not self._is_paused:
            self.cleanup_die_cells()
            self.move_guards()
            self.process_gravity()
            self.process_drill_scenario()
            self.broadcast()
            self._send_admin_info_func()
            shuffle(self._participants)
            self.allow_participants_action()

        if time.time() - self._start_time < self._session_timespan and self._is_running:
            self.loop.call_later(self._tick_time, self._tick)
        else:
            self._is_running = False
            self._send_admin_info_func()
            logger.info("Game session has been ended")

    @admin_command_decorator
    def update_gold_cells(self, number: int):
        if not self._is_running:
            number = int(number)
            if number != len(self._board.gold_cells):
                self._board.empty_gold_cells()
                self._board.init_gold_cells(number)

    @admin_command_decorator
    def update_guards_number(self, number=DEFAULT_GUARDS_NUMBER):
        if not self._is_running:
            number = int(number)
            for guard_obj in self.guards:
                self.unregister_participant(guard_obj.get_id())
            for idx in range(number):
                self.register_participant(uuid4(), f"{GUARD}-{idx}", GUARD)

    def cleanup_die_cells(self):
        while self._die_cells:
            cell = self._die_cells.pop()
            if not self._is_anyone_in_cell(cell):
                self._board.restore_original_cell(cell)
            else:
                self._update_participant_board_cell(
                    self._get_participant_object_by_cell(cell)
                )

    def move_guards(self):
        guard_player_data = []
        for guard_obj in self.guards:
            for player_cell in self.players_cells.values():
                next_target_distance = get_next_target_age(
                    self._board.global_wave_age_info,
                    self._board.joints_info,
                    [player_cell],
                    guard_obj.cell,
                )
                if next_target_distance:
                    guard_player_data.append(
                        [guard_obj.get_id(), guard_obj.cell, next_target_distance]
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
        if self._is_running:
            return int(self._session_timespan - (time.time() - self._start_time))
        return self._session_timespan

    def register_participant(self, client_id: UUID, name: str, participant_type: str):
        cell = choice(self._board.get_empty_cells())
        if self._is_participant_id_in_registry(client_id):
            participant_object = self._get_participant_object_by_id(client_id)
            participant_object.re_spawn(cell)
        else:
            participant_object = BaseParticipant.get_participant(
                participant_type=participant_type,
                participant_id=client_id,
                cell=cell,
                name=name,
            )
            self._registry.update({client_id: participant_object})
            participant_object = self._get_participant_object_by_id(client_id)

        self._update_participant_board_cell(participant_object)

    def process_action(self, action: str, player_id: UUID):
        player_object = self._get_participant_object_by_id(player_id)
        if (
                not self._board.can_fall_from_here(player_object.cell)
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

    def _process_move(self, move_action: str, participant_object: Union[Player, Guard]):
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
                self._die_cells.append(next_cell)

            else:
                if next_cell in self._board.gold_cells:
                    self._process_gold_cell_pickup(
                        player_object=participant_object, cell=next_cell
                    )

                next_cell_type = self._board.get_participant_on_cell_type(
                    cell=next_cell,
                    participant_type=participant_object.get_type(),
                    direction=participant_object.get_direction(),
                )

            participant_object.move(next_cell)
            self._board.process_move(
                current_cell=current_cell,
                next_cell=next_cell,
                next_cell_type=next_cell_type,
                is_cell_in_scenarios=self._is_cell_in_scenarios(current_cell),
            )
        else:
            self._update_participant_board_cell(participant_object)

        participant_object.disallow_action()

    def _can_participant_get_into_cell(
            self, participant_object: BaseParticipant, move_action: str, next_cell: Tuple
    ) -> bool:
        if not self._board.is_cell_valid(participant_object.cell):
            return False

        if (
                move_action == Move.Up
                and self._board.get_initial_cell_type(participant_object.cell)
                != CellType.Ladder
        ):
            return False

        if self._is_participant_in_cell(cell=next_cell, participant_type=GUARD):
            return False

        if participant_object.get_type() == PLAYER and self._is_anyone_in_cell(
                next_cell
        ):
            return False

        if self._board.get_initial_cell_type(next_cell) == CellType.UnbreakableBrick:
            return False

        if self._board.get_initial_cell_type(
                next_cell
        ) == CellType.DrillableBrick and not self._is_cell_in_scenarios(next_cell):
            return False

        if self._board.get_initial_cell_type(
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

    def _process_gold_cell_pickup(
            self, player_object: Union[Player, Guard], cell: Tuple
    ):
        if player_object.get_type() == PLAYER:
            player_object.pickup_gold()
        self._board.gold_cells.remove(cell)
        logger.debug("Gold cell %s has been picked up" % str(cell))
        self._board.spawn_gold_cell()

    def _process_drill(self, drill_action: str, player_object: Player):
        logger.debug("Processing %s of %s" % (drill_action, vars(player_object)))
        drill_vector = get_drill_vector(drill_action)
        cell = get_modified_cell(player_object.cell, drill_vector)
        if self._board.is_cell_drillable(cell) and not self._is_cell_in_scenarios(cell):
            self._add_drill_scenario(cell, player_id=player_object.get_id())
        player_object.disallow_action()

    def _add_drill_scenario(self, cell: Tuple, player_id: UUID):
        scenario = deepcopy(DRILL_SCENARIO)
        scenario.reverse()
        if player_id in self._drill_scenarios:
            self._drill_scenarios[player_id].update({cell: scenario})
        else:
            self._drill_scenarios.update({player_id: {cell: scenario}})

    def process_drill_scenario(self):
        logger.debug("Processing drill scenarios ...")
        for player_id, player_scenarios in self._drill_scenarios.items():
            for cell, scenario in player_scenarios.items():
                scenario_cell_type = scenario.pop()
                if not self._is_anyone_in_cell(cell):
                    self._board.update_board(cell, scenario_cell_type)
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
                            self._board.update_board(cell, CellType.HeroDies)

        self._delete_empty_scenarios()

    def _get_player_object_by_pit_cell(self, cell: Tuple):
        for player_id, player_scenarios in self._drill_scenarios.items():
            if cell in player_scenarios:
                return self._get_participant_object_by_id(player_id)

    def _delete_empty_scenarios(self):
        delete_empty_value_keys(self._drill_scenarios)

        for player_id, player_scenarios in self._drill_scenarios.items():
            delete_empty_value_keys(player_scenarios)

    @property
    def score_info(self):
        return {
            player_object.name: player_object.score["permanent"]
            for player_object in self.players
        }

    @property
    def players(self) -> List[Player]:
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
    def guards(self) -> List[Guard]:
        return [p_obj for p_obj in self._participants if p_obj.get_type() == GUARD]

    @property
    def player_clients(self):
        return [
            client
            for _, client in self._clients_info.items()
            if client.client_info["client_type"] == PLAYER
        ]

    def is_player_name_in_registry(self, name: str):
        return name in [player_object.name for player_object in self.players]

    def process_gravity(self):
        logger.debug("Processing Gravity ...")
        for participants_object in self._participants:
            if self._board.can_fall_from_here(participants_object.cell):
                self._process_move(
                    move_action=Move.Down, participant_object=participants_object
                )

    def _get_participant_direction_by_id(self, participant_id: UUID):
        if self._is_participant_id_in_registry(participant_id):
            participant_object = self._get_participant_object_by_id(participant_id)
            return participant_object.get_direction()

    def get_session_info(self, player_id: Optional[UUID] = None) -> Dict[str, Any]:
        cell = self._get_participant_cell_by_id(player_id)
        direction = self._get_participant_direction_by_id(player_id)
        return {
            "board": self._board.get_board_layers(cell=cell, direction=direction),
            "players": {"score": self.score_info, "names": self.players_cells},
            "size": self._board.size,
        }

    def run_admin_command(self, func_name: str, func_args: List):
        if func_name in AdminCommands:
            func = getattr(self, func_name)
            return func(*func_args)
        return "Command is not available"

    @admin_command_decorator
    def check_user_name(self, name: str):
        return name in [participant.name for _, participant in self._registry.items()]

    @admin_command_decorator
    def set_tick_time(self, tick_time: str):
        if not self._is_running:
            try:
                new_tick_time = float(tick_time)
                self._tick_time = new_tick_time
                return "Tick time has been set to %s sec" % new_tick_time
            except ValueError as e:
                return "Could't set tick time: %s" % str(e)

    @admin_command_decorator
    def regenerate_game_board(self, blocks_number=None):
        if not self._is_running:
            try:
                blocks_number = int(blocks_number)
            except ValueError:
                logger.warning(f"Invalid blocks number '{blocks_number}'")
                raise
            else:
                gold_cells_number = len(self._board.gold_cells)
                guards_number = len(self.guards)
                self._board.empty_gold_cells()
                for guard_obj in self.guards:
                    self.unregister_participant(guard_obj.get_id())
                for player in self.player_clients:
                    player.sendClose()
                time.sleep(0.1)
                self._board = GameBoard.from_blocks_number(int(blocks_number))
                for idx in range(guards_number):
                    self.register_participant(uuid4(), f"{GUARD}-{idx}", GUARD)
                self._board.init_gold_cells(gold_cells_number)

    @property
    def _participants(self) -> List[Union[Player, Guard]]:
        return [participant_object for participant_object in self._registry.values()]

    def _update_participant_board_cell(self, participant_obj: BaseParticipant):
        player_cell_type = self._board.get_participant_on_cell_type(
            cell=participant_obj.cell,
            participant_type=participant_obj.get_type(),
            direction=participant_obj.get_direction(),
        )
        self._board.update_board(cell=participant_obj.cell, cell_type=player_cell_type)

    def unregister_participant(self, participant_id):
        participant_cell = self._get_participant_cell_by_id(participant_id)
        self._board.restore_original_cell(participant_cell)
        participant_obj = self._registry.pop(participant_id)
        logger.info(
            "Unregistered {participant_type} '{name}', id: {id}".format(
                participant_type=participant_obj.get_type(),
                name=participant_obj.name,
                id=participant_id,
            )
        )

    def _get_participant_cell_by_id(self, participant_id):
        if self._is_participant_id_in_registry(participant_id):
            participant_object = self._get_participant_object_by_id(participant_id)
            return participant_object.cell

    def _get_participant_object_by_id(self, participant_id):
        if participant_id in self._registry:
            return self._registry[participant_id]
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
                    for player_scenarios in self._drill_scenarios.values()
                ]
            )
        )

    def _get_participant_object_by_cell(self, cell) -> BaseParticipant:
        for participant_object in self._participants:
            if participant_object.cell == cell:
                return participant_object

    def _is_participant_id_in_registry(self, participant_id):
        return participant_id in self._registry

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
# TODO: unify logic of getting into cell
