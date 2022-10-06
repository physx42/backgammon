from colour import Colour
import numpy as np
from typing import List, Tuple, Union
import copy
from tree import Tree
import logging

PLAYER_X = 0
PLAYER_O = 1
NUM_POINTS = 24
# NUM_PIECES = 15


class Board:
    def __init__(self, simple_board):
        self.o_board = self.generate_board_list(simple_board)
        self.x_board = self.generate_board_list(simple_board)
        self.o_bar = 0
        self.x_bar = 0
        self.o_removed = 0
        self.x_removed = 0
        self.o_home_area = 0
        self.x_home_area = 0

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

    def generate_board_list(self, simple_board: bool) -> List[int]:
        if simple_board:
            board = [3, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 0, 0, 0, 0, 0, 0, 0, 0]
            self.num_pieces = 5
        else:
            board = [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 3, 0, 5, 0, 0, 0, 0, 0]
            self.num_pieces = 15
        return board

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
                if self._move_permitted("bar", roll_value, player):
                    permitted_moves.append(("bar", roll_value))
            else:
                for p in range(0, NUM_POINTS):
                    if self._move_permitted(p, roll_value, player):
                        permitted_moves.append((p, roll_value))
        return permitted_moves

    def _move_permitted(self, start: Union[int, str], roll_value: int, player: int) -> bool:
        my_board = self.get_board(player)
        their_board = self.get_board(1 - player)
        bar = self.get_bar(player)

        if start == "bar":  # We are trying to move a piece from the bar
            if bar > 0:
                new_position = -1 + roll_value  # "bar" has effective position -1
                opp_point_occ = their_board[NUM_POINTS - new_position - 1]
                return opp_point_occ <= 1  # Can only move off bar if destination is empty or blotted
        else:  # Trying to move a piece not on bar
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
        my_bar = self.get_bar(player)
        their_bar = self.get_bar(1 - player)
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
                # if player == PLAYER_X:
                #     self.o_bar += 1
                # else:
                #     self.x_bar += 1
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






