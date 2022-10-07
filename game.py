# game
import copy
from typing import List
from board import Board
from TDGammon_agent import TDagent
from random_agent import RandomAgent
import numpy as np
import logging
import matplotlib.pyplot as plt
import time

class Game:
    def __init__(self, player1, player2, simple_board=False):
        self.players = [player1, player2]
        self.board = None
        self.pID = 0
        self.step = 0
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
        logging.info(f"First player is {self.pID}")

    def next_player(self):
        self.pID = 1 - self.pID
        self.step += 1
        logging.info(f"Turn {self.step}: Player {self.pID}")

    def roll_dice(self) -> List[int]:
        rolls = []
        for n in range(0, 2):
            roll = np.random.randint(1, 7)
            rolls.append(roll)
        if rolls[0] == rolls[1]:
            # Have rolled a double
            roll = rolls[0]
            rolls.append(roll)
            rolls.append(roll)
        return rolls

    def play_game(self, simple_board):
        start_game_time = time.time()
        self.board = Board(simple_board)
        self.choose_first_player()
        while True:
            player_agent = self.players[self.pID]
            rolls = self.roll_dice()
            logging.info(f"Dice rolls: {rolls}")
            max_move = None
            while len(rolls) > 0:
                logging.debug(f"Unused rolls: {rolls}")
                move_search_time = time.time()
                permitted_moves = self.board.permitted_moves(rolls, self.pID)
                logging.debug(f"Move search took {time.time() - move_search_time} seconds.")
                logging.info(f"{len(permitted_moves)} possible moves: {permitted_moves}")
                current_state = self.board.encode_features(self.pID)
                max_value = -np.inf
                max_move = None
                move_eval_time = time.time()
                for move in permitted_moves:
                    temp_board = copy.deepcopy(self.board)
                    temp_board.perform_move(*move, self.pID)
                    new_state = temp_board.encode_features(self.pID)
                    value = player_agent.assess_features(new_state)
                    # Find optimal policy. Note that due to randomness of dice rolls, epsilon-greedy is not required.
                    if value > max_value:
                        max_value = value
                        max_move = move
                logging.debug(f"Move evaluation took {move_eval_time - time.time()} seconds")
                if max_move is not None:
                    self.board.perform_move(*max_move, self.pID)
                    logging.debug(
                        f"Board state: X: (b{self.board.x_bar}){self.board.x_board}(r{self.board.x_removed}), O: (b{self.board.o_bar}){self.board.o_board} ({self.board.o_removed}). ")

                    if self.board.game_won(self.pID):
                        reward = 1
                        episode_end = True
                        break
                    else:
                        reward = 0
                        episode_end = False
                    player_agent.update_model(current_state, new_state, reward, episode_end)
                    del rolls[rolls.index(max_move[1])]
                else:
                    reward = 0
                    episode_end = False
                    break  # Couldn't make a move so go to next player
                new_state = self.board.encode_features(self.pID)

            if reward == 1:
                # Game ended
                logging.info(f"Player {self.pID} won!")
                self.game_count += 1
                self.win_counts[self.pID] += 1
                self.win_history.append(self.win_counts[0] / (self.win_counts[0] + self.win_counts[1]))
                self.game_len_history.append(self.step)
                print(f"Game: {self.game_count}\tSteps: {self.step}\tElapsed:{time.time() - start_game_time:.4f}s\t"
                      f"Winner: Player {self.pID}\tWin ratio: {self.win_history[-1]:.4f}")
                break
            else:
                self.next_player()


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format="%(message)s")
    common_TD_agent = TDagent(0.1, 0.7, 196)
    g = Game(common_TD_agent, common_TD_agent)
    for episode in range(0, 5000):
        g.play_game(simple_board=False)

    train_win_history = copy.deepcopy(g.win_history)
    train_len_history = copy.deepcopy(g.game_len_history)

    print("Starting test phase versus RandomAgent(). Learning disabled.")
    common_TD_agent.disable_learning()
    g = Game(common_TD_agent, RandomAgent())
    for episode in range(0, 1000):
        g.play_game(simple_board=False)
    plt.plot(train_win_history)
    plt.plot(g.win_history)
    plt.show()

    plt.plot(train_len_history)
    plt.plot(g.game_len_history)
    plt.show()




