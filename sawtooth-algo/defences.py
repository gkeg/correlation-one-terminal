# Defences class, will hold the priorities for everything, and find out
# what kind of shit to build next. Put reactive defence stuff in here
from heapq import heappush, heappop
import gamelib
import pdb
import ast
import copy

class Defences():
    # Initialize the build queue
    # Add back the config
    def __init__(self, config):
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]

        self.destroyed = []

        # What reactive defence can do, is look at the map, and see if it's a filter.
        # If it's a filter and was attacked by pings and died, replace with a DEST.
        # Otherwise, just do regular build

        # Location mapped to a tuple of <UNIT, Priority>
        self.priorities_map = {
            # Chunk 1 --> Initial defences
            '[2, 11]': (1, DESTRUCTOR),
            '[6, 11]': (2, DESTRUCTOR),
            '[11, 11]': (3, DESTRUCTOR),
            '[16, 11]': (4, DESTRUCTOR),
            '[21, 11]': (5, DESTRUCTOR),
            '[25, 11]': (6, DESTRUCTOR),
            '[0, 13]': (7, FILTER),
            '[1, 12]': (8, FILTER),
            '[26, 12]': (9, FILTER),
            '[27, 13]': (10, FILTER),

            # Chunk 2 --> Building out the first wall
            '[3, 11]': (12, FILTER),
            '[4, 11]': (13, FILTER),
            '[5, 11]': (14, FILTER),
            '[7, 11]': (15, FILTER),
            '[8, 11]': (16, FILTER),
            '[9, 11]': (17, FILTER),
            '[10, 11]': (18, FILTER),
            '[12, 11]': (19, FILTER),
            '[13, 11]': (20, FILTER),
            '[14, 11]': (21, FILTER),
            '[15, 11]': (22, FILTER),
            '[17, 11]': (23, FILTER),
            '[18, 11]': (24, FILTER),
            '[19, 11]': (25, FILTER),
            '[20, 11]': (26, FILTER),
            '[22, 11]': (27, FILTER),
            '[23, 11]': (28, DESTRUCTOR),

            # Chunk 3 --> Encryptors + some more defences
            '[25, 12]': (29, DESTRUCTOR),
            '[4, 9]': (30, ENCRYPTOR),
            '[5, 9]': (31, ENCRYPTOR),
            '[24, 13]': (32, FILTER),
            '[23, 13]': (33, FILTER),
            '[22, 13]': (34, FILTER),
            '[21, 13]': (35, FILTER),
            '[20, 13]': (36, FILTER),
            '[19, 13]': (37, FILTER),
            '[18, 13]': (38, FILTER),
            '[17, 13]': (39, FILTER),
            '[22, 9]': (40, ENCRYPTOR),
            '[23, 9]': (41, ENCRYPTOR),
            '[16, 13]': (42, FILTER),
            '[15, 13]': (43, FILTER),
            '[14, 13]': (44, FILTER),
            '[13, 13]': (45, FILTER),
            '[12, 13]': (46, FILTER),
            '[11, 13]': (47, FILTER),

            # Chunk 4 --> TBD
        }

        # Heapify the defences: Build our priority queue
        self._pq = []
        for k, v in self.priorities_map.items():
            # Value stored as a string, parse and unpack
            priority, defence_type = v
            heappush(self._pq, (priority, k, defence_type))

    def build_done(self):
        return self.pq == []

    def get_next_defence(self):
        # Find out if we should replace w/ destructor with some logic later
        if self.pq == []:
            return
        priority, loc, defence_type = heappop(self.pq)
        return (ast.literal_eval(loc), defence_type)

    # Adds any defences to the priority queue if we were destroyed
    def refresh_state(self, state: gamelib.AdvancedGameState):
        # Put reactive defence here
        self.pq = copy.deepcopy(self._pq)

    # Repair any defences that might be damaged
    def repair_defences(self, state: gamelib.AdvancedGameState):



# For debugging
'''
if __name__ == '__main__':
    defence = Defences()
    defence.get_next_defence()
'''
