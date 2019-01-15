from datetime import datetime
from functools import wraps
from itertools import chain
from logging import getLogger
from math import sqrt
from random import choice
from random import randint

from game.cell_types import CellType, Drill
from game.move_types import Move

logger = getLogger()

SCORE_STRING_HEADER = "score=%s"
PLAYERS_STRING_HEADER = "players=%s"
BOARD_SIZE_HEADER = "size=%d"


def get_upper_cell(cell):
    return cell[0], cell[1] - 1


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


def randomized_run_decorator(percentage):

    def wrapper(func):
        def inner(*args, **kwargs):
            is_run = randint(0, 100) < percentage
            if is_run:
                return func(*args, **kwargs)
        return inner
    return wrapper


class RestActions:
    rest_actions = []


def factory_action_decorator(func):
    @wraps(func)
    def wrapper(factory, *args, **kwargs):
        start_time = datetime.now()
        func(factory, *args, **kwargs)
        execution_time = datetime.now() - start_time
        logger.debug("%s execution time: %s" % (func.__name__, execution_time))

    return wrapper


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


def rest_action_decorator(func):
    RestActions().rest_actions.append(func.__name__)

    @wraps(func)
    def wrapper(game_session, *args, **kwargs):
        return func(game_session, *args, **kwargs)

    return wrapper


def coroutine(func):
    @wraps(func)
    def start(*args, **kwargs):
        res = func(*args, **kwargs)
        res.__next__()
        return res
    return start


def get_move_point_cell(cell, move):
    x_move, y_move = get_move_changes(move)
    return cell[0] + x_move, cell[1] + y_move


def get_modified_cell(cell, vector):
    return cell[0] + vector[0], cell[1] + vector[1]


def get_board_size(board_string):
    board_size = sqrt(len(board_string))
    if board_size != float(int(board_size)):
        raise Exception("Board string length %s should be square" % len(board_string))
    return int(board_size)


def get_index_from_cell(player_point, size):
    return player_point[1] * size + player_point[0]


def get_lower_cell(cell):
    return cell[0], cell[1] + 1


def get_left_cell(cell):
    return cell[0] - 1, cell[1]


def get_right_cell(cell):
    return cell[0] + 1, cell[1]


def get_wave_age_info(start_cell, joints_info):
    wave_info = {}
    wave_age = 1
    joints = joints_info[start_cell]
    while joints:
        wave_info.update({cell: wave_age for cell in joints})
        joints = set(list(chain(*[joints_info[cell] for cell in joints])))
        joints = joints - set(wave_info.keys())
        wave_age += 1
    return wave_info


def get_route(players_cells, wave_age_info, joints_info):
    target_candidates = [cell for cell in players_cells if cell in wave_age_info]
    if target_candidates:
        target_cell = min(target_candidates, key=lambda x: wave_age_info[x])
        wave_age = wave_age_info[target_cell]
        while wave_age > 1:
            wave_age -= 1
            target_cell = choice([cell for cell in wave_age_info.keys()
                                  if wave_age_info[cell] == wave_age and target_cell in joints_info[cell]])
        return target_cell


def get_move_changes(move):
    move_changes = {
            None:       (0, 0),
            Move.Right: (1, 0),
            Move.Left: (-1, 0),
            Move.Down: (0, 1),
            Move.Up: (0, -1)
        }
    return move_changes[move]


def get_move_action(start_cell, end_cell):
    if end_cell[0] - start_cell[0] == 1:
        return Move.Right
    if end_cell[0] - start_cell[0] == -1:
        return Move.Left
    if end_cell[1] - start_cell[1] == 1:
        return Move.Down
    return Move.Up
