# backgammon

from enum import Enum
import numpy as np
from typing import List, Tuple
import time
import copy
from agent import Agent


class Color(Enum):
    Empty = 0
    Red = 1
    White = 2


class Tree(object):
    """Generic tree node."""
    def __init__(self, name, children=None, isroot=False):
        self.name = name
        if isroot:
            self.rootname = name
        else:
            self.rootname = ""
        self.children = []
        if children is not None:
            for child in children:
                self.add_child(child)

    def __repr__(self):
        return self.name

    def add_child(self, node):
        assert isinstance(node, Tree)
        node.rootname = self.rootname
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
        leaves = []
        if self.count_children() > 0:
            for child in self.children:
                leaves = leaves + [child.name] + child.get_list_of_leaves()
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

    def occupancy(self):
        # Get actual confirmed occupancy of point (i.e. at end of last move)
        return self.num_pieces


class Board:
    def __init__(self, print_boards=True):
        self.board = [Point(0, 0, Color.Empty)] * 26  # Use of Point() constructor just dirty way of forcing type
        self.initialise_real_board()
        # Record current player
        self.current_player = Color.Empty
        # Provisional board for move calculations
        self.board_provisional = [copy.deepcopy(self.board), copy.deepcopy(self.board),
                                  copy.deepcopy(self.board), copy.deepcopy(self.board)]
        # Can print to console board and potential moves if print_boards is True
        self.print_boards = print_boards
        self.turn = 0

    def initialise_real_board(self):
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

    def simple_board_representation(self, title, board_to_print=None, header=False, count=-1):
        if self.print_boards:  # Only print if print mode enabled
            if title != "":
                print(title)
            red_total = 0
            white_total = 0
            if board_to_print is None:
                board_to_print = self.board
            if header:
                print("\t", end="")
                for p in range(0, 26):
                    print(f" {p:03}", end="")
                print("\tTotals\tW\tR")
            # If count is >=0 then print it at start of line
            if count >= 0:
                print(f"{count:>3}\t", end="")
            else:
                print("\t", end="")
            for p in board_to_print:
                if p.colour == Color.Empty:
                    print(" ---", end="")
                elif p.colour == Color.Red:
                    print(f" {p.num_pieces:2}R", end="")
                    red_total += p.num_pieces
                else:
                    print(f" {p.num_pieces:2}W", end="")
                    white_total += p.num_pieces
            print(f"\t\t\t{white_total}\t{red_total}")

    def print_move_tree(self, tree):
        if self.print_boards:
            move_tree.print_tree()

    def choose_first_player(self):
        self.turn = 0  # reset counter
        if np.random.rand() > 0.5:
            self.current_player = Color.Red
        else:
            self.current_player = Color.White
        print(f"First player is {self.current_player}")

    def change_player(self):
        self.turn += 1
        if self.current_player == Color.Red:
            self.current_player = Color.White
            print(f"Turn {self.turn}: White")
        elif self.current_player == Color.White:
            self.current_player = Color.Red
            print(f"Turn {self.turn}: Red")
        else:
            raise Exception("Cannot change player when first player has not been initialised.")
        # Make sure everything is cleared
        self.clear_provisional_moves(0)

    def other_player_colour(self):
        if self.current_player == Color.Red:
            other_colour = Color.White
        elif self.current_player == Color.White:
            other_colour = Color.Red
        else:
            raise Exception("Cannot identify 'other' player if the 'current player' is not specified.")
        return other_colour

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

    def initialise_point(self, point_index, colour, num_pieces, red_bar=False, white_bar=False) -> None:
        point = Point(point_index, num_pieces, colour, red_bar, white_bar)
        self.board[point_index] = point

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

    def get_possible_moves_from_dice(self, dice_rolls: List[int]) -> (Tree, Tree):
        # If only two dice values then could play two different permutations.
        # If four dice rolls then only one permutation.
        if len(dice_rolls) == 2:
            num_permutations = 2
        else:
            num_permutations = 1

        # For each permutation of rolls, work out possible board configurations by end of move
        move_tree = Tree("Possible moves (from, to):", isroot=True)
        board_tree = Tree("Possible boards", isroot=True)
        for _ in range(0, num_permutations):
            # print(f"Permutation {_}, dice rolls {dice_rolls}")
            self.get_board_from_dice_roll(dice_rolls, 0, move_tree, board_tree)
            self.clear_provisional_moves(0)  # Make sure provisional board is reset
            dice_rolls.reverse()  # Only has effect if more than one permutation

        return move_tree, board_tree

    def get_board_from_dice_roll(self, dice_rolls: List[int], roll_depth: int, move_tree: Tree, board_tree: Tree) -> None:
        # Recursive function, each time popping an element off dice_rolls
        if roll_depth == len(dice_rolls):
            # Used all dice rolls
            return
        else:
            roll = dice_rolls[roll_depth]

        # Check to see if any pieces on bar
        if self.board_provisional[roll_depth][self.bar_point()].occupancy() > 0:
            # This player has a piece on the bar
            new_move = self.get_point_move(self.bar_point(), roll, roll_depth, can_bear_off=False)
            if new_move is not None:
                # Have made a move
                move_tree.add_child(Tree(new_move))
                # Make move provisional
                self.make_provisional_move(new_move, roll_depth)
                board_tree.add_child(Tree(copy.deepcopy(self.board_provisional[roll_depth])))
                # Try next roll depth
                self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])
                # # Reset board
                # self.clear_provisional_moves(roll_depth)
        else:
            # Check to see if player is allowed to bear off (all pieces in home area)
            can_bear_off = True  # Initially assume can bear off, until proven otherwise
            for n in range(7, 26):
                abs_point = self.absolute_point(n)
                if self.board_provisional[roll_depth][abs_point].colour == self.current_player:
                    # Player has piece outside of home area
                    can_bear_off = False
            if can_bear_off:
                for p in range(1, 7):
                    abs_point = self.absolute_point(p)
                    if self.board_provisional[roll_depth][abs_point].occupancy() > 0 and \
                            self.board_provisional[roll_depth][abs_point].colour == self.current_player:
                        new_move = self.get_point_move(abs_point, roll, roll_depth, True)
                        if new_move is not None:
                            # Have made a move
                            move_tree.add_child(Tree(new_move))
                            # Make move provisional
                            self.make_provisional_move(new_move, roll_depth)
                            board_tree.add_child(Tree(copy.deepcopy(self.board_provisional[roll_depth])))
                            # Try next roll depth
                            self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])
                            # # Reset board
                            # self.clear_provisional_moves(roll_depth)
            else:
                # Look through all other points and identify if they have a piece that can move
                for i in range(1, 25):
                    point = self.board_provisional[roll_depth][i]
                    if point.occupancy() > 0:
                        if point.colour == self.current_player:
                            # Point belongs to current player, so see if player can make move
                            new_move = self.get_point_move(i, roll, roll_depth, False)
                            if new_move is not None:
                                # Have made a move
                                move_tree.add_child(Tree(new_move))
                                # Make move provisional
                                self.make_provisional_move(new_move, roll_depth)
                                board_tree.add_child(Tree(copy.deepcopy(self.board_provisional[roll_depth])))
                                # Try next roll depth
                                self.get_board_from_dice_roll(dice_rolls, roll_depth + 1, move_tree.children[-1], board_tree.children[-1])
                                # # Reset board
                                # self.clear_provisional_moves(roll_depth)

        # Reset board
        self.clear_provisional_moves(roll_depth)

    def get_point_move(self, point_index: int, roll_value: int, roll_depth: int, can_bear_off: bool) -> Tuple:
        move_info = None
        proposed_position = self.where_will_roll_take_piece(point_index, roll_value)
        can_move = self.can_move_to_point(proposed_position, roll_depth, can_bear_off)
        if can_move:
            move_info = (point_index, proposed_position)
        return move_info

    def where_will_roll_take_piece(self, current_position: int, roll_value: int) -> int:
        new_position = current_position + self.play_direction() * roll_value
        return new_position

    def can_move_to_point(self, dest_point_index: int, roll_depth: int, can_bear_off: bool) -> bool:
        can_move = False
        if not 0 <= dest_point_index <= 25:
            # Trying to move to a position off the board, which is plainly not allowed!
            can_move = False
        elif can_bear_off and dest_point_index == self.home_point():
            can_move = True
        elif dest_point_index != self.home_point():
            destination = self.board_provisional[roll_depth][dest_point_index]
            if destination.occupancy() == 0:
                can_move = True
            elif destination.colour == self.current_player:
                can_move = True
            elif destination.colour != self.current_player and \
                    destination.occupancy() == 1:
                can_move = True
        return can_move

    def make_provisional_move(self, provisional_move: Tuple[int, int], roll_depth: int):
        start_index, dest_index = provisional_move
        start_prov_point_d = self.board_provisional[roll_depth][start_index]
        dest_prov_point_d = self.board_provisional[roll_depth][dest_index]
        start_prov_point_d.num_pieces -= 1
        if dest_index == self.home_point():
            # Piece has been cleared from board so remove it from the board point tallies
            pass
        elif dest_prov_point_d.occupancy() == 0 or dest_prov_point_d.colour == self.current_player:
            dest_prov_point_d.colour = self.current_player
            dest_prov_point_d.num_pieces += 1
        elif dest_prov_point_d.colour != self.current_player:
            # Other player's one piece is being replaced by current player's piece
            dest_prov_point_d.colour = self.current_player
            # Move other player's piece to bar
            self.board_provisional[roll_depth][self.bar_point(other_player=True)].num_pieces += 1
            self.board_provisional[roll_depth][self.bar_point(other_player=True)].colour = self.other_player_colour()
        # In any case, piece has moved from start location
        if start_prov_point_d.occupancy() == 0:
            start_prov_point_d.colour = Color.Empty

        # Copy to higher roll depths to make sure they're starting from the same baseline
        for d in range(roll_depth + 1, 4):
            self.board_provisional[d] = copy.deepcopy(self.board_provisional[roll_depth])


    def clear_provisional_moves(self, roll_depth):
        # Clear provisional moves due to current dice roll depth
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

    def enact_provisional_move(self, target_board: List[Point]):
        # Update the board to match the provisional board that has been chosen to be used.
        self.board = copy.deepcopy(target_board)

    def calculate_board_features(self, board: List[Point]) -> np.ndarray:
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
        features = np.zeros(196)
        num_mine_cleared = 0
        num_theirs_cleared = 0
        for p in range(0, 24):
            point = board[p]
            if point.colour == self.current_player:
                num_mine_cleared += point.num_pieces
                if point.num_pieces == 1:
                    features[p * 8] = 1
                elif point.num_pieces == 2:
                    features[p * 8 + 1] = 1
                elif point.num_pieces == 3:
                    features[p * 8 + 2] = 1
                elif point.num_pieces > 3:
                    features[p * 8 + 3] = (point.num_pieces - 3) / 2
            elif point.colour == self.other_player_colour():
                num_theirs_cleared += point.num_pieces
                if point.num_pieces == 1:
                    features[p * 8 + 4] = 1
                elif point.num_pieces == 2:
                    features[p * 8 + 5] = 1
                elif point.num_pieces == 3:
                    features[p * 8 + 6] = 1
                elif point.num_pieces > 3:
                    features[p * 8 + 7] = (point.num_pieces - 3) / 2
        features[192] = board[self.bar_point()].num_pieces / 2
        features[193] = board[self.bar_point(other_player=True)].num_pieces / 2
        features[193] = num_mine_cleared / 15
        features[195] = num_theirs_cleared / 15
        return features

    def game_over(self):
        # Identify if current player has any pieces left
        pieces_left = False
        for i in range(0, 26):
            if self.board[i].colour == self.current_player:
                pieces_left = True
                break
        return not pieces_left


