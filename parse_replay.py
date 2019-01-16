import json
import sys

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

replay = 'p1-13-01-2019-12-04-37-1547399077700--1034977755.replay'

with open('replays/{}'.format(replay), 'r') as f:
    _ = f.readline()
    conf = f.readline()
    _ = f.readline()
    s = f.readline()

print(s)

game_state = gamelib.GameState(json.loads(conf) , s)

print(game_state.turn_number)
print(game_state.my_health)

	