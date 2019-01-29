from typing import Dict, Tuple, List

PLAYER = 'Player'
GUARD = 'Guard'
SPECTATOR = 'Spectator'
ADMIN = 'Admin'


def get_board_info(board_layers: List[List]) -> Dict[Tuple[int, int], str]:
    board_info = {}
    for y_coord, line in enumerate(board_layers):
        for x_coord, cell_code in enumerate(line):
            if CellType.is_code_valid(cell_code):
                board_info[(x_coord, y_coord)] = cell_code
            else:
                raise Exception("Cell code %s is invalid. Valid codes: %s" %
                                (cell_code, CellType.get_valid_codes()))
    return board_info


class CharCode:
    @classmethod
    def get_valid_codes(cls):
        return [getattr(cls, attr) for attr in dir(cls)
                if not callable(attr) and not attr.startswith("__") and isinstance(getattr(cls, attr), str)]

    @classmethod
    def is_code_valid(cls, code):
        return code in cls.get_valid_codes()


class CellType(CharCode):
    Empty = ' '
    UnbreakableBrick = '#'
    DrillableBrick = '='
    Ladder = 'H'
    Pipe = '-'

    Drill = '*'
    PitFill4 = '4'
    PitFill3 = '3'
    PitFill2 = '2'
    PitFill1 = '1'
    PitFilled = '0'

    Gold = '$'

    PlayerLooksLeft = '('
    PlayerLooksRight = ')'
    PlayerOnLadder = 'y'
    PlayerOnPipeLooksLeft = 'q'
    PlayerOnPipeLooksRight = 'p'

    HeroLooksLeft = '{'
    HeroLooksRight = '}'
    HeroOnLadder = 'Y'
    HeroOnPipeLooksLeft = 'C'
    HeroOnPipeLooksRight = 'D'
    HeroDies = '@'

    GuardLooksLeft = '<'
    GuardLooksRight = '>'
    GuardOnLadder = 'X'
    GuardOnPipeLooksLeft = 'd'
    GuardOnPipeLooksRight = 'b'


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


class Move(CharCode):
    Right = 'Right'
    Left = 'Left'
    Up = 'Up'
    Down = 'Down'


class CellGroups(object):
    ct = CellType
    PlayerCellTypes = [ct.PlayerLooksLeft, ct.PlayerLooksRight, ct.PlayerOnLadder, ct.PlayerOnPipeLooksLeft,
                       ct.PlayerOnPipeLooksRight]

    HeroCellTypes = [ct.HeroLooksLeft, ct.HeroLooksRight, ct.HeroOnLadder, ct.HeroOnPipeLooksLeft,
                     ct.HeroOnPipeLooksRight]

    @classmethod
    def get_hero_cell_type(cls, player_cell_type):
        player_hero_info = dict(zip(cls.PlayerCellTypes, cls.HeroCellTypes))
        return player_hero_info[player_cell_type]


CELL_TYPE_COERCION = {
    CellType.Gold: CellType.Empty,
    CellType.Drill: CellType.DrillableBrick,
    CellType.PitFill1: CellType.DrillableBrick,
    CellType.PitFill2: CellType.DrillableBrick,
    CellType.PitFill3: CellType.DrillableBrick,
    CellType.PitFill4: CellType.DrillableBrick,
    CellType.PitFilled: CellType.DrillableBrick,
    CellType.PlayerLooksLeft: CellType.Empty,
    CellType.PlayerLooksRight: CellType.Empty,
    CellType.PlayerOnLadder: CellType.Ladder,
    CellType.PlayerOnPipeLooksLeft: CellType.Pipe,
    CellType.PlayerOnPipeLooksRight: CellType.Pipe,
    CellType.GuardLooksLeft: CellType.Empty,
    CellType.GuardLooksRight: CellType.Empty,
    CellType.GuardOnLadder: CellType.Ladder,
    CellType.GuardOnPipeLooksLeft: CellType.Pipe,
    CellType.GuardOnPipeLooksRight: CellType.Pipe,
    CellType.HeroDies: CellType.Empty,
    CellType.HeroLooksLeft: CellType.Empty,
    CellType.HeroLooksRight: CellType.Empty,
    CellType.HeroOnLadder: CellType.Ladder,
    CellType.HeroOnPipeLooksLeft: CellType.Pipe,
    CellType.HeroOnPipeLooksRight: CellType.Pipe
}


def get_lower_cell(cell):
    return cell[0], cell[1] + 1


def get_upper_cell(cell):
    return cell[0], cell[1] - 1


def get_right_cell(cell):
    return cell[0] + 1, cell[1]


def get_left_cell(cell):
    return cell[0] - 1, cell[1]


class Drill(CharCode):
    DrillRight = 'DrillRight'
    DrillLeft = 'DrillLeft'
