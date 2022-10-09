import random

from game import Game
from TDGammon_agent import TDagent
import pygame
import logging
from enum import Enum
from human_agent import HumanAgent
from typing import List
import random
import time

BLACK = (0, 0, 0)
WHITE = (220, 220, 220)
GREY = (75, 75, 75)
DARK_GREY = (40, 40, 40)
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
RES_X = 800
RES_Y = 600

# Define board dimensions
TRI_WIDTH = (RES_X * 0.8) / 12.0
TRI_SPACING = (RES_X * 0.8) / 6.0
TRI_HEIGHT = RES_Y / 2.5
PIECE_RAD = TRI_WIDTH / 2.5

# Define start board
START_BOARD = [(2, PLAYER_X), None, None, None, None, (5, PLAYER_O),
               None, (3, PLAYER_X), None, None, None, (5, PLAYER_X),
               (5, PLAYER_O), None, None, None, (3, PLAYER_X), None,
               (5, PLAYER_X), None, None, None, None, (2, PLAYER_O)]


# Enums
class GameState(Enum):
    WELCOME = 0
    WAIT_GAME_CHOICE = 7
    CHOOSE_FIRST_PLAYER = 8
    NEW_BOARD = 1
    TURN_X = 2
    TURN_O = 3
    WAIT_X = 4
    WAIT_O = 5
    GAME_END = 6


class GameType(Enum):
    PvP = 0
    PvE = 0


def draw_board():
    # Clear screen
    screen.fill(BLACK)
    # Draw board
    for n in range(0, 6):
        # Insert gap for board middle (bar)
        if n >= 3:
            spacer = TRI_WIDTH
        else:
            spacer = 0
        w_border = RES_X / 100  # border width
        # White triangles (player O)
        pygame.draw.polygon(screen, WHITE, [[w_border + n * TRI_SPACING + spacer, 0],
                                            [w_border + n * TRI_SPACING + TRI_WIDTH / 2 + spacer, TRI_HEIGHT],
                                            [w_border + n * TRI_SPACING + TRI_WIDTH + spacer, 0]])
        pygame.draw.polygon(screen, WHITE, [[w_border + n * TRI_SPACING + TRI_WIDTH + spacer, RES_Y],
                                            [w_border + n * TRI_SPACING + TRI_WIDTH * 1.5 + spacer, RES_Y - TRI_HEIGHT],
                                            [w_border + (n + 1) * TRI_SPACING + spacer, RES_Y]])
        # Red triangles
        pygame.draw.polygon(screen, RED, [[w_border + n * TRI_SPACING + spacer, RES_Y],
                                          [w_border + n * TRI_SPACING + TRI_WIDTH / 2 + spacer, RES_Y - TRI_HEIGHT],
                                          [w_border + n * TRI_SPACING + TRI_WIDTH + spacer, RES_Y]])
        pygame.draw.polygon(screen, RED, [[w_border + n * TRI_SPACING + TRI_WIDTH + spacer, 0],
                                          [w_border + n * TRI_SPACING + TRI_WIDTH * 1.5 + spacer, TRI_HEIGHT],
                                          [w_border + (n + 1) * TRI_SPACING + spacer, 0]])
    # Bar
    pygame.draw.rect(screen, GREY, [w_border + TRI_WIDTH * 6, 0, TRI_WIDTH, RES_Y])
    # # Board edges
    # pygame.draw.rect(screen, GREY, [0, 0, w_border, RES_Y])
    # pygame.draw.rect(screen, GREY, [RES_X - w_border, 0, RES_X, RES_Y])
    # Screen border
    pygame.draw.rect(screen, GREY, [0, 0, TRI_WIDTH * 13 + w_border * 2, RES_Y], 10)


