import asyncio

import json
from autobahn.asyncio import WebSocketClientFactory
from autobahn.asyncio.websocket import WebSocketClientProtocol
from logging import getLogger
from random import choice
from typing import Dict

from common.utils import (PLAYER, GUARD, CellType, get_board_info, Move, CellGroups,
                          CELL_TYPE_COERCION, get_global_wave_age_info, get_joints_info, get_next_target_age)

logger = getLogger()


class GameClientFactory(WebSocketClientFactory):
    def __init__(self, url, client_type, name):
        self.name = name
        self.client_type = client_type
        super().__init__(f'{url}?client_type={client_type}&name={name}')
        self.protocol = LodeRunnerClientProtocol
        self.client = None


class LodeRunnerClientProtocol(WebSocketClientProtocol):
    target_cell_types = None
    board_info = None
    joints_info = None
    path_finder_cls = None

    @property
    def name(self):
        return self.factory.params['name'][0]

    @property
    def client_type(self):
        return self.factory.params['client_type'][0]

    def onConnect(self, response):
        logger.info(f"'{self.name}' has been connected to server {response.peer}")
        self.factory.client = self
        if self.client_type == PLAYER:
            self.target_cell_types = [CellType.Gold]
        elif self.client_type == GUARD:
            self.target_cell_types = CellGroups.PlayerCellTypes
        else:
            raise Exception

    def onMessage(self, payload, isBinary):
        if not isBinary:
            message = json.loads(payload.decode())

            board_layers = message['board']

            self.board_info = self.board_info or get_board_info(get_coerced_board_layers(board_layers))

            self.joints_info = self.joints_info or get_joints_info(self.board_info)

            self.path_finder_cls = self.path_finder_cls or path_finder_factory(self.joints_info,
                                                                               self.target_cell_types,
                                                                               self.board_info)

            path_finder = self.path_finder_cls(board_layers)
            action = path_finder.get_routed_move_action()
            self.sendMessage(bytes(action.encode()))
            logger.debug(f"'{self.name}' has sent message: '{action}'")

    def onClose(self, wasClean, code, reason):
        logger.info(f"WebSocket connection of '{self.name}' closed: {reason}")
        raise ConnectionRefusedError

    def connection_lost(self, exc):
        logger.info(f"WebSocket connection lost")
        asyncio.get_event_loop().stop()


def get_coerced_board_layers(board_layers):
    coerced = []
    for board_layer in board_layers:
        coerced.append([CELL_TYPE_COERCION.get(cell_code, cell_code) for cell_code in board_layer])
    return coerced


def path_finder_factory(joints_info, target_cell_types, board_info: Dict):
    global_wave_age_info = get_global_wave_age_info(joints_info, board_info)

    class ClientPathFinder:

        def __init__(self, board_layers):
            self.my_cell, self.target_cells = self.get_my_cell_and_target_cells(board_layers)

        @staticmethod
        def get_my_cell_and_target_cells(board_layers):
            target_cells = []
            my_cell = None
            for yid, layer in enumerate(board_layers):
                for xid, cell_code in enumerate(layer):
                    if not my_cell and cell_code in CellGroups.HeroCellTypes:
                        my_cell = (xid, yid)
                    elif cell_code in target_cell_types:
                        target_cells.append((xid, yid))
            return my_cell, target_cells

        def get_routed_move_action(self):
            if self.target_cells:
                next_cell, _, _ = get_next_target_age(global_wave_age_info,
                                                      joints_info,
                                                      self.target_cells,
                                                      self.my_cell)

                if next_cell:
                    return get_move_action(self.my_cell, next_cell)
                elif joints_info[self.my_cell]:
                    return get_move_action(self.my_cell, choice(joints_info[self.my_cell]))

            return choice(Move.get_valid_codes())

    return ClientPathFinder


def get_move_action(start_cell, end_cell):
    if end_cell[0] - start_cell[0] == 1:
        return Move.Right
    if end_cell[0] - start_cell[0] == -1:
        return Move.Left
    if end_cell[1] - start_cell[1] == 1:
        return Move.Down
    return Move.Up
