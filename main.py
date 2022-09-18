# backgammon

from enum import Enum
import numpy as np
from typing import List, Tuple
import time
import copy


class Color(Enum):
    Empty = 0
    Red = 1
    White = 2


class Tree(object):
    """Generic tree node."""
    def __init__(self, name, children=None):
        self.name = name
        self.children = []
        if children is not None:
            for child in children:
                self.add_child(child)

    def __repr__(self):
        return self.name

    def add_child(self, node):
        assert isinstance(node, Tree)
        self.children.append(node)

    def count_children(self):
        return len(self.children)

    def print_tree(self, depth=0):
        tabbing = "\t" * depth
        print(f"{tabbing}{self.name}")
        for child in self.children:
            child.print_tree(depth + 1)

    def get_total_nodes(self):
        count = 0
        if len(self.children) == 0:
            count = 0
        else:
            for child in self.children:
                count += 1 + child.get_total_nodes()
        return count

    def get_list_of_leaves(self):
        if self.count_children() == 0:
            leaves = [self.name]
        else:
            leaves = []
            for child in self.children:
                leaves = leaves + child.get_list_of_leaves()
        return leaves


class Point:
    def __init__(self, index, num_pieces, colour, red_bar=False, white_bar=False):
        self.is_red_bar = red_bar
        self.is_white_bar = white_bar
        if num_pieces > 0 and colour == Color.Empty:
            raise Exception("Non-zero number of pieces but colour specified for point.")
        self.num_pieces = num_pieces
        self.colour = colour
        self.index = index
        # When working out possible moves, pieces will be moved to these temporary lists.
        self.removed_pieces = [0] * 4  # tally for each possible dice roll in turn
        self.added_pieces = [0] * 4
        self.colour_provisional = [colour] * 4

    def occupancy(self):
        # Get actual confirmed occupancy of point (i.e. at end of last move)
        return self.num_pieces

    def occupancy_provisional(self):
        # Get provisional occupancy if current calculation of possible moves is performed
        count_added = 0
        count_removed = 0
        for r in self.removed_pieces:
            count_removed += r
        for a in self.added_pieces:
            count_added += a
        return self.num_pieces + count_added - count_removed


