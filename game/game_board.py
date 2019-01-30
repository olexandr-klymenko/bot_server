from itertools import chain
import json

from copy import deepcopy
from logging import getLogger
from random import choice
from typing import List

from common.utils import PLAYER, CellType, get_board_info, CellGroups, get_global_wave_age_info, get_joints_info

logger = getLogger()

BOARD_BLOCK = [
    #123456789
    '     H=HH',  # 1
    '=H---H H ',  # 2
    ' H     H ',  # 3
    ' H=##=HH ',  # 4
    ' H    H  ',  # 5
    '=HH===H==',  # 6
    '  H---H=H',  # 7
    '==H     H',  # 8
    '  H==H==H',  # 9
]

BLOCKS_NUMBER = 3
BLOCK_SIZE = len(BOARD_BLOCK)
VERT_FLIP_BLOCK = BOARD_BLOCK[::-1]
HORIZ_FLIP_BLOCK = [line[::1] for line in BOARD_BLOCK]
VERT_HORIZ_FLIP_BLOCK = [line[::-1] for line in BOARD_BLOCK[::-1]]
BLOCKS = [BOARD_BLOCK, VERT_FLIP_BLOCK, HORIZ_FLIP_BLOCK, VERT_HORIZ_FLIP_BLOCK]


def get_generated_board(blocks_number: int) -> List[List]:
    board_blocks = []
    for vert_idx in range(blocks_number):
        current_layer_blocks = [choice(BLOCKS) for _ in range(blocks_number)]
        board_blocks.extend(_get_concatenated_blocks_layer(current_layer_blocks))
    return board_blocks


def _get_concatenated_blocks_layer(layer_blocks) -> List:
    return [''.join(chain.from_iterable([list(block[line]) for block in layer_blocks])) for line in range(BLOCK_SIZE)]


class LodeRunnerGameBoard:
    blocks_number = BLOCKS_NUMBER

    def __init__(self, board_layers: List[List]):
        self.board_layers = board_layers
        self.size = len(board_layers)
        self.initial_board_info = get_board_info(board_layers)
        self.board_info = deepcopy(self.initial_board_info)
        # self.global_wave_age_info = self.get_global_wave_age_info()

    @classmethod
    def from_blocks_number(cls, blocks_number: int = BLOCKS_NUMBER):
        cls.blocks_number = blocks_number
        return cls(get_generated_board(blocks_number))

    def get_board_layers(self, cell, direction):
        board_list = []
        for y in range(self.size):
            board_list.append([self.board_info[(x, y)] for x in range(self.size)])
        if cell:
            self._update_board_list_by_hero(board_list=board_list, cell=cell, direction=direction)
        return board_list

    def get_global_wave_age_info(self):
        # TODO: Implement global_wave_age_info serializer/deserializer
        logger.info('Calculating global wave age info ...')
        joints_info = get_joints_info(self.size, self.board_info)
        global_wave_age_info = get_global_wave_age_info(joints_info, self.initial_board_info)
        logger.info('Global wave age info done.')
        return json.dumps({str(key): value for key, value in global_wave_age_info.items()})

    def _update_board_list_by_hero(self, board_list, cell, direction):
        player_cell_type = self.get_participant_on_cell_type(cell=cell,
                                                             participant_type=PLAYER,
                                                             direction=direction)
        board_list[cell[1]][cell[0]] = CellGroups.get_hero_cell_type(player_cell_type)

    def get_participant_on_cell_type(self, cell, participant_type, direction):
        cell_type = self.get_cell_type(cell)
        if cell_type in [CellType.Empty, CellType.DrillableBrick]:
            return getattr(CellType, '%sLooks%s' % (participant_type, direction))

        if cell_type == CellType.Ladder:
            return getattr(CellType, '%sOnLadder' % participant_type)

        if cell_type == CellType.Pipe:
            return getattr(CellType, '%sOnPipeLooks%s' % (participant_type, direction))

        if cell_type in CellGroups.PlayerCellTypes:
            return CellType.HeroDies

    def is_cell_drillable(self, cell):
        return self._is_cell_valid(cell) and self.get_cell_type(cell) == CellType.DrillableBrick

    def process_move(self, current_cell, next_cell, next_cell_type, is_cell_in_scenarios):
        if not is_cell_in_scenarios:
            self.update_board(cell=current_cell, cell_type=self.get_cell_type(current_cell))
        self.update_board(cell=next_cell, cell_type=next_cell_type)

    def get_cell_type(self, cell):
        return self.initial_board_info[cell]

    def update_board(self, cell, cell_type):
        self.board_info[cell] = cell_type

    def get_empty_cells(self):
        return [cell for cell, cell_type in self.initial_board_info.items() if cell_type == CellType.Empty]

    def _is_cell_valid(self, cell):
        try:
            self.get_cell_type(cell)
            return True
        except KeyError:
            return False


def get_index_from_cell(player_point, size):
    return player_point[1] * size + player_point[0]

# TODO: implement rectangular board support
