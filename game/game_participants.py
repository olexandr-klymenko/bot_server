from logging import getLogger
import sys
import inspect

from common.game_participants import ParticipantObject
from game.game_utils import get_random_direction
import game_config

logger = getLogger()


class ParticipantFactory(object):
    @classmethod
    def Create(cls, participant_id, participant_type, cell, name):
        participant_class = dict(inspect.getmembers(sys.modules[__name__], inspect.isclass))[participant_type]
        return participant_class(participant_id, cell, name)


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
        self.scores = {'permanent': 0, 'temporary': 0}

    def re_spawn(self, spawn_cell):
        super().re_spawn(spawn_cell)
        self.scores['temporary'] = 0

    def pickup_gold(self):
        self.scores['temporary'] += 1
        self.scores['permanent'] += self.scores['temporary']

    def trap_participant(self, participant_object):
        self.scores['permanent'] += getattr(game_config, "CATCH_%s_REWARD" % participant_object.get_type())


class Guard(LodeRunnerParticipantObject):
    def __init__(self, player_id, cell, name):
        super().__init__(participant_id=player_id, cell=cell, name=name)
