from logging import getLogger
from copy import deepcopy

from common.game_board import GameBoard
from common.game_utils import get_index_from_cell

from game.game_utils import is_pass
from game.cell_types import CellType, CellGroups, PLAYER

logger = getLogger()

BOARD_STRING_HEADER = "board=%s"


class LodeRunnerGameBoard(GameBoard):
    def __init__(self, board_string):
        super().__init__(board_string)
        self.cell_type = CellType
        self.initial_board_info = self.get_initial_board_info()
        self.board_info = deepcopy(self.initial_board_info)
        self.joints_info = self._get_joints_info()

    def _get_joints_info(self):
        joints_info = {}
        for vertical in range(self.size):
            for horizontal in range(self.size):
                cell = horizontal, vertical
                cell_joints = []
                neighbours = self.get_cell_neighbours(cell)
                for neighbour_cell in neighbours:
                    if is_pass(cell, neighbour_cell, self.initial_board_info):
                        cell_joints.append(neighbour_cell)
                joints_info.update({cell: cell_joints})
        return joints_info

    def get_board_string(self, cell, direction):
        board_string = ''
        for vertical in range(self.size):
            for horizontal in range(self.size):
                board_string += self._get_game_board_cell_type((horizontal, vertical))
        if cell:
            board_string = self._get_hero_board_string(board_string=board_string, cell=cell, direction=direction)
        board_string = BOARD_STRING_HEADER % board_string
        return board_string

    def _get_hero_board_string(self, board_string, cell, direction):
        board_list = list(board_string)
        board_index = get_index_from_cell(player_point=cell, size=self.size)
        player_cell_type = self.get_participant_on_cell_type(cell=cell, participant_type=PLAYER,
                                                             direction=direction)
        board_list[board_index] = CellGroups.get_hero_cell_type(player_cell_type)
        return ''.join(board_list)

    def is_cell_drillable(self, cell):
        return self._is_cell_valid(cell) and self.get_cell_type(cell) == CellType.DrillableBrick

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
