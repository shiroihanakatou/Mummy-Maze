import pygame
from pygame.locals import *

pygame.init()
FPS = 60
FramePerSec = pygame.time.Clock()

ALLOWED_BUTTON = [K_UP, K_w, K_DOWN, K_s, K_LEFT, K_a, K_RIGHT, K_d, K_SPACE]

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GRAY  = (150, 150, 150)
NGRAY = (165, 165, 165)
GREEN = (0, 255, 0)
CYAN  = (0, 255, 255)
YELLOW=(255,255,0)
ORANGE=(255,165,0)
PINK  = (255,192,203)
DARKGREEN=(0,100,0)

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 800

# ===== Difficulty -> Board size =====
DIFFICULTY_TO_SIZE = {
    "easy": 6,
    "medium": 8,
    "hard": 10,
}

# ===== Runtime-changeable grid config (default) =====
ROWS = COLS = 10

org_backdrop_w=494
org_backdrop_h=480
X,Y=org_backdrop_w*1.5,org_backdrop_h*1.5

CELL_SIZE = 0.0
BUTTON_SIZE=80
maze_width = 0.0
maze_height = 0.0

stair_padding = 0.0
# Tọa độ bắt đầu vẽ (Top-Left) để mê cung nằm giữa màn hình

OFFSET_X_1=490
OFFSET_Y_1=70




OFFSET_X = 0.0
OFFSET_Y = 0.0
wall_gap = 0.0


def apply_grid_size(size: int):
    """Recompute all variables derived from ROWS/COLS."""
    global ROWS, COLS, CELL_SIZE
    global maze_width, maze_height, stair_padding
    global OFFSET_X, OFFSET_Y, wall_gap

    size = int(size)
    ROWS = COLS = size

    # giữ công thức scale gốc của mày
    CELL_SIZE = 35.8 * 10 * X / org_backdrop_w / ROWS

    maze_width = COLS * CELL_SIZE
    maze_height = ROWS * CELL_SIZE

    stair_padding = CELL_SIZE // 6

    OFFSET_X = OFFSET_X_1 + 69 / org_backdrop_w * X
    OFFSET_Y = OFFSET_Y_1 + 80 / org_backdrop_h * Y

    wall_gap = 16 * CELL_SIZE / 60


# default
apply_grid_size(10)
# Khởi tạo màn hình
pygame.init()
DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

font = pygame.font.SysFont("Verdana", 60)
