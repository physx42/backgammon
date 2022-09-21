# agent
import random

# TODO import tf and keras
# import tensorflow as tf
# from tensorflow import keras
from typing import List
import numpy as np

class Agent:
    def __init__(self, alpha, epsilon, learning_rate, gamma):
        self.model = self.generate_model()
        self.alpha = alpha
        self.epsilon = epsilon
        self.learning_rate = learning_rate
        self.gamma = gamma

    def generate_model(self):
        # TODO implement model definition
        pass

    def assess_features(self, features):
        # TODO implement feedforward
        return random.random()

    def epsilon_greedy(self, networks_outputs: List[float]):
        if np.random.rand() < self.epsilon:
            # Explore
            chosen_index = np.random.randint(0, len(networks_outputs))
        else:
            # Exploit
            chosen_index = np.argmax(networks_outputs)
        return chosen_index

