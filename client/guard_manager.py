import asyncio
import gc

import json
from autobahn.asyncio.websocket import WebSocketClientFactory
from autobahn.asyncio.websocket import WebSocketClientProtocol
from logging import getLogger
from uuid import uuid4

from client.client_factory import GameClientFactory
from common.utils import GUARD_MANAGER, GUARD
from utils.configure_logging import setup_logging

logger = getLogger()

GAME_SERVER_WEB_SOCKET_URL = "ws://0.0.0.0"
GAME_SERVER_WEB_SOCKET_PORT = 9000


class GuardManagerClientFactory(WebSocketClientFactory):
    def __init__(self, url):
        super().__init__(f'{url}?client_type={GUARD_MANAGER}&name={uuid4()}')
        self.protocol = GuardManagerClientProtocol


class GuardManagerClientProtocol(WebSocketClientProtocol):
    guards_tasks = []

    def onConnect(self, response):
        logger.info(f"Connected to WebSocket: {response.peer}")

    def onMessage(self, payload, isBinary):
        if not isBinary:
            requested_guards_number = json.loads(payload)
            if requested_guards_number != len(self.guards_tasks):
                logger.info(f'Destroying {len(self.guards_tasks)} guards ...')
                self.sendMessage(b'Destroy guards')
                self.guards_tasks = []
                gc.collect()
                logger.info(f'Spawning {requested_guards_number} guards ...')
                for idx in range(requested_guards_number):
                    self.guards_tasks.append(run_guard())
                asyncio.gather(*self.guards_tasks)
            else:
                logger.info('Guards number remains unchanged')


def run_guard():
    loop = asyncio.get_event_loop()
    setup_logging('INFO')

    guard_factory = GameClientFactory(
        url=f'{GAME_SERVER_WEB_SOCKET_URL}:{GAME_SERVER_WEB_SOCKET_PORT}',
        client_type=GUARD,
        name=uuid4()
    )
    return loop.create_connection(guard_factory, '127.0.0.1', GAME_SERVER_WEB_SOCKET_PORT)
