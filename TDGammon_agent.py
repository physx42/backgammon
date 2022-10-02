from agent import Agent
from typing import List


class TDagent:
    def __init__(self):
        self.agent = Agent(0.1, 0.01, 0.7, 196)

    def choose_action(self, states: List[List]):
        assessments = []
        for state in states:
            assessments.append(self.agent.assess_features(state).numpy().item())
        chosen_board_index = self.agent.epsilon_greedy_action(assessments)

        return chosen_board_index

    def update_model(self, previous_state, new_state, reward):
        self.agent.update_model(previous_state, new_state, reward)



