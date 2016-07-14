from logging import getLogger

from common.game_utils import *

logger = getLogger()


BOARD_STRING_HEADER = "board=%s"


class GameBoard:
    def __init__(self, board_string):
        self.cell_type = None
        self.board_string = board_string
        self.size = get_board_size(board_string)
        self.initial_board_info = None
        self.board_info = None

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

    def get_participant_on_cell_type(self, cell, participant_type, direction):
        raise NotImplementedError
