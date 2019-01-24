from logging import getLogger
from uuid import uuid4

from autobahn.asyncio.websocket import WebSocketClientFactory
from autobahn.asyncio.websocket import WebSocketClientProtocol

from common.utils import GUARD_MANAGER

logger = getLogger()


class GuardManagerClientFactory(WebSocketClientFactory):
    def __init__(self, url):
        super().__init__(f'{url}?client_type={GUARD_MANAGER}&name={uuid4()}')
        self.protocol = GuardManagerClientProtocol


class GuardManagerClientProtocol(WebSocketClientProtocol):

    def onMessage(self, payload, isBinary):
        if not isBinary:
            logger.info(f'Incoming message to guard manager: {payload}')


# TODO: Finish Guard Manager
# TODO: Try to split websocket for players/guards/spectator from admin/guard_manager
