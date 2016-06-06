from logging import getLogger
from uuid import uuid1
from random import choice
from itertools import chain

from common.game_utils import rest_action_decorator, RestActions
from game_config import *
from utils.map_generation import get_generated_board

logger = getLogger()


class GameSession:
    def __init__(self, participant_factory):
        self.game_board = None
        self.artifacts = []
        self.registry = {}
        self.scenarios = {}
        self.paused = False
        self.participant_factory = participant_factory
        self.tick_time = None

    @rest_action_decorator
    def info(self):
        return RestActions().rest_actions

    def run_rest_action(self, func_name, func_args):
        logger.debug("Rest action request: %s %s" % (func_name, func_args))
        if func_name in RestActions().rest_actions:
            func = getattr(self, func_name)
            return func(*func_args)
        return "Rest action is not available"

    def is_paused(self):
        return self.paused

    @rest_action_decorator
    def pause(self):
        if not self.is_paused():
            self.paused = True
            message = "Game session has been paused"
            logger.info(message)
            return message
        return "Game session is already paused"

    @rest_action_decorator
    def resume(self):
        if self.is_paused():
            self.paused = False
            message = "Game session has been resumed"
            logger.info(message)
            return message
        return "Game session is already resumed"

    @rest_action_decorator
    def get_board_size(self):
        return self.game_board.size

    @rest_action_decorator
    def check_user_name(self, name):
        return name in [participant.name for _, participant in self.registry.items()]

    def add_ai_objects(self, ai_number, ai_type):
        current_ai_number = self.get_participants_number(ai_type)
        for index in range(int(ai_number)):
            guard_name = "%s%s" % (GUARD_NAME_PREFIX, str(current_ai_number + index))
            self.register_participant(client_id=uuid1(), name=guard_name, participant_type=ai_type)

    def get_participants_number(self, participant_type):
        return len([el for el in self._participants if el.get_type() == participant_type])

    def remove_ai_objects(self, ai_number, ai_type):
        for index in range(int(ai_number)):
            self.unregister_participant(choice([ai_object.get_id() for ai_object in self._participants
                                                if ai_object.get_type() == ai_type]))

    def spawn_artifacts(self, cell_type, number):
        spawned_cells = []
        for index in range(int(number)):
            artifact_cell = choice(self._get_free_to_spawn_cells())
            self.artifacts.append(artifact_cell)
            spawned_cells.append(artifact_cell)
            self.game_board.update_board(cell=artifact_cell, cell_type=cell_type)
        return spawned_cells

    def spawn_gold_cells(self):
        pass

    @rest_action_decorator
    def set_tick_time(self, tick_time):
        try:
            new_tick_time = float(tick_time)
            self.tick_time = new_tick_time
            return "Tick time has been set to %s sec" % new_tick_time
        except ValueError as e:
            return "Could't set tick time: %s" % str(e)

    @rest_action_decorator
    def regenerate_game_board(self):
        self.pause()
        self.scenarios = {}
        new_board_string = get_generated_board()
        self.game_board.__init__(new_board_string)
        free_cells = self._get_free_to_spawn_cells()
        for participant in self._participants:
            cell = choice(free_cells)
            participant.set_cell(cell)
        self.artifacts = []
        self.spawn_gold_cells(GOLD_CELLS_NUMBER)
        self.resume()

    def _get_free_to_spawn_cells(self):
        empty_cells = self.game_board.get_empty_cells()
        participants_cells = [participant_object.cell for participant_object in self._participants]
        participants_neighbour_cells = list(chain.from_iterable([self.game_board.get_cell_neighbours(cell)
                                                                 for cell in participants_cells]))
        return list(set(empty_cells) - set(participants_cells + participants_neighbour_cells + self.artifacts))

    @property
    def _participants(self):
        return [participant_object for participant_object in self.registry.values()]

    def register_participant(self, client_id, name, participant_type):
        cell = choice(self._get_free_to_spawn_cells())
        if self._is_participant_id_in_registry(client_id):
            participant_object = self._get_participant_object_by_id(client_id)
            participant_object.re_spawn(cell)
        else:
            participant_object = self.participant_factory.Create(participant_id=client_id,
                                                                 participant_type=participant_type,
                                                                 cell=cell, name=name)
            self.registry.update({client_id: participant_object})
            participant_object = self._get_participant_object_by_id(client_id)

        self._update_participant_board_cell(participant_object)

    def _update_participant_board_cell(self, participant_object):
        cell = participant_object.get_cell()
        player_cell_type = self.game_board.get_participant_on_cell_type(cell=cell,
                                                                        participant_type=participant_object.get_type(),
                                                                        direction=participant_object.get_direction())
        self.game_board.update_board(cell=cell, cell_type=player_cell_type)

    def unregister_participant(self, participant_id):
        participant_cell = self._get_participant_cell_by_id(participant_id)
        participant_cell_type = self.game_board.get_cell_type(participant_cell)
        self.game_board.update_board(participant_cell, participant_cell_type)
        participant_obj = self.registry.pop(participant_id)
        logger.info("Unregistered {participant_type} '{name}', id: {id}"
                    .format(participant_type=participant_obj.participant_type,
                            name=participant_obj.name,
                            id=participant_id))

    def _get_participant_cell_by_id(self, participant_id):
        if self._is_participant_id_in_registry(participant_id):
            participant_object = self._get_participant_object_by_id(participant_id)
            return participant_object.get_cell()

    def can_process_action(self, player_id, action):
        return True

    def _get_participant_object_by_id(self, participant_id):
        if participant_id in self.registry:
            return self.registry[participant_id]
        return ''

    def _can_participant_get_into_cell(self, participant_object, move_action, next_cell):
        return True

    def _is_participant_in_cell(self, cell, participant_type):
        return cell in [participant_object.get_cell() for participant_object in self._participants
                        if participant_object.get_type() == participant_type]

    def _is_anyone_in_cell(self, cell):
        return cell in [participant_object.get_cell() for participant_object in self._participants]

    def _is_cell_in_scenarios(self, cell):
        return cell in self._scenarios_info

    @property
    def _scenarios_info(self):
        return dict(chain.from_iterable([player_scenarios.items() for player_scenarios in self.scenarios.values()]))

    def _process_move(self, move_action, participant_object):
        participant_object.disallow_action()

    def _get_participant_object_by_cell(self, cell):
        for participant_object in self._participants:
            if participant_object.get_cell() == cell:
                return participant_object

    def _is_participant_id_in_registry(self, participant_id):
        return participant_id in self.registry

    def allow_participants_action(self):
        for participant_object in self._participants:
            participant_object.allow_action()

    def get_participant_id_by_name(self, name):
        for participant_object in self._participants:
            if participant_object.get_name() == name:
                return participant_object.get_id()

    def get_cell_by_name(self, name):
        participant_obj = self.registry[self.get_participant_id_by_name(name)]
        return participant_obj.get_cell()

    def get_participant_obj_by_name(self, name):
        for participant_object in self._participants:
            if participant_object.get_name() == name:
                return participant_object
