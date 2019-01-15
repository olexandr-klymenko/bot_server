from copy import deepcopy
from logging import getLogger

from game.cell_types import CellType, CellGroups, PLAYER
from game.game_utils import (get_board_size, is_pass, get_index_from_cell, get_left_cell, get_right_cell,
                             get_lower_cell, get_upper_cell)

logger = getLogger()

BOARD_STRING_HEADER = "board="


class LodeRunnerGameBoard:
    def __init__(self, board_string):
        self.board_string = board_string
        self.size = get_board_size(board_string)
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
        board_string = "%s%s" % (BOARD_STRING_HEADER, board_string)
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

    def get_initial_board_info(self):
        board_info = {}
        board_list = list(self.board_string)
        for vertical in range(self.size):
            for horizontal in range(self.size):
                cell_code = board_list.pop(0)
                if self.cell_type.is_code_valid(cell_code):
                    board_info[(horizontal, vertical)] = cell_code
                else:
                    raise Exception("Cell code %s is invalid. Valid codes: %s" %
                                    (cell_code, self.cell_type.get_valid_codes()))
        return board_info

    def get_cell_neighbours(self, cell):
        neighbours = []
        if get_left_cell(cell) in self.board_info:
            neighbours.append(get_left_cell(cell))

        if get_right_cell(cell) in self.board_info:
            neighbours.append(get_right_cell(cell))

        if get_lower_cell(cell) in self.board_info:
            neighbours.append(get_lower_cell(cell))

        if get_upper_cell(cell) in self.board_info:
            neighbours.append(get_upper_cell(cell))

        return neighbours

    def process_move(self, current_cell, next_cell, next_cell_type, is_cell_in_scenarios):
        if not is_cell_in_scenarios:
            self.update_board(cell=current_cell, cell_type=self.get_cell_type(current_cell))
        self.update_board(cell=next_cell, cell_type=next_cell_type)

    def get_cell_type(self, cell):
        return self.initial_board_info[cell]

    def update_board(self, cell, cell_type):
        self.board_info[cell] = cell_type

    def get_empty_cells(self):
        return [cell for cell, cell_type in self.initial_board_info.items() if cell_type == self.cell_type.Empty]

    def _get_game_board_cell_type(self, cell):
        return self.board_info[cell]

    def _is_cell_valid(self, cell):
        try:
            self.get_cell_type(cell)
            return True
        except KeyError:
            return False