def draw_welcome():
    font = pygame.font.SysFont(None, 50)
    # Welcome message
    text = font.render('Welcome to MRGammon backgammon', True, WHITE)
    text_rect = text.get_rect(center=((RES_X * 0.9)/2, RES_Y * 0.45))
    screen.blit(text, text_rect)
    # Game type options
    font = pygame.font.SysFont(None, 32)
    pvp = pygame.draw.rect(screen, DARK_GREY, [TRI_WIDTH * 1.25, RES_Y * 0.48, TRI_WIDTH * 3.8, 48])
    text = font.render("Player vs Player", True, WHITE)
    screen.blit(text, [TRI_WIDTH * 1.5, RES_Y * 0.5])
    pve = pygame.draw.rect(screen, DARK_GREY, [TRI_WIDTH * 7.75, RES_Y * 0.48, TRI_WIDTH * 4.5, 48])
    text = font.render("Player vs Computer", True, WHITE)
    screen.blit(text, [TRI_WIDTH * 8, RES_Y * 0.5])
    return pvp, pve


def draw_piece(global_point: int, point_occupancy: int, player: int):
    if player == PLAYER_X:
        colour = COLOUR_X
        border_colour = WHITE
        bar_y = RES_Y * 0.95 - (point_occupancy - 1) * PIECE_RAD / 2
    else:
        colour = COLOUR_O
        border_colour = RED
        bar_y = RES_Y * 0.05 + (point_occupancy - 1) * PIECE_RAD / 2
    if global_point == BAR_INDEX:
        # On bar
        y_pos = bar_y
        x_pos = TRI_WIDTH * 6.5 + RES_X / 100
        logging.debug(f"Piece is on bar at [{x_pos}, {y_pos}]")
    elif global_point == HOME_INDEX:
        # Removed from board
        y_pos = bar_y
        x_pos = TRI_WIDTH * 14
        logging.debug(f"Piece has been removed at [{x_pos}, {y_pos}]")
    elif global_point > 11:
        # In top row
        if global_point > 17:
            global_point += 1  # due to spacer
        y_pos = PIECE_RAD * (2 * point_occupancy - 1)
        x_pos = TRI_WIDTH / 2.0 * ((global_point - 11) * 2 - 1)
    else:
        # In bottom row
        if global_point < 6:
            global_point -= 1
        y_pos = RES_Y - PIECE_RAD * (2 * point_occupancy - 1)
        x_pos = TRI_WIDTH / 2.0 * ((12 - global_point) * 2 - 1)
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
    font = pygame.font.SysFont(None, 42)
    text = font.render(str(face_value), True, BLACK)
    screen.blit(text, face)
    # Update display
    pygame.display.update()


def draw_dice_roll(num_die: int, player: int):
    logging.debug(f"Rolling {num_die} dice for player {player}")
    roll_time = []
    centers = []
    die_width = TRI_WIDTH / 2
    for n in range(0, num_die):
        # Choose random amount of time for the die to take to settle
        roll_time.append(1.5 + random.random() * 2)
        logging.debug(f"Die {n} will take {roll_time[-1]} to stop.")
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
                    face_value[n] = random.randint(1, 7)
                    draw_die(player, face_value[n], centers[n], die_width)
        clock.tick(10)

    return face_value


def determine_first_player(first_attempt=True) -> int:
    x_score = draw_dice_roll(1, PLAYER_X)
    o_score = draw_dice_roll(1, PLAYER_O)
    if x_score == o_score:
        # Same roll for both so try again
        draw_roll_again()
        winning_player = determine_first_player(False)
    else:
        if x_score > o_score:
            winning_player = PLAYER_X
        else:
            winning_player = PLAYER_O
        draw_declare_starter(winning_player)
    return winning_player


def draw_roll_again() -> None:
    font = pygame.font.SysFont(None, 60)
    text = font.render("Draw! Roll again", True, WHITE)
    screen.blit(text, [TRI_WIDTH * 4, RES_Y * 0.45])
    pygame.display.update()
    time.sleep(2)


def draw_declare_starter(player: int) -> None:
    font = pygame.font.SysFont(None, 60)
    if player == PLAYER_X:
        player_name = NAME_X
    else:
        player_name = NAME_O
    text = font.render(f"{player_name} to start the game!", True, WHITE)
    screen.blit(text, [TRI_WIDTH * 4, RES_Y * 0.45])
    pygame.display.update()
    time.sleep(2)


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
        # Draw empty board
        draw_board()
        pygame.display.update()
        # Randomly choose first player by rolling dice
        first_player = determine_first_player()
        if first_player == PLAYER_X:
            game_state = GameState.TURN_X
        else:
            game_state = GameState.TURN_O
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






