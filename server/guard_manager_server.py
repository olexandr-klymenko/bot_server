import asyncio
import gc

import json
from autobahn.asyncio.websocket import WebSocketServerFactory
from autobahn.asyncio.websocket import WebSocketServerProtocol
from logging import getLogger
from uuid import uuid4

from client.game_client import GameClientFactory
from common.utils import GUARD
from utils.configure_logging import setup_logging

logger = getLogger()

GAME_SERVER_WEB_SOCKET_URL = "ws://0.0.0.0"
GAME_SERVER_WEB_SOCKET_PORT = 9000


class GuardManagerServerFactory(WebSocketServerFactory):
    def __init__(self, url):
        super().__init__(url)
        logger.info('Lode Runner guard manager server has been initialized')


class GuardManagerServerProtocol(WebSocketServerProtocol):
    guards_tasks = []
    guard_objects = []

    def onMessage(self, payload, isBinary):
        if not isBinary:
            requested_guards_number = json.loads(payload)
            if requested_guards_number != len(self.guards_tasks):
                logger.info(f'Destroying {len(self.guards_tasks)} guards ...')
                for factory in self.guard_objects:
                    factory.client.sendClose()
                self.guards_tasks = []
                self.guard_objects = []
                gc.collect()
                if requested_guards_number:
                    logger.info(f'Spawning {requested_guards_number} guards ...')
                    for idx in range(requested_guards_number):
                        self.guards_tasks.append(self.run_guard())
                    asyncio.gather(*self.guards_tasks)
            else:
                logger.info('Guards number remains unchanged')

    def run_guard(self):
        loop = asyncio.get_event_loop()
        setup_logging('INFO')
        guard_factory = GameClientFactory(
            url=f'{GAME_SERVER_WEB_SOCKET_URL}:{GAME_SERVER_WEB_SOCKET_PORT}',
            client_type=GUARD,
            name=uuid4()
        )
        self.guard_objects.append(guard_factory)
        return loop.create_connection(guard_factory, '127.0.0.1', GAME_SERVER_WEB_SOCKET_PORT)
