import json
from datetime import datetime, timedelta
from functools import wraps
from uuid import uuid1

from autobahn.asyncio.websocket import WebSocketServerFactory

from game.cell_types import SPECTATOR, PLAYER, GUARD
from game.game_session import LodeRunnerGameSession
from game.game_utils import logger

INACTIVITY_TIMEOUT = 100 * 60


def factory_action_decorator(func):
    @wraps(func)
    def wrapper(factory, *args, **kwargs):
        start_time = datetime.now()
        func(factory, *args, **kwargs)
        execution_time = datetime.now() - start_time
        logger.debug("%s execution time: %s" % (func.__name__, execution_time))

    return wrapper


class BroadcastServerFactory(WebSocketServerFactory):

    def __init__(self, url):
        super().__init__(url)
        self.is_locked = False
        self.game_session = LodeRunnerGameSession()
        self.board_size = self.game_session.game_board.size
        self.clients = {}
        self.tick()
        logger.info('Lode Runner game server has been initialized')

    def tick(self):
        if not self.game_session.is_paused():
            start_time = datetime.now()
            self.process_gravity()
            self.play_drill_scenarios()
            self.check_inactivity()
            self.broadcast()
            self.game_session.allow_participants_action()
            execution_time = datetime.now() - start_time
            logger.debug("Tick execution time: %s" % execution_time)
        self.loop.call_later(self.game_session.tick_time, self.tick)

    @factory_action_decorator
    def broadcast(self):
        logger.debug("Broadcasting data for websocket clients ...")
        for client_id, client in self.clients.items():
            client.sendMessage(json.dumps(self.game_session.get_session_info(client_id)).encode())

    def check_inactivity(self):
        for client_id, client in self.clients.items():
            if datetime.now() - client.latest_activity_time > timedelta(seconds=INACTIVITY_TIMEOUT):
                if client_id in self.game_session.registry:
                    self.unregister(client)
                    logger.info("Player '%s' has been disconnected by inactivity" % client_id)

    @factory_action_decorator
    def process_gravity(self):
        self.game_session.process_gravity()

    @factory_action_decorator
    def register_client(self, client):
        client_id = uuid1()
        self.clients.update({client_id: client})
        if client.client_info['client_type'] == SPECTATOR:
            logger.info("Registered Spectator client {}, id: '{}'".format(client.peer, client_id))
        elif self.game_session.is_player_name_in_registry(client.client_info['name']):
            logger.error("Client with id % is already registered")
        elif client.client_info['client_type'] in [PLAYER, GUARD]:
            self.game_session.register_participant(client_id=client_id, name=client.client_info['name'],
                                                   participant_type=client.client_info['client_type'])
            logger.info("Registered {} '{}', id: '{}', client: '{}'".format(client.client_info['client_type'],
                                                                            client.client_info['name'],
                                                                            client_id, client.peer))

    @factory_action_decorator
    def unregister(self, client):
        if client in self.clients.values():
            client_id = self.get_client_id(client)
            logger.info("Unregistered client '{}' '{}'".format(client.peer, client_id))
            self.clients.pop(client_id)
            if not client.client_info['client_type'] == SPECTATOR:
                self.game_session.unregister_participant(client_id)

    @factory_action_decorator
    def process_action(self, client, action):
        if not client.client_info['client_type'] == SPECTATOR:
            logger.debug("From {participant} '{name}', id: '{id}' received action '{action}'".
                         format(participant=client.client_info['client_type'],
                                action=action,
                                name=client.client_info['name'],
                                id=self.game_session.get_participant_id_by_name(client.client_info['name'])))
            self.game_session.process_action(action=action, player_id=self.get_client_id(client))

    def get_client_id(self, client):
        return dict(zip(self.clients.values(), self.clients.keys()))[client]

    @factory_action_decorator
    def play_drill_scenarios(self):
        logger.debug("Playing Drill scenarios ...")
        self.game_session.process_drill_scenario()
