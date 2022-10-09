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
START_BOARD = [(2, PLAYER_X), None, None, None, None, (5, PLAYER_O),
               None, (3, PLAYER_O), None, None, None, (5, PLAYER_X),
               (5, PLAYER_O), None, None, None, (3, PLAYER_X), None,
               (5, PLAYER_X), None, None, None, None, (2, PLAYER_O)]

# Miscellaneous
MSG_DISPLAY_TIME = 2

# Enums
class GameState(Enum):
    WELCOME = 0
    WAIT_GAME_CHOICE = 7
    CHOOSE_FIRST_PLAYER = 8
    NEW_BOARD = 1
    START_GAME = 9
    PLAYER_SELECT_PIECE = 2
    PLAYER_SELECT_DEST = 3
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


class Piece:
    def __init__(self, rect, global_point: int, occupancy: int, player_num: int):
        self.rect = rect
        self.global_point = global_point
        self.occupancy = occupancy
        self.player = player_num
        self.is_selected = False

    def select(self):
        self.is_selected = True
        draw_piece(self.global_point, self.occupancy, -1)

    def deselect(self):
        self.is_selected = False
        draw_piece(self.global_point, self.occupancy, self.player)


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
    triangles = [None] * 24
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


def draw_piece(global_point: int, point_occupancy: int, player: int):
    # Determine player-specific attributes
    if player == PLAYER_X:
        colour = COLOUR_X
        border_colour = WHITE
        bar_y = RES_Y * 0.95 - (point_occupancy - 1) * PIECE_RAD / 2
    elif player == PLAYER_O:
        colour = COLOUR_O
        border_colour = RED
        bar_y = RES_Y * 0.05 + (point_occupancy - 1) * PIECE_RAD / 2
    else:
        colour = BLUE
        border_colour = BLACK
        bar_y = RES_Y / 2
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


def draw_die(player: int, face_value: int, center: List[float], size: float):
    if len(center) != 2:
        logging.error("draw_die() called with center defined other than as [x,y]")
    # Draws dice face with defined centre and width.
    # logging.debug(f"Showing die with center: {center} with width {size}.")
    if player == PLAYER_X:
        colour = COLOUR_X
    else:
        colour = COLOUR_O
    # Draw cube surface
    face = pygame.draw.rect(screen, colour, [center[0] - size/2, center[1] - size/2, size, size])
    # Show face value
    font = pygame.font.SysFont(None, int(RES_Y / 20))
    text = font.render(str(face_value), True, BLACK)
    screen.blit(text, face)
    # Update display
    pygame.display.update()


def roll_dice(num_die: int, player: int) -> List[int]:
    logging.debug(f"Rolling {num_die} dice for player {player}")
    roll_time = []
    centers = []
    die_width = TRI_WIDTH / 2
    for n in range(0, num_die):
        # Choose random amount of time for the die to take to settle
        roll_time.append(1.5 + random.random() * 2)
        # Specify die position
        if player == PLAYER_X:
            center = [TRI_WIDTH * (1 + n), RES_Y * 0.55]
        else:
            center = [TRI_WIDTH * (8 + n), RES_Y * 0.55]
        centers.append(center)

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
                    draw_die(player, face_value[n], centers[n], die_width)
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


def setup_starting_board():
    # Draw empty board
    triangles = draw_board()
    # Clear lists of pieces
    pieces_x = []
    pieces_o = []
    # Populate pieces, using global point indices (0 = point nearest white home)
    for p in range(0, len(START_BOARD)):
        if START_BOARD[p] is None:
            # No pieces at this point
            pass
        else:
            occupancy, player = START_BOARD[p]
            for n in range(0, occupancy):
                piece = draw_piece(p, n + 1, player)
                if player == PLAYER_X:
                    pieces_x.append(Piece(piece, p, n + 1, player))
                else:
                    pieces_o.append(Piece(piece, p, n + 1, player))
    logging.debug(f"Lengths {len(pieces_x)} and {len(pieces_o)}")
    return pieces_x, pieces_o, triangles


def draw_player_controls(player: int):
    # Draw buttons for player to control game
    quit = draw_button("Exit", TRI_WIDTH * 14, RES_Y * 0.45, TRI_WIDTH * 0.75, RES_Y * 0.03)
    return quit


def transfer_board_to_game(game: Game, pieces_x: List[Piece], pieces_o: List[Piece]):
    for x in pieces_x:
        game.board.x_board[x.global_point]
        # TODO finish transcription. Remember that X is in opposite direction in Game




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
btn_quit = None
current_player = 0
selected_piece = 0
pieces_x = []
pieces_o = []
my_pieces = []
point_tris = []
while not done:
    all_events = pygame.event.get()
    for event in all_events:
        if event.type == pygame.QUIT:
            done = True

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
        game_state = GameState.START_GAME
    elif game_state == GameState.START_GAME:
        # Populate initial board
        pieces_x, pieces_o, point_tris = setup_starting_board()
        transfer_board_to_game(game, pieces_x, pieces_o)
        piece_positions = copy.deepcopy(START_BOARD)
        game_state = GameState.PLAYER_SELECT_PIECE
    elif game_state == GameState.PLAYER_SELECT_PIECE:
        if current_player == PLAYER_X:
            my_pieces = pieces_x
        else:
            my_pieces = pieces_o
        # If controls don't already exist, we've just started the turn
        if btn_quit is None:
            btn_quit = draw_player_controls(current_player)
            # Roll dice
            rolls = roll_dice(2, current_player)
            if rolls[0] == rolls[1]:
                # Rolled a double
                rolls = rolls + rolls
            # Set player in game logic
            game.set_player(current_player)
        # Wait for user to choose piece to move
        for event in all_events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for piece in my_pieces:
                    if piece.rect.collidepoint(pygame.mouse.get_pos()):
                        # Clicked on a piece
                        logging.info(f"Selected piece on point {piece.global_point} at [{piece.rect.left}, {piece.rect.top}]")
                        if piece.is_selected:
                            piece.deselect()
                        else:
                            # Clear existing selection before selecting another
                            for piece_2 in my_pieces:
                                if piece_2.is_selected:
                                    piece_2.deselect()
                            piece.select()
                            selected_piece = piece.global_point
                            game_state = GameState.PLAYER_SELECT_DEST
                    elif btn_quit.collidepoint(pygame.mouse.get_pos()):
                        # User clicked exit
                        game_state = GameState.WELCOME
    elif game_state == GameState.PLAYER_SELECT_DEST:
        # Wait for user to choose destination
        for event in all_events:
            if event.type == pygame.MOUSEBUTTONDOWN:
                for tri in point_tris:
                    if tri.rect.collidepoint(pygame.mouse.get_pos()):
                        # Clicked on a triangle point
                        logging.info(f"Clicked on triangle")
                        # Check to see if move is permitted
                        game.board
                for piece in my_pieces:
                    if piece.rect.collidepoint(pygame.mouse.get_pos()):
                        # Clicked on a piece
                        logging.info(f"Selected piece on point {piece.global_point} at [{piece.rect.left}, {piece.rect.top}]")
                        if piece.is_selected:
                            piece.deselect()
                            game_state = GameState.PLAYER_SELECT_PIECE
                            break
                        # else:
                        #     # Clear existing selection before selecting another
                        #     for piece_2 in my_pieces:
                        #         if piece_2.is_selected:
                        #             piece_2.deselect()
                        #     piece.select()
                        #     selected_piece = piece.global_point
                    elif btn_quit.collidepoint(pygame.mouse.get_pos()):
                        # User clicked exit
                        game_state = GameState.WELCOME



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






