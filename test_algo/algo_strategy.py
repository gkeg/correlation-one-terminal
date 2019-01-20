import gamelib
import random
import copy
import math
import warnings
from sys import maxsize

# Import our strategies
# offense
from strategies import emp_cheese, sell_vulnerable_line

class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        random.seed()

    def on_game_start(self, config):
        """
        Read in config and perform any initial setup here
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]

    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.AdvancedGameState(self.config, turn_state)

        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        # game_state.suppress_warnings(True)  #Uncomment this line to suppress warnings.

        self.build_bad_wall(game_state)
        sell_vulnerable_line(game_state)

        best, num = emp_cheese(game_state)
        if best and game_state.can_spawn(EMP, best[1]):
            game_state.attempt_spawn(EMP, best[1], num)

        game_state.submit_turn()


    def build_bad_wall(self, game_state):
        line = 12
        for i in range(1,20):
            if game_state.CORES < 1:
                return
            unit = FILTER if i % 2 else DESTRUCTOR
            if game_state.can_spawn(unit, (i, line)):
                game_state.attempt_spawn(unit, (i, line))


    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