# class Point:
#     def __init__(self, index, num_pieces, colour, red_bar=False, white_bar=False):
#         self.is_red_bar = red_bar
#         self.is_white_bar = white_bar
#         if num_pieces > 0 and colour == Colour.Empty:
#             raise Exception("Non-zero number of pieces but colour specified for point.")
#         self.num_pieces = num_pieces
#         self.colour = colour
#         self.index = index
#
#     def occupancy(self):
#         # Get actual confirmed occupancy of point (i.e. at end of last move)
#         return self.num_pieces
#
#
# class Board:
#     def __init__(self, debug_print=True, simple_board=False):
#         self.print_boards = debug_print  # Determines whether debug output can be printed
#         self.board = [Point(0, 0, Colour.Empty)] * 26  # Use of Point() constructor just dirty way of forcing type
#         if simple_board:
#             self.initialise_simple_board()
#         else:
#             self.initialise_real_board()
#         # Record current player
#         self.current_player = Colour.Empty
#         # Provisional board for move calculations
#         self.board_provisional = [copy.deepcopy(self.board), copy.deepcopy(self.board),
#                                   copy.deepcopy(self.board), copy.deepcopy(self.board)]
#         self.turn = 0
#         # Allow for recording of previous board, to aid training
#         self.last_white_features = None
#         self.last_red_features = None
#
#     def initialise_simple_board(self):
#         self.initialise_point(0, Colour.Empty, num_pieces=0, red_bar=True)
#         self.initialise_point(1, Colour.Red, num_pieces=5)
#         self.initialise_point(2, Colour.Empty, num_pieces=0)
#         self.initialise_point(3, Colour.Empty, num_pieces=0)
#         self.initialise_point(4, Colour.Empty, num_pieces=0)
#         self.initialise_point(5, Colour.Empty, num_pieces=0)
#         self.initialise_point(6, Colour.Empty, num_pieces=0)
#         self.initialise_point(7, Colour.Empty, num_pieces=0)
#         self.initialise_point(8, Colour.Empty, num_pieces=0)
#         self.initialise_point(9, Colour.Empty, num_pieces=0)
#         self.initialise_point(10, Colour.Empty, num_pieces=0)
#         self.initialise_point(11, Colour.Empty, num_pieces=0)
#         self.initialise_point(12, Colour.Empty, num_pieces=0)
#         self.initialise_point(13, Colour.Empty, num_pieces=0)
#         self.initialise_point(14, Colour.Empty, num_pieces=0)
#         self.initialise_point(15, Colour.Empty, num_pieces=0)
#         self.initialise_point(16, Colour.Empty, num_pieces=0)
#         self.initialise_point(17, Colour.Empty, num_pieces=0)
#         self.initialise_point(18, Colour.Empty, num_pieces=0)
#         self.initialise_point(19, Colour.Empty, num_pieces=0)
#         self.initialise_point(20, Colour.Empty, num_pieces=0)
#         self.initialise_point(21, Colour.Empty, num_pieces=0)
#         self.initialise_point(22, Colour.Empty, num_pieces=0)
#         self.initialise_point(23, Colour.Empty, num_pieces=0)
#         self.initialise_point(24, Colour.White, num_pieces=5)
#         self.initialise_point(25, Colour.Empty, num_pieces=0, white_bar=True)
#
#     def initialise_real_board(self):
#         self.initialise_point(0, Colour.Empty, num_pieces=0, red_bar=True)
#         self.initialise_point(1, Colour.Red, num_pieces=2)
#         self.initialise_point(2, Colour.Empty, num_pieces=0)
#         self.initialise_point(3, Colour.Empty, num_pieces=0)
#         self.initialise_point(4, Colour.Empty, num_pieces=0)
#         self.initialise_point(5, Colour.Empty, num_pieces=0)
#         self.initialise_point(6, Colour.White, num_pieces=5)
#         self.initialise_point(7, Colour.Empty, num_pieces=0)
#         self.initialise_point(8, Colour.White, num_pieces=3)
#         self.initialise_point(9, Colour.Empty, num_pieces=0)
#         self.initialise_point(10, Colour.Empty, num_pieces=0)
#         self.initialise_point(11, Colour.Empty, num_pieces=0)
#         self.initialise_point(12, Colour.Red, num_pieces=5)
#         self.initialise_point(13, Colour.White, num_pieces=5)
#         self.initialise_point(14, Colour.Empty, num_pieces=0)
#         self.initialise_point(15, Colour.Empty, num_pieces=0)
#         self.initialise_point(16, Colour.Empty, num_pieces=0)
#         self.initialise_point(17, Colour.Red, num_pieces=3)
#         self.initialise_point(18, Colour.Empty, num_pieces=0)
#         self.initialise_point(19, Colour.Red, num_pieces=5)
#         self.initialise_point(20, Colour.Empty, num_pieces=0)
#         self.initialise_point(21, Colour.Empty, num_pieces=0)
#         self.initialise_point(22, Colour.Empty, num_pieces=0)
#         self.initialise_point(23, Colour.Empty, num_pieces=0)
#         self.initialise_point(24, Colour.White, num_pieces=2)
#         self.initialise_point(25, Colour.Empty, num_pieces=0, white_bar=True)
#         if self.print_boards:
#             for p in self.board:
#                 logging.debug(f"Point {p.index} is {p.colour}, with {p.occupancy()} pieces.")
#
#     def print(self, message, force_show=False):
#         if self.print_boards:
#             print(message)
#
#     def simple_board_representation(self, title, board_to_print=None, header=False, count=-1):
#         if self.print_boards:  # Only print if print mode enabled
#             if title != "":
#                 logging.info(title)
#             red_total = 0
#             white_total = 0
#             if board_to_print is None:
#                 board_to_print = self.board
#             if header:
#                 text = "\t" + " ".join([f"{p:03}" for p in range(0, 26)]) + "\tTotals\tW\tR"
#                 logging.info(text)
#             # If count is >=0 then print it at start of line
#             if count >= 0:
#                 text = f"{count:>4}"
#             else:
#                 text = f"    "
#             for p in board_to_print:
#                 if p.colour == Colour.Empty:
#                     text = text + " ---"
#                 elif p.colour == Colour.Red:
#                     text = text + f" {p.num_pieces:2}R"
#                     red_total += p.num_pieces
#                 else:
#                     text = text + f" {p.num_pieces:2}W"
#                     white_total += p.num_pieces
#             text = text + f"\t\t{white_total}\t{red_total}"
#             logging.info(text)
#
#     def print_move_tree(self, tree):
#         tree.print_tree()
#
#     def set_player(self, colour):
#         self.current_player = colour
#         # Make sure everything is cleared
#         self.clear_provisional_moves(0)
#
#     def other_player_colour(self):
#         if self.current_player == Colour.Red:
#             other_colour = Colour.White
#         elif self.current_player == Colour.White:
#             other_colour = Colour.Red
#         else:
#             raise Exception("Cannot identify 'other' player if the 'current player' is not specified.")
#         return other_colour
#
#     def play_direction(self):
#         if self.current_player == Colour.Red:
#             direction = 1
#         elif self.current_player == Colour.White:
#             direction = -1
#         else:
#             raise Exception("Play direction has no meaning for non-colour.")
#         return direction
#
#     def home_point(self):
#         if self.current_player == Colour.Red:
#             point = 25
#         elif self.current_player == Colour.White:
#             point = 0
#         else:
#             raise Exception("Home point has no meaning for non-colour.")
#         return point
#
#     def bar_point(self, other_player=False):
#         if other_player:
#             # Bar point is current player's home point
#             point = self.home_point()
#         else:
#             if self.current_player == Colour.Red:
#                 point = 0
#             elif self.current_player == Colour.White:
#                 point = 25
#             else:
#                 raise Exception("Bar point has no meaning for non-colour.")
#         return point
#
#     def absolute_point(self, relative_point: int) -> int:
#         # Converts relative position indices to the universal positions
#         # (i.e. 0 = white home, 25 = red home)
#         if self.current_player == Colour.Red:
#             abs_point = 25 - relative_point
#         elif self.current_player == Colour.Empty:
#             raise Exception("Point has no meaning for non-colour.")
#         else:
#             abs_point = relative_point
#         return abs_point
#
#     def relative_point(self, abs_point: int) -> int:
#         # Converts position indices so that 0 is home for both players
#         if self.current_player == Colour.White:
#             rel_point = abs_point
#         elif self.current_player == Colour.Empty:
#             raise Exception("Point has no meaning for non-colour.")
#         else:
#             rel_point = 25 - abs_point
#         return rel_point
#
#     def initialise_point(self, point_index, colour, num_pieces, red_bar=False, white_bar=False) -> None:
#         point = Point(point_index, num_pieces, colour, red_bar, white_bar)
#         self.board[point_index] = point
#

