import gamelib
import random
import copy
import math
import warnings
from sys import maxsize

from . import gamelib
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
        self.filter,self.encryptor,self.destructor,self.ping,self.emp,self.scrambler = [i for i in range(6)]
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
        game_state.suppress_warnings(True)  #Uncomment this line to suppress warnings.

        self.blackbeard(game_state)
        # self.build_bad_wall(game_state)
        # sell_vulnerable_line(game_state)
        #
        # best, num = emp_cheese(game_state)
        # if best and game_state.can_spawn(EMP, best[1]):
        #     game_state.attempt_spawn(EMP, best[1], num)

        game_state.submit_turn()


    def build_bad_wall(self, game_state):
        line = 12
        for i in range(1,20):
            if game_state.CORES < 1:
                return
            unit = FILTER if i % 2 else DESTRUCTOR
            if game_state.can_spawn(unit, (i, line)):
                game_state.attempt_spawn(unit, (i, line))


    def blackbeard(self, state: gamelib.AdvancedGameState, left=False):
        # Spawn front destructors and encryptors
        destr = [[23,13], [24,13]]
        encr = [[23,12], [24,12], [25,13], [23,11]]
        for i in destr:
            if state.can_spawn(DESTRUCTOR, i):
                state.attempt_spawn(DESTRUCTOR, i)

        for i in encr:
            if state.can_spawn(ENCRYPTOR, i):
                state.attempt_spawn(ENCRYPTOR, i)

        end = 12 if state.turn_number > 0 else 19

        # open = False
        #spawn remaining filters
        for i in range(22,end,-1):
            # if not state.contains_stationary_unit([i,i-12]) and state.get_resource(state.CORES) < 1:
            #     open = True
            if state.can_spawn(FILTER, [i,i-12]):
                state.attempt_spawn(FILTER, [i,i-12])

        # if we have extra cores use some of them18,13,9,5 then filters between
        prio = [[1,13], [1,12], [0,13],[18,10], [18,11], [13,11], [9,10], [9,11],[5,11]]
        which = [DESTRUCTOR, DESTRUCTOR, FILTER, DESTRUCTOR, FILTER, DESTRUCTOR, DESTRUCTOR, FILTER, DESTRUCTOR]

        for i in range(len(prio)):
            if state.get_resource(state.CORES) > 4:
                if state.can_spawn(which[i], prio[i]):
                    state.attempt_spawn(which[i], prio[i])

        i = 0
        # Try to spawn some random stuff
        while i < 10 and state.get_resource(state.CORES) > 6:
            row = random.randint(10,11)
            col = random.randint(13-row, 19)
            type = DESTRUCTOR if random.randint(0,1) else FILTER
            if state.can_spawn(type, [row,col] ):
                state.attempt_spawn(type, [row,col])

        if state.turn_number == 0:
            state.attempt_spawn(PING, [13,0],2)
            state.attempt_spawn(PING, [14,0],2)
        # elif open:
        #     state.attempt_spawn(EMP, [17, 3])
        elif state.turn_number % 2:
            bits = state.get_resource(state.BITS)
            if bits > 4:
                state.attempt_spawn(PING, [14,0], 4)
            state.attempt_spawn(PING, [13,0], int(state.get_resource(state.BITS)))


    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
