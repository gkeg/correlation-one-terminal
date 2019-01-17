import json
import sys
import pdb
import os

# Workaround to get gamelib in
sys.path.insert(0, './python-algo/')
import gamelib

s = ""

"""
Replay is of form
empty
conf
empty
turn0
turn1
...
"""

# Probably want some functionality to keep only one replay in the replay folder

# Look at the replay, get the history, and then delete. Explore later.
# If you want a specific replay, you need to specify the file name
# Otherwise we assume there is only one
def parse_replay(replay=None):
    # Keep a memory of all of the states
	files = os.listdir('./replays/')

	if not len(files):
		return None

	filename = replay if replay else files[0]
	with open('replays/{}'.format(filename), 'r') as f:
		_ = f.readline()
		conf = f.readline()
		_ = f.readline()
		# Get all the rest of the states
		memory =  [gamelib.GameState(json.loads(conf), x) for x in f.readlines()]

	return memory


# For testing
if __name__ == '__main__':
    parse_replay()
