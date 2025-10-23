import pygame, sys, random
from pygame.locals import *
from variable import *

class Gamestate:
    def __init__(self):
        self.gameover = False
        self.storedmove = []
        self.initpos = (0,0,0,0)
        self.solution = []