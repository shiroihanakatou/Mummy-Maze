import pygame, sys, random
from pygame.locals import *
from variable import *

class Gamestate:
    def __init__(self):
        # ===== game flow =====
        # mode: "classic" | "adventure"
        self.mode = "classic"
        self.chapter = 1
        self.level = 1


        # ui state (main đang set lại, nhưng để default cho chắc)
        self.state = "Home"

        # ===== map items / mechanics =====
        # positions are tuples (r,c) in grid coordinates
        self.keys = set()
        self.traps = set()

        # gates on horizontal walls_h: key is (rh, c) where rh in [0..ROWS]
        # value True=open, False=closed
        self.gates_h = {}

        # inventory / flags
        self.has_key = False
        # result: None | "win" | "lose" (để main biết show overlay nextlevel)
        self.result = None

        self.gameover = False
        self.storedmove = []
        self.initpos = (0,0,0,0)
        self.solution = []
        self.goal_row = ROWS - 1
        self.goal_col = COLS - 1
        # stairs sprite depends on current board size; fallback to stairs6.png
        try:
            self.sprite_sheet = pygame.image.load(f"game/assets/stairs{ROWS}.png").convert_alpha()
        except Exception:
            self.sprite_sheet = pygame.image.load("game/assets/stairs6.png").convert_alpha()

        self._build_stairs_frames()
        
        
    def start_game(self):
        self.state="PLAYING"
    
    
    def _build_stairs_frames(self):
        sheet_w = self.sprite_sheet.get_width()
        sheet_h = self.sprite_sheet.get_height()
        fw = sheet_w // 4
        fh = sheet_h

        # order: up, right, down, left
        stairs_location = {
            "up":    (0*fw, 0, fw, fh),
            "right": (1*fw, 0, fw, fh),
            "down":  (2*fw, 0, fw, fh),
            "left":  (3*fw, 0, fw, fh),
        }

        self.stairs_frames = {}
        for k, r in stairs_location.items():
            img = self.sprite_sheet.subsurface(r).copy()
            self.stairs_frames[k] = pygame.transform.smoothscale(img, (CELL_SIZE, CELL_SIZE))

        
    def draw_stairs(self, surface):
        x = OFFSET_X + self.goal_col * CELL_SIZE
        y = OFFSET_Y + self.goal_row * CELL_SIZE

        # goal luôn ở rìa: suy ra hướng
        if self.goal_row == 0:
            direction = "up"
        elif self.goal_row == ROWS - 1:
            direction = "down"
        elif self.goal_col == 0:
            direction = "left"
        else:
            direction = "right"

        frame = self.stairs_frames[direction]
        if direction == "up":
            stair_rect = pygame.Rect(x, y - CELL_SIZE+stair_padding, CELL_SIZE, CELL_SIZE)
        elif direction == "down":
            stair_rect = pygame.Rect(x, y + CELL_SIZE-stair_padding, CELL_SIZE, CELL_SIZE)
        elif direction == "left":
            stair_rect = pygame.Rect(x - CELL_SIZE+stair_padding, y, CELL_SIZE, CELL_SIZE)
        else: 
            stair_rect = pygame.Rect(x + CELL_SIZE-stair_padding, y, CELL_SIZE, CELL_SIZE)

        surface.blit(frame, stair_rect)

def reset_items(self):
    self.keys.clear()
    self.traps.clear()
    self.gates_h.clear()
    self.has_key = False

def set_gate_h(self, rh: int, c: int, is_open: bool):
    self.gates_h[(rh, c)] = bool(is_open)

def get_gate_h(self, rh: int, c: int):
    return self.gates_h.get((rh, c), None)

