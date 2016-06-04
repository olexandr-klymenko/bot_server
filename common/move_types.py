from logging import getLogger

__all__ = ['CharCode', 'Move']


logger = getLogger()


class CharCode(object):

    @classmethod
    def get_valid_codes(cls):
        return [getattr(cls, attr) for attr in dir(cls)
                if not callable(attr) and not attr.startswith("__") and isinstance(getattr(cls, attr), str)]

    @classmethod
    def is_code_valid(cls, code):
        return code in cls.get_valid_codes()


class Move(CharCode):
    Right = 'Right'
    Left = 'Left'
    Up = 'Up'
    Down = 'Down'
