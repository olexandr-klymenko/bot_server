from random import choice
from logging import getLogger

from common.game_utils import get_upper_cell, get_lower_cell
from common.move_types import Move

from game.cell_types import CellType, Drill
from game_config import SCORE_STRING_HEADER, PLAYERS_STRING_HEADER, BOARD_SIZE_HEADER

logger = getLogger()


__all__ = ['is_pass', 'get_random_direction', 'get_drill_vector', 'get_formatted_scores', 'get_formatted_names',
           'get_formatted_board_size', 'delete_empty_value_keys']


def is_pass(start_cell, end_cell, board_info):
    if board_info[end_cell] not in [CellType.Empty, CellType.Ladder, CellType.Pipe]:
        return False

    if board_info[start_cell] not in [CellType.Empty, CellType.Ladder, CellType.Pipe]:
        return False

    if board_info[start_cell] != CellType.Ladder and end_cell == get_upper_cell(start_cell):
        return False

    if get_lower_cell(start_cell) in board_info:
        if board_info[start_cell] == CellType.Empty and board_info[get_lower_cell(start_cell)] == CellType.Empty\
                and end_cell != get_lower_cell(start_cell):
            return False

    return True


def get_random_direction():
    return choice([Move.Left, Move.Right])


def get_drill_vector(drill_action):
    if drill_action == Drill.DrillLeft:
        return -1, 1
    if drill_action == Drill.DrillRight:
        return 1, 1


def get_formatted_scores(scores):
    return SCORE_STRING_HEADER % '\n'.join('%s: %s' % (key, value)
                                           for key, value in sorted(scores.items(), key=lambda x: x[1], reverse=True))


def get_formatted_names(players_info):
    return PLAYERS_STRING_HEADER % ' '.join('%s,%s,%s' % (key, value[0], value[1])
                                            for key, value in players_info.items())


def get_formatted_board_size(size):
    return BOARD_SIZE_HEADER % str(size)


def delete_empty_value_keys(info):
    empty_value_keys = []
    for key, value in info.items():
        if not value:
            empty_value_keys.append(key)

    for elem in empty_value_keys:
        info.pop(elem)
