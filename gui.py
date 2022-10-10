import copy

from game import Game
from TDGammon_agent import TDagent
import pygame
import logging
from enum import Enum
from human_agent import HumanAgent
from typing import List, Union
import random
import time
import ctypes

# Cope with Windows display scaling
ctypes.windll.user32.SetProcessDPIAware()

BLACK = (30, 30, 30)
WHITE = (220, 220, 220)
GREY = (75, 75, 75)
DARK_GREY = (50, 50, 50)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (200, 0, 0)

PLAYER_X = 0
COLOUR_X = RED
NAME_X = "Red"
PLAYER_O = 1
COLOUR_O = WHITE
NAME_O = "White"
BAR_INDEX = 24
HOME_INDEX = -1

# Resolution
RES_Y = 1920
RES_X = RES_Y / 3 * 4

# Define board dimensions
TRI_WIDTH = (RES_X * 0.8) / 12.0
TRI_SPACING = (RES_X * 0.8) / 6.0
TRI_HEIGHT = RES_Y / 2.5
PIECE_RAD = TRI_WIDTH / 2.5
W_BORDER = RES_X / 100  # border width

# Define start board
START_BOARD = [2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 0, 0, 0, 0, 3, 0, 5, 0, 0, 0, 0, 0]

# Miscellaneous
MSG_DISPLAY_TIME = 2


# Enums
class GameState(Enum):
    WELCOME = 0
    WAIT_GAME_CHOICE = 7
    CHOOSE_FIRST_PLAYER = 8
    NEW_BOARD = 1
    START_GAME = 9
    PLAYER_ROLL_DICE = 10
    PLAYER_SELECT_PIECE = 2
    PLAYER_SELECT_DEST = 3
    CHANGE_PLAYER = 11
    WAIT_X = 4
    WAIT_O = 5
    GAME_END = 6


class GameType(Enum):
    PvP = 0
    PvE = 0


class Point:
    def __init__(self, rect, global_point: int):
        self.rect = rect
        self.global_point = global_point
        self.point_x = global_point
        self.point_o = 23 - global_point


class Piece:
    def __init__(self, rect, player_point: int, point_position: int, player_num: int):
        self.rect = rect
        self.player_point = player_point
        self.point_position = point_position
        self.player = player_num
        self.is_selected = False

    def select(self):
        self.is_selected = True
        draw_piece(self.player_point, self.point_position, self.player, self.is_selected)

    def deselect(self):
        self.is_selected = False
        draw_piece(self.player_point, self.point_position, self.player)


def draw_button(text_string: str, left: Union[float, int], top: Union[float, int], width: Union[float, int], height: Union[float, int]) -> pygame.rect:
    font = pygame.font.SysFont(None, int(height * 0.9))
    # Draw button rectangle
    rect = pygame.draw.rect(screen, DARK_GREY, [left, top, width, height])
    # Draw text centered in rectangle
    text = font.render(text_string, True, WHITE)
    text_rect = text.get_rect()
    text_rect.center = (left + width / 2, top + height / 2)
    screen.blit(text, text_rect)
    # Return rectangle
    return rect


