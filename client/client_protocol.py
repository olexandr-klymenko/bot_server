import json
from itertools import chain
from logging import getLogger
from random import choice

from autobahn.asyncio.websocket import WebSocketClientProtocol

from game.cell_types import CellType, CellGroups, CELL_TYPE_COERCION
from common.utils import PLAYER, GUARD
from game.game_board import LodeRunnerGameBoard
from game.game_utils import get_joints_info
from game.move_types import Move

logger = getLogger()


class LodeRunnerClientProtocol(WebSocketClientProtocol):
    target_cell_types = None
    initial_game_board = None
    joints_info = None
    path_finder_klas = None

    @property
    def name(self):
        return self.factory.params['name'][0]

    @property
    def client_type(self):
        return self.factory.params['client_type'][0]

    def onConnect(self, response):
        logger.info("'{user}' has been connected to server {server}".format(user=self.name, server=response.peer))
        if self.client_type == PLAYER:
            self.target_cell_types = [CellType.Gold]
        elif self.client_type == GUARD:
            self.target_cell_types = CellGroups.PlayerCellTypes
        else:
            raise Exception

    def onMessage(self, payload, isBinary):
        if not isBinary:
            board_layers = json.loads(payload.decode())['board']
            self.initial_game_board = self.initial_game_board or LodeRunnerGameBoard(
                get_coerced_board_layers(board_layers)
            )
            self.joints_info = self.joints_info or get_joints_info(
                self.initial_game_board.board_info, self.initial_game_board.size
            )
            self.path_finder_klas = self.path_finder_klas or path_finder_factory(self.joints_info,
                                                                                 self.target_cell_types
                                                                                 )
            path_finder = self.path_finder_klas(board_layers)
            logger.debug("My cell: %s" % str(path_finder.my_cell))
            logger.debug("Gold cells: %s" % path_finder.target_cells)
            action = path_finder.get_routed_move_action()
            self.sendMessage(bytes(action.encode()))
            logger.info(f"'{self.name}' has sent message: '{action}'")

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection of '{user}' closed: {reason}".format(user=self.name, reason=reason))


def get_coerced_board_layers(board_layers):
    coerced = []
    for board_layer in board_layers:
        coerced.append([CELL_TYPE_COERCION.get(cell_code, cell_code) for cell_code in board_layer])
    return coerced


def path_finder_factory(joints_info, target_cell_types):

    class ClientPathFinder:
        joints_info = None
        target_cell_types = None

        def __init__(self, board_layers):
            self.game_board = LodeRunnerGameBoard(board_layers)
            self.my_cell, self.target_cells = self.my_cell_and_gold()

        def my_cell_and_gold(self):
            gold_cells = []
            my_cell = None
            for cell, cell_code in self.game_board.board_info.items():
                if cell_code in CellGroups.HeroCellTypes:
                    my_cell = cell
                elif cell_code in self.target_cell_types:
                    gold_cells.append(cell)
            if my_cell is None:
                raise Exception("Couldn't find my cell")
            return my_cell, gold_cells

        def get_routed_move_action(self):
            if self.target_cells:
                wave_age_info = get_wave_age_info(self.my_cell, self.joints_info)
                next_cell = get_route(self.target_cells, wave_age_info, self.joints_info)

                if next_cell:
                    return get_move_action(self.my_cell, next_cell)
                elif self.joints_info[self.my_cell]:
                    return get_move_action(self.my_cell, choice(self.joints_info[self.my_cell]))

            return choice(Move.get_valid_codes())

    ClientPathFinder.joints_info = joints_info
    ClientPathFinder.target_cell_types = target_cell_types
    return ClientPathFinder


def get_wave_age_info(start_cell, joints_info):
    wave_info = {}
    wave_age = 1
    joints = joints_info[start_cell]
    while joints:
        wave_info.update({cell: wave_age for cell in joints})
        joints = set(list(chain(*[joints_info[cell] for cell in joints])))
        joints = joints - set(wave_info.keys())
        wave_age += 1
    return wave_info


def get_route(target_cells, wave_age_info, joints_info):
    target_candidates = [cell for cell in target_cells if cell in wave_age_info]
    if target_candidates:
        target_cell = min(target_candidates, key=lambda x: wave_age_info[x])
        wave_age = wave_age_info[target_cell]
        while wave_age > 1:
            wave_age -= 1
            target_cell = choice([cell for cell in wave_age_info.keys()
                                  if wave_age_info[cell] == wave_age and target_cell in joints_info[cell]])
        return target_cell


def get_move_action(start_cell, end_cell):
    if end_cell[0] - start_cell[0] == 1:
        return Move.Right
    if end_cell[0] - start_cell[0] == -1:
        return Move.Left
    if end_cell[1] - start_cell[1] == 1:
        return Move.Down
    return Move.Up
