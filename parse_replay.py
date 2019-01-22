import json
import sys
import os
import numpy as np

# Workaround to get gamelib in
sys.path.insert(0, './python-algo/')
import gamelib


# Replay is of form
# empty
# conf
# empty
# turn0
# turn1
# ...


def create_parsed_units(game_map, units, config):
    """ Parses player units and updates the state map with player units.

    :param game_map: a [28 x 28] numpy matrix.
    :param units: player units object usually found in state["p1Units"].
    :param config: parsed json of the game config.
    :return: updated game_map [28 x 28] matrix.
    """
    typedef = config.get("unitInformation")
    for i, unit_types in enumerate(units):
        for uinfo in unit_types:
            unit_type = typedef[i].get("shorthand")
            sx, sy, shp = uinfo[:3]
            x, y = map(int, [sx, sy])

            game_map[x][y] = unit_type

    return game_map


def find_attack_paths(opponent_map, num_wall_levels=4, wall_thresh=.3):
    """ WIP do not use.

    :param opponent_map:
    :param num_wall_levels:
    :return:
    """
    for level in range(num_wall_levels):
        level_idx = 14 - level
        total_units_on_level = np.sum(opponent_map[level_idx, :])
        level_width = 28 - 2 * level_idx

        if float(total_units_on_level) / float(level_width) > wall_thresh:
            # Find what exit points are blocked
            pass


def parse_state(serialized_config, serialized_state_string):
    """ Parses state from serialized state string and returns a [28 x 28] matrix of the game_map.

    :param serialized_config: serialized config read from the config file.
    :param serialized_state_string: serialized string from the .replay file.
    :return: [28 x 28] game_state matrix with player units positions.
    """
    state = json.loads(serialized_state_string)
    config = json.loads(serialized_config)
    game_map = np.zeros((28, 28))

    game_map = create_parsed_units(game_map, state["p1Units"], config)
    game_map = create_parsed_units(game_map, state["p2Units"], config)
    return game_map


def parse_replay(replay=None, config_filename=None):
    # Probably want some functionality to keep only one replay in the replay folder
    # Look at the replay, get the history, and then delete. Explore later.
    # If you want a specific replay, you need to specify the file name
    # Otherwise we assume there is only one

    # Keep a memory of all of the states
    files = os.listdir('./replays/')
    config_raw = ""

    if config_filename is not None:
        with open(config_filename, 'r') as f:
            config_raw = f.read()

    if not len(files):
        return None

    filename = replay if replay else files[0]
    with open('replays/{}'.format(filename), 'r') as f:
        _ = f.readline()
        conf = f.readline()
        _ = f.readline()
        # Get all the rest of the states
        memory = [gamelib.GameState(json.loads(conf if config_filename is None else config_raw), x)
                  for x in f.readlines()]

        # Ruslan is just testing here.
        # all_items = [memory[i].game_map[[9, 8]] for i in range(len(memory))]
        #
        # state = memory[60]
        # m = state.game_map
        # attack_path = state.find_path_to_edge([6, 7], m.BOTTOM_LEFT)
        # path_to_defend = [i for i in attack_path if i[1] <= 13]


# For testing
if __name__ == '__main__':
    parse_replay('0-0-2019-19-17-45.replay',
                 '/home/nikolaevra/dev/correlation-one-terminal/game-configs.json')
