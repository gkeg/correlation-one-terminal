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
turn1
...
"""

replay = 'p1-13-01-2019-12-04-37-1547399077700--1034977755.replay'
replay = 'p1-16-01-2019-10-17-45-1547651865424--2108863707.replay'

with open('replays/{}'.format(replay), 'r') as f:
    _ = f.readline()
    conf = f.readline()
    _ = f.readline()
    rest = f.readlines()

rest = [x.strip() for x in rest] 

memory = list(map(lambda x: gamelib.GameState(json.loads(conf) , x), rest))


# Testing to make sure it's right
print(memory)
print(memory[0].turn_number)
print(memory[0].my_health)

	