def draw_board() -> List[Point]:
    # Clear screen
    screen.fill(BLACK)
    # Draw board
    triangles: List[Point] = [None] * 24
    for n in range(0, 6):
        # Insert gap for board middle (bar)
        if n >= 3:
            spacer = TRI_WIDTH
        else:
            spacer = 0
        # White triangles (player O)
        triangles[12 + 2 * n] = pygame.draw.polygon(screen, WHITE, [
                                            [W_BORDER + n * TRI_SPACING + spacer, 0],
                                            [W_BORDER + n * TRI_SPACING + TRI_WIDTH / 2 + spacer, TRI_HEIGHT],
                                            [W_BORDER + n * TRI_SPACING + TRI_WIDTH + spacer, 0]])
        triangles[10 - 2 * n] = pygame.draw.polygon(screen, WHITE, [
                                            [W_BORDER + n * TRI_SPACING + TRI_WIDTH + spacer, RES_Y],
                                            [W_BORDER + n * TRI_SPACING + TRI_WIDTH * 1.5 + spacer, RES_Y - TRI_HEIGHT],
                                            [W_BORDER + (n + 1) * TRI_SPACING + spacer, RES_Y]])
        # Red triangles
        triangles[11 - 2 * n] = pygame.draw.polygon(screen, RED, [
                                            [W_BORDER + n * TRI_SPACING + spacer, RES_Y],
                                            [W_BORDER + n * TRI_SPACING + TRI_WIDTH / 2 + spacer, RES_Y - TRI_HEIGHT],
                                            [W_BORDER + n * TRI_SPACING + TRI_WIDTH + spacer, RES_Y]])
        triangles[13 + 2 * n] = pygame.draw.polygon(screen, RED, [
                                            [W_BORDER + n * TRI_SPACING + TRI_WIDTH + spacer, 0],
                                            [W_BORDER + n * TRI_SPACING + TRI_WIDTH * 1.5 + spacer, TRI_HEIGHT],
                                            [W_BORDER + (n + 1) * TRI_SPACING + spacer, 0]])
    # Save triangles into classes for easier access (upgrade triangles array to contain class object)
    for n in range(0, 24):
        triangles[n] = Point(triangles[n], n)
    # Bar
    pygame.draw.rect(screen, GREY, [W_BORDER + TRI_WIDTH * 6, 0, TRI_WIDTH, RES_Y])
    # Screen border
    pygame.draw.rect(screen, GREY, [0, 0, TRI_WIDTH * 13 + W_BORDER * 2, RES_Y], 10)

    # Write global coord into triangles
    font = pygame.font.SysFont(None, 24)
    for n in range(0, 24):
        text = font.render(str(n), True, WHITE)
        screen.blit(text, triangles[n].rect)

    return triangles


def draw_welcome():
    font = pygame.font.SysFont(None, int(RES_Y/12))
    # Welcome message
    text = font.render("Welcome to Martin's backgammon", True, WHITE)
    text_rect = text.get_rect(center=((RES_X * 0.9)/2, RES_Y * 0.45))
    screen.blit(text, text_rect)
    # Game type options
    pvp = draw_button("Player vs Player", TRI_WIDTH * 1.25, RES_Y * 0.48, TRI_WIDTH * 3.8, RES_Y / 15)
    pve = draw_button("Player vs Computer", TRI_WIDTH * 7.75, RES_Y * 0.48, TRI_WIDTH * 4.5, RES_Y / 15)
    return pvp, pve


def convert_coords_to_global(player_point: int, player: int) -> int:
    if player == PLAYER_X:
        global_point = player_point
    else:
        global_point = 23 - player_point
    return global_point


def draw_piece(player_point: int, point_occupancy: int, player: int, is_selected: bool=False) -> pygame.rect:
    # Determine player-specific attributes
    if player == PLAYER_X:
        if is_selected:
            colour = BLUE
            border_colour = BLACK
        else:
            colour = COLOUR_X
            border_colour = WHITE
        bar_y = RES_Y * 0.95 - (point_occupancy - 1) * PIECE_RAD / 2
    else:
        if is_selected:
            colour = BLUE
            border_colour = BLACK
        else:
            colour = COLOUR_O
            border_colour = RED
        bar_y = RES_Y * 0.05 + (point_occupancy - 1) * PIECE_RAD / 2
    # Convert player point numbering to global (i.e. screen space)
    global_point = convert_coords_to_global(player_point, player)
    # Transform position according to special features
    if global_point == BAR_INDEX:
        # On bar
        y_pos = bar_y
        x_pos = TRI_WIDTH * 6.5 + RES_X / 100
    elif global_point == HOME_INDEX:
        # Removed from board
        y_pos = bar_y
        x_pos = TRI_WIDTH * 14
    elif global_point > 11:
        # In top row
        if global_point > 17:
            global_point += 1  # due to spacer
        y_pos = PIECE_RAD * (2 * point_occupancy - 1) + W_BORDER
        x_pos = TRI_WIDTH / 2.0 * ((global_point - 11) * 2 - 1) + W_BORDER
    else:
        # In bottom row
        if global_point < 6:
            global_point -= 1
        y_pos = RES_Y - PIECE_RAD * (2 * point_occupancy - 1) - W_BORDER
        x_pos = TRI_WIDTH / 2.0 * ((12 - global_point) * 2 - 1) + W_BORDER
    sprite = pygame.draw.circle(screen, colour, [x_pos, y_pos], PIECE_RAD)
    pygame.draw.circle(screen, border_colour, [x_pos, y_pos], PIECE_RAD, 2)
    return sprite


