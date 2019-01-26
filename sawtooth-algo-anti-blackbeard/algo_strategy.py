import gamelib
import random
import copy
import time
import math
import warnings
from sys import maxsize
# Import our strategies
# offense
from strategies import emp_cheese, sell_vulnerable_line
from defences import Defences


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

        self.defences = Defences(config)
        self.prev_state = None

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

        self.defences.build_template(game_state, self.prev_state)
        self.prev_state = copy.deepcopy(game_state)

        if game_state.turn_number != 0:
            try:
                self.best_spawn(game_state)
            except Exception:
                self.attack(game_state)

        game_state.submit_turn()

    def best_spawn(self, state):
        self.time_start = time.time()
        locs = [[24, 10], [3, 10], [13, 0], [11, 2], [22, 8]]
        units = [EMP, PING, SCRAMBLER]
        bits = state.get_resource(state.BITS)

        # og_map = copy.deepcopy(state.game_map)

        best = (0, None)
        for loc in locs:
            for unit in units:
                cost = 3 if unit == EMP else 1
                if not state.can_spawn(unit, loc):
                    continue

                if time.time() - self.time_start < 2:
                    val = self.simulate(copy.deepcopy(state), unit, loc, int(bits / cost))
                    if val > best[0]:
                        best = (val, (loc, unit, int(bits / cost)))
                    else:
                        break

        top = 9 if state.turn_number <= 6 else 15

        if best[0] > 0:
            loc, unit, num = best[1]
            if best[0] > num * cost or state.get_resource(state.BITS) >= top:
                state.attempt_spawn(unit, loc, num)
        else:
            self.attack(state)

    def simulate(self, state: gamelib.AdvancedGameState, unit_type, spawn_loc=(13, 0), num_units=1):
        map = state.game_map

        """
        TODO: ENCRYPTORS
        """
        target_edge = map.TOP_RIGHT if spawn_loc[0] < 14 else map.TOP_LEFT

        path = state.find_path_to_edge(spawn_loc, target_edge)

        total_dmg = 0
        total_cores = 0

        frames = 2 if unit_type == PING else 4
        dmg = 0 if unit_type == SCRAMBLER else (1 if unit_type == PING else 3)

        for i in range(num_units):
            map.add_unit(unit_type, spawn_loc)
        idx = 0

        remaining = map[spawn_loc]

        map.remove_unit(spawn_loc)
        pings = 0
        while idx < len(path):

            loc = path[idx]

            for i in remaining:
                i.x = loc[0]
                i.y = loc[1]
                map[loc].append(i)

            for i in range(frames):
                defense_dmg = 4 * len(state.get_attackers(loc, 0))
                our_dmg = len(map[loc]) * dmg

                initial = len(map[loc])

                if map[loc]:
                    target = state.get_target(map[loc][0])
                else:
                    break

                if target:
                    target.stability -= our_dmg
                    total_dmg += our_dmg
                    total_cores += (our_dmg / target.max_stability) * target.cost
                    if target.stability < 0:
                        map.remove_unit([target.x, target.y])

                dead = 0
                for i in range(initial):

                    if defense_dmg <= 0 or dead == len(map[loc]):
                        break

                    # Killed one, did they kill more
                    if defense_dmg >= map[loc][dead].stability:
                        defense_dmg -= map[loc][dead].stability
                        dead += 1

                    # They didn't kill this one
                    else:
                        map[loc][dead].stability -= defense_dmg
                        break

                # kill the dead ones
                for i in range(dead):
                    map[loc].pop(0)

            remaining = map[loc]
            pings = remaining

            if len(remaining) == 0:
                break

            map.remove_unit(loc)

            idx += 1

            if loc[1] > 14:
                mod_path = state.find_path_to_edge(spawn_loc, target_edge)
                if path != mod_path and loc in mod_path:
                    idx = mod_path.index(loc) + 1
                    path = mod_path

        return 3.5 * len(pings) + total_cores

    # Attack with EMPs lol
    def attack(self, state: gamelib.AdvancedGameState):
        emp_loc = [3, 10]
        while state.can_spawn(EMP, emp_loc, 1):
            state.attempt_spawn(EMP, emp_loc, 1)

    # Build our static defence template
    def build_defences(self, state: gamelib.AdvancedGameState):
        # When we're at full build, do nothing!
        while state.get_resource(state.CORES) > 0 and not self.defences.build_done():
            loc, defence_type = self.defences.get_next_defence()
            if state.can_spawn(defence_type, loc):
                state.attempt_spawn(defence_type, loc)


    # Check if we need to do an anti-blackbeard defence
    def anti_blackbeard(self, state: gamelib.AdvancedGameState):
        return True

    def blackbeard(self, state: gamelib.AdvancedGameState, left=False):
        # Do initial first turn setup
        # Spawn front destructors and encryptors
        destr = [[23,13], [24, 13]]
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
