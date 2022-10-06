from typing import List
import numpy as np


class RandomAgent:
    def __init__(self):
        pass

    def assess_features(self, state):
        return np.random.rand()

    def choose_action(self, states: List[List]):
        chosen_board_index = np.random.randint(0, len(states))
        return chosen_board_index

    def update_model(self, previous_state, new_state, reward, episode_end):
        pass

