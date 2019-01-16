import json
import sys
import pdb

# Workaround to get gamelib in
sys.path.insert(0, './pickle-algo/')
import gamelib

s = ""

"""
Replay is of form
empty
conf
empty
turn0
rmpty
turn1
...
"""

# Tilman Testing
# replay = 'p1-13-01-2019-12-04-37-1547399077700--1034977755.replay'

# Probably want some functionality to keep only one replay in the replay folder

# Look at the replay, get the history, and then delete. Explore later.
def parse_replay(replay='p1-15-01-2019-18-42-30-1547595750490-1556220261.replay'):
    # Keep a memory of all of the states
    with open('replays/{}'.format(replay), 'r') as f:
        _ = f.readline()
        conf = f.readline()
        _ = f.readline()
        # Get all the rest of the states
        memory = [gamelib.GameState(json.loads(conf), x) for x in f.readlines()]

    return memory

# For testing
if __name__ == '__main__':
    parse_replay()
