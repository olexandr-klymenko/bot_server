from logging import getLogger

from autobahn.asyncio.websocket import WebSocketClientFactory
from autobahn.asyncio.websocket import WebSocketClientProtocol

logger = getLogger()


class GameClientFactory(WebSocketClientFactory):
    def __init__(self, url, client_type, name):
        self.name = name
        self.client_type = client_type
        super().__init__(f'{url}?client_type={client_type}&name={name}')
        self.protocol = GuardManagerClientProtocol


class GuardManagerClientProtocol(WebSocketClientProtocol):
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

    def onMessage(self, payload, isBinary):
        if not isBinary:
            pass

    def onClose(self, wasClean, code, reason):
        logger.info("WebSocket connection of '{user}' closed: {reason}".format(user=self.name, reason=reason))


# TODO: Finish Guard Manager
# TODO: Try to split websocket for players/guards/spectator from admin/guard_manager
