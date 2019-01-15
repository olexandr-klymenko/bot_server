import re
from autobahn.asyncio.websocket import WebSocketClientProtocol
from logging import getLogger
from random import choice

from game.game_board import BOARD_STRING_HEADER
from game.game_utils import get_wave_age_info, get_route, get_move_action
from game.move_types import Move
from game.cell_types import *
from game.game_board import LodeRunnerGameBoard

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
            board_string = re.sub(BOARD_STRING_HEADER, '', payload.decode())
            path_finder = ClientPathFinder(board_string, target_cell_types)
            logger.debug("My cell: %s" % str(path_finder.my_cell))
            logger.debug("Gold cells: %s" % path_finder.target_cells)
            action = path_finder.get_routed_move_action()
            self.sendMessage(bytes(action.encode()))
            logger.info(f"'{self.name}' has sent message: '{action}'")

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection of '{user}' closed: {reason}".format(user=self.name, reason=reason))


def get_coerced_board_string(board_string):
    coerced = ''
    for cell_char in board_string:
        coerced += CELL_TYPE_COERCION.get(cell_char, cell_char)
    return coerced


class ClientPathFinder:

    def __init__(self, board_string, target_cell_types):
        super().__init__()
        self.pure_game_board = LodeRunnerGameBoard(get_coerced_board_string(board_string))
        self.game_board = LodeRunnerGameBoard(board_string)
        self.my_cell, self.target_cells = self.my_cell_and_gold(target_cell_types)

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
            joints_info = self.pure_game_board.joints_info
            wave_age_info = get_wave_age_info(self.my_cell, joints_info)
            next_cell = get_route(self.target_cells, wave_age_info, joints_info)

            if next_cell:
                return get_move_action(self.my_cell, next_cell)
            elif joints_info[self.my_cell]:
                return get_move_action(self.my_cell, choice(joints_info[self.my_cell]))

        return choice(Move.get_valid_codes())
