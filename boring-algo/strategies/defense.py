import pdb
import copy

import sys
sys.path.insert(0, '../')
import gamelib


def sell_vulnerable_line(state: gamelib.AdvancedGameState):
    state.warn("DEBUG")

    danger = []
    removed = False
    for i in range(13,11, -1):
        for j in range(13-i, i + 15):
            if state.contains_stationary_unit([j,i]):
                state.attempt_remove([j,i])
                removed = True

        if removed:
            break


# Probably not worth it, might delete later

# def find_vulnerable_line(state: gamelib.AdvancedGameState):
#
#     # Figure out how to get this another way
#     global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
#     config = state.config
#     FILTER = config["unitInformation"][0]["shorthand"]
#     ENCRYPTOR = config["unitInformation"][1]["shorthand"]
#     DESTRUCTOR = config["unitInformation"][2]["shorthand"]
#     PING = config["unitInformation"][3]["shorthand"]
#     EMP = config["unitInformation"][4]["shorthand"]
#     SCRAMBLER = config["unitInformation"][5]["shorthand"]
#
#
#     enemy_cores =  state.get_resource(state.CORES, player_index=1)
#
#
#     # Check enemy front lines for any gaps
#     for i in range(15,18):
#         streak = 0
#         gap = 0
#         vulnerable_line = 0
#         for j in range(i-13, ):
#             if not state.contains_stationary_unit([j,i]):
#                 gap += 1
#
#             streak += 1
#         if enemy_cores > gap:







