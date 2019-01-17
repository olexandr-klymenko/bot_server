from logging import getLogger

from game.game_utils import get_random_direction

logger = getLogger()


class ParticipantObject(object):
    def __init__(self, participant_id, cell, name):
        self.participant_id = participant_id
        self.cell = cell
        self.name = name
        self.is_allowed_to_act = True

    @property
    def participant_type(self):
        return self.__class__.__name__

    def get_id(self):
        return self.participant_id

    def get_cell(self):
        return self.cell

    def get_name(self):
        return self.name

    def get_type(self):
        return self.participant_type

    def re_spawn(self, spawn_cell):
        self.cell = spawn_cell

    def move(self, next_cell):
        self.cell = next_cell

    def allow_action(self):
        self.is_allowed_to_act = True

    def disallow_action(self):
        self.is_allowed_to_act = False

    def set_cell(self, cell):
        self.cell = cell


class LodeRunnerParticipantObject(ParticipantObject):
    def __init__(self, participant_id, cell, name):
        super().__init__(participant_id, cell, name)
        self.direction = get_random_direction()
        logger.debug("Created participant '%s' object: %s" % (self.participant_type, vars(self)))

    def get_direction(self):
        return self.direction

    def set_direction(self, direction):
        self.direction = direction

    def re_spawn(self, spawn_cell):
        logger.debug("Participant has been killed: %s " % vars(self))
        super().re_spawn(spawn_cell)
        logger.debug("Participant has been spawned: %s " % vars(self))


class Player(LodeRunnerParticipantObject):
    def __init__(self, player_id, cell, name):
        super().__init__(participant_id=player_id, cell=cell, name=name)
        self.score = {'permanent': 0, 'temporary': 0}

    def re_spawn(self, spawn_cell):
        super().re_spawn(spawn_cell)
        self.score['temporary'] = 0

    def pickup_gold(self):
        self.score['temporary'] += 1
        self.score['permanent'] += self.score['temporary']


class Guard(LodeRunnerParticipantObject):
    pass


def get_participant(participant_id, participant_type, cell, name):
    return eval(participant_type)(participant_id, cell, name)