if __name__ == '__main__':
    b = Board(True)
    agent = Agent(0.1, 0.01, 0.1, 0.95, 196)
    for pp in b.board:
        print(f"Point {pp.index} is {pp.colour}, with {pp.occupancy()} pieces.")
    b.choose_first_player()

    while True:
        dice_rolls = b.roll_dice()
        print(f"Dice rolls: {dice_rolls}")
        move_tree, board_tree = b.get_possible_moves_from_dice(dice_rolls)
        b.print_move_tree(move_tree)
        b.simple_board_representation("Initial board:", header=True)
        print(f"Number of possible moves: {len(board_tree.get_list_of_leaves())}")
        possible_boards = board_tree.get_list_of_leaves()
        if len(board_tree.children) > 0:
            board_assessments = []
            for possible_board in possible_boards:
                b.simple_board_representation("", possible_board, count=len(board_assessments))
                board_features = b.calculate_board_features(possible_board)
                board_assessments.append(agent.assess_features(board_features))
            action_index = agent.epsilon_greedy_action(board_assessments, print_outputs=b.print_boards)
            # Perform chosen action
            # TODO put some kind of assert here as possible board will always be defined
            b.enact_provisional_move(possible_boards[action_index])
        if b.game_over():
            break
        else:
            b.change_player()
    print(f"Game over! Game won by {b.current_player}")


        # print(leaf)
    # potential_boards = b.get_boards_from_moves(board_tree, [])


