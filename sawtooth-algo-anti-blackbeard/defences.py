# Defences class, will hold the priorities for everything, and find out
# what kind of shit to build next. Put reactive defence stuff in here
import gamelib
from gamelib import debug_write


class Defences:
    def __init__(self, config):
        """ Constructor.

        :param config: config object.
        """
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER, TEMPLATE_MASK
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]

        self.config = config
        self.UNIT_HEALTH = self.get_unit_params('stability')
        self.UNIT_COSTS = self.get_unit_params('cost')
        self.REMOVE_HEALTH_THRESH = 0.3
        self.BUILD_DESTRUCTOR_WALLS_THRESH = 30
        self.CORNER_DAMAGE_THRESH = 30

        # What reactive defence can do, is look at the map, and see if it's a filter.
        # If it's a filter and was attacked by pings and died, replace with a DEST.
        # Otherwise, just do regular build

        # Location mapped to a tuple of <UNIT, Priority>
        self.BASE_TEMPLATE = [
            # Chunk 1 --> Initial defences
            ([2, 11],  DESTRUCTOR),
            ([6, 11],  DESTRUCTOR),
            ([11, 11], DESTRUCTOR),
            ([16, 11], DESTRUCTOR),
            ([21, 11], DESTRUCTOR),
            ([25, 11], DESTRUCTOR),
            ([0, 13],  FILTER),
            ([1, 12],  FILTER),
            ([26, 12], FILTER),
            ([27, 13], FILTER),

            # Chunk 2 --> Building out the first wall
            ([3, 11],  FILTER),
            ([4, 11],  FILTER),
            ([5, 11],  FILTER),
            ([7, 11],  FILTER),
            ([8, 11],  FILTER),
            ([9, 11],  FILTER),
            ([10, 11], FILTER),
            ([12, 11], FILTER),
            ([13, 11], FILTER),
            ([23, 11], DESTRUCTOR),
            ([14, 11], FILTER),
            ([15, 11], FILTER),
            ([17, 11], FILTER),
            ([4, 9],   ENCRYPTOR),
            ([18, 11], FILTER),
            ([19, 11], FILTER),
            ([20, 11], FILTER),
            ([22, 11], FILTER),
            ([23, 11], FILTER),

            # Chunk 3 --> Encryptors + Some more defences
            ([25, 12], DESTRUCTOR),
            ([5, 9],   ENCRYPTOR),
            ([24, 13], FILTER),
            ([23, 13], FILTER),
            ([22, 13], FILTER),
            ([21, 13], FILTER),
            ([20, 13], FILTER),
            ([19, 13], FILTER),
            ([18, 13], FILTER),
            ([17, 13], FILTER),
            ([22, 9],  ENCRYPTOR),
            ([23, 9],  ENCRYPTOR),
            ([16, 13], FILTER),
            ([15, 13], FILTER),
            ([14, 13], FILTER),
            ([13, 13], FILTER),
            ([12, 13], FILTER),
            ([11, 13], FILTER),

        ]
        self.TEMPLATE_MASK = [item[0] for item in self.BASE_TEMPLATE]
        self.LEFT_CORNER_MASK = [
            [0, 13], [1, 13], [2, 13],
                     [1, 12], [2, 12],
                              [2, 11],
        ]
        self.RIGHT_CORNER_MASK = [
            [25, 13], [26, 13], [27, 13],
            [25, 12], [26, 12],
            [25, 11]
        ]
        self.R_CORNER_ATTACKED, self.L_CORNER_ATTACKED = False, False

    def get_unit_params(self, param):
        """ Extracts config parameters of units into a python dictionary.

        :param param: parameter key.
        :return: (dict)
        """
        params = {}

        for unit in self.config["unitInformation"]:
            if unit['display'] == 'Remove':
                continue
            else:
                params[unit['shorthand']] = unit[param]
        return params

    def find_low_health_units(self, state: gamelib.AdvancedGameState, search_mask, health_thresh):
        """ Find all static units that lost some health during last round.

        :param state: current game state.
        :param search_mask: list of locations - mask where to  search for damaged units.
        :param health_thresh: threshold for filtering low health units.
        :return: (list) locations of damaged units.
        """
        damaged_locs = []

        for loc in search_mask:
            # Find defensive unit at current location.
            curr_unit = [unit for unit in state.game_map[loc]
                         if unit.unit_type in [DESTRUCTOR, FILTER, ENCRYPTOR]]
            curr_unit = None if len(curr_unit) == 0 else curr_unit[0]
            if curr_unit is not None:
                health_limit = health_thresh * self.UNIT_HEALTH[curr_unit.unit_type]

                if curr_unit.stability < health_limit:
                    damaged_locs.append(loc)

        return damaged_locs

    @staticmethod
    def destroy_low_health_units(state, locs):
        """ Removes units provided in locs list.

        :param state: state object.
        :param locs: list of locations to be removed.
        :return:
        """
        for loc in locs:
            state.attempt_remove(loc)

    @staticmethod
    def check_corner(curr_state, prev_state, corner_mask):
        damage_sum = 0

        for loc in corner_mask:
            prev_units = prev_state.game_map[loc]
            curr_units = curr_state.game_map[loc]
            prev_unit = None
            prev_type = None
            curr_unit = None

            if prev_units is None or prev_units == []:
                # If unit did not exist here in last round, ignore location.
                continue
            else:
                for unit in prev_units:
                    if unit.unit_type in [DESTRUCTOR, FILTER, ENCRYPTOR]:
                        # If we find a defensive unit, then remember it.
                        prev_unit = unit
                        prev_type = unit.unit_type
                        break

            if prev_unit:
                if curr_units is None or curr_units == []:
                    # If we had a unit in prev round, but not in this one, increment damage.
                    damage_sum += prev_unit.stability
                else:
                    for unit in curr_units:
                        if unit.unit_type == prev_type:
                            # If we find a defensive unit of same type as last round, remember it.
                            curr_unit = unit
                            break
                    # Increment damage taken based on change in unit stability.
                    damage_sum += curr_unit.stability - prev_unit.stability

        return damage_sum

    def were_corners_attacked(self, curr_state, prev_state):
        """ Checks if corners were attacked in the last round.

        :param curr_state: state object.
        :param prev_state: state object.
        """
        left_damage, right_damage = 0, 0

        if not self.R_CORNER_ATTACKED:
            right_damage = max(0, self.check_corner(curr_state, prev_state, self.RIGHT_CORNER_MASK))
            debug_write("Right damage ", right_damage)

        if not self.L_CORNER_ATTACKED:
            left_damage = max(0, self.check_corner(curr_state, prev_state, self.LEFT_CORNER_MASK))
            debug_write("Left damage ", left_damage)

        self.R_CORNER_ATTACKED = right_damage > self.CORNER_DAMAGE_THRESH
        self.L_CORNER_ATTACKED = left_damage > self.CORNER_DAMAGE_THRESH

    def build_template(self, state: gamelib.AdvancedGameState, prev_state):
        """ Adds any defences to the priority queue if we were destroyed.

        :param state: game state.
        :param prev_state: game state.
        """
        if prev_state:
            self.were_corners_attacked(state, prev_state)
            debug_write(
                "Right Corner State: {}".format(self.R_CORNER_ATTACKED),
                "Left Corner State: {}".format(self.L_CORNER_ATTACKED)
            )
            #
            # if self.R_CORNER_ATTACKED:
            #     for i in range(len(self.BASE_TEMPLATE)):
            #         if self.BASE_TEMPLATE[i][0] in self.RIGHT_CORNER_MASK:
            #             debug_write("Updating Template ", self.BASE_TEMPLATE[i])
            #             self.BASE_TEMPLATE[i] = (self.BASE_TEMPLATE[i][0], DESTRUCTOR)
            #
            # if self.L_CORNER_ATTACKED:
            #     for i in range(len(self.BASE_TEMPLATE)):
            #         if self.BASE_TEMPLATE[i][0] in self.LEFT_CORNER_MASK:
            #             debug_write("Updating Template ", self.BASE_TEMPLATE[i])
            #             self.BASE_TEMPLATE[i] = (self.BASE_TEMPLATE[i][0], DESTRUCTOR)
            if self.R_CORNER_ATTACKED:
                for i in range(len(self.BASE_TEMPLATE)):
                    if self.BASE_TEMPLATE[i][0] in self.RIGHT_CORNER_MASK:
                        self.BASE_TEMPLATE[i] = (self.BASE_TEMPLATE[i][0], DESTRUCTOR)

                new_units = []
                for loc in self.RIGHT_CORNER_MASK:
                    if loc not in self.TEMPLATE_MASK:
                        new_units.append((loc, DESTRUCTOR))
                self.BASE_TEMPLATE = new_units + self.BASE_TEMPLATE

            if self.L_CORNER_ATTACKED:
                for i in range(len(self.BASE_TEMPLATE)):
                    if self.BASE_TEMPLATE[i][0] in self.LEFT_CORNER_MASK:
                        self.BASE_TEMPLATE[i] = (self.BASE_TEMPLATE[i][0], DESTRUCTOR)

                new_units = []
                for loc in self.LEFT_CORNER_MASK:
                    if loc not in self.TEMPLATE_MASK:
                        new_units.append((loc, DESTRUCTOR))
                self.BASE_TEMPLATE = new_units + self.BASE_TEMPLATE

        for unit in self.BASE_TEMPLATE:
            if state.get_resource(state.CORES) > self.UNIT_COSTS[unit[1]]:
                use_destruct = state.get_resource(state.CORES) > self.BUILD_DESTRUCTOR_WALLS_THRESH
                unit_type = DESTRUCTOR if use_destruct else unit[1]
                if state.can_spawn(unit_type, unit[0]):
                    state.attempt_spawn(unit_type, unit[0])

        low_health_units = self.find_low_health_units(
            state, self.TEMPLATE_MASK, self.REMOVE_HEALTH_THRESH)
        self.destroy_low_health_units(state, low_health_units)

    # def find_prev_unit_states(self, search_mask):
    #     """ Find states of units under search mast in the previous state.
    #
    #     :param search_mask: list of locations where to search for states.
    #     :return: list of (location, unit) pairs.
    #     """
    #     prev_units = []
    #     prev_locs = []
    #
    #     for loc in search_mask:
    #         units = self.prev_state.game_map[loc]
    #
    #         if units is None or units == []:
    #             continue
    #         else:
    #             for unit in units:
    #                 prev_units.append(unit)
    #                 prev_locs.append(loc)
    #
    #     return zip(prev_locs, prev_units)

