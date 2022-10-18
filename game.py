# game
import copy
from typing import List, Tuple
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
        return self.pID

    def next_player(self):
        self.pID = 1 - self.pID
        self.step += 1
        logging.info(f"Turn {self.step}: Player {self.pID}")

    def set_player(self, player_num):
        self.pID = player_num
        self.step += 1
        logging.info(f"Turn {self.step}: Player {self.pID} (externally set)")

    def _roll_dice(self) -> List[int]:
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

    def generate_starting_board(self, endgame_board=False):
        self.board = Board(endgame_board)

    def training_game(self, endgame_board: bool) -> float:
        start_game_time = time.time()
        # Generate start board
        self.generate_starting_board(endgame_board)
        # Start game
        self.choose_first_player()
        while True:
            player_agent = self.players[self.pID]
            rolls = self._roll_dice()
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
                    logging.debug(f"Board state: X: (b{self.board.x_bar}){self.board.x_board}(r{self.board.x_removed}),"
                                  f" O: (b{self.board.o_bar}){self.board.o_board} ({self.board.o_removed}). ")
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
                total_game_time = time.time() - start_game_time
                steps_per_second = self.step / total_game_time
                print(f"Game: {self.game_count}\tSteps: {self.step}\tElapsed:{total_game_time:.4f}s\t"
                      f"Steps per sec:{steps_per_second:.1f}\tWinner: Player {self.pID}\t"
                      f"Win ratio: {self.win_history[-1]:.4f}")
                break
            else:
                self.next_player()
        return total_game_time

    def testing_game(self, endgame_board: bool) -> float:
        start_game_time = time.time()
        # Generate start board
        self.generate_starting_board(endgame_board)
        # Start game
        self.choose_first_player()
        while True:
            player_agent = self.players[self.pID]
            rolls = self._roll_dice()
            logging.info(f"Player {self.pID} rolls dice: {rolls}")
            # max_move = None
            best_value, best_moves = self.move_tree_analysis(player_agent, self.board, rolls, [])
            for move in best_moves:
                logging.debug(f"Moves planned by AI: {best_moves} from dice rolls {rolls}")
                old_board = copy.deepcopy(self.board)
                start_pos_player, move_distance = move
                logging.debug(
                    f"AI now performing move (with anim): piece at {start_pos_player}, moving {move_distance} pips")
                self.board.perform_move(start_pos_player, move_distance, self.pID)
                del rolls[rolls.index(move_distance)]
                logging.debug(f"Rolls left after this move: {rolls}")
            if self.board.game_won(self.pID):
                logging.info(f"Game won by player {self.pID}")
                break

            else:
                self.next_player()


    def move_tree_analysis(self, agent, current_board: Board, available_rolls: List[int], prior_moves: List[Tuple[int, int]]):
        logging.debug(f"AI looking for moves subsequent to prior moves {prior_moves}")
        possible_moves = current_board.permitted_moves(available_rolls, self.pID)
        if len(possible_moves) == 0:
            # No valid moves, so return current state
            logging.debug(f"AI found no valid moves with remaining dice rolls ({available_rolls}")
            new_state = current_board.encode_features(self.pID)
            value = agent.assess_features(new_state)
            return value, prior_moves
        else:
            # At least one valid move to look at
            logging.debug(f"AI examining subsequent moves: {possible_moves}")
            max_value = -np.inf
            max_branch = None
            for move in possible_moves:
                temp_board = copy.deepcopy(current_board)
                temp_board.perform_move(*move, self.pID)
                remaining_rolls = [available_rolls[i] for i in range(len(available_rolls)) if
                                   i != available_rolls.index(move[1])]
                extant_moves = prior_moves + [move]
                if len(remaining_rolls) > 0:
                    # Still got rolls to do
                    best_subsequent_value, best_subsequent_move_tree = \
                        self.move_tree_analysis(agent, temp_board, remaining_rolls, extant_moves)
                    if best_subsequent_value > max_value:
                        max_value = best_subsequent_value
                        max_branch = best_subsequent_move_tree
                else:
                    new_state = temp_board.encode_features(self.pID)
                    value = agent.assess_features(new_state)
                    if value > max_value:
                        max_value = value
                        max_branch = extant_moves
            logging.debug(f"AI's best board found so far with score {max_value} on branch {max_branch}")
            return max_value, max_branch


if __name__ == '__main__':
    logging.basicConfig(level=logging.WARN, format="%(message)s")
    common_TD_agent = TDagent(0.1, 0.7, 196)

    # Ask what board configuration to use
    response = input("Use endgame backgammon starting board (y/n)?: ")
    use_endgame_board = (str(response).upper() == "Y")
    # Offer to load existing model
    response = input("Do you want to load a checkpoint (y/n): ")
    if str(response).upper() == "Y":
        # response = input("Specify checkpoint name (TDGammon): ")
        # if use_endgame_board:
        #     common_TD_agent.load("TDGammon_endgame")
        # else:
        #     common_TD_agent.load("TDGammon")
        common_TD_agent.load("TDGammon")

    # Ask for length
    response = input("How many training episodes: ")
    num_training_episodes = int(response)
    response = input("How often to save checkpoints: ")
    checkpoint_period = int(response)
    response = input("How many test episodes per checkpoint: ")
    num_test_episodes = int(response)

    g = Game(common_TD_agent, common_TD_agent)
    g_test = Game(common_TD_agent, RandomAgent())
    last_ten_ep_lengths = [0.0] * 10
    for episode in range(1, num_training_episodes + 1):
        episode_length = g.training_game(use_endgame_board)
        last_ten_ep_lengths = last_ten_ep_lengths[1:] + [episode_length]
        if episode % checkpoint_period == 0 and episode > 1:
            print("Saving checkpoint")
            common_TD_agent.save("TDGammon")
            # if use_endgame_board:
            #     common_TD_agent.save("TDGammon_simple")
            # else:
            #     common_TD_agent.save("TDGammon")
            print("Starting test phase versus RandomAgent(). Learning disabled.")
            common_TD_agent.disable_learning()
            for test_episode in range(0, num_test_episodes):
                g_test.training_game(use_endgame_board)
            print("Resuming training.")
            common_TD_agent.enable_learning()
        if episode % 10 == 0 and episode > 1 and num_test_episodes == 0:
            # Give estimate of time to complete
            remaining_episodes = num_training_episodes - episode
            remaining_time = remaining_episodes * np.average(last_ten_ep_lengths)
            print(f"Estimated time to complete: {remaining_time / 60:.2f} mins")


    train_win_history = copy.deepcopy(g.win_history)
    train_len_history = copy.deepcopy(g.game_len_history)

    plt.plot(train_win_history, label="Training")
    plt.plot(g_test.win_history, label="Testing")
    plt.plot([0.5] * num_training_episodes, ":")
    plt.legend()
    plt.show()





