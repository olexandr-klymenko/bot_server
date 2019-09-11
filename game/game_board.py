from copy import deepcopy
from itertools import chain
from logging import getLogger
from random import choice
from typing import List

from common.utils import (
    PLAYER,
    CellType,
    get_board_info,
    CellGroups,
    get_global_wave_age_info,
    get_joints_info,
    get_lower_cell,
)

logger = getLogger()

BOARD_BLOCK: List[str] = [
    # 123456789
    "     H=HH",  # 1
    "=H---H H ",  # 2
    " H     H ",  # 3
    " H=#===H ",  # 4
    " H     H ",  # 5
    "=HH====H=",  # 6
    "  H----HH",  # 7
    "==H     H",  # 8
    "  H==H==H",  # 9
]

BLOCKS_NUMBER = 3
BLOCK_SIZE = len(BOARD_BLOCK)
VERT_FLIP_BLOCK = BOARD_BLOCK[::-1]
HORIZ_FLIP_BLOCK = [line[::1] for line in BOARD_BLOCK]
VERT_HORIZ_FLIP_BLOCK = [line[::-1] for line in BOARD_BLOCK[::-1]]
BLOCKS = [BOARD_BLOCK, VERT_FLIP_BLOCK, HORIZ_FLIP_BLOCK, VERT_HORIZ_FLIP_BLOCK]
DEFAULT_GOLD_CELLS_NUMBER = 30


class GameBoard:
    blocks_number = BLOCKS_NUMBER

    def __init__(self, board_layers: List[str]):
        self.size = len(board_layers)
        self._initial_board_info = get_board_info(board_layers)
        self._board_info = deepcopy(self._initial_board_info)
        self.joints_info = get_joints_info(self._initial_board_info)
        self.global_wave_age_info = get_global_wave_age_info(
            self.joints_info, self._initial_board_info
        )
        self.gold_cells = []
        self.init_gold_cells()

    def init_gold_cells(self, number=DEFAULT_GOLD_CELLS_NUMBER):
        for _ in range(number):
            self.spawn_gold_cell()

    def spawn_gold_cell(self):
        cell = choice(self.get_empty_cells_on_bricks())
        self.gold_cells.append(cell)
        self._board_info[cell] = CellType.Gold

    def empty_gold_cells(self):
        while self.gold_cells:
            self._board_info.update({self.gold_cells.pop(): CellType.Empty})

    @classmethod
    def from_blocks_number(cls, blocks_number: int = BLOCKS_NUMBER):
        cls.blocks_number = blocks_number
        board_blocks: List[str] = []
        for vert_idx in range(blocks_number):
            current_layer_blocks = [choice(BLOCKS) for _ in range(blocks_number)]
            board_blocks.extend(cls._get_concatenated_blocks_layer(current_layer_blocks))
        return cls(board_blocks)

    @staticmethod
    def _get_concatenated_blocks_layer(layer_blocks: List[List]) -> List[str]:
        return [
            "".join(chain.from_iterable([list(block[line]) for block in layer_blocks]))
            for line in range(BLOCK_SIZE)
        ]

    def get_board_layers(self, cell, direction):
        board_list = []
        for y in range(self.size):
            board_list.append([self._board_info[(x, y)] for x in range(self.size)])
        if cell:
            self._update_board_list_by_hero(
                board_list=board_list, cell=cell, direction=direction
            )
        return board_list

    def _update_board_list_by_hero(self, board_list, cell, direction):
        player_cell_type = self.get_participant_on_cell_type(
            cell=cell, participant_type=PLAYER, direction=direction
        )
        board_list[cell[1]][cell[0]] = CellGroups.get_hero_cell_type(player_cell_type)

    def get_participant_on_cell_type(self, cell, participant_type, direction):
        cell_type = self.get_initial_cell_type(cell)
        if cell_type in [CellType.Empty, CellType.DrillableBrick]:
            return getattr(CellType, "%sLooks%s" % (participant_type, direction))

        if cell_type == CellType.Ladder:
            return getattr(CellType, "%sOnLadder" % participant_type)

        if cell_type == CellType.Pipe:
            return getattr(CellType, "%sOnPipeLooks%s" % (participant_type, direction))

        if cell_type in CellGroups.PlayerCellTypes:
            return CellType.HeroDies

    def is_cell_drillable(self, cell):
        return (
            self.is_cell_valid(cell)
            and self.get_initial_cell_type(cell) == CellType.DrillableBrick
        )

    def process_move(
        self, current_cell, next_cell, next_cell_type, is_cell_in_scenarios
    ):
        if not is_cell_in_scenarios:
            self.restore_original_cell(current_cell)
        self.update_board(cell=next_cell, cell_type=next_cell_type)

    def get_initial_cell_type(self, cell):
        return self._initial_board_info[cell]

    def update_board(self, cell, cell_type):
        self._board_info[cell] = cell_type

    def restore_original_cell(self, cell):
        self._board_info[cell] = self._initial_board_info[cell]

    def get_empty_cells(self):
        return [
            cell
            for cell, cell_type in self._board_info.items()
            if cell_type == CellType.Empty
        ]

    def get_empty_cells_on_bricks(self):
        empty_on_floor = []
        for cell in self.get_empty_cells():
            lower_cell_code = self._initial_board_info.get(get_lower_cell(cell))
            if lower_cell_code is None:
                empty_on_floor.append(cell)
            elif lower_cell_code in CellGroups.FloorCellTypes:
                empty_on_floor.append(cell)
        return empty_on_floor

    def is_cell_valid(self, cell):
        return cell in self._initial_board_info

    def can_fall_from_here(self, cell):
        lower_cell_code = self._board_info.get(get_lower_cell(cell))
        if lower_cell_code is None:
            return False
        if (
            lower_cell_code != CellType.Pipe
            and lower_cell_code not in CellGroups.EmptyCellTypes
        ):
            return False
        if self._initial_board_info[cell] in [CellType.Pipe, CellType.Ladder]:
            return False
        return True


# TODO: implement rectangular board support
