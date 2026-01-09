import pygame, sys, random
from pygame.locals import *
from variable import *
from module import new_enemy_position, add_sprite_frames, impossible_mode_move


class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.up = 0
        self.down = 0
        self.left = 0
        self.right = 0
        self.sprite_sheet = pygame.image.load("game/assets/images/walls6.png").convert_alpha()

    def _scale(self, frame):
        factor = CELL_SIZE / 60
        if hasattr(pygame.transform, "smoothscale_by"):
            return pygame.transform.smoothscale_by(frame, factor)
        w, h = frame.get_size()
        return pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))

    def draw(self, surface, grid):
        x = OFFSET_X + self.col * CELL_SIZE
        y = OFFSET_Y + self.row * CELL_SIZE

        wall_location = {
            "down": (12, 0, 72, 18),
            "left_end": (0, 0, 12, 78),
            "left": (84, 0, 12, 78),
        }

        if self.left:
            if self.row < ROWS - 1 and grid[self.row + 1][self.col].left == 0:
                frame = self.sprite_sheet.subsurface(wall_location["left_end"])
            else:
                frame = self.sprite_sheet.subsurface(wall_location["left"])
            surface.blit(self._scale(frame), (x, y - wall_gap))

        # IMPORTANT: down==1 is wall. down==2/3 is gate (don't draw wall for gates)
        if self.down == 1:
            frame = self.sprite_sheet.subsurface(wall_location["down"])
            surface.blit(self._scale(frame), (x, y + CELL_SIZE - wall_gap))


class Player:
    def __init__(self):
        self.row = 0
        self.col = 0
        self.direction = "down"
        self.type = "explorer"

        self.sprite_sheet = pygame.image.load(f"game/assets/images/{self.type}6.png").convert_alpha()
        sheet_rect = self.sprite_sheet.get_rect()
        self.frame_w = sheet_rect.width // 5
        self.frame_h = sheet_rect.height // 4

        self.frames = {"up": [], "left": [], "down": [], "right": []}
        add_sprite_frames(self)

        self.anim_idx = 0
        self.anim_timer = 0.0

        self.animation_container = []
        self.anim_sequences = {
            "move": [0, 1, 2, 3, 4],
            "idle": [0, 1, 2, 3, 4, 3, 2, 1],
        }

        self.inactive_timer = 0.0
        self.idle_delay = random.uniform(8, 12)

        # render offset (trượt)
        self.render_dx = 0.0
        self.render_dy = 0.0
        self.is_moving = False

        # tween controller (FIX: nội suy về 0)
        self._move_t = 0.0
        self._move_T = 0.0
        self._move_start_dx = 0.0
        self._move_start_dy = 0.0

    def play_animation(self, name, speed, loop=False, reset=True):
        if reset:
            self.animation_container.clear()

        self.animation_container.append({"name": name, "speed": speed, "loop": loop})
        self.anim_idx = 0
        self.anim_timer = 0.0

        if name == "move" and not loop:
            self.is_moving = True
            self._move_t = 0.0
            self._move_T = speed * len(self.anim_sequences["move"])
            self._move_start_dx = self.render_dx
            self._move_start_dy = self.render_dy

    def move(self, key, grid):
        if self.is_moving:
            return False

        self.inactive_timer = 0.0
        self.idle_delay = random.uniform(8, 12)

        if self.animation_container and self.animation_container[0]["name"] == "idle":
            self.animation_container.clear()
            self.anim_idx = 0
            self.anim_timer = 0.0

        cell = grid[self.row][self.col]
        old_row, old_col = self.row, self.col
        moving = False

        # gate logic:
        # - đi xuống: chặn nếu cell.down in (1 wall, 2 gate đóng)
        # - đi lên: xem down của cell phía trên
        # Space key = skip turn (stay in place)
        if key == K_SPACE:
            return True  # Signal that player took an action (skip turn)

        if (key == K_UP or key == K_w) and self.row > 0 and grid[self.row - 1][self.col].down not in (1, 2):
            self.row -= 1
            self.direction = "up"
            moving = True
        elif (key == K_DOWN or key == K_s) and self.row < ROWS - 1 and cell.down not in (1, 2):
            self.row += 1
            self.direction = "down"
            moving = True
        elif (key == K_LEFT or key == K_a) and (not cell.left) and self.col > 0:
            self.col -= 1
            self.direction = "left"
            moving = True
        elif (key == K_RIGHT or key == K_d) and (not cell.right) and self.col < COLS - 1:
            self.col += 1
            self.direction = "right"
            moving = True

        if moving:
            # base position là ô MỚI, offset kéo ngược về ô CŨ
            dc = old_col - self.col
            dr = old_row - self.row
            self.render_dx = dc * CELL_SIZE
            self.render_dy = dr * CELL_SIZE

            # 5 frame, tổng ~0.5s giống code cũ
            self.play_animation("move", speed=0.5 / 5.0, loop=False, reset=True)

        return moving

    def update(self, dt):
        # idle trigger (disabled)
        # if (not self.is_moving) and (not self.animation_container):
        #     self.inactive_timer += dt
        #     if self.inactive_timer >= self.idle_delay:
        #         self.play_animation("idle", speed=0.14, loop=True, reset=True)

        if not self.animation_container:
            return

        cur = self.animation_container[0]
        seq = self.anim_sequences[cur["name"]]

        # update animation frames
        self.anim_timer += dt
        if self.anim_timer >= cur["speed"]:
            self.anim_timer -= cur["speed"]
            self.anim_idx += 1

            if self.anim_idx >= len(seq):
                if cur["loop"]:
                    self.anim_idx = 0
                else:
                    self.animation_container.pop(0)
                    self.anim_idx = 0
                    self.anim_timer = 0.0

        # FIX: tween offset về 0 theo thời gian, không phụ thuộc direction
        if self.is_moving and self._move_T > 0:
            self._move_t += dt
            a = self._move_t / self._move_T
            if a >= 1.0:
                a = 1.0
            self.render_dx = self._move_start_dx * (1.0 - a)
            self.render_dy = self._move_start_dy * (1.0 - a)

            if a >= 1.0:
                self.render_dx = 0.0
                self.render_dy = 0.0
                self.is_moving = False
                self._move_t = 0.0
                self._move_T = 0.0

    def _scale_frame(self, frame):
        factor = CELL_SIZE / 60
        if hasattr(pygame.transform, "smoothscale_by"):
            return pygame.transform.smoothscale_by(frame, factor)
        w, h = frame.get_size()
        return pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))

    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2 + OFFSET_X + int(self.render_dx)
        y = self.row * CELL_SIZE + CELL_SIZE // 2 + OFFSET_Y + int(self.render_dy)

        if self.animation_container:
            name = self.animation_container[0]["name"]
            seq = self.anim_sequences[name]
            frame_idx = seq[self.anim_idx]
        else:
            frame_idx = 0

        frame = self._scale_frame(self.frames[self.direction][frame_idx])
        rect = frame.get_rect(center=(x, y))
        surface.blit(frame, rect)


