from logging import getLogger
from random import choice
from itertools import chain
from functools import wraps

from game.board_blocks import board_block
from game_config import BOARD_BLOCKS_SIZE
from common.game_board import get_board_size


__all__ = ['get_generated_board']


logger = getLogger()


matrix_transformations = []


def get_generated_board():
    board_blocks = []
    block_matrix = get_block_matrix(board_block)
    previous_func = None
    for vert_idx in range(BOARD_BLOCKS_SIZE):
        current_layer_blocks = []
        for horiz_idx in range(BOARD_BLOCKS_SIZE):
            transformation_function = get_transformed_block_matrix(previous_func)
            current_layer_blocks.append(transformation_function(block_matrix))
            previous_func = transformation_function
        board_blocks.append(get_concatenated_blocks_layer(current_layer_blocks))
    return ''.join(chain.from_iterable(board_blocks))


def get_block_matrix(block):
    block_size = get_board_size(block)
    return [block[idx:idx + block_size] for idx in range(0, len(block), block_size)]


def get_transformed_block_matrix(previous_func):
    func = choice(matrix_transformations)
    while func == previous_func:
        func = choice(matrix_transformations)
    logger.info(func)
    return func


def get_concatenated_blocks_layer(current_layer_blocks):
    return chain.from_iterable(chain.from_iterable(zip(*current_layer_blocks)))


def transformation(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)

    matrix_transformations.append(wrapper)
    return wrapper


@transformation
def flip_horizontally(block_matrix):
    return [el[::-1] for el in block_matrix]


@transformation
def rotate_block_matrix(block_matrix):
    return zip(*list(zip(*block_matrix[::-1]))[::-1])


@transformation
def do_nothing(block_matrix):
    return block_matrix


@transformation
def flip_and_rotate(block_matrix):
    return flip_horizontally(rotate_block_matrix(block_matrix))
