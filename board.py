import numpy as np
from typing import List, Tuple, Union
import logging

PLAYER_X = 0
PLAYER_O = 1
NUM_POINTS = 24


class Board:
    def __init__(self, endgame_board):
        self.num_pieces = 0
        self.o_board, self.o_bar = self.generate_board_list(endgame_board)
        self.x_board, self.x_bar = self.generate_board_list(endgame_board)
        self.o_removed = 0
        self.x_removed = 0

    def get_bar(self, player: int) -> int:
        if player == PLAYER_X:
            bar = self.x_bar
        else:
            bar = self.o_bar
        return bar

    def adjust_bar(self, player: int, delta: int) -> None:
        if player == PLAYER_X:
            self.x_bar += delta
        else:
            self.o_bar += delta

    def get_board(self, player: int) -> List:
        if player == PLAYER_X:
            board = self.x_board
        else:
            board = self.o_board
        return board

    def set_board(self, player: int, index: int, delta: int) -> None:
        if player == PLAYER_X:
            self.x_board[index] += delta
        else:
            self.o_board[index] += delta

    def generate_board_list(self, endgame_board: bool) -> Tuple[List[int], int]:
        if endgame_board:
            remaining = 15
            board = [0] * 24
            # Only have pieces in opponent's home half
            for n in range(15, 23):
                this_point = np.random.randint(0, min(np.random.randint(1, 6), remaining) + 1)
                remaining -= this_point
                board[n] = this_point
            # board = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 0, 0]
            board[0] = min(2, remaining)
            bar = max(remaining - board[0], 0)
            self.num_pieces = 15
            print(board)
        else:
            board = [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 3, 0, 5, 0, 0, 0, 0, 0]
            bar = 0
            self.num_pieces = 15
        return board, bar

    def _can_bear_off(self, board: List[int], bar: int) -> bool:
        can_bear_off = (bar == 0)
        for p in range(0, NUM_POINTS - 6):
            if board[p] > 0:
                can_bear_off = False
        return can_bear_off

    def permitted_moves(self, rolls: List[int], player: int) -> List[Tuple[int, int]]:
        rolls = list(set(rolls))  # Remove duplicates (e.g. if rolled a double)
        permitted_moves = []
        bar = self.get_bar(player)
        for roll_value in rolls:
            if bar > 0:
                if self.move_permitted("bar", roll_value, player):
                    permitted_moves.append(("bar", roll_value))
            else:
                for p in range(0, NUM_POINTS):
                    if self.move_permitted(p, roll_value, player):
                        permitted_moves.append((p, roll_value))
        return permitted_moves

    def move_permitted(self, start: Union[int, str], roll_value: int, player: int) -> bool:
        my_board = self.get_board(player)
        their_board = self.get_board(1 - player)
        bar = self.get_bar(player)

        if start == "bar":  # We are trying to move a piece from the bar
            if bar > 0:
                new_position = -1 + roll_value  # "bar" has effective position -1
                opp_point_occ = their_board[NUM_POINTS - new_position - 1]
                return opp_point_occ <= 1  # Can only move off bar if destination is empty or blotted
        else:  # Trying to move a piece not on bar
            if bar > 0:  # There's a piece on the bar so can't move a non-bar piece
                return False
            if my_board[start] > 0:  # There is a piece here
                new_position = start + roll_value
                if new_position == NUM_POINTS:  # Will be removed from board
                    return self._can_bear_off(my_board, bar)  # Can only be removed if all pieces in home area
                elif new_position > NUM_POINTS:  # Will overshoot board end
                    return False
                their_position = NUM_POINTS - new_position - 1
                if their_board[their_position] > 1:  # Other player has 2 or more pieces there
                    return False
            else:
                return False

        # If reached here then move is permitted
        return True

    def perform_move(self, position: int, roll: int, player: int):
        my_board = self.get_board(player)
        their_board = self.get_board(1 - player)
        # Lift piece from start position
        if position == "bar":
            self.adjust_bar(player, -1)
        else:
            my_board[position] -= 1
        # Place piece in finish position
        if position == "bar":
            position = -1  # Effective position on number scale
        new_position = position + roll
        if new_position == NUM_POINTS:  # Piece has been removed from board
            if player == PLAYER_X:
                self.x_removed += 1
            else:
                self.o_removed += 1
        else:  # Piece has moved to a new location on the board
            my_board[new_position] += 1
            # If piece has taken an opponent's piece, then move it to the opponent's bar
            opp_position = NUM_POINTS - new_position - 1
            if their_board[opp_position] > 0:
                # their_board[opp_position] -= 1
                self.set_board(1 - player, opp_position, -1)
                self.adjust_bar(1 - player, +1)
                logging.info(f"Piece taken by player {player} at point {new_position} (player's own coords).  bar={self.x_bar},{self.o_bar}")

    def encode_features(self, player: int):
        # Based on Tesauro TDGammon v0.0
        # For each point on the board (1-24), features:
        # 1: 1 if current player has single piece (blot)
        # 2: 1 if current player has two pieces (made point)
        # 3: 1 if current player has three pieces (single spare)
        # 4: (n-3)/2 if current player has >3 pieces
        # 5-8: Same as above for other player's pieces
        # Also, general features:
        # - Number of current and other player's pieces on bar (n/2)
        # - Number of current and other player's pieces already removed (n/15)
        # For the purposes of calculating features, the board direction is adjusted
        # such that 0 is the home point and 25 is the bar.
        my_board = self.get_board(player)
        their_board = self.get_board(1 - player)
        my_bar = self.get_bar(player)
        their_bar = self.get_bar(1 - player)
        features = np.zeros(196)
        num_mine_cleared = 0
        num_theirs_cleared = 0
        for p in range(0, 24):
            point = my_board[p]
            num_mine_cleared += point
            index = p * 4
            features[index:index + 4] = self._encode_point(point)
            point = their_board[p]
            num_theirs_cleared += point
            index = (p + 24) * 4
            features[index:index + 4] = self._encode_point(point)
        features[192] = my_bar / 2
        features[193] = their_bar / 2
        features[193] = num_mine_cleared / 15
        features[195] = num_theirs_cleared / 15
        return features[np.newaxis]

    def _encode_point(self, point: int) -> List:
        point_features = [0] * 4
        if point == 1:
            point_features[0] = 1
        elif point == 2:
            point_features[1] = 1
        elif point == 3:
            point_features[2] = 1
        elif point > 3:
            point_features[3] = (point - 3) / 2
        return point_features

    def game_won(self, player):
        if player == PLAYER_X:
            num_removed = self.x_removed
        else:
            num_removed = self.o_removed
        return num_removed == self.num_pieces
