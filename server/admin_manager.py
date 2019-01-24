import json
from datetime import datetime
from functools import wraps
from logging import getLogger

from autobahn.asyncio.websocket import WebSocketServerFactory
from autobahn.asyncio.websocket import WebSocketServerProtocol

from common.utils import PLAYER, GUARD
from game.game_session import LodeRunnerGameSession

logger = getLogger()


class AdminServerProtocol(WebSocketServerProtocol):

    def onOpen(self):
        self.factory.register_client(self)

    def onMessage(self, payload, isBinary):
        self.factory.process_message(self, payload.decode())

    def onClose(self, wasClean, code, reason):
        super(AdminServerProtocol, self).onClose(wasClean, code, reason)
        self.factory.unregister(self)


def factory_action_decorator(func):
    @wraps(func)
    def wrapper(factory, *args, **kwargs):
        start_time = datetime.now()
        func(factory, *args, **kwargs)
        execution_time = datetime.now() - start_time
        logger.debug("%s execution time: %s" % (func.__name__, execution_time))

    return wrapper


class AdminServerFactory(WebSocketServerFactory):
    game_session: LodeRunnerGameSession = None

    def __init__(self, url):
        super().__init__(url)
        self.admin_client = None

    @factory_action_decorator
    def register_client(self, client):
        if self.admin_client:
            logger.warning("Admin client has been already registered")
            return

        self.admin_client = client
        logger.info(f"Registered Admin client {client.peer}")
        self.admin_client.sendMessage(json.dumps(self.game_info).encode())

    def unregister(self, _):
        self.admin_client = None

    @property
    def game_info(self):
        guards = 0
        players = []
        for _, client in self.game_session.clients_info.items():
            if client.client_info['client_type'] == GUARD:
                guards += 1
            if client.client_info['client_type'] == PLAYER:
                players.append(client.client_info['name'])
        return {
            'guards': guards,
            'players': players,
            'started': not self.game_session.is_paused,
            'size': self.game_session.blocks_number
        }

    @factory_action_decorator
    def process_message(self, _, message):
        self.game_session.run_admin_command(message['command'], message['args'])
