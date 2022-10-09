#from game import Game
import pygame
import logging

BLACK = (0, 0, 0)
WHITE = (220, 220, 220)
GREY = (75, 75, 75)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
RED = (200, 0, 0)

PLAYER_X = 0
PLAYER_O = 1
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


def draw_board():
    # Draw board
    for n in range(0, 6):
        # Insert gap for board middle (bar)
        if n >= 3:
            spacer = TRI_WIDTH
        else:
            spacer = 0
        w_border = RES_X / 100  # border width
        # White triangles
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


def draw_piece(global_point: int, point_occupancy: int, player: int):
    if player == PLAYER_X:
        colour = RED
        border_colour = WHITE
        bar_y = RES_Y * 0.95 - (point_occupancy - 1) * PIECE_RAD / 2
    else:
        colour = WHITE
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
    pygame.draw.circle(screen, colour, [x_pos, y_pos], PIECE_RAD)
    pygame.draw.circle(screen, border_colour, [x_pos, y_pos], PIECE_RAD, 2)


# Configure debugging
logging.basicConfig(level=logging.DEBUG, format="%(message)s")

# initilize the pygame module
pygame.init()
# Setting your screen size with a tuple of the screen width and screen height
screen = pygame.display.set_mode((RES_X, RES_Y))
# Setting a random caption title for your pygame graphical window.
pygame.display.set_caption("MRGammon")
draw_board()
draw_piece(-1, 1, PLAYER_X)
draw_piece(24, 1, PLAYER_X)
# Update your screen when required
pygame.display.update()

done = False
while not done:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            done = True




