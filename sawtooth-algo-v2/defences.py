#  Defences class, will hold the priorities for everything, and find out
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
        self.flipped = False

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
            ([4, 9], ENCRYPTOR),
            ([18, 11], FILTER),
            ([19, 11], FILTER),
            ([20, 11], FILTER),
            ([22, 11], FILTER),
            ([23, 11], FILTER),

            # Chunk 3 --> Encryptors + Some more defences
            ([25, 12], DESTRUCTOR),
            ([5, 9], ENCRYPTOR),
            ([24, 13], FILTER),
            ([23, 13], FILTER),
            ([22, 13], FILTER),
            ([21, 13], FILTER),
            ([20, 13], FILTER),
            ([19, 13], FILTER),
            ([18, 13], FILTER),
            ([17, 13], FILTER),
            ([22, 9], ENCRYPTOR),
            ([23, 9], ENCRYPTOR),
            ([16, 13], FILTER),
            ([15, 13], FILTER),
            ([14, 13], FILTER),
            ([13, 13], FILTER),
            ([12, 13], FILTER),
            ([11, 13], FILTER),
        ]


        self.TEMPLATE_MASK = [item[0] for item in self.BASE_TEMPLATE]

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

    def build_template(self, state: gamelib.AdvancedGameState):
        """ Adds any defences to the priority queue if we were destroyed.
        :param state: game state.
        :return:
        """
        for unit in self.BASE_TEMPLATE:
            if state.get_resource(state.CORES) > self.UNIT_COSTS[unit[1]]:
                if state.can_spawn(unit[1], unit[0]):
                    state.attempt_spawn(unit[1], unit[0])

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
