from logging import getLogger
from datetime import datetime

from autobahn.asyncio.websocket import WebSocketServerProtocol

from game.cell_types import PLAYER, GUARD, SPECTATOR

logger = getLogger()


class BroadcastServerProtocol(WebSocketServerProtocol):

    def __init__(self):
        super(BroadcastServerProtocol, self).__init__()
        self.latest_activity_time = datetime.now()

    def onOpen(self):
        self.factory.register_client(self)

    def onMessage(self, payload, isBinary):
        self.latest_activity_time = datetime.now()
        self.factory.process_action(self, payload.decode())

    def onClose(self, wasClean, code, reason):
        super(BroadcastServerProtocol, self).onClose(wasClean, code, reason)
        self.factory.unregister(self)

    @property
    def client_info(self):
        if 'user' in self.http_request_params:
            return {'client_type': PLAYER, 'name': self.http_request_params['user'][0]}
        if 'guard' in self.http_request_params:
            return {'client_type': GUARD, 'name': self.http_request_params['guard'][0]}
        return {'client_type': SPECTATOR, 'name': ''}
