from functools import partial
from itertools import chain
from logging import getLogger
from multiprocessing import Pool, cpu_count
from typing import Dict, Tuple, List


logger = getLogger()

PLAYER = "Player"
GUARD = "Guard"
SPECTATOR = "Spectator"
ADMIN = "Admin"


def get_board_info(board_layers: List[List]) -> Dict[Tuple[int, int], str]:
    board_info = {}
    for y_coord, line in enumerate(board_layers):
        for x_coord, cell_code in enumerate(line):
            if CellType.is_code_valid(cell_code):
                board_info[(x_coord, y_coord)] = cell_code
            else:
                raise Exception(
                    "Cell code %s is invalid. Valid codes: %s"
                    % (cell_code, CellType.get_valid_codes())
                )
    return board_info


class CharCode:
    @classmethod
    def get_valid_codes(cls):
        return [
            getattr(cls, attr)
            for attr in dir(cls)
            if not callable(attr)
            and not attr.startswith("__")
            and isinstance(getattr(cls, attr), str)
        ]

    @classmethod
    def is_code_valid(cls, code):
        return code in cls.get_valid_codes()


class CellType(CharCode):
    Empty = " "
    UnbreakableBrick = "#"
    DrillableBrick = "="
    Ladder = "H"
    Pipe = "-"

    Drill = "*"
    PitFill4 = "4"
    PitFill3 = "3"
    PitFill2 = "2"
    PitFill1 = "1"
    PitFilled = "0"

    Gold = "$"

    PlayerLooksLeft = "("
    PlayerLooksRight = ")"
    PlayerOnLadder = "y"
    PlayerOnPipeLooksLeft = "q"
    PlayerOnPipeLooksRight = "p"

    HeroLooksLeft = "{"
    HeroLooksRight = "}"
    HeroOnLadder = "Y"
    HeroOnPipeLooksLeft = "C"
    HeroOnPipeLooksRight = "D"
    HeroDies = "@"

    GuardLooksLeft = "<"
    GuardLooksRight = ">"
    GuardOnLadder = "X"
    GuardOnPipeLooksLeft = "d"
    GuardOnPipeLooksRight = "b"


def get_cell_neighbours(cell, board_cells):
    neighbours = []
    if get_left_cell(cell) in board_cells:
        neighbours.append(get_left_cell(cell))

    if get_right_cell(cell) in board_cells:
        neighbours.append(get_right_cell(cell))

    if get_lower_cell(cell) in board_cells:
        neighbours.append(get_lower_cell(cell))

    if get_upper_cell(cell) in board_cells:
        neighbours.append(get_upper_cell(cell))

    return neighbours


class Move(CharCode):
    Right = "Right"
    Left = "Left"
    Up = "Up"
    Down = "Down"

    @classmethod
    def get_move_from_start_end_cells(cls, start_cell, end_cell):
        if end_cell == get_right_cell(start_cell):
            return cls.Right
        if end_cell == get_left_cell(start_cell):
            return cls.Left
        if end_cell == get_upper_cell(start_cell):
            return cls.Up
        if end_cell == get_lower_cell(start_cell):
            return cls.Down


class CellGroups(object):
    ct = CellType
    PlayerCellTypes = [
        ct.PlayerLooksLeft,
        ct.PlayerLooksRight,
        ct.PlayerOnLadder,
        ct.PlayerOnPipeLooksLeft,
        ct.PlayerOnPipeLooksRight,
    ]

    HeroCellTypes = [
        ct.HeroLooksLeft,
        ct.HeroLooksRight,
        ct.HeroOnLadder,
        ct.HeroOnPipeLooksLeft,
        ct.HeroOnPipeLooksRight,
    ]

    EmptyCellTypes = [
        ct.Empty,
        ct.Gold,
        ct.Drill,
        ct.PitFill1,
        ct.PitFill2,
        ct.PitFill3,
        ct.PitFill4,
    ]

    FloorCellTypes = [ct.DrillableBrick, ct.UnbreakableBrick, ct.Ladder]

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
    CellType.HeroOnPipeLooksRight: CellType.Pipe,
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
    DrillRight = "DrillRight"
    DrillLeft = "DrillLeft"


def get_global_wave_age_info(joints_info, board_info):
    get_wave_age_info_for_joints_info = partial(get_wave_age_info, joints_info)
    pool = Pool(cpu_count())
    logger.info("Start calculating global wave age info ...")
    global_wave_age_info = {
        el[0]: el[1]
        for el in pool.map(get_wave_age_info_for_joints_info, board_info.keys())
    }
    pool.close()
    logger.info("Global wave age info has been calculated")
    return global_wave_age_info


def get_wave_age_info(joints_info, start_cell):
    wave_info = {}
    wave_age = 1
    joints = joints_info[start_cell]
    while joints:
        wave_info.update({cell: wave_age for cell in joints})
        joints = set(list(chain(*[joints_info[cell] for cell in joints])))
        joints = joints - set(wave_info.keys())
        wave_age += 1
    return start_cell, wave_info


def get_joints_info(
    board_info: Dict[Tuple[int, int], str]
) -> Dict[Tuple[int, int], List]:
    joints_info = {}
    for cell in board_info:
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

    if board_info[start_cell] != CellType.Ladder and end_cell == get_upper_cell(
        start_cell
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


def get_next_target_age(global_wave_age_info, joints_info, target_cells, start_cell):
    age_info = global_wave_age_info[start_cell]
    target_candidates = [cell for cell in target_cells if cell in age_info]
    if target_candidates:
        target_cell = next_cell = min(target_candidates, key=lambda x: age_info[x])
        real_age = age = age_info[next_cell]
        while age > 1:
            age -= 1
            neighbours = get_cell_neighbours(next_cell, global_wave_age_info.keys())
            next_cell = [
                cell
                for cell in neighbours
                if next_cell in joints_info[cell] and age_info.get(cell) == age
            ][0]
        return next_cell, target_cell, real_age
