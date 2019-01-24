from logging import getLogger

from autobahn.asyncio.websocket import WebSocketServerProtocol

from common.utils import SPECTATOR, ADMIN

logger = getLogger()


class BroadcastServerProtocol(WebSocketServerProtocol):

    def onOpen(self):
        self.factory.register_client(self)

    def onMessage(self, payload, isBinary):
        self.factory.process_message(self, payload.decode())

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
