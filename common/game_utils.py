from math import sqrt
from itertools import chain
from random import choice
from datetime import datetime
from functools import wraps
from logging import getLogger

from common.move_types import Move


logger = getLogger()


__all__ = ['TimeOutExceeded', 'factory_action_decorator', 'session_method_profiler_decorator',
           'rest_action_decorator', 'get_move_point_cell', 'get_modified_cell', 'get_board_size',
           'get_index_from_cell', 'get_upper_cell', 'get_lower_cell', 'get_left_cell', 'get_right_cell',
           'get_wave_age_info', 'get_route', 'get_move_changes', 'get_move_action', 'coroutine']


class TimeOutExceeded(Exception):
    def __init__(self, message):
        super(TimeOutExceeded, self).__init__(message)


class RestActions:
    rest_actions = []


def factory_action_decorator(func):
    @wraps(func)
    def wrapper(factory, *args, **kwargs):
        start_time = datetime.now()
        factory.lock_game_server()
        func(factory, *args, **kwargs)
        factory.unlock_game_server()
        execution_time = datetime.now() - start_time
        logger.debug("%s execution time: %s" % (func.__name__, execution_time))

    return wrapper


def session_method_profiler_decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        ret = func(*args, **kwargs)
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


def get_upper_cell(cell):
    return cell[0], cell[1] - 1


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
