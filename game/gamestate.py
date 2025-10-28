import pygame, sys, random
from pygame.locals import *
from variable import *

class Gamestate:
    def __init__(self):
        self.gameover = False
        self.storedmove = [] #lưu vị trí, hướng của player và enemy
        self.initpos = (0,0,0,0)
        self.solution = []
        self.goal_row = ROWS - 1
        self.goal_col = COLS - 1