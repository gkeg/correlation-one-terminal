# Defences class, will hold the priorities for everything, and find out
# what kind of shit to build next. Put reactive defence stuff in here
from heapq import heappush, heappop
import gamelib
import pdb
import ast

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
        }

        # Heapify the defences: Build our priority queue
        self.pq = []
        for k, v in self.priorities_map.items():
            # Value stored as a string, parse and unpack
            priority, defence_type = v
            heappush(self.pq, (priority, k, defence_type))

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
        return True


# For debugging
'''
if __name__ == '__main__':
    defence = Defences()
    defence.get_next_defence()
'''
