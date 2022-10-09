from typing import List
import numpy as np
import tensorflow as tf
import logging
import os
import datetime


class TDagent:
    def __init__(self, alpha=0.1, LAMBDA=0.7, num_features=196):
        self.num_features = num_features
        self.model = self.generate_model()
        self.alpha = alpha
        self.LAMBDA = LAMBDA

        self.trace = []
        self.learning_enabled = True

    def reset_trace(self):
        for i in range(len(self.trace)):
            self.trace[i].assign(tf.zeros(self.trace[i].get_shape()))

    def generate_model(self):
        inputs = tf.keras.Input(shape=(self.num_features,))
        x = tf.keras.layers.Dense(40, activation="sigmoid")(inputs)
        outputs = tf.keras.layers.Dense(1, activation="sigmoid")(x)
        return tf.keras.Model(inputs=inputs, outputs=outputs)

    def assess_features(self, state: np.ndarray):
        prediction = self.model(state)
        return tf.reduce_sum(prediction)

    @tf.function
    def update_model(self, previous_state, new_state, reward, episode_end):
        if self.learning_enabled:
            with tf.GradientTape() as tape:
                value_next = self.assess_features(new_state)
            trainable_vars = self.model.trainable_variables
            grads = tape.gradient(value_next, trainable_vars)

            if len(self.trace) == 0:
                for grad in grads:
                    self.trace.append(tf.Variable(tf.zeros(grad.get_shape()), trainable=False))
            td_error = tf.reduce_sum(reward + value_next - self.assess_features(previous_state))
            for i in range(len(grads)):
                self.trace[i].assign((self.LAMBDA * self.trace[i]) + grads[i])
                grad_trace = self.alpha * td_error * self.trace[i]
                self.model.trainable_variables[i].assign_add(grad_trace)

            if episode_end:
                self.reset_trace()

    def enable_learning(self):
        self.learning_enabled = True

    def disable_learning(self):
        self.learning_enabled = False

    def save(self, checkpoint_name):
        directory = "checkpoints"
        if not os.path.exists(directory):
            os.mkdir(directory)

        path = directory + "/" + checkpoint_name
        self.model.save_weights(path)

        logging.info("saving checkpoint [path = %s]", path)

        return path

    def load(self, checkpoint_name):
        logging.info("loading checkpoint [path = %s]", checkpoint_name)

        self.model.load_weights("checkpoints/" + checkpoint_name)


if __name__ == '__main__':
    a = TDagent(0.1, 0.01, 0.7, 10)
    features = np.random.rand(10)
    print(features)
    print(a.assess_features(features))
