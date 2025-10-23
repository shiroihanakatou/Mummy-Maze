import pygame, sys, random
from pygame.locals import *
from variable import *
from module import new_enemy_position

class Cell:
    def __init__(self, row, col):
        # Một ô sẽ có các thuộc tính: vị trí và các bước tường
        self.row = row
        self.col = col
        self.up = 0
        self.down = 0
        self.left = 0
        self.right = 0

    def draw(self, surface):
        x = self.col * CELL_SIZE
        y = self.row * CELL_SIZE
        
        # Vẽ các trước ô rect màu xám,nếu có tường thì line trắng
        pygame.draw.rect(surface, GRAY, (x, y, CELL_SIZE, CELL_SIZE), 1)

        if self.up:
            pygame.draw.line(surface, WHITE, (x, y), (x + CELL_SIZE, y), 3)
        if self.down:
            pygame.draw.line(surface, WHITE, (x, y + CELL_SIZE),(x + CELL_SIZE, y + CELL_SIZE), 3)
        if self.left:
            pygame.draw.line(surface, WHITE, (x, y), (x, y + CELL_SIZE), 3)
        if self.right:
            pygame.draw.line(surface, WHITE, (x + CELL_SIZE, y),(x + CELL_SIZE, y + CELL_SIZE), 3)

class Player:
    def __init__(self):
        self.row = 0
        self.col = 0
        self.color = BLUE

    def move(self, key, grid):
        cell = grid[self.row][self.col]

        #Di chuyển người chơi (có check tường)
        if key == K_UP and not cell.up and self.row > 0:
            self.row -= 1
        elif key == K_DOWN and not cell.down and self.row < ROWS - 1:
            self.row += 1
        elif key == K_LEFT and not cell.left and self.col > 0:
            self.col -= 1
        elif key == K_RIGHT and not cell.right and self.col < COLS - 1:
            self.col += 1

    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2
        y = self.row * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, self.color, (x, y), CELL_SIZE // 3)


class Enemy:
    def __init__(self):
        self.row = random.randint(0, ROWS - 1)
        self.col = random.randint(0, COLS - 1)
        self.color = RED

    def move(self, player, grid):
        #Quái sẽ move theo hàm new_enemy_position
        self.row,self.col = new_enemy_position(self.row,self.col,player.row,player.col,grid)

    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2
        y = self.row * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, self.color, (x, y), CELL_SIZE // 3)