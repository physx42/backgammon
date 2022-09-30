# agent
import random

# TODO import tf and keras
import tensorflow as tf
# from tensorflow import keras
from typing import List
import numpy as np

class Agent:
    def __init__(self, alpha, epsilon, learning_rate, gamma, num_features):
        self.num_features = num_features
        self.model = self.generate_model()
        self.alpha = alpha
        self.epsilon = epsilon
        self.learning_rate = learning_rate
        self.gamma = gamma

    def generate_model(self):
        inputs = tf.keras.Input(shape=(self.num_features,))
        x = tf.keras.layers.Dense(40, activation="sigmoid")(inputs)
        outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)
        return tf.keras.Model(inputs=inputs, outputs=outputs)

    def assess_features(self, features: np.ndarray):
        prediction = self.model(features[np.newaxis])
        return prediction[0].numpy().item()

    def epsilon_greedy_action(self, networks_outputs: List[float]) -> int:
        if np.random.rand() < self.epsilon:
            # Explore
            chosen_index = np.random.randint(0, len(networks_outputs))
        else:
            # Exploit
            possible_indices = np.argwhere(networks_outputs == np.amax(networks_outputs)).flatten().tolist()
            chosen_index = np.random.choice(possible_indices)
        return chosen_index

    def greedy_action(self, networks_outputs: List[float]) -> int:
        possible_indices = np.argmax(networks_outputs)
        chosen_index = np.random.choice(possible_indices)
        return chosen_index

if __name__ == '__main__':
    a = Agent(0.1, 0.01, 0.1, 0.95, 10)
    features = np.random.rand(10)
    print(features)
    print(a.assess_features(features))