class Enemy:
    _UID = 0

    def __init__(self):
        Enemy._UID += 1
        self.uid = Enemy._UID
        self.on_step = None

        self.row = random.randint(0, ROWS - 1)
        self.col = random.randint(0, COLS - 1)
        self.direction = "down"
        self.type = random.choice(["red_mummy", "white_mummy", "red_scorpion"])

        self.sprite_sheet = pygame.image.load(f"game/assets/images/{self.type}6.png").convert_alpha()
        sheet_rect = self.sprite_sheet.get_rect()
        self.frame_w = sheet_rect.width // 5
        self.frame_h = sheet_rect.height // 4

        self.frames = {"up": [], "right": [], "down": [], "left": []}
        add_sprite_frames(self)

        self.anim_idx = 0
        self.anim_timer = 0.0

        self.animation_container = []
        self.anim_sequences = {"move": [0, 1, 2, 3, 4]}

        self.render_dx = 0.0
        self.render_dy = 0.0
        self.is_moving = False

        self.pending_steps = []
        self.base_move_frame_time = 0.12

        # tween controller
        self._move_t = 0.0
        self._move_T = 0.0
        self._move_start_dx = 0.0
        self._move_start_dy = 0.0

    def set_type(self, new_type: str):
        if self.type == new_type:
            return
        self.type = new_type
        add_sprite_frames(self)
        self.anim_idx = 0
        self.anim_timer = 0.0

    def play_animation(self, name, speed, loop=False, reset=True):
        if reset:
            self.animation_container.clear()

        self.animation_container.append({"name": name, "speed": speed, "loop": loop})
        self.anim_idx = 0
        self.anim_timer = 0.0

        if name == "move" and not loop:
            self.is_moving = True
            self._move_t = 0.0
            self._move_T = speed * len(self.anim_sequences["move"])
            self._move_start_dx = self.render_dx
            self._move_start_dy = self.render_dy

    def _start_next_step(self):
        if not self.pending_steps:
            self.is_moving = False
            return

        step = self.pending_steps.pop(0)
        dr, dc, ndir = step["dr"], step["dc"], step["dir"]

        self.row += dr
        self.col += dc
        self.direction = ndir

        if callable(self.on_step):
            self.on_step(self)

        # base position là ô MỚI, offset kéo ngược về ô CŨ
        self.render_dx = (-dc) * CELL_SIZE
        self.render_dy = (-dr) * CELL_SIZE

        self.play_animation("move", speed=self.base_move_frame_time, loop=False, reset=True)

    def move(self, player, grid, gamestate=None):
        if self.is_moving or self.pending_steps:
            return 0

        steps = 2 if self.type != "red_scorpion" else 1

        temp_r, temp_c = self.row, self.col
        planned = []

        # Check if impossible mode is enabled
        use_impossible = gamestate and getattr(gamestate, "impossible_mode", False)

        for _ in range(steps):
            if use_impossible:
                nr, nc = impossible_mode_move(temp_r, temp_c, player.row, player.col, grid, self.type)
            else:
                nr, nc = new_enemy_position(temp_r, temp_c, player.row, player.col, grid, self.type)
            if nr == temp_r and nc == temp_c:
                break

            dr = nr - temp_r
            dc = nc - temp_c

            if dr < 0:
                ndir = "up"
            elif dr > 0:
                ndir = "down"
            elif dc < 0:
                ndir = "left"
            else:
                ndir = "right"

            planned.append({"dr": dr, "dc": dc, "dir": ndir})
            temp_r, temp_c = nr, nc

        # Face player even if not moving
        if not planned:
            dr = player.row - self.row
            dc = player.col - self.col
            if abs(dr) > abs(dc):
                self.direction = "down" if dr > 0 else "up"
            elif dc != 0:
                self.direction = "right" if dc > 0 else "left"
            return 0

        self.pending_steps = planned
        self._start_next_step()
        return len(self.pending_steps)

    def update(self, dt):
        if not self.animation_container:
            return

        cur = self.animation_container[0]
        seq = self.anim_sequences[cur["name"]]

        # update frames
        self.anim_timer += dt
        if self.anim_timer >= cur["speed"]:
            self.anim_timer -= cur["speed"]
            self.anim_idx += 1

            if self.anim_idx >= len(seq):
                if cur["loop"]:
                    self.anim_idx = 0
                else:
                    self.animation_container.pop(0)
                    self.anim_idx = 0
                    self.anim_timer = 0.0

        # tween về 0
        if self.is_moving and self._move_T > 0:
            self._move_t += dt
            a = self._move_t / self._move_T
            if a >= 1.0:
                a = 1.0
            self.render_dx = self._move_start_dx * (1.0 - a)
            self.render_dy = self._move_start_dy * (1.0 - a)

            if a >= 1.0:
                self.render_dx = 0.0
                self.render_dy = 0.0
                self.is_moving = False
                self._move_t = 0.0
                self._move_T = 0.0

                # chain bước tiếp theo sau khi kết thúc 1 ô
                if self.pending_steps:
                    self._start_next_step()

    def _scale_frame(self, frame):
        factor = CELL_SIZE / 60
        if hasattr(pygame.transform, "smoothscale_by"):
            return pygame.transform.smoothscale_by(frame, factor)
        w, h = frame.get_size()
        return pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))

    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2 + OFFSET_X + int(self.render_dx)
        y = self.row * CELL_SIZE + CELL_SIZE // 2 + OFFSET_Y + int(self.render_dy)

        if self.animation_container:
            seq = self.anim_sequences[self.animation_container[0]["name"]]
            frame_idx = seq[self.anim_idx]
        else:
            frame_idx = 0

        frame = self._scale_frame(self.frames[self.direction][frame_idx])
        rect = frame.get_rect(center=(x, y))
        surface.blit(frame, rect)
