import json
from autobahn.asyncio import WebSocketServerProtocol
from autobahn.asyncio.websocket import WebSocketServerFactory
from datetime import datetime
from functools import wraps
from logging import getLogger
from uuid import uuid1

from common.utils import PLAYER, GUARD, SPECTATOR, ADMIN
from game.game_session import LodeRunnerGameSession

logger = getLogger()


def factory_action_decorator(func):
    @wraps(func)
    def wrapper(factory, *args, **kwargs):
        start_time = datetime.now()
        func(factory, *args, **kwargs)
        execution_time = datetime.now() - start_time
        logger.debug("%s execution time: %s" % (func.__name__, execution_time))

    return wrapper


class BroadcastServerFactory(WebSocketServerFactory):
    game_session: LodeRunnerGameSession = None

    def __init__(self, url):
        super().__init__(url)
        self.clients_info = {}
        self.admin_client = None
        logger.info('Lode Runner game server has been initialized')

    @property
    def spectators(self):
        return [value for key, value in self.clients_info.items() if value.client_info['client_type'] == SPECTATOR]

    def broadcast(self, client_types=(SPECTATOR, PLAYER, GUARD)):
        logger.debug("Broadcasting data for websocket clients ...")
        for client_id, client in self.clients_info.items():
            if client.client_info['client_type'] in client_types:
                client.sendMessage(json.dumps(self.game_session.get_session_info(client_id)).encode())

    @factory_action_decorator
    def register_client(self, client):
        if client.client_info['client_type'] == ADMIN:
            self._register_admin_client(client)
        else:
            self._register_non_admin_client(client)

    def _register_admin_client(self, client):
        if self.admin_client and client.client_info['name'] != self.admin_client.client_info['name']:
            logger.warning("Admin client has been already registered")
            return

        self.admin_client = client
        logger.info(f"Registered Admin client {client.peer}")
        self.admin_client.sendMessage(json.dumps(self.game_info).encode())

    @property
    def game_info(self):
        return {
            'guards': len(self.guard_clients),
            'gold': len(self.game_session.gold_cells),
            'players': [client.client_info['name'] for client in self.player_clients],
            'started': not self.game_session.is_paused,
            'size': self.game_session.game_board.blocks_number
        }

    @property
    def guard_clients(self):
        return [client for _, client in self.clients_info.items() if client.client_info['client_type'] == GUARD]

    @property
    def player_clients(self):
        return [client for _, client in self.clients_info.items() if client.client_info['client_type'] == PLAYER]

    def _register_non_admin_client(self, client):
        client_id = uuid1()
        self.clients_info.update({client_id: client})
        if self.game_session.is_player_name_in_registry(client.client_info['name']):
            logger.error("Client with id % is already registered")
            return

        if client.client_info['client_type'] == SPECTATOR:
            logger.info(f"Registered Spectator client {client.peer}, id: '{client_id}'")
            client.sendMessage(json.dumps(self.game_session.get_session_info(client_id)).encode())
            return

        if client.client_info['client_type'] in [PLAYER, GUARD]:
            self.game_session.register_participant(client_id=client_id, name=client.client_info['name'],
                                                   participant_type=client.client_info['client_type'])
            logger.info(f"Registered {client.client_info['client_type']} '{client.client_info['name']}',"
                        f" id: '{client_id}', client: '{client.peer}'")
            for client in self.spectators:
                client.sendMessage(json.dumps(self.game_session.get_session_info(client_id)).encode())

        if self.admin_client is not None:
            self.admin_client.sendMessage(json.dumps(self.game_info).encode())

    @factory_action_decorator
    def unregister(self, client):
        if client in self.clients_info.values():
            client_id = self.get_client_id(client)
            logger.info("Unregistered client '{}' '{}'".format(client.peer, client_id))
            self.clients_info.pop(client_id)
            if not client.client_info['client_type'] == SPECTATOR:
                self.game_session.unregister_participant(client_id)
                for client in self.spectators:
                    client.sendMessage(json.dumps(self.game_session.get_session_info(client_id)).encode())

                if self.admin_client:
                    self.admin_client.sendMessage(json.dumps(self.game_info).encode())

    @factory_action_decorator
    def process_message(self, client, message):
        logger.debug("From {participant} '{name}', id: '{id}' received action '{action}'".
                     format(participant=client.client_info['client_type'],
                            action=message,
                            name=client.client_info['name'],
                            id=self.game_session.get_participant_id_by_name(client.client_info['name'])))

        self.game_session.process_action(action=message, player_id=self.get_client_id(client))

    def get_client_id(self, client):
        return dict(zip(self.clients_info.values(), self.clients_info.keys()))[client]


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
            return {'client_type': self.http_request_params['client_type'][0],
                    'name': self.http_request_params['name'][0]}
        return {'client_type': SPECTATOR, 'name': ''}
