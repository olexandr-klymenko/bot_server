from logging import getLogger
from random import choice

from autobahn.asyncio.websocket import WebSocketClientProtocol

from common.move_types import Move
from game.game_utils import Drill


logger = getLogger()


class BroadcastClientProtocol(WebSocketClientProtocol):

    @property
    def user(self):
        return self.factory.params['user'][0]

    def onConnect(self, response):
        logger.info("'{user}' has been connected to server {server}".format(user=self.user, server=response.peer))

    def onMessage(self, payload, isBinary):
        if not isBinary:
            move = choice(Move.get_valid_codes() + Drill.get_valid_codes())
            self.sendMessage(bytes(move.encode('utf8')))
            logger.info("'{user}' has sent message: '{message}'".format(user=self.user, message=move))

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection of '{user}' closed: {reason}".format(user=self.user, reason=reason))
