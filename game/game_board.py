from copy import deepcopy
from logging import getLogger
from typing import List

from game.cell_types import CellType, CellGroups, PLAYER

logger = getLogger()


class LodeRunnerGameBoard:
    def __init__(self, board_layers: List[str]):
        self.board_layers = tuple(board_layers)
        self.size = len(board_layers)
        self.initial_board_info = self.get_initial_board_info()
        self.board_info = deepcopy(self.initial_board_info)

    def get_board_string(self, cell, direction):
        board_list = self._get_board_list()
        if cell:
            self._update_board_list_by_hero(board_list=board_list, cell=cell, direction=direction)
        return ''.join(board_list)

    def _get_board_list(self):
        board_list = []
        for vertical in range(self.size):
            for horizontal in range(self.size):
                board_list.append(self._get_game_board_cell_type((horizontal, vertical)))
        return board_list

    def _update_board_list_by_hero(self, board_list, cell, direction):
        board_index = get_index_from_cell(player_point=cell, size=self.size)
        player_cell_type = self.get_participant_on_cell_type(cell=cell, participant_type=PLAYER,
                                                             direction=direction)
        board_list[board_index] = CellGroups.get_hero_cell_type(player_cell_type)

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
        for y_coord, line in enumerate(self.board_layers):
            for x_coord, cell_code in enumerate(line):
                if CellType.is_code_valid(cell_code):
                    board_info[(x_coord, y_coord)] = cell_code
                else:
                    raise Exception("Cell code %s is invalid. Valid codes: %s" %
                                    (cell_code, CellType.get_valid_codes()))
        return board_info

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

    def _get_game_board_cell_type(self, cell):
        return self.board_info[cell]

    def _is_cell_valid(self, cell):
        try:
            self.get_cell_type(cell)
            return True
        except KeyError:
            return False


def get_index_from_cell(player_point, size):
    return player_point[1] * size + player_point[0]