def draw_die(player: int, face_value: int, die_index: int):
    # Specify die position and colour
    if player == PLAYER_X:
        center = [TRI_WIDTH * (1 + die_index), RES_Y * 0.55]
        colour = COLOUR_X
    else:
        center = [TRI_WIDTH * (8 + die_index), RES_Y * 0.55]
        colour = COLOUR_O
    # Die size
    width = TRI_WIDTH / 2
    # Draw cube surface
    face = pygame.draw.rect(screen, colour, [center[0] - width/2, center[1] - width/2, width, width])
    # Show face value
    font = pygame.font.SysFont(None, int(RES_Y / 20))
    text = font.render(str(face_value), True, BLACK)
    screen.blit(text, face)
    # Update display
    pygame.display.update()


def roll_dice(num_die: int, player: int) -> List[int]:
    logging.debug(f"Rolling {num_die} dice for player {player}")
    roll_time = []
    for n in range(0, num_die):
        # Choose random amount of time for the die to take to settle
        roll_time.append(1.5 + random.random() * 2)

    start_time = time.time()
    dice_stopped = [False] * num_die
    num_stopped = 0
    face_value = [0] * num_die
    done = False
    clock = pygame.time.Clock()
    while num_stopped < num_die or done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                face_value = None

        elapsed = time.time() - start_time
        for n in range(0, num_die):
            if elapsed > roll_time[n]:
                dice_stopped[n] = True
                num_stopped += 1
            if not dice_stopped[n]:
                if random.random() > elapsed / roll_time[n]:
                    face_value[n] = random.randint(1, 6)
                    draw_die(player, face_value[n], n)
        clock.tick(10)
    logging.info(f"Value(s) rolled: {' and '.join(str(v) for v in face_value)}")
    return face_value


def determine_first_player(first_attempt=True) -> int:
    # Draw empty board
    draw_board()
    pygame.display.update()
    # Roll dice
    logging.info("Players to roll one die each; highest score gets to start the game.")
    x_score = roll_dice(1, PLAYER_X)
    o_score = roll_dice(1, PLAYER_O)
    if x_score == o_score:
        # Same roll for both so try again
        logging.info(f"Players drew when rolling for first ply.")
        draw_roll_again()
        winning_player = determine_first_player(False)
    else:
        if x_score > o_score:
            winning_player = PLAYER_X
        else:
            winning_player = PLAYER_O
        logging.info(f"Player {winning_player} to start the game.")
        draw_declare_starter(winning_player)
    return winning_player


def draw_roll_again() -> None:
    font = pygame.font.SysFont(None, int(RES_Y / 10))
    text = font.render("Draw! Roll again", True, WHITE)
    screen.blit(text, [TRI_WIDTH * 4, RES_Y * 0.45])
    pygame.display.update()
    time.sleep(MSG_DISPLAY_TIME)


def draw_declare_starter(player: int) -> None:
    font = pygame.font.SysFont(None, int(RES_Y / 10))
    if player == PLAYER_X:
        player_name = NAME_X
    else:
        player_name = NAME_O
    text = font.render(f"{player_name} to start the game!", True, WHITE)
    screen.blit(text, [TRI_WIDTH * 2, RES_Y * 0.45])
    pygame.display.update()
    time.sleep(MSG_DISPLAY_TIME)


