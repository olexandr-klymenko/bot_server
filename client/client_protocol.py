import re
from autobahn.asyncio.websocket import WebSocketClientProtocol
from logging import getLogger
from random import choice

from common.game_board import BOARD_STRING_HEADER
from common.game_utils import get_wave_age_info, get_route, get_move_action
from common.move_types import Move
from game.cell_types import *
from game.game_board import LodeRunnerGameBoard

logger = getLogger()


class BroadcastClientProtocol(WebSocketClientProtocol):

    @property
    def name(self):
        return self.factory.params['user'][0]

    def onConnect(self, response):
        logger.info("'{user}' has been connected to server {server}".format(user=self.name, server=response.peer))

    def onMessage(self, payload, isBinary):
        if not isBinary:
            board_string = re.sub(BOARD_STRING_HEADER, '', payload.decode())
            game_session = ClientGameSession(board_string)
            logger.debug("My cell: %s" % str(game_session.my_cell))
            logger.debug("Gold cells: %s" % game_session.gold_cells)
            move = game_session.get_routed_move_action()
            # move = choice(Move.get_valid_codes() + Drill.get_valid_codes())
            self.sendMessage(bytes(move.encode('utf8')))
            logger.info("'{user}' has sent message: '{message}'".format(user=self.name, message=move))

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection of '{user}' closed: {reason}".format(user=self.name, reason=reason))


def get_coerced_board_string(board_string):
    coerced = ''
    for cell_char in board_string:
        coerced += CELL_TYPE_COERCION.get(cell_char, cell_char)
    return coerced


class ClientGameSession:

    def __init__(self, board_string):
        super().__init__()
        self.pure_game_board = LodeRunnerGameBoard(get_coerced_board_string(board_string))
        self.game_board = LodeRunnerGameBoard(board_string)
        self.my_cell, self.gold_cells = self.my_cell_and_gold()

    def my_cell_and_gold(self):
        gold_cells = []
        my_cell = None
        for cell, cell_code in self.game_board.board_info.items():
            if cell_code in CellGroups.HeroCellTypes:
                my_cell = cell
            elif cell_code == CellType.Gold:
                gold_cells.append(cell)
        if my_cell is None:
            raise Exception("Couldn't find my cell")
        return my_cell, gold_cells

    def get_routed_move_action(self):
        if self.gold_cells:
            joints_info = self.pure_game_board.joints_info
            wave_age_info = get_wave_age_info(self.my_cell, joints_info)
            next_cell = get_route(self.gold_cells, wave_age_info, joints_info)

            if next_cell:
                return get_move_action(self.my_cell, next_cell)
            elif joints_info[self.my_cell]:
                return get_move_action(self.my_cell, choice(joints_info[self.my_cell]))

        return choice(Move.get_valid_codes())
