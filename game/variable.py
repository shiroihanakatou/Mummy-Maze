import pygame

pygame.init()
FPS = 60
FramePerSec = pygame.time.Clock()


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

ROWS = 10
COLS = 10

CELL_SIZE = 60
BUTTON_SIZE = 60

SCREEN_WIDTH = COLS * CELL_SIZE 
SCREEN_HEIGHT = ROWS * CELL_SIZE + BUTTON_SIZE 

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

font = pygame.font.SysFont("Verdana", 60)