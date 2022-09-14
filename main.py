# backgammon

from enum import Enum
import numpy as np
from typing import List


class Color(Enum):
    Empty = 0
    Red = 1
    White = 2


class Point:
    def __init__(self, index, num_pieces, colour, red_bar=False, white_bar=False):
        self.is_red_bar = red_bar
        self.is_white_bar = white_bar
        if num_pieces > 0 and colour != Color.Empty:
            raise Exception("Non-zero number of pieces but colour specified for point.")
        self.pieces = [colour] * num_pieces
        self.index = index

    def occupancy(self):
        return len(self.pieces)


class Board:
    def __init__(self):
        self.board = [] * 26
        self.initialise_point(0, Color.Empty, num_pieces=0, red_bar=True)
        self.initialise_point(1, Color.Red, num_pieces=2)
        self.initialise_point(2, Color.Empty, num_pieces=0)
        self.initialise_point(3, Color.Empty, num_pieces=0)
        self.initialise_point(4, Color.Empty, num_pieces=0)
        self.initialise_point(5, Color.Empty, num_pieces=0)
        self.initialise_point(6, Color.White, num_pieces=5)
        self.initialise_point(7, Color.Empty, num_pieces=0)
        self.initialise_point(8, Color.White, num_pieces=3)
        self.initialise_point(9, Color.Empty, num_pieces=0)
        self.initialise_point(10, Color.Empty, num_pieces=0)
        self.initialise_point(11, Color.Empty, num_pieces=0)
        self.initialise_point(12, Color.Red, num_pieces=5)
        self.initialise_point(13, Color.White, num_pieces=5)
        self.initialise_point(14, Color.Empty, num_pieces=0)
        self.initialise_point(15, Color.Empty, num_pieces=0)
        self.initialise_point(16, Color.Empty, num_pieces=0)
        self.initialise_point(17, Color.Red, num_pieces=3)
        self.initialise_point(18, Color.Empty, num_pieces=0)
        self.initialise_point(19, Color.Red, num_pieces=5)
        self.initialise_point(20, Color.Empty, num_pieces=0)
        self.initialise_point(21, Color.Empty, num_pieces=0)
        self.initialise_point(22, Color.Empty, num_pieces=0)
        self.initialise_point(23, Color.Empty, num_pieces=0)
        self.initialise_point(24, Color.White, num_pieces=2)
        self.initialise_point(25, Color.Empty, num_pieces=0, white_bar=True)

    def initialise_point(self, point_index, colour, num_pieces, red_bar=False, white_bar=False):
        point = Point(point_index, num_pieces, colour, red_bar, white_bar)
        self.board[point_index] = point

    def roll_dice(self):
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

    def get_possible_boards_from_dice(self, current_player: Color, dice_rolls: List[int]):
        # If only two dice values then could play two different permutations.
        # If four dice rolls then only one permutation.
        if len(dice_rolls) == 2:
            num_permutations = 2
        else:
            num_permutations = 1

        # Get info about player's objectives
        if current_player == Color.Red:
            play_direction = 1
            home_point = 25
            bar_point = 0
        else:
            play_direction = -1
            home_point = 0
            bar_point = 25

        # For each permutation of rolls, work out possible board configurations by end of move
        for p in range(0, num_permutations):
            self.get_board_from_dice_permutation(current_player, dice_rolls, play_direction, home_point, bar_point)
            # Only has effect if more than one permutation
            dice_rolls.reverse()

    def get_board_from_dice_permutation(self, current_player: Color, dice_rolls: List[int], play_direction: int, home_point: int, bar_point: int):
        move_list = []
        for roll in dice_rolls:
            # TODO what about board state on second/3rd/4th roll? Moves will branch
            # Check to see if any pieces on bar
            if self.board[bar_point].occupancy() > 0 and self.board[bar_point].colour == current_player:
                # This player has a piece on the bar
                move_list.append(self.get_point_moves(bar_point, current_player, roll, play_direction))
            else:
                # Check to see if player can bear off
                can_bear_off = True
                for n in range(7, 25):  # Go through all points outside home area
                    point = home_point + n * play_direction
                    if self.board[point].colour == current_player:
                        # Player has piece outside of home area
                        can_bear_off = False
                if can_bear_off:
                    # TODO bear off
                    pass
                else:
                    # Look through all other pieces and identify if they can move
                    for i in range(1, 25):
                        point = self.board[i]
                        if point.occupancy() > 0:
                            if point[0].colour == current_player:  # All pieces on point will be same colour
                                # Point belongs to current player, so see if player can make move
                                move_list.append(self.get_point_moves(i, current_player, roll, play_direction))
                                # TODO think about what happens if there are multiple options for a single roll

    def get_point_moves(self, point_index: int, current_player: Color, roll_value: int, play_direction: int):
        move_info = None
        proposed_position = self.coerce_new_position(point_index, roll_value, play_direction)
        can_move = self.can_move_to_point(current_player, proposed_position)
        if can_move:
            move_info = (point_index, proposed_position)

        return move_info

    def coerce_new_position(self, current_position: int, roll_value: int, play_direction: int):
        # Work out where you would be if you applied the roll to the piece at current position
        # with checks to ensure that the new position is in range of the board.
        new_position = current_position + play_direction * roll_value
        new_position = max(0, min(new_position, 25))
        return new_position

    def can_move_to_point(self, current_player: Color, proposed_position: int) -> bool:
        can_move = False
        if self.board[proposed_position].colour == Color.Empty:
            can_move = True
        elif self.board[proposed_position].colour == current_player:
            can_move = True
        elif self.board[proposed_position].colour != current_player and \
                self.board[proposed_position].occupancy() == 1:
            can_move = True

        return can_move


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    pass
