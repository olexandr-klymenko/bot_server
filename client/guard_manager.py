import asyncio
import sys

import json
import subprocess
from autobahn.asyncio.websocket import WebSocketClientFactory
from autobahn.asyncio.websocket import WebSocketClientProtocol
from logging import getLogger
from uuid import uuid4

from common.utils import GUARD_MANAGER

logger = getLogger()
logger.level = 'DEBUG'

GAME_SERVER_WEB_SOCKET_URL = "ws://0.0.0.0"
GAME_SERVER_WEB_SOCKET_PORT = 9000


class GuardManagerClientFactory(WebSocketClientFactory):
    def __init__(self, url):
        super().__init__(f'{url}?client_type={GUARD_MANAGER}&name={uuid4()}')
        self.protocol = GuardManagerClientProtocol


class GuardManagerClientProtocol(WebSocketClientProtocol):
    guards_number = 0

    def onConnect(self, response):
        logger.info(f"Connected to WebSocket: {response.peer}")

    def onMessage(self, payload, isBinary):
        if not isBinary:
            requested_guards_number = json.loads(payload)
            if requested_guards_number != self.guards_number:
                if self.guards_number:
                    logger.info(f'Destroying {self.guards_number} guards ...')

                if requested_guards_number:
                    logger.info(f'Spawning {requested_guards_number} guards ...')
                    for _ in range(requested_guards_number):
                        try:
                            completed = subprocess.run(['python', 'guard_runner.py'],
                                           shell=True,
                                           stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE
                                           )
                        except Exception as err:
                            print('ERROR:', err)
                        finally:
                            print('returncode:', completed.returncode)
                            print('Have {} bytes in stdout: {!r}'.format(
                                len(completed.stdout),
                                completed.stdout.decode('utf-8'))
                            )
                            print('Have {} bytes in stderr: {!r}'.format(
                                len(completed.stderr),
                                completed.stderr.decode('utf-8'))
                            )
            else:
                logger.info('Guards number remains unchanged')

    def connection_lost(self, exc):
        logger.info(f"WebSocket connection lost")
        asyncio.get_event_loop().stop()
