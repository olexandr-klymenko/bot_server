from logging import getLogger

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
