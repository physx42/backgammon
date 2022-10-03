# game
import copy
from typing import List
from board import Board
from colour import Colour
from TDGammon_agent import TDagent
from random_agent import RandomAgent
import numpy as np
import logging
import matplotlib.pyplot as plt
import time

class Game:
    def __init__(self, player1, player2):
        self.b = None
        self.players = [player1, player2]
        self.pID = 0
        self.player_colours = [Colour.Red, Colour.White]
        self.step = 0
        self.features_log = [None, None]
        self.game_count = 0
        self.win_counts = [0, 0]
        self.game_len_history = []
        self.win_history = []  # Will record ratio of games won by player 0 by game

    def choose_first_player(self):
        self.step = 0
        if np.random.rand() > 0.5:
            self.pID = 0
        else:
            self.pID = 1
        self.b.set_player(self.player_colours[self.pID])
        self.update_features_log()
        logging.info(f"First player is {self.pID}")

    def next_player(self):
        self.pID = 1 - self.pID
        self.b.set_player(self.player_colours[self.pID])
        self.update_features_log()
        self.step += 1
        logging.info(f"Turn {self.step}: {self.player_colours[self.pID]}")

    def update_features_log(self):
        self.features_log[self.pID] = self.b.calculate_board_features(self.b.board)

    def play_game(self, simple_board=False):
        self.b = Board(True, simple_board)
        self.choose_first_player()
        while True:
            dice_rolls = self.b.roll_dice()
            logging.info(f"Dice rolls: {dice_rolls}")
            start_move_search = time.time()
            move_tree, board_tree = self.b.get_possible_moves_from_dice(dice_rolls)
            print(f"Move search took {time.time() - start_move_search} seconds.")
            self.b.print_move_tree(move_tree)
            self.b.simple_board_representation("Initial board:", header=True)
            possible_boards = board_tree.get_list_of_leaves(top=True)
            logging.info(f"{len(possible_boards)} possible moves")

            reward = 0  # default
            if len(board_tree.children) > 0:
                possible_features = []
                for board in possible_boards:
                    possible_features.append(self.b.calculate_board_features(board))
                    self.b.simple_board_representation("", board, count=len(possible_features))
                chosen_action = self.players[self.pID].choose_action(possible_features)
                self.b.enact_provisional_move(possible_boards[chosen_action])
                if self.b.game_won(self.player_colours[self.pID]):
                    reward = 1
                else:
                    reward = 0
                self.players[self.pID].update_model(
                        self.features_log[self.pID], possible_features[chosen_action], reward)

            if reward == 1:
                # Game ended
                logging.info(f"Player {self.pID} ({self.player_colours[self.pID]}) won!")
                self.game_count += 1
                self.win_counts[self.pID] += 1
                self.win_history.append(self.win_counts[0] / (self.win_counts[0] + self.win_counts[1]))
                self.game_len_history.append(self.step)
                print(f"Game {self.game_count} ended after {self.step} steps (win ratio: {self.win_history[-1]:.4f}).")
                break
            else:
                self.next_player()


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format="%(message)s")
    common_TD_agent = TDagent()
    g = Game(common_TD_agent, common_TD_agent)
    for episode in range(0, 5000):
        g.play_game(simple_board=False)
    # plt.plot(g.win_history)
    # plt.show()
    train_win_history = copy.deepcopy(g.win_history)
    train_len_history = copy.deepcopy(g.game_len_history)

    g = Game(common_TD_agent, RandomAgent())
    for episode in range(0, 200):
        g.play_game(simple_board=False)
    plt.plot(train_win_history)
    plt.plot(g.win_history)
    plt.show()

    plt.plot(train_len_history)
    plt.plot(g.game_len_history)
    plt.show()




