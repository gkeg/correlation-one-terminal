import gamelib
import random
import copy
import math
import warnings
from sys import maxsize

from defences import Defences


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
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        self.filter,self.encryptor,self.destructor,self.ping,self.emp,self.scrambler = [i for i in range(6)]
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]

        self.defences = Defences(config)

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.AdvancedGameState(self.config, turn_state)

        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Uncomment this line to suppress warnings.

        self.build_defences(game_state)

        if game_state.turn_number != 0:
            self.attack(game_state)

        game_state.submit_turn()

    def attack(self, state: gamelib.AdvancedGameState):
        emp_loc = [3, 10]
        while state.can_spawn(EMP, emp_loc, 1):
            state.attempt_spawn(EMP, emp_loc, 1)

    def build_defences(self, state: gamelib.AdvancedGameState):
        self.defences.build_template(state)

    @staticmethod
    def attack_hole(state: gamelib.AdvancedGameState, rush_loc, rush_unit):
        """ Spawns as many pings/scramblers at the given location

        :param state:
        :param rush_loc:
        :param rush_unit:
        :return:
        """
        if state.can_spawn(rush_unit, rush_loc):
            # Find out the proper amount for the amount of bits to spend
            state.attempt_spawn(rush_unit, rush_loc, state.my_bits())

    @staticmethod
    def scan_opponent_defences(state: gamelib.AdvancedGameState):
        """ Finds the side where they have the most defences. Checks the first 5 rows and
        determines if it's left-heavy or right-heavy. Returns left-heavy by default.

        :param state:
        :return:
        """
        return True

    def sawtooth(self, state: gamelib.AdvancedGameState):
        """ Sawtooth defence.

        :param state:
        :return:
        """
        # Find the defences that were destroyed
        damaged_locations = self._find_damaged_def_units(state)

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

    # Set up the classic sawtooth defence
    def sawtooth_setup(self, state: gamelib.AdvancedGameState):
        # Almost symmetrical setup, just need filter on <14, 10>
        dest_locs = [[2, 11], [6, 11], [11, 11], [16, 11], [21, 11], [25, 11]]
        filter_locs = [[0, 13], [1, 12], [26, 12], [27, 13]]

        for dest in destr_locs:
            if state.can_spawn(DESTRUCTOR, dest):
                state.attempt_spawn(DESTRUCTOR, dest)

        for f in filter_locs:
            if state.can_spawn(FILTER, f):
                state.attempt_spawn(FILTER, f)

    # Idea behind escort strategy --> 2 EMPs + 2 Scramblers + Rerouting with filters
    # Finds out the optimal side to attack from as well
    # For now, hardcode it to be the LHS
    def escort_strategy(self, state: gamelib.AdvancedGameState, defensive_side='left'):
        # See if we need to use more filters here
        # This should be dynamic, depending on the board state, kind of like
        # What stage of the game are we in
        filter_locs = [[6, 10], [11, 10], [16, 10], [22, 10]]

        # Spawn 2 EMPs and 2 Scramblers. Again, this should be dynamic
        emp_locs = [[3, 10], [3, 10]]
        scrambler_locs = [[4, 9], [4, 9]]

        for e in emp_locs:
            if state.can_spawn(EMP, e):
                state.attempt_spawn(EMP, e)

        for s in scrambler_locs:
            if state.can_spawn(SCRAMBLER, s):
                state.attempt_spawn(SCRAMBLER, s)


    def blackbeard(self, state: gamelib.AdvancedGameState, left=False):
        # Do initial first turn setup
        # Spawn front destructors and encryptors
        destr = [[23,13], [24, 13]]
        encr = [[23,12], [24,12], [25,13], [23,11]]
        for i in destr:
            if state.can_spawn(DESTRUCTOR, i):
                state.attempt_spawn(DESTRUCTOR, i)

        for i in encr:
            if state.can_spawn(ENCRYPTOR, i):
                state.attempt_spawn(ENCRYPTOR, i)

        end = 12 if state.turn_number > 0 else 19

        # open = False
        #spawn remaining filters
        for i in range(22,end,-1):
            # if not state.contains_stationary_unit([i,i-12]) and state.get_resource(state.CORES) < 1:
            #     open = True
            if state.can_spawn(FILTER, [i,i-12]):
                state.attempt_spawn(FILTER, [i,i-12])

        # if we have extra cores use some of them18,13,9,5 then filters between
        prio = [[1,13], [1,12], [0,13],[18,10], [18,11], [13,11], [9,10], [9,11],[5,11]]
        which = [DESTRUCTOR, DESTRUCTOR, FILTER, DESTRUCTOR, FILTER, DESTRUCTOR, DESTRUCTOR, FILTER, DESTRUCTOR]

        for i in range(len(prio)):
            if state.get_resource(state.CORES) > 4:
                if state.can_spawn(which[i], prio[i]):
                    state.attempt_spawn(which[i], prio[i])

        i = 0
        # Try to spawn some random stuff
        while i < 10 and state.get_resource(state.CORES) > 6:
            row = random.randint(10,11)
            col = random.randint(13-row, 19)
            type = DESTRUCTOR if random.randint(0,1) else FILTER
            if state.can_spawn(type, [row,col] ):
                state.attempt_spawn(type, [row,col])

        if state.turn_number == 0:
            state.attempt_spawn(PING, [13,0],2)
            state.attempt_spawn(PING, [14,0],2)
        # elif open:
        #     state.attempt_spawn(EMP, [17, 3])
        elif state.turn_number % 2:
            bits = state.get_resource(state.BITS)
            if bits > 4:
                state.attempt_spawn(PING, [14,0], 4)
            state.attempt_spawn(PING, [13,0], int(state.get_resource(state.BITS)))


    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
