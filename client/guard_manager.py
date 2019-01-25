import asyncio
from logging import getLogger
import json
from uuid import uuid4

from autobahn.asyncio.websocket import WebSocketClientFactory
from autobahn.asyncio.websocket import WebSocketClientProtocol

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
            logger.info(f'Incoming message to guard manager: {payload}')
            requested_guards_number = json.loads(payload)
            logger.info(f"Requested guards number: {requested_guards_number}, actual: {len(self.guards_tasks)}")
            if requested_guards_number > len(self.guards_tasks):
                logger.info('Running guard ...')
                self.run_guard()
            else:
                logger.info('')

    def run_guard(self):
        loop = asyncio.get_event_loop()
        setup_logging('INFO')

        guard_factory = GameClientFactory(
            url=f'ws://127.0.0.1:{GAME_SERVER_WEB_SOCKET_PORT}',
            client_type=GUARD,
            name=uuid4()
        )
        task = loop.create_connection(guard_factory, '127.0.0.1', GAME_SERVER_WEB_SOCKET_PORT)
        loop.run_until_complete(task)
        self.guards_tasks.append(task)

# TODO: Finish Guard Manager