class Board:
    def __init__(self):
        self.board = [Point(0, 0, Color.Empty)] * 26  # Use of Point() constructor just dirty way of forcing type
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
        # Record current player
        self.current_player = Color.Empty
        # Provisional board for move calculations
        self.board_provisional = [copy.deepcopy(self.board)] * 4

    def simple_board_representation(self, board_to_print=None, header=False):
        if board_to_print is None:
            board_to_print = self.board
        if header:
            for p in range(0, 26):
                print(f" {p:03}", end="")
            print("")
        for p in board_to_print:
            if p.colour == Color.Empty:
                print(" 000", end="")
            elif p.colour == Color.Red:
                print(f" +{p.num_pieces:2}", end="")
            else:
                print(f" -{p.num_pieces:2}", end="")
        print("")


    def choose_first_player(self):
        if np.random.rand() > 0.5:
            self.current_player = Color.Red
        else:
            self.current_player = Color.White
        print(f"First player is {self.current_player}")

    def change_player(self):
        if self.current_player == Color.Red:
            self.current_player = Color.White
        elif self.current_player == Color.White:
            self.current_player = Color.Red
        else:
            raise Exception("Cannot change player when first player has not been initialised.")

    def play_direction(self):
        if self.current_player == Color.Red:
            direction = 1
        elif self.current_player == Color.White:
            direction = -1
        else:
            raise Exception("Play direction has no meaning for non-colour.")
        return direction

    def home_point(self):
        if self.current_player == Color.Red:
            point = 25
        elif self.current_player == Color.White:
            point = 0
        else:
            raise Exception("Home point has no meaning for non-colour.")
        return point

    def bar_point(self, other_player=False):
        if other_player:
            # Bar point is current player's home point
            point = self.home_point()
        else:
            if self.current_player == Color.Red:
                point = 0
            elif self.current_player == Color.White:
                point = 25
            else:
                raise Exception("Bar point has no meaning for non-colour.")
        return point

    def absolute_point(self, point):
        if self.current_player == Color.Red:
            abs_point = 25 - point
        elif self.current_player == Color.Empty:
            raise Exception("Point has no meaning for non-colour.")
        else:
            abs_point = point
        return abs_point

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

    def get_possible_moves_from_dice(self, dice_rolls: List[int]) -> (Tree, Tree):
        # If only two dice values then could play two different permutations.
        # If four dice rolls then only one permutation.
        if len(dice_rolls) == 2:
            num_permutations = 2
        else:
            num_permutations = 1

        # For each permutation of rolls, work out possible board configurations by end of move
        move_tree = Tree("Possible moves (from, to):")
        board_tree = Tree("Possible boards")
        for _ in range(0, num_permutations):
            # print(f"Permutation {_}, dice rolls {dice_rolls}")
            self.get_board_from_dice_roll(dice_rolls, 0, move_tree, board_tree)
            dice_rolls.reverse()  # Only has effect if more than one permutation

        return move_tree, board_tree

    def get_board_from_dice_roll(self, dice_rolls: List[int], roll_depth: int, move_tree: Tree, board_tree: Tree):
        # Recursive function, each time popping an element off dice_rolls
        if roll_depth == len(dice_rolls):
            # Used all dice rolls
            return move_tree, board_tree
        else:
            roll = dice_rolls[roll_depth]

        # Check to see if any pieces on bar
        if self.board[self.bar_point()].occupancy_provisional() > 0:
            # This player has a piece on the bar
            new_move = self.get_point_move(self.bar_point(), roll, roll_depth, can_bear_off=False)
            if new_move is not None:
                # Have made a move
                move_tree.add_child(Tree(new_move))
                # Make move provisional
                provisional_board = self.make_provisional_move(new_move, roll_depth)
                board_tree.add_child(Tree(provisional_board))
                # Try next roll
                self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])
        else:
            # Check to see if player is allowed to bear off (all pieces in home area)
            can_bear_off = True  # Initially assume can bear off, until proven otherwise
            # for n in range(7, 25):  # Go through all points outside home area
            for n in range(7, 25):
                point = self.absolute_point(n) # self.home_point() + n * self.play_direction()
                if self.board[point].colour_provisional[roll_depth] == self.current_player:
                    # Player has piece outside of home area
                    can_bear_off = False
            if can_bear_off:
                for p in range(1, 7):
                    abs_point = self.absolute_point(p)
                    new_move = self.get_point_move(abs_point, roll, roll_depth, True)
                    if new_move is not None:
                        # Have made a move
                        move_tree.add_child(Tree(new_move))
                        # Make move provisional
                        provisional_board = self.make_provisional_move(new_move, roll_depth)
                        board_tree.add_child(Tree(provisional_board))
                        # Try next roll
                        self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])
            else:
                # Look through all other points and identify if they have a piece that can move
                for i in range(1, 25):
                    point = self.board[i]
                    if point.occupancy_provisional() > 0:
                        if point.colour_provisional[roll_depth] == self.current_player:
                            # Point belongs to current player, so see if player can make move
                            new_move = self.get_point_move(i, roll, roll_depth, False)
                            if new_move is not None:
                                # Have made a move
                                move_tree.add_child(Tree(new_move))
                                # Make move provisional
                                provisional_board = self.make_provisional_move(new_move, roll_depth)
                                board_tree.add_child(Tree(provisional_board))
                                # Try next roll
                                self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])

        self.clear_provisional_moves(roll_depth)

    def get_point_move(self, point_index: int, roll_value: int, roll_depth: int, can_bear_off: bool):
        move_info = None
        proposed_position = self.coerce_new_position(point_index, roll_value)
        can_move = self.can_move_to_point(proposed_position, roll_depth, can_bear_off)
        if can_move:
            move_info = (point_index, proposed_position)
            #self.make_provisional_move(move_info, roll_depth)
        return move_info

    def coerce_new_position(self, current_position: int, roll_value: int):
        # Work out where you would be if you applied the roll to the piece at current position
        # with checks to ensure that the new position is in range of the board.
        new_position = current_position + self.play_direction() * roll_value
        new_position = max(0, min(new_position, 25))
        return new_position

    def can_move_to_point(self, dest_point_index: int, roll_depth: int, can_bear_off: bool) -> bool:
        can_move = False
        if can_bear_off and dest_point_index == self.home_point():
            can_move = True
        elif dest_point_index != self.home_point():
            destination = self.board[dest_point_index]
            if destination.occupancy_provisional() == 0:
                can_move = True
            elif destination.colour_provisional[roll_depth] == self.current_player:
                can_move = True
            elif destination.colour_provisional[roll_depth] != self.current_player and \
                    destination.occupancy_provisional() == 1:
                can_move = True
        return can_move

    def make_provisional_move(self, provisional_move: Tuple[int, int], roll_depth: int):
        start_index, dest_index = provisional_move
        start_point = self.board[start_index]
        start_prov_point = self.board_provisional[roll_depth][start_index]
        dest_point = self.board[dest_index]
        dest_prov_point = self.board_provisional[roll_depth][dest_index]
        for d in range(roll_depth, 4):
            start_point.removed_pieces[d] += 1
            start_prov_point.num_pieces -= 1
            if dest_point.occupancy_provisional() == 0 or dest_point.colour_provisional[d] == self.current_player:
                dest_point.added_pieces[d] += 1
                dest_prov_point.colour = self.current_player
                dest_prov_point.num_pieces += 1
            elif dest_point.colour_provisional[d] != self.current_player:
                # Other player's one piece is being replaced by current player's piece
                dest_point.colour_provisional[d] = self.current_player
                dest_prov_point.colour = self.current_player
                # Move other player's piece to bar
                self.board[self.bar_point(other_player=True)].added_pieces[d] += 1
                self.board_provisional[roll_depth][self.bar_point(other_player=True)].num_pieces += 1
            # In any case, piece has moved from start location
            if start_point.occupancy_provisional() == 0:
                start_point.colour_provisional[d] = Color.Empty
                start_prov_point.colour = Color.Empty
        return self.board_provisional[roll_depth]

    def clear_provisional_moves(self, roll_depth):
        # Clear provisional moves due to current dice roll depth
        for p in range(0, 25):
            if roll_depth == 0:
                for d in range(0, 4):
                    self.board[p].removed_pieces[d] = 0
                    self.board[p].added_pieces[d] = 0
                    self.board[p].colour_provisional[d] = self.board[p].colour
            else:
                for d in range(roll_depth, 4):
                    self.board[p].removed_pieces[d] = self.board[p].removed_pieces[d - 1]
                    self.board[p].added_pieces[d] = self.board[p].added_pieces[d - 1]
                    self.board[p].colour_provisional[d] = self.board[p].colour_provisional[d - 1]

        if roll_depth == 0:
            for d in range(0, 4):
                self.board_provisional[d] = copy.deepcopy(self.board)
        else:
            for d in range(roll_depth, 4):
                self.board_provisional[d] = copy.deepcopy(self.board_provisional[roll_depth - 1])

    def get_boards_from_moves(self, board_tree: Tree, board_list: List):
        # Gets board at end of each move branch
        for b in board_tree.children:
            print(b.name)
            if b.children == 0:
                board_list.append(b.name)
            else:
                self.get_boards_from_moves(board_tree, board_list)



# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    b = Board()
    for pp in b.board:
        print(f"Point {pp.index} is {pp.colour}, with {pp.occupancy()} pieces.")
    b.choose_first_player()
    dice_rolls = b.roll_dice()
    print(f"Dice rolls: {dice_rolls}")
    move_tree, board_tree = b.get_possible_moves_from_dice(dice_rolls)
    move_tree.print_tree()
    print("Initial board:")
    b.simple_board_representation(header=True)
    print("Potential boards:")
    for c in board_tree.children:
        b.simple_board_representation(c.name)
    # ls = board_tree.get_list_of_leaves()
    # for leaf in ls:
    #     b.simple_board_representation(leaf)
    #     # print(leaf)
    # # potential_boards = b.get_boards_from_moves(board_tree, [])


