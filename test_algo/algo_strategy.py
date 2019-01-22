import gamelib
import random
import copy
import math
import warnings
from sys import maxsize


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        random.seed()

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, BARREL_MASK, BARREL_MASK_IDX, BASE_PASSIVE_LOCS
        self.filter, self.encryptor, self.destructor, \
        self.ping, self.emp, self.scrambler = [i for i in range(6)]

        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]

        BARREL_MASK = [
            # Destructors
            [23, 13], [24, 13],
            # Encryptors
            [23, 12], [24, 12], [25, 13], [23, 11],
            # Filters
            [1, 13], [1, 12], [0, 13], [18, 10], [18, 11], [13, 11], [9, 10], [9, 11], [5, 11],
        ]
        BARREL_MASK_IDX = {
            "destructors": (0, 2),
            "encryptors": (2, 6),
            "filters": (6, 15)
        }
        BASE_PASSIVE_LOCS = [[3, 12], [10, 10], [17, 8]]
        self.prev_state = None

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        # TODO: remove advanced state from function signatures if we initialize it here already.
        game_state = gamelib.AdvancedGameState(self.config, turn_state)
        game_state.suppress_warnings(True)  # Uncomment this line to suppress warnings.

        self.build_barrel(game_state)
        self.shoot(game_state)

        damaged_locations = self._find_damaged_def_units(game_state)
        if damaged_locations:
            self.build_reactive_defence(game_state, damaged_locations)

        self.build_passive_defence(game_state)

        # Must run at the very end of the algo.
        self.prev_state = copy.deepcopy(game_state)
        game_state.submit_turn()

    @staticmethod
    def _has_loc_been_attacked(curr_unit_obj, prev_unit_obj):
        """ Helper to check if location has been attacked based on changes in
        current and previous unit state.

        :param curr_unit_obj: current round unit object.
        :param prev_unit_obj: previous round unit object.
        :return: (boolean) if the unit has been attacked.
        """
        if not curr_unit_obj:
            return False
        else:
            return curr_unit_obj.stability < prev_unit_obj.stability

    @staticmethod
    def _find_locs_w_def_units(state):
        """ Finds all locations of the defensive units on our side of the map.

        :param state: game state object.
        :return: (list) tuples of location and defensive units at that location.
        """
        locations = []
        def_units = []

        for x in range(state.ARENA_SIZE):
            for y in range(state.HALF_ARENA):
                units = state.game_map[[x, y]]
                if units is None or units == []:
                    continue
                else:
                    for unit in units:
                        if unit.unit_type in [DESTRUCTOR, FILTER, ENCRYPTOR]:
                            locations.append([x, y])
                            def_units.append(unit)
                            # gamelib.debug_write("Unit --> ", unit)

        return zip(locations, def_units)

    def _find_damaged_def_units(self, state: gamelib.AdvancedGameState, apply_barrel_mask=True):
        """ Find all static units that lost some health during last round.

        :param state: current game state.
        :param apply_barrel_mask: flag to ignore units that are part of the barrel.
        :return: (list) locations of damaged units.
        """
        damaged_locs = []

        # If previous state of the game does not exist, then return empty array.
        if self.prev_state is None:
            return []

        # Get locations of all defensive units in previous round.
        prev_locs_and_units = self._find_locs_w_def_units(self.prev_state)

        for prev_loc, prev_unit in prev_locs_and_units:
            # Find defensive unit at current location.
            curr_unit = [
                unit for unit in state.game_map[prev_loc]
                if unit.unit_type in [DESTRUCTOR, FILTER, ENCRYPTOR]
            ]
            curr_unit = None if len(curr_unit) == 0 else curr_unit[0]

            # Check if unit has been attacked over the last round.
            if self._has_loc_been_attacked(curr_unit, prev_unit):

                # Apply barrel mask - do not count damaged units that are part of the barrel.
                if apply_barrel_mask:
                    if prev_loc not in BARREL_MASK:
                        damaged_locs.append(prev_loc)
                else:
                    damaged_locs.append(prev_loc)

        return damaged_locs

    @staticmethod
    def shoot(state: gamelib.AdvancedGameState, left=False):
        """ Shoots from the blackbeard barrel.

        :param state: current game state.
        :param left:
        :return:
        """
        if state.turn_number == 0:
            state.attempt_spawn(PING, [13, 0], 2)
            state.attempt_spawn(PING, [14, 0], 2)
        # elif open:
        #     state.attempt_spawn(EMP, [17, 3])
        elif state.turn_number % 2:
            bits = state.get_resource(state.BITS)
            if bits > 4:
                state.attempt_spawn(PING, [14, 0], 4)
            state.attempt_spawn(PING, [13, 0], int(state.get_resource(state.BITS)))

    @staticmethod
    def build_barrel(state: gamelib.AdvancedGameState, left=False):
        """ Builds the blackbear barrel on the map.

        :param state: current game state.
        :param left:
        """
        # Spawn front destructors and encryptors
        destructors = BARREL_MASK[
                      BARREL_MASK_IDX['destructors'][0]: BARREL_MASK_IDX['destructors'][1]]
        for i in destructors:
            if state.can_spawn(DESTRUCTOR, i):
                state.attempt_spawn(DESTRUCTOR, i)

        encryptors = BARREL_MASK[BARREL_MASK_IDX['encryptors'][0]: BARREL_MASK_IDX['encryptors'][1]]
        for i in encryptors:
            if state.can_spawn(ENCRYPTOR, i):
                state.attempt_spawn(ENCRYPTOR, i)

        end = 12 if state.turn_number > 0 else 19

        # open = False
        # spawn remaining filters
        for i in range(22, end, -1):
            # if not state.contains_stationary_unit([i,i-12]) and state.get_resource(state.CORES) < 1:
            #     open = True
            if state.can_spawn(FILTER, [i, i - 12]):
                state.attempt_spawn(FILTER, [i, i - 12])

    @staticmethod
    def build_passive_defence(state: gamelib.AdvancedGameState):
        """ Builds out a passive defense. Has 3 hard-coded positions that are best optimized to
        cover as much of the field as possible on the unprotected side of the barrel of blackbear.

        :param state: current game state.
        """
        passive_defence_locations = BASE_PASSIVE_LOCS

        for loc in passive_defence_locations:
            # First build the Destructor at the proper location.
            if state.get_resource(state.CORES) > 4:
                if state.can_spawn(DESTRUCTOR, loc):
                    state.attempt_spawn(DESTRUCTOR, loc)

            # If we have some more cores left, then build the Filter on top of it.
            if state.get_resource(state.CORES) > 1:
                if state.can_spawn(FILTER, loc):
                    state.attempt_spawn(FILTER, [loc[0], loc[1] + 1])

    @staticmethod
    def build_reactive_defence(state: gamelib.AdvancedGameState, damaged_locs):
        """ Builds reactive defence according to the provided damaged_locs.

        :param state: current game state.
        :param damaged_locs: (list) locations of damaged units. Will define where defence
        units will be spawned.
        """
        num_funded_destructors = int(state.get_resource(state.CORES) // 4)

        if num_funded_destructors < len(damaged_locs):
            # If there are less funded destructors then damaged locations, then take as many
            # damaged locations as we can fund and build there.
            funded_locs = damaged_locs[:num_funded_destructors]
        else:
            # If we have more funded locations then was actually damaged, then build defences
            # around damaged locations until we run out of funding.
            funded_locs = [damaged_locs[i % len(damaged_locs)] for i in
                           range(num_funded_destructors)]

        # Deploy defensive units until we either run out of damaged locations
        for funded_loc in funded_locs:
            # Find all possible spawn points in the range of 1 unit around the damaged
            # unit's location.
            potential_spawn_locs = state.game_map.get_locations_in_range(funded_loc, 1)

            for loc in potential_spawn_locs:
                if state.can_spawn(DESTRUCTOR, loc):
                    state.attempt_spawn(DESTRUCTOR, loc)

    @staticmethod
    def build_bad_wall(game_state):
        line = 12
        for i in range(1, 20):
            if game_state.CORES < 1:
                return
            unit = FILTER if i % 2 else DESTRUCTOR
            if game_state.can_spawn(unit, (i, line)):
                game_state.attempt_spawn(unit, (i, line))

    @staticmethod
    def build_passive_blackbeard_defence(state: gamelib.AdvancedGameState):
        # if we have extra cores use some of them 18,13,9,5 then filters between
        prio = [[1, 13], [1, 12], [0, 13], [18, 10], [18, 11], [13, 11], [9, 10], [9, 11], [5, 11]]
        which = [DESTRUCTOR, DESTRUCTOR, FILTER, DESTRUCTOR, FILTER, DESTRUCTOR, DESTRUCTOR, FILTER,
                 DESTRUCTOR]

        for i in range(len(prio)):
            if state.get_resource(state.CORES) > 4:
                if state.can_spawn(which[i], prio[i]):
                    state.attempt_spawn(which[i], prio[i])

        i = 0
        # Try to spawn some random stuff
        while i < 10 and state.get_resource(state.CORES) > 6:
            row = random.randint(10, 11)
            col = random.randint(13 - row, 19)
            type = DESTRUCTOR if random.randint(0, 1) else FILTER
            if state.can_spawn(type, [row, col]):
                state.attempt_spawn(type, [row, col])

        if state.turn_number == 0:
            state.attempt_spawn(PING, [13, 0], 2)
            state.attempt_spawn(PING, [14, 0], 2)
        # elif open:
        #     state.attempt_spawn(EMP, [17, 3])
        elif state.turn_number % 2:
            bits = state.get_resource(state.BITS)
            if bits > 4:
                state.attempt_spawn(PING, [14, 0], 4)
            state.attempt_spawn(PING, [13, 0], int(state.get_resource(state.BITS)))

    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
