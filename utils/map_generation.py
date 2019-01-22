from itertools import chain
from random import choice


__all__ = ['get_generated_board']


BOARD_BLOCK = [
#    123456789
    '     H=HH',  #1
    '=H---H H ',  #2
    ' H     H ',  #3
    ' H=##=HH ',  #4
    ' H    H  ',  #5
    '=HH===H==',  #6
    '  H---H=H',  #7
    '==H     H',  #8
    '  H==H==H',  #9
]


BLOCKS_NUMBER = 3
BLOCK_SIZE = len(BOARD_BLOCK)
VERT_FLIP_BLOCK = BOARD_BLOCK[::-1]
HORIZ_FLIP_BLOCK = [line[::1] for line in BOARD_BLOCK]
VERT_HORIZ_FLIP_BLOCK = [line[::-1] for line in BOARD_BLOCK[::-1]]
BLOCKS = [BOARD_BLOCK, VERT_FLIP_BLOCK, HORIZ_FLIP_BLOCK, VERT_HORIZ_FLIP_BLOCK]


def get_generated_board(blocks_number=None):
    blocks_number = blocks_number or BLOCKS_NUMBER
    board_blocks = []
    for vert_idx in range(blocks_number):
        current_layer_blocks = [choice(BLOCKS) for _ in range(blocks_number)]
        board_blocks.extend(_get_concatenated_blocks_layer(current_layer_blocks))
    return board_blocks


def _get_concatenated_blocks_layer(layer_blocks):
    return [''.join(chain.from_iterable([list(block[line]) for block in layer_blocks])) for line in range(BLOCK_SIZE)]