#
#     def get_possible_moves_from_dice(self, dice_rolls: List[int]) -> (Tree, Tree):
#         # If only two dice values then could play two different permutations.
#         # If four dice rolls then only one permutation.
#         if len(dice_rolls) == 2:
#             num_permutations = 2
#         else:
#             num_permutations = 1
#
#         # For each permutation of rolls, work out possible board configurations by end of move
#         move_tree = Tree("Possible moves (from, to):", isroot=True)
#         board_tree = Tree("Possible boards", isroot=True)
#         for _ in range(0, num_permutations):
#             # print(f"Permutation {_}, dice rolls {dice_rolls}")
#             self.get_board_from_dice_roll(dice_rolls, 0, move_tree, board_tree)
#             self.clear_provisional_moves(0)  # Make sure provisional board is reset
#             dice_rolls.reverse()  # Only has effect if more than one permutation
#
#         return move_tree, board_tree
#
#     def get_board_from_dice_roll(self, dice_rolls: List[int], roll_depth: int, move_tree: Tree, board_tree: Tree) -> None:
#         # Recursive function, each time popping an element off dice_rolls
#         if roll_depth == len(dice_rolls):
#             # Used all dice rolls
#             return
#         else:
#             roll = dice_rolls[roll_depth]
#
#         # Check to see if any pieces on bar
#         if self.board_provisional[roll_depth][self.bar_point()].occupancy() > 0:
#             # This player has a piece on the bar
#             new_move = self.get_point_move(self.bar_point(), roll, roll_depth, can_bear_off=False)
#             if new_move is not None:
#                 # Have made a move
#                 move_tree.add_child(Tree(new_move))
#                 # Make move provisional
#                 self.make_provisional_move(new_move, roll_depth)
#                 board_tree.add_child(Tree(copy.deepcopy(self.board_provisional[roll_depth])))
#                 # Try next roll depth
#                 self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])
#                 # # Reset board
#                 self.clear_provisional_moves(roll_depth)
#         else:
#             # Check to see if player is allowed to bear off (all pieces in home area)
#             can_bear_off = True  # Initially assume can bear off, until proven otherwise
#             for n in range(7, 26):
#                 abs_point = self.absolute_point(n)
#                 if self.board_provisional[roll_depth][abs_point].colour == self.current_player:
#                     # Player has piece outside of home area
#                     can_bear_off = False
#             if can_bear_off:
#                 for p in range(1, 7):
#                     abs_point = self.absolute_point(p)
#                     if self.board_provisional[roll_depth][abs_point].occupancy() > 0 and \
#                             self.board_provisional[roll_depth][abs_point].colour == self.current_player:
#                         new_move = self.get_point_move(abs_point, roll, roll_depth, True)
#                         if new_move is not None:
#                             # Have made a move
#                             move_tree.add_child(Tree(new_move))
#                             # Make move provisional
#                             self.make_provisional_move(new_move, roll_depth)
#                             board_tree.add_child(Tree(copy.deepcopy(self.board_provisional[roll_depth])))
#                             # Try next roll depth
#                             self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])
#                             # # Reset board
#                             self.clear_provisional_moves(roll_depth)
#             else:
#                 # Look through all other points and identify if they have a piece that can move
#                 for i in range(1, 25):
#                     point = self.board_provisional[roll_depth][i]
#                     if point.occupancy() > 0:
#                         if point.colour == self.current_player:
#                             # Point belongs to current player, so see if player can make move
#                             new_move = self.get_point_move(i, roll, roll_depth, False)
#                             if new_move is not None:
#                                 # Have made a move
#                                 move_tree.add_child(Tree(new_move))
#                                 # Make move provisional
#                                 self.make_provisional_move(new_move, roll_depth)
#                                 board_tree.add_child(Tree(copy.deepcopy(self.board_provisional[roll_depth])))
#                                 # Try next roll depth
#                                 self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])
#                                 # # Reset board
#                                 self.clear_provisional_moves(roll_depth)
#
#         # Reset board
#         self.clear_provisional_moves(roll_depth)
#
#     def get_point_move(self, point_index: int, roll_value: int, roll_depth: int, can_bear_off: bool) -> Tuple:
#         move_info = None
#         proposed_position = self.where_will_roll_take_piece(point_index, roll_value)
#         can_move = self.can_move_to_point(proposed_position, roll_depth, can_bear_off)
#         if can_move:
#             move_info = (point_index, proposed_position)
#         return move_info
#
#     def where_will_roll_take_piece(self, current_position: int, roll_value: int) -> int:
#         new_position = current_position + self.play_direction() * roll_value
#         return new_position
#
#     def can_move_to_point(self, dest_point_index: int, roll_depth: int, can_bear_off: bool) -> bool:
#         can_move = False
#         if not 0 <= dest_point_index <= 25:
#             # Trying to move to a position off the board, which is plainly not allowed!
#             can_move = False
#         elif can_bear_off and dest_point_index == self.home_point():
#             can_move = True
#         elif dest_point_index != self.home_point():
#             destination = self.board_provisional[roll_depth][dest_point_index]
#             if destination.occupancy() == 0:
#                 can_move = True
#             elif destination.colour == self.current_player:
#                 can_move = True
#             elif destination.colour != self.current_player and \
#                     destination.occupancy() == 1:
#                 can_move = True
#         return can_move
#
#     def make_provisional_move(self, provisional_move: Tuple[int, int], roll_depth: int):
#         start_index, dest_index = provisional_move
#         start_prov_point_d = self.board_provisional[roll_depth][start_index]
#         dest_prov_point_d = self.board_provisional[roll_depth][dest_index]
#         start_prov_point_d.num_pieces -= 1
#         if dest_index == self.home_point():
#             # Piece has been cleared from board so remove it from the board point tallies
#             pass
#         elif dest_prov_point_d.occupancy() == 0 or dest_prov_point_d.colour == self.current_player:
#             dest_prov_point_d.colour = self.current_player
#             dest_prov_point_d.num_pieces += 1
#         elif dest_prov_point_d.colour != self.current_player:
#             # Other player's one piece is being replaced by current player's piece
#             dest_prov_point_d.colour = self.current_player
#             # Move other player's piece to bar
#             self.board_provisional[roll_depth][self.bar_point(other_player=True)].num_pieces += 1
#             self.board_provisional[roll_depth][self.bar_point(other_player=True)].colour = self.other_player_colour()
#         # In any case, piece has moved from start location
#         if start_prov_point_d.occupancy() == 0:
#             start_prov_point_d.colour = Colour.Empty
#
#         # Copy to higher roll depths to make sure they're starting from the same baseline
#         for d in range(roll_depth + 1, 4):
#             self.board_provisional[d] = copy.deepcopy(self.board_provisional[roll_depth])
#
#     def clear_provisional_moves(self, roll_depth):
#         # Clear provisional moves due to current dice roll depth
#         if roll_depth == 0:
#             for d in range(0, 4):
#                 self.board_provisional[d] = copy.deepcopy(self.board)
#         else:
#             for d in range(roll_depth, 4):
#                 self.board_provisional[d] = copy.deepcopy(self.board_provisional[roll_depth - 1])
#
#     def get_boards_from_moves(self, board_tree: Tree, board_list: List):
#         # Gets board at end of each move branch
#         for b in board_tree.children:
#             print(b.name)
#             if b.children == 0:
#                 board_list.append(b.name)
#             else:
#                 self.get_boards_from_moves(board_tree, board_list)
#
#     def enact_provisional_move(self, target_board: List[Point]):
#         # Update the board to match the provisional board that has been chosen to be used.
#         self.board = copy.deepcopy(target_board)
#
#     def calculate_board_features(self, board: List[Point]) -> np.ndarray:
#         # Based on Tesauro TDGammon v0.0
#         # For each point on the board (1-24), features:
#         # 1: 1 if current player has single piece (blot)
#         # 2: 1 if current player has two pieces (made point)
#         # 3: 1 if current player has three pieces (single spare)
#         # 4: (n-3)/2 if current player has >3 pieces
#         # 5-8: Same as above for other player's pieces
#         # Also, general features:
#         # - Number of current and other player's pieces on bar (n/2)
#         # - Number of current and other player's pieces already removed (n/15)
#         # For the purposes of calculating features, the board direction is adjusted
#         # such that 0 is the home point and 25 is the bar.
#         features = np.zeros(196)
#         num_mine_cleared = 0
#         num_theirs_cleared = 0
#         for p in range(0, 24):
#             point = board[self.relative_point(p + 1)]
#             if point.colour == self.current_player:
#                 num_mine_cleared += point.num_pieces
#                 if point.num_pieces == 1:
#                     features[p * 8] = 1
#                 elif point.num_pieces == 2:
#                     features[p * 8 + 1] = 1
#                 elif point.num_pieces == 3:
#                     features[p * 8 + 2] = 1
#                 elif point.num_pieces > 3:
#                     features[p * 8 + 3] = (point.num_pieces - 3) / 2
#             elif point.colour == self.other_player_colour():
#                 num_theirs_cleared += point.num_pieces
#                 if point.num_pieces == 1:
#                     features[p * 8 + 4] = 1
#                 elif point.num_pieces == 2:
#                     features[p * 8 + 5] = 1
#                 elif point.num_pieces == 3:
#                     features[p * 8 + 6] = 1
#                 elif point.num_pieces > 3:
#                     features[p * 8 + 7] = (point.num_pieces - 3) / 2
#         features[192] = board[self.bar_point()].num_pieces / 2
#         features[193] = board[self.bar_point(other_player=True)].num_pieces / 2
#         features[193] = num_mine_cleared / 15
#         features[195] = num_theirs_cleared / 15
#         return features
#
#     def game_won(self, player_colour):
#         # Identify if specified player has any pieces left
#         pieces_left = False
#         for i in range(0, 26):
#             if self.board[i].colour == player_colour:
#                 pieces_left = True
#                 break
#         return not pieces_left

