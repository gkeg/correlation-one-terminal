import pdb
import copy

import sys
sys.path.insert(0, '../')
import gamelib

"""
Need to encode the fact that you have more bits for next turn
Idea: Defend with scramblers, flip

"""


def emp_cheese(current_state: gamelib.AdvancedGameState):
    bits = current_state.get_resource(current_state.CORES)
    if bits < 3.0:
        return None, None

    global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
    config = current_state.config
    FILTER = config["unitInformation"][0]["shorthand"]
    ENCRYPTOR = config["unitInformation"][1]["shorthand"]
    DESTRUCTOR = config["unitInformation"][2]["shorthand"]
    PING = config["unitInformation"][3]["shorthand"]
    EMP = config["unitInformation"][4]["shorthand"]
    SCRAMBLER = config["unitInformation"][5]["shorthand"]

    """
    Tries to deploy emp's behind a line of units, while they fire at enemies
    Idk how many to send yet, but first need to make sure that it will fire at something while being hidden

    Check our side for rows from either side that we could hide behind
	For each, make sure we are NOT being hit and that we ARE hitting something
	Take the row where we hit the most
	For each of these calculate how much damage we could do with a single emp
	Place them at the point where we could do the most damage

    :param current_state: current game state object
    :param current_coins: current coins tuple (shield_money, attack_money)
    :return: tuple of (updated current_state object, updated current_coins object)
    """

    m = current_state.game_map

    # Check top 4 lines
    check = []
    for i in m.get_edge_locations(m.BOTTOM_LEFT)[:-5:-1]:
        check.append(i)
    for i in m.get_edge_locations(m.BOTTOM_RIGHT)[:-5:-1]:
        check.append(i)

    best = None
    for i in check:
        # Can we deploy?
        if current_state.contains_stationary_unit(i):
            continue

        curr = simulate_emp(copy.deepcopy(current_state), i)

        if best is None or curr > best[0]:
            best = [curr, i]

    num = min(int(best[0] / 15) + 1, int(bits/3))

    # I think
    # current_state.attempt_spawn(EMP, best[1], num)
    return best, num


"""
HELPER FUNCTIONS
"""


def has_destructor(state, locs):
    # destructor = json.loads(state.config)[]
    for i in locs:
        if len(state.game_map[i]) and state.game_map[i][0] == DESTRUCTOR:
            return True
    return False


# Checks how much damage the emp does if it starts in this state until it cross to enemy territory
def simulate_emp(state, loc):
    score = 0
    m = state.game_map
    path = state.find_path_to_edge(loc, m.TOP_RIGHT if loc[0] < 14 else m.TOP_LEFT)

    for i in path:
        if has_destructor(state, filter(lambda x: x[1] > 13, m.get_locations_in_range(i, 3))) or i[1] > 13:
            break

        unit = gamelib.GameUnit(EMP, state.config, 0, 40, *i)
        target = state.get_target(unit)
        if target:
            target.stability -= 4
            if target.stability < 0:
                m.remove_unit((target.x, target.y))
            score += min(4, target.stability + 4)

    return score
