from datetime import datetime
from logging import getLogger

from autobahn.asyncio.websocket import WebSocketServerProtocol

from game.cell_types import SPECTATOR, ADMIN

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
        if ADMIN in self.http_request_params['client_type']:
            return {'client_type': ADMIN, 'name': hash(self.http_headers['user-agent'])}
        if 'name' in self.http_request_params:
            return {'client_type': self.http_request_params['client_type'][0], 'name': self.http_request_params['name'][0]}
        return {'client_type': SPECTATOR, 'name': ''}
