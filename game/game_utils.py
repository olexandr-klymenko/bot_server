from datetime import datetime
from functools import wraps
from logging import getLogger

from game.cell_types import CellType

logger = getLogger()


def session_method_profiler_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            ret = func(*args, **kwargs)
        except Exception as err:
            logger.error(str(err))
            raise
        execution_time = datetime.now() - start_time
        logger.debug("%s execution time: %s" % (func.__name__, execution_time))
        return ret

    return wrapper


def get_lower_cell(cell):
    return cell[0], cell[1] + 1


def get_joints_info(board_info, size):
    joints_info = {}
    for vertical in range(size):
        for horizontal in range(size):
            cell = horizontal, vertical
            cell_joints = []
            for neighbour_cell in get_cell_neighbours(cell, board_info):
                if is_pass(cell, neighbour_cell, board_info):
                    cell_joints.append(neighbour_cell)
            joints_info.update({cell: cell_joints})
    return joints_info


def is_pass(start_cell, end_cell, board_info):
    if board_info[end_cell] not in [CellType.Empty, CellType.Ladder, CellType.Pipe]:
        return False

    if board_info[start_cell] not in [CellType.Empty, CellType.Ladder, CellType.Pipe]:
        return False

    if (
            board_info[start_cell] != CellType.Ladder
            and end_cell == get_upper_cell(start_cell)
    ):
        return False

    if (
            get_lower_cell(start_cell) in board_info
            and board_info[start_cell] in [CellType.Empty, CellType.Gold]
            and board_info[get_lower_cell(start_cell)] in [CellType.Empty, CellType.Pipe]
            and end_cell != get_lower_cell(start_cell)
    ):
        return False

    return True


def get_cell_neighbours(cell, board_info):
    neighbours = []
    if get_left_cell(cell) in board_info:
        neighbours.append(get_left_cell(cell))

    if get_right_cell(cell) in board_info:
        neighbours.append(get_right_cell(cell))

    if get_lower_cell(cell) in board_info:
        neighbours.append(get_lower_cell(cell))

    if get_upper_cell(cell) in board_info:
        neighbours.append(get_upper_cell(cell))

    return neighbours


def get_left_cell(cell):
    return cell[0] - 1, cell[1]


def get_right_cell(cell):
    return cell[0] + 1, cell[1]


def get_upper_cell(cell):
    return cell[0], cell[1] - 1
