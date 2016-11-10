from logging import getLogger
from random import choice
import re

from autobahn.asyncio.websocket import WebSocketClientProtocol

from common.move_types import Move
from game.game_utils import Drill
from common.game_board import BOARD_STRING_HEADER
from common.game_session import GameSession
from game.game_board import LodeRunnerGameBoard
from game.cell_types import *


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
            my_cell, gold_cells = game_session.my_cell_and_gold
            logger.debug("My cell: %s" % str(my_cell))
            logger.debug("Gold cells: %s" % gold_cells)
            move = game_session.get_routed_move_action(my_cell, gold_cells)
            # move = choice(Move.get_valid_codes() + Drill.get_valid_codes())
            self.sendMessage(bytes(move.encode('utf8')))
            logger.info("'{user}' has sent message: '{message}'".format(user=self.name, message=move))

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection of '{user}' closed: {reason}".format(user=self.name, reason=reason))


class ClientGameSession(GameSession):
    def __init__(self, board_string):
        super().__init__()
        self.game_board = LodeRunnerGameBoard(board_string)

    @property
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
