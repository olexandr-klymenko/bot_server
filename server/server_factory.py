from logging import getLogger
from uuid import uuid1
from time import sleep
from datetime import datetime, timedelta

from autobahn.asyncio.websocket import WebSocketServerFactory

from game_config import *
from common.game_utils import factory_action_decorator, TimeOutExceeded
from game.game_session import LodeRunnerGameSession
from game.game_utils import get_formatted_scores, get_formatted_names


logger = getLogger()


class BroadcastServerFactory(WebSocketServerFactory):
    def __init__(self, url):
        super().__init__(url)
        self.is_locked = False
        self.game_session = LodeRunnerGameSession()
        self.board_size = self.game_session.game_board.size
        self.clients = {}
        self.tick()

    def tick(self):
        if not self.game_session.is_paused():
            self.process_gravity()
            self.play_drill_scenarios()
            self.move_guards()
            self.check_inactivity()
            self.broadcast()
            self.game_session.allow_participants_action()
        self.loop.call_later(self.game_session.tick_time, self.tick)

    @factory_action_decorator
    def broadcast(self):
        logger.debug("Broadcasting data for websocket clients ...")
        for client_id, client in self.clients.items():
            client.sendMessage(self.game_session.get_board_string(client_id).encode('utf8'))

            if client.websocket_origin:
                score_message = get_formatted_scores(self.game_session.scores)
                client.sendMessage(score_message.encode('utf8'))

                players_message = get_formatted_names(self.game_session.players_cells)
                client.sendMessage(players_message.encode('utf8'))

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
        if not self.game_session.is_player_name_in_registry(client.name):
            client_id = uuid1()
            self.clients.update({client_id: client})
            if client.name:
                self.game_session.register_participant(client_id=client_id, name=client.name)
                logger.info("Registered Player '{}', id: '{}', client: '{}'".format(client.name, client_id,
                                                                                    client.peer))
            else:
                logger.info("Registered Spectator client {}, id: '{}'".format(client.peer, client_id))

    @factory_action_decorator
    def unregister(self, client):
        if client in self.clients.values():
            client_id = self.get_client_id(client)
            logger.info("Unregistered client '{}' '{}'".format(client.peer, client_id))
            self.clients.pop(client_id)
            if client.name:
                self.game_session.unregister_participant(client_id)

    @factory_action_decorator
    def process_action(self, client, action):
        if client.name:
            logger.debug("From player '{player}', id: '{id}' received action '{action}'".
                         format(action=action,
                                player=client.name,
                                id=self.game_session.get_participant_id_by_name(client.name)))
            self.game_session.process_action(action=action, player_id=self.get_client_id(client))

    def get_client_id(self, client):
        return dict(zip(self.clients.values(), self.clients.keys()))[client]

    @factory_action_decorator
    def move_guards(self):
        logger.debug("Moving Guards ...")
        self.game_session.move_guards()

    @factory_action_decorator
    def play_drill_scenarios(self):
        logger.debug("Playing Drill scenarios ...")
        self.game_session.process_drill_scenario()

    def lock_game_server(self):
        timeout = 0
        while self.is_locked:
            sleep(WAIT_FREE_CELL_TICK)
            timeout += WAIT_FREE_CELL_TICK
            if timeout > STOP_WAIT_FREE_CELL_TIMEOUT:
                raise TimeOutExceeded("Game Server Lock Timeout has been exceeded")
        self.is_locked = True
        logger.debug("Game server is locked")

    def unlock_game_server(self):
        self.is_locked = False
        logger.debug("Game server is unlocked")
