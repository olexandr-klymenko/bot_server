from common.utils import CellType, CharCode


class Drill(CharCode):
    DrillRight = 'DrillRight'
    DrillLeft = 'DrillLeft'


DRILL_SCENARIO = [CellType.Drill, CellType.Empty, CellType.Empty, CellType.Empty, CellType.Empty, CellType.Empty,
                  CellType.PitFill4, CellType.PitFill3, CellType.PitFill2, CellType.PitFill1,
                  CellType.PitFilled, CellType.DrillableBrick]


