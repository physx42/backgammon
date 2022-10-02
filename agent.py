# agent
import logging

import tensorflow as tf
from typing import List
import numpy as np
import logging


class Agent:
    def __init__(self, alpha, epsilon, learning_rate, num_features):
        self.num_features = num_features
        self.model = self.generate_model()
        self.alpha = alpha
        self.epsilon = epsilon
        self.learning_rate = learning_rate

        self.trace = []

    def reset_trace(self):
        for i in range(len(self.trace)):
            self.trace[i].assign(tf.zeros(self.trace[i].get_shape()))

    def generate_model(self):
        inputs = tf.keras.Input(shape=(self.num_features,))
        x = tf.keras.layers.Dense(40, activation="sigmoid")(inputs)
        outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)
        return tf.keras.Model(inputs=inputs, outputs=outputs)

    def assess_features(self, features: np.ndarray):
        prediction = self.model(features[np.newaxis])
        return tf.reduce_sum(prediction)

    def epsilon_greedy_action(self, networks_outputs: List[float]) -> int:
        if np.random.rand() < self.epsilon:
            # Explore
            chosen_index = np.random.randint(0, len(networks_outputs))
        else:
            # Exploit
            possible_indices = np.argwhere(networks_outputs == np.amax(networks_outputs)).flatten().tolist()
            chosen_index = np.random.choice(possible_indices)
        logging.debug("Network outputs:")
        logging.debug([f"{x:.5f}" for x in networks_outputs])
        logging.info(f"Chosen action: {chosen_index}")
        return chosen_index

    def greedy_action(self, networks_outputs: List[float]) -> int:
        possible_indices = np.argmax(networks_outputs)
        chosen_index = np.random.choice(possible_indices)
        return chosen_index

    def update_model(self, previous_state, new_state, reward):
        with tf.GradientTape() as tape:
            value_next = self.assess_features(new_state)
        trainable_vars = self.model.trainable_variables
        grads = tape.gradient(value_next, trainable_vars)

        if len(self.trace) == 0:
            for grad in grads:
                self.trace.append(tf.Variable(tf.zeros(grad.get_shape()), trainable=False))
        td_error = tf.reduce_sum(reward + value_next - self.assess_features(previous_state))
        for i in range(len(grads)):
            self.trace[i].assign((self.learning_rate * self.trace[i]) + grads[i])
            grad_trace = self.alpha * td_error * self.trace[i]
            self.model.trainable_variables[i].assign_add(grad_trace)


if __name__ == '__main__':
    a = Agent(0.1, 0.01, 0.7, 10)
    features = np.random.rand(10)
    print(features)
    print(a.assess_features(features))
