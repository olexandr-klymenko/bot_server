import json
from itertools import chain
from logging import getLogger
from random import choice

from autobahn.asyncio.websocket import WebSocketClientProtocol

from game.cell_types import PLAYER, GUARD, CellType, CellGroups, CELL_TYPE_COERCION
from game.game_board import LodeRunnerGameBoard
from game.move_types import Move
from game.game_utils import get_joints_info

logger = getLogger()


class LodeRunnerClientProtocol(WebSocketClientProtocol):

    @property
    def name(self):
        return self.factory.params['name'][0]

    @property
    def client_type(self):
        return self.factory.params['client_type'][0]

    def onConnect(self, response):
        logger.info("'{user}' has been connected to server {server}".format(user=self.name, server=response.peer))

    def onMessage(self, payload, isBinary):
        if not isBinary:
            if self.client_type == PLAYER:
                target_cell_types = [CellType.Gold]
            elif self.client_type == GUARD:
                target_cell_types = CellGroups.PlayerCellTypes
            else:
                raise Exception

            board_string = json.loads(payload.decode())['board']
            path_finder = ClientPathFinder(board_string, target_cell_types)
            logger.debug("My cell: %s" % str(path_finder.my_cell))
            logger.debug("Gold cells: %s" % path_finder.target_cells)
            action = path_finder.get_routed_move_action()
            self.sendMessage(bytes(action.encode()))
            logger.info(f"'{self.name}' has sent message: '{action}'")

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection of '{user}' closed: {reason}".format(user=self.name, reason=reason))


def get_coerced_board_string(board_layers):
    coerced = []
    for board_layer in board_layers:
        coerced.append(''.join([CELL_TYPE_COERCION.get(cell_code, cell_code) for cell_code in board_layer]))
    return coerced


class ClientPathFinder:

    def __init__(self, board_string, target_cell_types):
        board_layers = [board_string[i:i+27] for i in range(0, len(board_string), 27)]
        self.game_board = LodeRunnerGameBoard(board_layers)
        self.initial_game_board = LodeRunnerGameBoard(get_coerced_board_string(board_layers))
        self.my_cell, self.target_cells = self.my_cell_and_gold(target_cell_types)
        self.joints_info = get_joints_info(self.initial_game_board.board_info, self.initial_game_board.size)

    def my_cell_and_gold(self, target_cell_types):
        gold_cells = []
        my_cell = None
        for cell, cell_code in self.game_board.board_info.items():
            if cell_code in CellGroups.HeroCellTypes:
                my_cell = cell
            elif cell_code in target_cell_types:
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