def draw_pieces_for_player(player: int, board: List[int], bar: int, removed: int) -> List[Piece]:
    pieces = []
    for p in range(0, len(board)):
        for n in range(0, board[p]):
            pieces.append(Piece(draw_piece(p, n + 1, player), p, n + 1, player))
    for n in range(0, bar):
        pieces.append(Piece(draw_piece(BAR_INDEX, n + 1, player), BAR_INDEX, n + 1, player))
    for n in range(0, removed):
        pieces.append(Piece(draw_piece(HOME_INDEX, n + 1, player), HOME_INDEX, n + 1, player))
    return pieces


def draw_board_and_pieces(board_x: List[int], board_o: List[int], bar_x: int, bar_o: int, removed_x: int, removed_o: int):
    logging.info(f"Drawing board and pieces")
    # Draw empty board
    triangles = draw_board()
    # Populate pieces according to starting boards
    pieces_x = draw_pieces_for_player(PLAYER_X, board_x, bar_x, removed_x)
    pieces_o = draw_pieces_for_player(PLAYER_O, board_o, bar_o, removed_o)
    logging.debug(f"Drew {len(pieces_x)} X pieces and {len(pieces_o)} O pieces")
    return pieces_x, pieces_o, triangles


def draw_player_controls(player: int):
    # Draw buttons for player to control game
    quit = draw_button("Exit", TRI_WIDTH * 14, RES_Y * 0.45, TRI_WIDTH * 0.75, RES_Y * 0.03)
    menu = draw_button("Menu", TRI_WIDTH * 13, RES_Y * 0.45, TRI_WIDTH * 0.75, RES_Y * 0.03)
    return quit, menu


def move_piece(piece_to_move: Piece, destination_point: Point):
    piece_to_move.global_point = destination_point.global_point
    piece_to_move.point_position = destination_point.occupancy + 1
    destination_point.occupancy += 1
    piece_to_move.is_selected = False






# Configure debugging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")

# Initialise pygame viewport
pygame.init()
screen = pygame.display.set_mode((RES_X, RES_Y))
pygame.display.set_caption("MRGammon")
#

# Set up states
game_state = GameState.WELCOME

done = False
press_enter = False
game = None
btn_menu = None
current_player = 0
selected_piece = 0
pieces_x = []
pieces_o = []
my_pieces = []
point_tris = []

clock = pygame.time.Clock()

