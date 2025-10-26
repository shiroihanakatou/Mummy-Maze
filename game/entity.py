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
        self.sprite_sheet = pygame.image.load("assets/walls6.png").convert_alpha()

    def draw(self, surface,grid):
        x = self.col * CELL_SIZE
        y = self.row * CELL_SIZE
        wall_location = {
            "down" : (12, 0, 72, 18),
            "left_end" : (0, 0, 12, 78),
            "left" : (84, 0, 12, 78)
        }
        # Vẽ các trước ô rect màu xám,nếu có tường thì line trắng
        if self.left:
            if self.row<ROWS-1 and grid[self.row+1][self.col].left==0:
                frame = self.sprite_sheet.subsurface(wall_location['left_end'])
            else:
                frame = self.sprite_sheet.subsurface(wall_location['left'])
            surface.blit(frame, (x, y-18))
        if self.down:
            frame = self.sprite_sheet.subsurface(wall_location['down'])
            surface.blit(frame, (x, y + CELL_SIZE - 18))

class Player:
    def __init__(self):
        self.row = 0
        self.col = 0
        self.direction = "down"  # hướng mặc định
        self.color = BLUE

        # Load sprite sheet
        self.sprite_sheet = pygame.image.load("assets/explorer6.png").convert_alpha()
        sheet_rect = self.sprite_sheet.get_rect()

        self.frame_w = sheet_rect.width // 5
        self.frame_h = sheet_rect.height // 4

        self.frames={
            "up"    : [],
            "left"  : [],
            "down"  : [],
            "right" : []
        }
        for row in range(4):
            tmp = []
            for col in range(5):
                rect = pygame.Rect(col * self.frame_w,row * self.frame_h,self.frame_w,self.frame_h)
                frame = self.sprite_sheet.subsurface(rect)
                tmp.append(frame)

            # Gán từng hàng cho hướng tương ứng
            if row == 0:
                self.frames["up"] = tmp
            elif row == 1:
                self.frames["right"] = tmp
            elif row == 2:
                self.frames["down"] = tmp
            elif row == 3:
                self.frames["left"] = tmp


    def move(self, key, grid):
        cell = grid[self.row][self.col]

        if key == K_UP and not cell.up and self.row > 0:
            self.row -= 1
            self.direction = "up"
        elif key == K_DOWN and not cell.down and self.row < ROWS - 1:
            self.row += 1
            self.direction = "down"
        elif key == K_LEFT and not cell.left and self.col > 0:
            self.col -= 1
            self.direction = "left"
        elif key == K_RIGHT and not cell.right and self.col < COLS - 1:
            self.col += 1
            self.direction = "right"


    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2
        y = self.row * CELL_SIZE + CELL_SIZE // 2
        rect = self.frames[self.direction][0].get_rect(center=(x, y))
        surface.blit(self.frames[self.direction][0], rect)

class Enemy:
    def __init__(self):
        self.row = random.randint(0, ROWS - 1)
        self.col = random.randint(0, COLS - 1)
        self.direction = "down"  
        self.color = RED

        # Load sprite sheet (ví dụ: white_mummy.png)
        self.sprite_sheet = pygame.image.load("assets/white_mummy6.png").convert_alpha()
        sheet_rect = self.sprite_sheet.get_rect()

        # Sprite sheet: 4 hàng, 5 cột
        self.frame_w = sheet_rect.width // 5
        self.frame_h = sheet_rect.height // 4

        # Lưu các frame cho từng hướng
        self.frames = {
            "up": [],
            "right": [],
            "down": [],
            "left": []
        }

        for row in range(4):
            tmp = []
            for col in range(5):
                rect = pygame.Rect(col * self.frame_w, row * self.frame_h, self.frame_w, self.frame_h)
                frame = self.sprite_sheet.subsurface(rect)
                tmp.append(frame)

            if row == 0:
                self.frames["up"] = tmp
            elif row == 1:
                self.frames["right"] = tmp
            elif row == 2:
                self.frames["down"] = tmp
            elif row == 3:
                self.frames["left"] = tmp

    def move(self, player, grid):
        # Lưu vị trí cũ
        old_row, old_col = self.row, self.col

        # Di chuyển theo new_enemy_position
        self.row, self.col = new_enemy_position(self.row, self.col, player.row, player.col, grid)

        # Cập nhật hướng dựa vào thay đổi vị trí
        dr = self.row - old_row
        dc = self.col - old_col

        if dr < 0:
            self.direction = "up"
        elif dr > 0:
            self.direction = "down"
        elif dc < 0:
            self.direction = "left"
        elif dc > 0:
            self.direction = "right"

    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2
        y = self.row * CELL_SIZE + CELL_SIZE // 2
        rect = self.frames[self.direction][0].get_rect(center=(x, y))
        surface.blit(self.frames[self.direction][0], rect)
