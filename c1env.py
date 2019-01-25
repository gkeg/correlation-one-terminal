import os

class C1Env():
    def __init__(self, name):
        self.name = name
        self.num_inputs = 100
        self.num_attack_outputs = 100
        self.num_defence_outputs = 100

    def play_game(algo1, algo2):
        os.system('../scripts/run_algorithm.py ' + algo1 + ' ' + algo2)

        # Put the parse_replay shit in here, return the states, actions, rewards, dones w.r.t.
        # EACH PLAYER!
        return None