while not done:
    # Draw quit and main menu buttons
    btn_quit, btn_menu = draw_player_controls(current_player)

    # Get events
    all_events = pygame.event.get()
    for event in all_events:
        if event.type == pygame.QUIT:
            done = True
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if btn_quit.collidepoint(pygame.mouse.get_pos()):
                logging.info("User clicked 'Exit' button")
                done = True
            if btn_menu.collidepoint(pygame.mouse.get_pos()):
                # User clicked exit
                game_state = GameState.WELCOME

    if done:
        break

    # State machine
    if game_state == GameState.WELCOME:
        # Draw empty board
        draw_board()
        # Print welcome message
        btn_pvp, btn_pve = draw_welcome()
        # Next state
        game_state = GameState.WAIT_GAME_CHOICE
        logging.info("Showing welcome screen")
    elif game_state == GameState.WAIT_GAME_CHOICE:
        # Detect user choice of game type
        for event in all_events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                if btn_pve.collidepoint(pygame.mouse.get_pos()):
                    logging.info("Chosen to play a game of PvP")
                    game = Game(HumanAgent(), HumanAgent())
                    game_type = GameType.PvP
                    game_state = GameState.CHOOSE_FIRST_PLAYER
                elif btn_pvp.collidepoint(pygame.mouse.get_pos()):
                    logging.info("Chosen to play a game of PvE")
                    game = Game(HumanAgent(), TDagent())
                    game_type = GameType.PvE
                    game_state = GameState.CHOOSE_FIRST_PLAYER
    elif game_state == GameState.CHOOSE_FIRST_PLAYER:
        # Randomly choose first player by rolling dice
        current_player = determine_first_player()
        # Set player in game logic
        game.set_player(current_player)
        game_state = GameState.START_GAME
    elif game_state == GameState.START_GAME:
        # Populate initial board
        game.generate_starting_board(False)
        pieces_x, pieces_o, point_tris = draw_board_and_pieces(game.board.x_board, game.board.o_board, 0, 0, 0, 0)
        game_state = GameState.PLAYER_ROLL_DICE
    elif game_state == GameState.PLAYER_ROLL_DICE:
        # Roll dice
        rolls = roll_dice(2, current_player)
        if rolls[0] == rolls[1]:
            # Rolled a double
            rolls = rolls + rolls
            # Draw additional dice
            draw_die(current_player, rolls[0], 2)
            draw_die(current_player, rolls[0], 3)
        game_state = GameState.PLAYER_SELECT_PIECE
    elif game_state == GameState.PLAYER_SELECT_PIECE:
        if current_player == PLAYER_X:
            my_pieces = pieces_x
        else:
            my_pieces = pieces_o
        # Wait for user to choose piece to move
        for event in all_events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for piece in my_pieces:
                    if piece.rect.collidepoint(pygame.mouse.get_pos()):
                        # Clicked on a piece
                        logging.info(f"Selected {piece.point_position}th piece at point {piece.player_point} [pc]")
                        piece.select()
                        selected_piece = piece
                        game_state = GameState.PLAYER_SELECT_DEST
    elif game_state == GameState.PLAYER_SELECT_DEST:
        # Play direction dependent on player
        if current_player == PLAYER_X:
            play_direction = 1
        else:
            play_direction = -1
        # Wait for user to choose destination
        for event in all_events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for piece in my_pieces:
                    if piece.rect.collidepoint(pygame.mouse.get_pos()) and piece.is_selected:
                        # Player wants to unselect piece
                        piece.deselect()
                        selected_piece = None
                        game_state = GameState.PLAYER_SELECT_PIECE
                for tri in point_tris:
                    if tri.rect.collidepoint(pygame.mouse.get_pos()) and selected_piece is not None:
                        # Clicked on a triangle point with a piece selected
                        # Check if the distance to the point is equal to one of the remaining dice rolls
                        start_pos = selected_piece.player_point
                        if current_player == PLAYER_X:
                            dest_pos = tri.point_x
                        else:
                            dest_pos = tri.point_o
                        logging.info(f"Clicked on triangle at point {dest_pos} [pc]")
                        move_distance = dest_pos - start_pos
                        if move_distance in rolls:
                            # Can make that move according to dice, but still need to check that it's a legal move
                            selected_point = tri
                            logging.info(f"Proposed move can use a dice roll (distance {move_distance})")
                            # Check to see if move is permitted (e.g. not blocked by double-stack)
                            if start_pos == BAR_INDEX:
                                start_pos = "bar"  # convert to board.Board() implementation
                            if game.board.move_permitted(start_pos, move_distance, current_player):
                                logging.info(f"Proposed move is considered permitted by game mechanics")
                                game.board.perform_move(start_pos, move_distance, current_player)
                                pieces_x, pieces_o, point_tris = draw_board_and_pieces(game.board.x_board,
                                                                                       game.board.o_board,
                                                                                       game.board.x_bar,
                                                                                       game.board.x_removed,
                                                                                       game.board.o_bar,
                                                                                       game.board.o_removed)
                                # Remove roll from set of rolls and draw remaining dice
                                del rolls[rolls.index(move_distance)]
                                for roll, n in zip(rolls, range(0, len(rolls))):
                                    draw_die(current_player, roll, n)
                                # Determine if player can make another move, or if it's next player's turn
                                if len(rolls) > 0:
                                    game_state = GameState.PLAYER_SELECT_PIECE
                                else:
                                    game_state = GameState.CHANGE_PLAYER
                            else:
                                logging.info(f"Move is not permitted by game mechanics")
    elif game_state == GameState.CHANGE_PLAYER:
        current_player = 1 - current_player
        game.set_player(current_player)
        game_state = GameState.PLAYER_ROLL_DICE

    elif game_state == GameState.NEW_BOARD:
        # Draw empty board
        draw_board()
        # Draw pieces

    else:
        # Default state
        logging.error(f"Unrecognised game state: {game_state}.")
        game_state = GameState.WELCOME


    # Update your screen when required
    pygame.display.update()
    clock.tick(30)






