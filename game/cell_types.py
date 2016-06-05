from logging import getLogger

from common.move_types import CharCode

logger = getLogger()

__all__ = ['PLAYER', 'GUARD', 'CellType', 'Drill', 'CellGroups', 'DRILL_SCENARIO']


PLAYER = 'Player'
GUARD = 'Guard'
SPECTATOR = 'Spectator'


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


class Drill(CharCode):
    DrillRight = 'DrillRight'
    DrillLeft = 'DrillLeft'


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


DRILL_SCENARIO = [CellType.Drill, CellType.Empty, CellType.Empty, CellType.Empty, CellType.Empty, CellType.Empty,
                  CellType.PitFill4, CellType.PitFill3, CellType.PitFill2, CellType.PitFill1,
                  CellType.PitFilled, CellType.DrillableBrick]
