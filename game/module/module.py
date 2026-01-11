import pygame, sys, random, math
import json
from collections import deque
from pygame.locals import *
from variable import *
from module.gamestate import Gamestate, load_frames_with_mask

def play_footstep_sound(gamestate, enemy_type: str, grid_size: int):
    """Play footstep sound based on enemy type and grid size."""
    if not gamestate or not gamestate.sfx:
        return
    
    # Choose footstep based on enemy type and grid size
    if grid_size <= 6:
        key = f"{enemy_type}_small"
    elif grid_size <= 8:
        key = f"{enemy_type}_medium"
    else:
        key = f"{enemy_type}_large"
    
    sound = gamestate.sfx.get(key)
    if sound is not None:
        try:
            sound.play()
        except: pass

def wait(seconds):
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < seconds * 1000:
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()
        FramePerSec.tick(FPS)

def make_snapshot(player, enemies, gamestate=None, killed_this_turn=None, killed_uids=None):
    """Snapshot cho undo/restart: (p_row, p_col, p_dir, enemies_state_tuple, keys, gates_h, killed_this_turn).
    
    killed_this_turn: list of (row, col, direction, type) for enemies killed THIS turn
    killed_uids: set of UIDs of killed enemies to exclude from enemies_state
    """
    # Only capture ALIVE enemies (not in killed_uids)
    if killed_uids:
        enemies_state = tuple(
            (e.row, e.col, getattr(e, "direction", "down"), getattr(e, "type", None))
            for e in enemies if e.uid not in killed_uids
        )
    else:
        enemies_state = tuple(
            (e.row, e.col, getattr(e, "direction", "down"), getattr(e, "type", None))
            for e in enemies
        )
    
    # Phase 3: Include keys and gate states in snapshot
    keys_state = set(gamestate.keys) if gamestate else set()
    gates_state = dict(gamestate.gates_h) if gamestate else {}
    
    # Store killed enemies this turn so undo can restore them
    killed_state = tuple(killed_this_turn) if killed_this_turn else ()
    
    return (
        player.row, 
        player.col, 
        getattr(player, "direction", "down"), 
        enemies_state,
        keys_state,
        gates_state,
        killed_state
    )

def apply_snapshot(snapshot, player, enemies, grid=None, gamestate=None):
    """Apply snapshot và rebuild enemies list nếu cần."""
    # Support old format (4 items), 6-item format, and new 7-item format with killed_this_turn
    if len(snapshot) == 4:
        p_row, p_col, p_dir, enemies_state = snapshot
        keys_state = None
        gates_state = None
    elif len(snapshot) == 6:
        p_row, p_col, p_dir, enemies_state, keys_state, gates_state = snapshot
    else:
        # 7-item format - killed_state is stored but not auto-applied here
        # (undo_move handles combining killed enemies manually)
        p_row, p_col, p_dir, enemies_state, keys_state, gates_state, _ = snapshot
    
    player.row, player.col, player.direction = p_row, p_col, p_dir
    # Reset player animation states
    if hasattr(player, "render_dx"):
        player.render_dx = 0.0
    if hasattr(player, "render_dy"):
        player.render_dy = 0.0
    if hasattr(player, "is_moving"):
        player.is_moving = False

    if enemies_state is None:
        enemies.clear()
        return

    target_n = len(enemies_state)

    from entity.entity import Enemy as EnemyClass

    if target_n == 0:
        enemies.clear()
        return

    while len(enemies) < target_n:
        enemies.append(EnemyClass())
    if len(enemies) > target_n:
        del enemies[target_n:]

    for e, st in zip(enemies, enemies_state):
        r, c, d, t = st
        e.row, e.col, e.direction = r, c, d
        if t is not None:
            if hasattr(e, "set_type"):
                e.set_type(t)
            else:
                e.type = t
        # Reset enemy animation states to prevent auto-movement
        if hasattr(e, "render_dx"):
            e.render_dx = 0.0
        if hasattr(e, "render_dy"):
            e.render_dy = 0.0
        if hasattr(e, "is_moving"):
            e.is_moving = False
        if hasattr(e, "pending_steps"):
            e.pending_steps.clear()
    
    # Phase 3: Restore keys and gate states
    if keys_state is not None and gamestate is not None:
        gamestate.keys = set(keys_state)
    
    if gates_state is not None and gamestate is not None and grid is not None:
        gamestate.gates_h = dict(gates_state)
        # Reset gate animation states to match restored gate states
        gamestate.gate_anim_state.clear()
        for gate_pos, is_open in gamestate.gates_h.items():
            gamestate.gate_anim_state[gate_pos] = {
                "frame": 7 if is_open else 0,
                "time": 0.0,
                "is_closing": not is_open
            }
        # Sync Cell.down with gate states (2=closed, 3=open)
        for gate_pos, is_open in gamestate.gates_h.items():
            rh, c = gate_pos
            if 0 <= rh - 1 < ROWS and 0 <= c < COLS:
                grid[rh - 1][c].down = 3 if is_open else 2

###scale màn
class ScreenManager:
    def __init__(self, virtual_w, virtual_h):
        self.virtual_w = virtual_w
        self.virtual_h = virtual_h
        self.virtual_surface = pygame.Surface((self.virtual_w, self.virtual_h))
        self.real_screen = pygame.display.set_mode((self.virtual_w, self.virtual_h), pygame.RESIZABLE)

    def get_mouse_pos(self):
        real_w, real_h = self.real_screen.get_size()
        raw_x, raw_y = pygame.mouse.get_pos()
        ratio_w = real_w / self.virtual_w
        ratio_h = real_h / self.virtual_h
        return (raw_x / ratio_w, raw_y / ratio_h)

    def toggle_fullscreen(self):
        if self.real_screen.get_flags() & pygame.FULLSCREEN:
            pygame.display.set_mode((self.virtual_w, self.virtual_h), pygame.RESIZABLE)
        else:
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    def render(self):
        real_w, real_h = self.real_screen.get_size()
        scaled_surface = pygame.transform.smoothscale(self.virtual_surface, (real_w, real_h))
        self.real_screen.blit(scaled_surface, (0, 0))
        pygame.display.update()

def add_sprite_frames(entity):
    entity.sprite_sheet = pygame.image.load(f"assets/images/{entity.type}6.png").convert_alpha()
    sheet_rect = entity.sprite_sheet.get_rect()

    entity.frame_w = sheet_rect.width // 5
    entity.frame_h = sheet_rect.height // 4

    entity.frames = {"up": [], "right": [], "down": [], "left": []}

    for row in range(4):
        tmp = []
        for col in range(5):
            rect = pygame.Rect(col * entity.frame_w, row * entity.frame_h, entity.frame_w, entity.frame_h)
            # Copy subsurface to preserve alpha
            tmp.append(entity.sprite_sheet.subsurface(rect).copy())
        if row == 0:
            entity.frames["up"] = tmp
        elif row == 1:
            entity.frames["right"] = tmp
        elif row == 2:
            entity.frames["down"] = tmp
        elif row == 3:
            entity.frames["left"] = tmp
def get_actor_center(actor):
    dx = int(getattr(actor, "render_dx", 0))
    dy = int(getattr(actor, "render_dy", 0))
    x = OFFSET_X + actor.col * CELL_SIZE + CELL_SIZE // 2 + dx
    y = OFFSET_Y + actor.row * CELL_SIZE + CELL_SIZE // 2 + dy
    return x, y

def new_enemy_position(e_row, e_col, p_row, p_col, grid, type):
    new_row, new_col = e_row, e_col
    directions = [('up', -1, 0), ('down', 1, 0), ('left', 0, -1), ('right', 0, 1)]
    if type == "white_mummy":
        directions = [('left', 0, -1), ('right', 0, 1), ('up', -1, 0), ('down', 1, 0)]

    best_dist = abs(e_row - p_row) + abs(e_col - p_col)
    cell = grid[e_row][e_col]

    def _can_move(dir_name):
        if dir_name == "up":
            if e_row <= 0:
                return False
            edge = grid[e_row - 1][e_col].down
            return edge not in (1, 2)
        if dir_name == "down":
            if e_row >= ROWS - 1:
                return False
            edge = cell.down
            return edge not in (1, 2)
        if dir_name == "left":
            return (e_col > 0) and (cell.left == 0)
        if dir_name == "right":
            return (e_col < COLS - 1) and (cell.right == 0)
        return False

    for dname, dr, dc in directions:
        if _can_move(dname):
            cand_r = e_row + dr
            cand_c = e_col + dc
            dist = abs(cand_r - p_row) + abs(cand_c - p_col)
            if dist < best_dist:
                best_dist = dist
                new_row, new_col = cand_r, cand_c

    return new_row, new_col


def impossible_mode_move(e_row, e_col, p_row, p_col, grid, enemy_type):
    """
    Impossible mode AI: Uses BFS to find actual shortest path to player,
    accounting for walls. Returns the next cell (nr, nc) to move toward player.
    """
    from collections import deque
    
    # If already at player position, don't move
    if e_row == p_row and e_col == p_col:
        return e_row, e_col
    
    rows = len(grid)
    cols = len(grid[0]) if rows > 0 else 0
    
    def _can_move_from(r, c, direction):
        """Check if can move from (r, c) in given direction."""
        if direction == "up":
            if r <= 0:
                return False
            # Check wall below the cell above (which blocks us from going up)
            edge = grid[r - 1][c].down
            return edge not in (1, 2)
        elif direction == "down":
            if r >= rows - 1:
                return False
            edge = grid[r][c].down
            return edge not in (1, 2)
        elif direction == "left":
            if c <= 0:
                return False
            return grid[r][c].left == 0
        elif direction == "right":
            if c >= cols - 1:
                return False
            return grid[r][c].right == 0
        return False
    
    # BFS from enemy to player (forward search)
    # We find the shortest path enemy can walk to reach player
    queue = deque()
    queue.append((e_row, e_col))
    visited = {(e_row, e_col): None}  # Maps position to (parent_position, direction_taken)
    
    directions = [("up", -1, 0), ("down", 1, 0), ("left", 0, -1), ("right", 0, 1)]
    if enemy_type == "white_mummy":
        directions = [("left", 0, -1), ("right", 0, 1), ("up", -1, 0), ("down", 1, 0)]
    found = False
    while queue and not found:
        cr, cc = queue.popleft()
        
        for dname, dr, dc in directions:
            nr, nc = cr + dr, cc + dc
            if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited:
                # Check if enemy can move FROM (cr, cc) TO (nr, nc)
                if _can_move_from(cr, cc, dname):
                    visited[(nr, nc)] = (cr, cc, dname)
                    if nr == p_row and nc == p_col:
                        found = True
                        break
                    queue.append((nr, nc))
    
    # If player position not reachable, fall back to Manhattan-based move
    if (p_row, p_col) not in visited:
        return new_enemy_position(e_row, e_col, p_row, p_col, grid, enemy_type)
    
    # Backtrack from player to find the first step enemy should take
    current = (p_row, p_col)
    first_step = None
    
    while visited[current] is not None:
        parent_r, parent_c, direction = visited[current]
        if parent_r == e_row and parent_c == e_col:
            # current is where enemy should move first
            first_step = current
            break
        current = (parent_r, parent_c)
    
    if first_step:
        return first_step
    return e_row, e_col


def winning_check(surface, font, player, gamestate):
    if gamestate.gameover:
        return

    if player.row == gamestate.goal_row and player.col == gamestate.goal_col:
        gamestate.gameover = True
        gamestate.result = "win"
        
        # Play level complete sound
        if gamestate.sfx.get("finishedlevel") is not None:
            try:
                gamestate.sfx["finishedlevel"].play()
            except Exception as e:
                debug_log(f"[Sound] finishedlevel play failed: {e}")
        
        text = font.render("You Win", True, GREEN)
        surface.blit(
            text,
            (
                SCREEN_WIDTH // 2 - text.get_width() // 2,
                SCREEN_HEIGHT // 2 - text.get_height() // 2,
            ),
        )

def losing_check(surface, font, player, enemies, gamestate):
    global menu_y
    if gamestate.gameover:
        return

    for e in enemies:
        if player.row == e.row and player.col == e.col:
            gamestate.gameover = True
            gamestate.result = "lose"

            cause = "white"
            etype = getattr(e, "type", "")
            if "scorpion" in etype:
                cause = "stung"
            elif etype.startswith("red"):
                cause = "red"

            # Ensure undo snapshot exists before starting death
            if getattr(gamestate, "pending_snapshot", False):
                gamestate.storedmove.append(make_snapshot(player, enemies, gamestate))
                gamestate.pending_snapshot = False
            gamestate.state = "DEATH_ANIM"
            start_stage = "fight" if cause == "stung" else "dust"
            # Sync animation duration with sound:
            # pummel.mp3 = 0.50s for red/white fights; poison + 20 frames for stung = 1.7s
            if cause == "stung":
                fight_dur = 1.7  # 20 frames at 12 fps = 1.67s
                # Play poison sound immediately
                if gamestate.sfx.get("poison") is not None:
                    try:
                        gamestate.sfx["poison"].play()
                    except Exception as e:
                        debug_log(f"[Sound] poison play failed: {e}")
            elif cause == "red":
                fight_dur = 0.5  # Match pummel.mp3 (0.50s)
                # Play pummel sound immediately
                if gamestate.sfx.get("pummel") is not None:
                    try:
                        gamestate.sfx["pummel"].play()
                    except Exception as e:
                        debug_log(f"[Sound] pummel play failed: {e}")
            else:  # white
                fight_dur = 0.5  # Match pummel.mp3
                if gamestate.sfx.get("pummel") is not None:
                    try:
                        gamestate.sfx["pummel"].play()
                    except Exception as e:
                        debug_log(f"[Sound] pummel play failed: {e}")
            
            gamestate.death_state = {
                "cause": cause,
                "row": player.row,
                "col": player.col,
                "stage": start_stage,  # dust -> fight -> done (stung skips dust)
                "timer": 0.0,
                "dust_idx": 0,
                "dust_timer": 0.0,
                "dust_fps": 20,
                "fight_timer": 0.0,
                "fight_dur": fight_dur,
                "fight_idx": 0,
                "fight_anim_timer": 0.0,
                "fight_fps": 12,
            }
            break

# Progress / maps / options UI helpers (from PV branch, adapted for enemies list)
class ProgressManager:
    def __init__(self, ASSETS_DIR):
        self.current_chapter = 1
        self.current_level = 1
        self.total_levels_per_chap = 15

        self.img_tower_bg = pygame.image.load(str(ASSETS_DIR / "images/map.png")).convert_alpha()
        self.img_tower_bg = pygame.transform.smoothscale(self.img_tower_bg, (270, 180))
        marker_size = (28, 20)
        
        # Load mapx (cross) with mask for transparency
        try:
            mapx_frames = load_frames_with_mask(
                str(ASSETS_DIR / "images/mapx.gif"),
                str(ASSETS_DIR / "images/_mapx.gif"),
                1
            )
            self.img_mapx = pygame.transform.smoothscale(mapx_frames[0], marker_size)
        except Exception as e:
            debug_log(f"[ProgressManager] mapx mask load failed: {e}")
            self.img_mapx = pygame.image.load(str(ASSETS_DIR / "images/mapx.gif")).convert_alpha()
            self.img_mapx = pygame.transform.smoothscale(self.img_mapx, marker_size)
        
        # Load maphead (explorer head) with mask for transparency
        try:
            maphead_frames = load_frames_with_mask(
                str(ASSETS_DIR / "images/maphead.gif"),
                str(ASSETS_DIR / "images/_maphead.gif"),
                1
            )
            self.img_head = pygame.transform.smoothscale(maphead_frames[0], marker_size)
        except Exception as e:
            debug_log(f"[ProgressManager] maphead mask load failed: {e}")
            self.img_head = pygame.image.load(str(ASSETS_DIR / "images/maphead.gif")).convert_alpha()
            self.img_head = pygame.transform.smoothscale(self.img_head, marker_size)
        
        self.level_positions = [
            (50, 145), (85, 145), (120, 145), (155, 145), (190, 145),
            (173, 120), (138, 120), (103, 120), (68, 120),
            (86, 95), (121, 95), (156, 95),
            (139, 70), (104, 70),
            (122, 45),
        ]

    def get_level_filename(self):
        return f"level{self.current_chapter}-{self.current_level}.json"

    def update_progress(self):
        self.current_level += 1
        if self.current_level > self.total_levels_per_chap:
            self.current_level = 1
            self.current_chapter += 1
            if self.current_chapter > 3:
                return "FINISH_GAME"
            return "NEW_CHAPTER"
        return "NEXT_LEVEL"

    def draw_sidebar_map(self, surface, x_pos, y_pos):
        surface.blit(self.img_tower_bg, (x_pos, y_pos))
        for i in range(self.total_levels_per_chap):
            level_idx = i + 1
            rel_x, rel_y = self.level_positions[i]
            draw_x = x_pos + rel_x
            draw_y = y_pos + rel_y
            if level_idx < self.current_level:
                surface.blit(self.img_mapx, (draw_x, draw_y))
            elif level_idx == self.current_level:
                surface.blit(self.img_head, (draw_x, draw_y))


def load_current_level(progress_mgr, grid, player, enemies, gamestate):
    filename = progress_mgr.get_level_filename()
    filepath = f"assets/map/{filename}"
    try:
        rows, cols, tiles, walls_v, walls_h, exit_pos = read_map_json(filepath)
    except Exception:
        return False
    apply_map_to_grid(rows, cols, tiles, walls_v, walls_h, grid, player, enemies, gamestate, exit_pos)
    return True


class AdventureWorldMap:
    def __init__(self, ASSETS_DIR, SCREEN_WIDTH, SCREEN_HEIGHT):
        self.bg = pygame.image.load(str(ASSETS_DIR / "images/adventuremap.jpg")).convert_alpha()
        self.bg = pygame.transform.smoothscale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
        self.level_font = pygame.font.Font(str(ASSETS_DIR / "font" / "romeo.ttf"), 22)
        self.pyramid_strip = pygame.image.load(str(ASSETS_DIR / "images/pyramidlit.gif")).convert_alpha()
        self.frame_count = 16
        self.frame_w = self.pyramid_strip.get_width() // self.frame_count
        self.frame_h = self.pyramid_strip.get_height()

        x1 = SCREEN_WIDTH - 412
        y1 = SCREEN_HEIGHT - 145
        self.level_coords = [
            (0, 0),
            (x1, y1), (x1 - 174, y1 - 34), (x1 - 380, y1 + 24), (x1 - 500, y1 - 20),
            (x1 - 300, y1 - 243), (x1 - 45, y1 - 132), (x1 + 10, y1 - 255),
            (x1 + 105, y1 - 100), (x1 + 175, y1 - 195), (x1 + 110, y1 - 320),
            (x1 - 35, y1 - 405), (x1 + 120, y1 - 455), (x1 + 385, y1 - 425),
            (x1 - 75, y1 - 475), (x1 - 175, y1 - 365),
        ]

    def draw_mini_pyramid(self, surface, center_pos, completed_count):
        index = max(0, min(completed_count, 15))
        area = pygame.Rect(index * self.frame_w, 0, self.frame_w, self.frame_h)
        pyramid_img = self.pyramid_strip.subsurface(area)
        pyramid_img = pygame.transform.smoothscale(
            pyramid_img, (int(self.frame_w * 1.8), int(self.frame_h * 1.8))
        )
        rect = pyramid_img.get_rect(center=center_pos)
        surface.blit(pyramid_img, rect)

    def draw(self, surface, progress_mgr, mouse_pos):
        surface.blit(self.bg, (0, 0))
        for i in range(1, 16):
            pos = self.level_coords[i]
            if i <= progress_mgr.current_chapter:
                dots = 15 if i < progress_mgr.current_chapter else (progress_mgr.current_level - 1)
                self.draw_mini_pyramid(surface, pos, dots)
                color = (255, 255, 0) if i == progress_mgr.current_chapter else (255, 255, 255)
                text = self.level_font.render(str(i), True, color)
                text_rect = text.get_rect(center=(pos[0], pos[1] - 50))
                surface.blit(text, text_rect)

    def get_clicked_chapter(self, mouse_pos, progress_mgr):
        for i in range(1, 16):
            pos = self.level_coords[i]
            dist = math.hypot(mouse_pos[0] - pos[0], mouse_pos[1] - pos[1])
            if dist < 40 and i <= progress_mgr.current_chapter:
                return i
        return None


class OptionsSlider:
    def __init__(self, label, x, y, width, initial_val):
        self.label = label
        self.rect = pygame.Rect(x, y, width, 10)
        self.val = initial_val
        self.is_dragging = False
        self.handle_rect = pygame.Rect(x + (width * initial_val) - 13, y - 10, 26, 32)

    def draw(self, surface, font, handle_img):
        txt = font.render(self.label, True, (0, 0, 0))
        surface.blit(txt, (self.rect.x - 120, self.rect.y - 10))
        pygame.draw.rect(surface, (50, 30, 10), self.rect)
        surface.blit(handle_img, self.handle_rect)

    def handle_event(self, e, mouse_pos):
        if e.type == pygame.MOUSEBUTTONDOWN and self.handle_rect.collidepoint(mouse_pos):
            self.is_dragging = True
        elif e.type == pygame.MOUSEBUTTONUP:
            self.is_dragging = False

        if self.is_dragging and e.type == pygame.MOUSEMOTION:
            new_x = max(self.rect.x, min(mouse_pos[0], self.rect.x + self.rect.w))
            self.handle_rect.centerx = new_x
            self.val = (new_x - self.rect.x) / self.rect.w

def read_map_json(filepath: str):
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = int(data["size"]["rows"])
    cols = int(data["size"]["cols"])
    tiles = data.get("tiles", [])
    walls_v = data.get("walls_v", [])
    walls_h = data.get("walls_h", [])
    exit_pos = None

    # Handle both old format (rows/cols) and new format (row/col)
    if "exit" in data and data["exit"] is not None:
        exit_info = data["exit"]
        if "row" in exit_info:
            exit_pos = (int(exit_info["row"]), int(exit_info["col"]))
        elif "rows" in exit_info:
            exit_pos = (int(exit_info["rows"]), int(exit_info["cols"]))

    return rows, cols, tiles, walls_v, walls_h, exit_pos

def apply_map_to_grid(rows, cols, tiles, walls_v, walls_h, grid, player, enemies, gamestate, exit_pos=None):
    """Gate:
      '-' wall
      '=' gate closed (cell.down = 2)
      '~' gate open   (cell.down = 3)
      '.' open
    Gate chỉ nằm ở cell.down (của ô phía trên).
    """

    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            cell.up = cell.down = cell.left = cell.right = 0

    if not hasattr(gamestate, "keys"):
        gamestate.keys = set()
    if not hasattr(gamestate, "traps"):
        gamestate.traps = set()
    if not hasattr(gamestate, "gates_h"):
        gamestate.gates_h = {}

    gamestate.keys.clear()
    gamestate.traps.clear()
    gamestate.gates_h.clear()
    gamestate.has_key = False

    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            cell.left = 1 if walls_v[r][c] == "|" else 0
            cell.right = 1 if walls_v[r][c + 1] == "|" else 0

            up_ch = walls_h[r][c]
            cell.up = 1 if up_ch == "-" else 0

            down_ch = walls_h[r + 1][c]
            if down_ch == "-":
                cell.down = 1
            elif down_ch == "=":
                cell.down = 2
                gamestate.gates_h[(r + 1, c)] = False
            elif down_ch == "~":
                cell.down = 3
                gamestate.gates_h[(r + 1, c)] = True
            else:
                cell.down = 0

    found_p = False
    legacy_goal = None
    enemies.clear()

    from entity.entity import Enemy as EnemyClass

    for r in range(rows):
        line = tiles[r]
        for c in range(cols):
            ch = line[c]

            if ch == "P":
                player.row, player.col = r, c
                found_p = True

            elif ch in ("W", "R", "S"):
                e = EnemyClass()
                if ch == "W":
                    e.set_type("white_mummy")
                elif ch == "R":
                    e.set_type("red_mummy")
                else:
                    e.set_type("red_scorpion")
                e.row, e.col = r, c
                enemies.append(e)

            elif ch == "K":
                gamestate.keys.add((r, c))
            elif ch == "T":
                gamestate.traps.add((r, c))
            elif ch == "E":
                legacy_goal = (r, c)

    if not found_p:
        player.row, player.col = 0, 0

    if len(enemies) == 0:
        e = EnemyClass()
        e.set_type("white_mummy")
        e.row, e.col = rows - 1, cols - 1
        enemies.append(e)

    if exit_pos is not None:
        gamestate.goal_row, gamestate.goal_col = exit_pos
    elif legacy_goal is not None:
        gamestate.goal_row, gamestate.goal_col = legacy_goal
    else:
        gamestate.goal_row, gamestate.goal_col = rows - 1, cols - 1

    gamestate.initpos = make_snapshot(player, enemies, gamestate)
    gamestate.storedmove.clear()
    gamestate.storedmove.append(gamestate.initpos)
    gamestate.pending_snapshot = False
    gamestate.gameover = False
    gamestate.result = None
    
    # Generate solution for adventure levels
    # print(f"[Adventure] Generating solution for level with {len(enemies)} enemies...")
    if is_playable(player, enemies, grid, gamestate):
        pass  # print(f"[Adventure] Level is solvable!")
    else:
        pass  # print(f"[Adventure] WARNING: No solution found for this level!")
        gamestate.solution = []

def path_finding(player, enemy, grid, gamestate, impossible_mode=False):
    """BFS over (player, enemies, gate_state).

    - Supports multiple enemies (ordered as provided)
    - Enemies move after player each turn (2 steps unless red_scorpion)
    - Gate open/closed state included in visited key
    - Avoids traps and player/enemy deaths
    - impossible_mode: if True, enemies use BFS shortest path instead of Manhattan
    """

    directions = [("up", -1, 0), ("down", 1, 0), ("left", 0, -1), ("right", 0, 1)]

    # Normalize enemy list
    enemies_list = list(enemy) if isinstance(enemy, (list, tuple)) else [enemy]

    # Gate ordering for stable encoding
    gate_positions = sorted(getattr(gamestate, "gates_h", {}).keys())
    gate_index = {pos: i for i, pos in enumerate(gate_positions)}

    def encode_gates(gates_dict):
        if not gate_positions:
            return tuple()
        return tuple(1 if gates_dict.get(pos, False) else 0 for pos in gate_positions)

    def toggle_gates_state(gate_state_tuple):
        return tuple(0 if v else 1 for v in gate_state_tuple)

    def enemy_type_code(t: str):
        if "white" in t:
            return "W"
        if t.startswith("red_scorpion"):
            return "S"
        if t.startswith("red"):
            return "R"
        return "W"

    def decode_steps(tcode: str):
        return 1 if tcode == "S" else 2

    def encode_enemies(ens):
        out = []
        for e in ens:
            tcode = enemy_type_code(getattr(e, "type", "white_mummy"))
            out.append((tcode, int(e.row), int(e.col)))
        return tuple(out)

    start_gate_state = encode_gates(getattr(gamestate, "gates_h", {}))
    start_enemy_state = encode_enemies(enemies_list)
    start = (player.row, player.col, start_enemy_state, start_gate_state)

    # Visited as set of tuples for memory efficiency
    # State includes full enemy info (type + position) and order matters
    prev = {}
    iterations = 0

    # Search budget:
    # - normal: smaller is fine (state space is tiny)
    # - impossible: allow more but rely on A* to avoid explosion
    max_iterations = 1200000 if impossible_mode else 500000

    if impossible_mode:
        import heapq

        def h_est(r, c):
            # Admissible heuristic (Manhattan) => A* stays optimal on step count
            return abs(r - gamestate.goal_row) + abs(c - gamestate.goal_col)

        best_g = {start: 0}
        heap = [(h_est(player.row, player.col), 0, start)]  # (f, g, state)
    else:
        visited = {start}
        q = deque([start])

    def gate_is_open(rh, c, gate_state_tuple):
        if (rh, c) not in gate_index:
            return True
        return bool(gate_state_tuple[gate_index[(rh, c)]])

    def can_move(pr, pc, dir_name, gate_state_tuple):
        cell = grid[pr][pc]
        if dir_name == "up":
            if pr <= 0:
                return None
            above = grid[pr - 1][pc]
            if above.down == 1:
                return None
            if above.down in (2, 3):
                if not gate_is_open(pr, pc, gate_state_tuple):
                    return None
            return (pr - 1, pc)
        if dir_name == "down":
            if pr >= ROWS - 1:
                return None
            if cell.down == 1:
                return None
            if cell.down in (2, 3):
                if not gate_is_open(pr + 1, pc, gate_state_tuple):
                    return None
            return (pr + 1, pc)
        if dir_name == "left":
            if pc <= 0 or cell.left == 1:
                return None
            return (pr, pc - 1)
        if dir_name == "right":
            if pc >= COLS - 1 or cell.right == 1:
                return None
            return (pr, pc + 1)
        return None

    def enemy_best_step_manhattan(er, ec, tcode, pr, pc, gate_state_tuple):
        """Manhattan distance based enemy movement (normal mode)."""
        dirs = [("up", -1, 0), ("down", 1, 0), ("left", 0, -1), ("right", 0, 1)]
        if tcode == "W":
            dirs = [("left", 0, -1), ("right", 0, 1), ("up", -1, 0), ("down", 1, 0)]

        best_r, best_c = er, ec
        best_dist = abs(er - pr) + abs(ec - pc)

        for name, dr, dc in dirs:
            target = can_move(er, ec, name, gate_state_tuple)
            if target is None:
                continue
            tr, tc = target
            dist = abs(tr - pr) + abs(tc - pc)
            if dist < best_dist:
                best_dist = dist
                best_r, best_c = tr, tc
        return best_r, best_c

    # ---- Impossible-mode speedup: dist map cache (player -> all cells) ----
    # Cache key: (player_row, player_col, gate_state_tuple)
    dist_cache = {}
    dist_cache_order = deque()
    DIST_CACHE_MAX = 256

    def get_player_dist_map(pr, pc, gate_state_tuple):
        key = (pr, pc, gate_state_tuple)
        if key in dist_cache:
            return dist_cache[key]

        dist = [[-1] * COLS for _ in range(ROWS)]
        dq = deque([(pr, pc)])
        dist[pr][pc] = 0

        while dq:
            r, c = dq.popleft()
            for dname, dr, dc in directions:
                nxt = can_move(r, c, dname, gate_state_tuple)
                if nxt is None:
                    continue
                nr, nc = nxt
                if dist[nr][nc] == -1:
                    dist[nr][nc] = dist[r][c] + 1
                    dq.append((nr, nc))

        dist_cache[key] = dist
        dist_cache_order.append(key)
        if len(dist_cache_order) > DIST_CACHE_MAX:
            old = dist_cache_order.popleft()
            dist_cache.pop(old, None)
        return dist

    # ---- Goal distance map cache (goal -> all cells), used for impossible-mode blocking ----
    goal_cache = {}
    goal_cache_order = deque()
    GOAL_CACHE_MAX = 256

    def get_goal_dist_map(gate_state_tuple):
        key = gate_state_tuple
        if key in goal_cache:
            return goal_cache[key]

        gr, gc = gamestate.goal_row, gamestate.goal_col
        dist = [[-1] * COLS for _ in range(ROWS)]
        dq = deque([(gr, gc)])
        dist[gr][gc] = 0

        while dq:
            r, c = dq.popleft()
            for name, dr, dc in directions:
                nxt = can_move(r, c, name, gate_state_tuple)
                if nxt is None:
                    continue
                nr, nc = nxt
                if dist[nr][nc] == -1:
                    dist[nr][nc] = dist[r][c] + 1
                    dq.append((nr, nc))

        goal_cache[key] = dist
        goal_cache_order.append(key)
        if len(goal_cache_order) > GOAL_CACHE_MAX:
            old = goal_cache_order.popleft()
            goal_cache.pop(old, None)
        return dist
    def enemy_ranked_moves_impossible(er, ec, tcode, pr, pc, gate_state_tuple):
        """Candidate next positions ranked (impossible mode).

        This is intentionally conservative: enemies can either chase the player or move to block the goal.
        Ranking uses two cached distance maps:
        - distP: distance to player
        - distG: distance to goal

        Score: (min(distP, distG), distP, distG, direction_order)
        """
        distP = get_player_dist_map(pr, pc, gate_state_tuple)
        distG = get_goal_dist_map(gate_state_tuple)

        BIG = 10**9

        if tcode == "W":
            dirs = [("left", 0, -1), ("right", 0, 1), ("up", -1, 0), ("down", 1, 0)]
        else:
            dirs = [("up", -1, 0), ("down", 1, 0), ("left", 0, -1), ("right", 0, 1)]

        dp0 = distP[er][ec]
        dg0 = distG[er][ec]
        dp0 = dp0 if dp0 >= 0 else BIG
        dg0 = dg0 if dg0 >= 0 else BIG

        # Staying is always an option (last tie-break)
        cand = [((min(dp0, dg0), dp0, dg0, 99), (er, ec))]

        for order_idx, (name, dr, dc) in enumerate(dirs):
            nxt = can_move(er, ec, name, gate_state_tuple)
            if nxt is None:
                continue
            nr, nc = nxt

            # Immediate kill is always top priority
            if (nr, nc) == (pr, pc):
                return [(nr, nc), (er, ec)]

            dp = distP[nr][nc]
            dg = distG[nr][nc]
            dp = dp if dp >= 0 else BIG
            dg = dg if dg >= 0 else BIG

            cand.append(((min(dp, dg), dp, dg, order_idx), (nr, nc)))

        cand.sort(key=lambda x: x[0])
        return [pos for _, pos in cand]

    def enemy_best_step_bfs(er, ec, tcode, pr, pc, gate_state_tuple):
        """Deterministic enemy step (impossible mode), before collision-avoidance filtering."""
        return enemy_ranked_moves_impossible(er, ec, tcode, pr, pc, gate_state_tuple)[0]

    def enemy_best_step(er, ec, tcode, pr, pc, gate_state_tuple):
        """Choose movement strategy based on impossible_mode flag."""
        if impossible_mode:
            return enemy_best_step_bfs(er, ec, tcode, pr, pc, gate_state_tuple)
        else:
            return enemy_best_step_manhattan(er, ec, tcode, pr, pc, gate_state_tuple)

    while (heap if impossible_mode else q):
        iterations += 1
        if iterations > max_iterations:
            # print(f"[BFS] Max iterations ({max_iterations}) reached, aborting search")
            return None
        if impossible_mode:
            _, g, cur = heapq.heappop(heap)
            if g != best_g.get(cur, 10**18):
                continue
        else:
            cur = q.popleft()
            g = None

        p_row, p_col, enemy_state, gate_state = cur

        # Goal check
        if p_row == gamestate.goal_row and p_col == gamestate.goal_col:
            path = []
            node = cur
            while node in prev:
                node, move = prev[node]
                path.append(move)
            path.reverse()
            # print(f"[BFS] Found solution in {iterations} iterations, visited {len(visited)} states")
            return path

        for name, dr, dc in directions:
            nxt_p = can_move(p_row, p_col, name, gate_state)
            if nxt_p is None:
                continue
            np_row, np_col = nxt_p

            # Player cannot step on trap
            if (np_row, np_col) in getattr(gamestate, "traps", set()):
                continue

            # Toggle gates if stepping on key
            next_gate_state = gate_state
            if (np_row, np_col) in getattr(gamestate, "keys", set()):
                next_gate_state = toggle_gates_state(gate_state)

            # If player steps onto an enemy before they move -> death
            enemy_positions = {(er, ec) for (_, er, ec) in enemy_state}
            if (np_row, np_col) in enemy_positions:
                continue

            # Simulate enemy moves in order
            alive = [True] * len(enemy_state)
            positions = [(er, ec) for (_, er, ec) in enemy_state]
            types = [t for (t, _, _) in enemy_state]

            stationary = {(r, c): idx for idx, (r, c) in enumerate(positions) if alive[idx]}
            moved_positions = set()

            player_dead = False  # <<< ADD

            for idx, (er, ec) in enumerate(positions):
                if not alive[idx]:
                    continue
                tcode = types[idx]
                steps = decode_steps(tcode)

                for _ in range(steps):
                    # Leaving current tile
                    stationary.pop((er, ec), None)

                    if impossible_mode:
                        # In impossible mode, enemies avoid colliding/killing each other.
                        chosen_r, chosen_c = er, ec
                        for cand_r, cand_c in enemy_ranked_moves_impossible(er, ec, tcode, np_row, np_col, next_gate_state):
                            if (cand_r, cand_c) == (np_row, np_col):
                                chosen_r, chosen_c = cand_r, cand_c
                                break
                            if (cand_r, cand_c) in stationary or (cand_r, cand_c) in moved_positions:
                                continue
                            chosen_r, chosen_c = cand_r, cand_c
                            break
                        nr, nc = chosen_r, chosen_c
                    else:
                        nr, nc = enemy_best_step(er, ec, tcode, np_row, np_col, next_gate_state)
                    if (nr, nc) == (er, ec):
                        stationary[(er, ec)] = idx
                        break

                    # Collision with stationary enemy: kill the stationary one, move in
                    if (nr, nc) in stationary:
                        if impossible_mode:
                            # Conservative: enemies do not suicide/kill each other in impossible mode
                            stationary[(er, ec)] = idx
                            break
                        killed_idx = stationary.pop((nr, nc))
                        alive[killed_idx] = False
                    elif (nr, nc) in moved_positions:
                        stationary[(er, ec)] = idx
                        break

                    er, ec = nr, nc
                    moved_positions.add((er, ec))

                    # >>> ADD: mid-step death check (SINGLE SOURCE OF TRUTH)
                    if (er, ec) == (np_row, np_col):
                        player_dead = True
                        break

                if player_dead:
                    break

                positions[idx] = (er, ec)

            if player_dead:
                continue  # reject this player move, because game would be over immediately


            # If any alive enemy ends on player -> death
            if any(alive[i] and positions[i] == (np_row, np_col) for i in range(len(positions))):
                continue

            # Build next enemy state (preserve order for determinism)
            next_enemy_state = tuple(
                (types[i], positions[i][0], positions[i][1])
                for i in range(len(positions))
                if alive[i]
            )

            nxt_state = (np_row, np_col, next_enemy_state, next_gate_state)

            if impossible_mode:
                g2 = g + 1
                if g2 < best_g.get(nxt_state, 10**18):
                    best_g[nxt_state] = g2
                    prev[nxt_state] = (cur, name)
                    f2 = g2 + h_est(np_row, np_col)
                    heapq.heappush(heap, (f2, g2, nxt_state))
            else:
                if nxt_state in visited:
                    continue
                visited.add(nxt_state)
                prev[nxt_state] = (cur, name)
                q.append(nxt_state)
    
    # print(f"[BFS] No solution found after {iterations} iterations, visited {len(visited)} states")
    return None

def is_playable(player, enemy, grid, gamestate):
    """Check solvability; enemy can be a single enemy or list of enemies."""
    impossible_mode = getattr(gamestate, "impossible_mode", False)
    path = path_finding(player, enemy, grid, gamestate, impossible_mode)
    if path is None:
        # print("[BFS] No solution found")
        return False
    gamestate.solution = path
    # print(f"[BFS] Solution found! {len(path)} moves: {path}")
    return True

def is_not_too_easy(player, enemy, grid, gamestate):
    directions = [('up', -1, 0), ('down', 1, 0), ('left', 0, -1), ('right', 0, 1)]
    visited = [[False] * COLS for _ in range(ROWS)]
    q = deque([(enemy.row, enemy.col, 0)])
    visited[enemy.row][enemy.col] = True

    while q:
        r, c, dist = q.popleft()
        if (r, c) == (player.row, player.col) and dist <= 5:
            return False
        cell = grid[r][c]
        for dname, dr, dc in directions:
            nr, nc = r + dr, c + dc
            if 0 <= nr < ROWS and 0 <= nc < COLS:
                ok = False
                if dname == "up":
                    ok = (r > 0 and grid[r - 1][c].down not in (1, 2))
                elif dname == "down":
                    ok = (cell.down not in (1, 2))
                elif dname == "left":
                    ok = (cell.left == 0)
                elif dname == "right":
                    ok = (cell.right == 0)

                if ok and not visited[nr][nc]:
                    visited[nr][nc] = True
                    q.append((nr, nc, dist + 1))
    for r in range(ROWS):
        for c in range(COLS):
            if visited[r][c] == 0:
                #print("Some cells are unreachable.")
                return False
    return True


def generate_game(grid, player, enemies, gamestate):
    # print("Generating new game...")

    enemy_count = getattr(gamestate, "enemy_count", None)
    if enemy_count is None:
        if ROWS <= 6:
            enemy_count = 1
        elif ROWS <= 8:
            enemy_count = 2
        else:
            enemy_count = 3

    from entity.entity import Enemy as EnemyClass
    enemies.clear()
    for _ in range(enemy_count):
        enemies.append(EnemyClass())

    if hasattr(gamestate, "reset_items"):
        gamestate.reset_items()

    while True:
        for row in grid:
            for cell in row:
                cell.up, cell.down, cell.left, cell.right = 0, 0, 0, 0

        player.row = random.randint(0, ROWS - 1)
        player.col = random.randint(0, COLS - 1)

        taken = {(player.row, player.col)}
        for e in enemies:
            while True:
                e.row = random.randint(0, ROWS - 1)
                e.col = random.randint(0, COLS - 1)
                # print(e.row, e.col)
                if (e.row, e.col) not in taken:
                    taken.add((e.row, e.col))
                    break

        while True:
            side = random.choice(['up', 'down', 'left', 'right'])
            if side == 'up':
                gamestate.goal_row = 0
                gamestate.goal_col = random.randint(0, COLS - 1)
            elif side == 'down':
                gamestate.goal_row = ROWS - 1
                gamestate.goal_col = random.randint(0, COLS - 1)
            elif side == 'left':
                gamestate.goal_row = random.randint(0, ROWS - 1)
                gamestate.goal_col = 0
            else:
                gamestate.goal_row = random.randint(0, ROWS - 1)
                gamestate.goal_col = COLS - 1

            if (gamestate.goal_row, gamestate.goal_col) not in taken:
                break

        # Set enemy types based on mode
        if getattr(gamestate, "impossible_mode", False) and len(enemies) >= 5:
            # Impossible mode: 2 scorpions + 3 random mummies
            enemies[0].type = "red_scorpion"
            enemies[1].type = "red_scorpion"
            for e in enemies[2:]:
                e.type = random.choice(["red_mummy", "white_mummy"])
            for e in enemies:
                add_sprite_frames(e)
        else:
            for e in enemies:
                e.type = random.choice(["red_mummy", "white_mummy", "red_scorpion"])
                add_sprite_frames(e)

        generate_walls_pr(grid, random.randint(ROWS * COLS // 4, 2*ROWS * COLS))
        
        # Randomly place keys, gates, and traps
        generate_random_items(grid, player, enemies, gamestate, taken)

        #check if some cells are unreachable
        # if not is_not_too_easy(player, enemies[0], grid, gamestate):
        #     print("[Generate] Rejecting map: too easy")
        #     continue
        # # Solvability + difficulty checks
        if not is_playable(player, enemies, grid, gamestate):
            #print("[Generate] Rejecting map: no solution")
            continue

        # Enforce minimum solution length
        min_len = max(6, ROWS)
        if len(gamestate.solution) < min_len:
            #print(f"[Generate] Rejecting map: solution too short ({len(gamestate.solution)} < {min_len})")
            continue
        #print(f"[Generate] Accepted map: solution length {len(gamestate.solution)}")
        break

    gamestate.initpos = make_snapshot(player, enemies, gamestate)
    gamestate.storedmove.clear()
    gamestate.storedmove.append(gamestate.initpos)
    gamestate.pending_snapshot = False
    gamestate.gameover = False
    gamestate.result = None

    # print("New game generated.")
    # print(gamestate.solution)
def _set_wall_between(grid, r, c, nr, nc, val):
    # val: 0=open, 1=wall
    if nr == r - 1 and nc == c:  # up
        grid[nr][nc].down = val
        grid[r][c].up = val
        return
    if nr == r + 1 and nc == c:  # down
        grid[r][c].down = val
        grid[nr][nc].up = val
        return
    if nr == r and nc == c - 1:  # left
        grid[r][c].left = val
        grid[nr][nc].right = val
        return
    if nr == r and nc == c + 1:  # right
        grid[r][c].right = val
        grid[nr][nc].left = val
        return


def generate_walls_pr(grid, num_walls):
    R, C = ROWS, COLS
    N = R * C
    E = R * (C - 1) + C * (R - 1)
    max_walls_connected = E - (N - 1)  # = (R-1)(C-1)

    # Clamp để luôn solvable, khỏi spam reject
    target_walls = max(0, min(int(num_walls), max_walls_connected))

    # 1) Close all (tường kín)
    for r in range(1,R-1):
        for c in range(1,C-1):
            cell = grid[r][c]
            cell.up = 1
            cell.down = 1
            cell.left = 1
            cell.right = 1

    def neighbors(r, c):
        if r > 0: yield (r - 1, c)
        if r < R - 1: yield (r + 1, c)
        if c > 0: yield (r, c - 1)
        if c < C - 1: yield (r, c + 1)

    # 2) Prim: mở N-1 cạnh để connected chắc chắn
    sr = random.randint(0, R - 1)
    sc = random.randint(0, C - 1)

    in_maze = {(sr, sc)}
    frontier = []

    def add_frontier(r, c):
        for nr, nc in neighbors(r, c):
            if (nr, nc) not in in_maze:
                frontier.append((r, c, nr, nc))

    add_frontier(sr, sc)

    while frontier:
        i = random.randrange(len(frontier))
        r, c, nr, nc = frontier.pop(i)
        if (nr, nc) in in_maze:
            continue
        _set_wall_between(grid, r, c, nr, nc, 0)
        in_maze.add((nr, nc))
        add_frontier(nr, nc)

    # 3) Mở thêm để đạt đúng target_walls
    extra_opens = max_walls_connected - target_walls
    if extra_opens <= 0:
        return

    closed_edges = []
    for r in range(R):
        for c in range(C):
            if r < R - 1 and grid[r][c].down == 1:
                closed_edges.append((r, c, r + 1, c))
            if c < C - 1 and grid[r][c].right == 1:
                closed_edges.append((r, c, r, c + 1))

    if closed_edges:
        random.shuffle(closed_edges)
        for k in range(min(extra_opens, len(closed_edges))):
            r, c, nr, nc = closed_edges[k]
            _set_wall_between(grid, r, c, nr, nc, 0)

def generate_walls(grid, num_walls):
    directions = [('up', 'down', -1, 0), ('down', 'up', 1, 0),
                  ('left', 'right', 0, -1), ('right', 'left', 0, 1)]
    for _ in range(num_walls):
        no_wall = True
        while no_wall:
            r = random.randint(0, ROWS - 1)
            c = random.randint(0, COLS - 1)
            d = random.choice(directions)
            if 0 <= r + d[2] < ROWS and 0 <= c + d[3] < COLS and not getattr(grid[r][c], d[0]):
                setattr(grid[r][c], d[0], 1)
                setattr(grid[r + d[2]][c + d[3]], d[1], 1)
                no_wall = False
    # print("Walls generated.")

def generate_random_items(grid, player, enemies, gamestate, taken_positions):
    """Randomly place keys, gates, and traps on available cells (Phase 3).
    
    Rules:
    - If key exists, gates MUST be placed
    - Gates cannot be on map border (0 < r < ROWS-1, 0 < c < COLS-1)
    - Traps are independent
    """
    
    # Clear existing items
    gamestate.keys.clear()
    gamestate.traps.clear()
    gamestate.gates_h.clear()
    gamestate.gate_anim_state.clear()
    
    # Probability thresholds by grid size (Easy 6, Medium 8, Hard 10)
    if ROWS <= 6:
        key_prob = 0.30
        trap_prob = 0.08
        max_traps = 1
        max_gates = 1
    elif ROWS <= 8:
        key_prob = 0.50
        trap_prob = 0.18
        max_traps = 3
        max_gates = 2
    else:
        key_prob = 0.65
        trap_prob = 0.28
        max_traps = max(3, ROWS // 3)
        max_gates = 3
    
    available_cells = []
    for r in range(ROWS):
        for c in range(COLS):
            if (r, c) not in taken_positions:
                available_cells.append((r, c))
    
    # Decide if we add a key (at most 1)
    has_key = random.random() < key_prob and len(available_cells) > 0

    if has_key:
        kr, kc = random.choice(available_cells)
        gamestate.keys.add((kr, kc))
        if (kr, kc) in available_cells:
            available_cells.remove((kr, kc))
        # print(f"[Generate] Placed 1 key")
        
        # MANDATORY: Place gates if key exists
        # Gates stored as (row_below_gate, col), so valid range: 0 < r < ROWS and 0 < c < COLS
        # This means gate is blocking passage between row r-1 and row r
        valid_gate_positions = []
        for r in range(1, ROWS):  # r from 1 to ROWS-1 (not on top/bottom border)
            for c in range(COLS):  # c from 0 to COLS-1
                gate_pos = (r, c)
                if gate_pos not in gamestate.gates_h:
                    valid_gate_positions.append(gate_pos)
        
        num_gates = random.randint(1, min(max_gates, len(valid_gate_positions)))
        if num_gates > 0:
            gate_positions = random.sample(valid_gate_positions, num_gates)
            for gr, gc in gate_positions:
                is_open = random.choice([True, False])
                gamestate.gates_h[(gr, gc)] = is_open
                # Sync grid cell with gate state
                if 0 <= gr - 1 < ROWS and 0 <= gc < COLS:
                    grid[gr - 1][gc].down = 3 if is_open else 2
                # Initialize gate animation state
                gamestate.gate_anim_state[(gr, gc)] = {
                    "frame": 7 if is_open else 0,
                    "time": 0.0,
                    "is_closing": not is_open
                }
                # print(f"[Generate] Gate at ({gr}, {gc}) - {'open' if is_open else 'closed'}")
        else:
            # print("[Generate] WARNING: No valid gate positions found! Placing gates anyway...")
            # Fallback: place at least 1 gate even if in non-ideal position
            if valid_gate_positions:
                gr, gc = random.choice(valid_gate_positions)
                is_open = random.choice([True, False])
                gamestate.gates_h[(gr, gc)] = is_open
                # Sync grid cell with gate state
                if 0 <= gr - 1 < ROWS and 0 <= gc < COLS:
                    grid[gr - 1][gc].down = 3 if is_open else 2
                # Initialize gate animation state
                gamestate.gate_anim_state[(gr, gc)] = {
                    "frame": 7 if is_open else 0,
                    "time": 0.0,
                    "is_closing": not is_open
                }
    
    # Place traps (avoid occupied cells and key cells)
    if random.random() < trap_prob and len(available_cells) > 0:
        num_traps = random.randint(1, min(max_traps, len(available_cells)))
        trap_positions = random.sample(available_cells, min(num_traps, len(available_cells)))
        for tr, tc in trap_positions:
            gamestate.traps.add((tr, tc))
        # print(f"[Generate] Placed {len(trap_positions)} trap(s)")
    
    # print("[Generate] Items placed")


def solution_touches_key(path, player, grid, gamestate):
    """Check if the solution path visits at least one key tile.

    We simulate only player moves using grid walls/gates. Enemy turns are irrelevant
    for the key-visit condition because the BFS already validated legality.
    """
    if not gamestate.keys:
        return False
    r, c = player.row, player.col
    directions = {
        "up": (-1, 0),
        "down": (1, 0),
        "left": (0, -1),
        "right": (0, 1),
    }

    for move in path:
        dr, dc = directions.get(move, (0, 0))
        nr, nc = r + dr, c + dc
        # Validate movement like Player.move
        if move == "up" and r > 0 and grid[r - 1][c].down not in (1, 2):
            r, c = nr, nc
        elif move == "down" and r < ROWS - 1 and grid[r][c].down not in (1, 2):
            r, c = nr, nc
        elif move == "left" and c > 0 and grid[r][c].left == 0:
            r, c = nr, nc
        elif move == "right" and c < COLS - 1 and grid[r][c].right == 0:
            r, c = nr, nc

        if (r, c) in gamestate.keys:
            return True
    return False

# ===== Phase 2: Key, Gate, Trap Rendering =====

def draw_key(surface, gamestate, dt):
    """Draw spinning key animation on all key tiles (Phase 2)."""
    if not gamestate.key_frames:
        return
    
    # Update animation frame
    gamestate.key_anim_timer += dt
    if gamestate.key_anim_timer >= 0.05:  # ~20 FPS for key spin
        gamestate.key_anim_timer -= 0.05
        gamestate.key_anim_idx = (gamestate.key_anim_idx + 1) % len(gamestate.key_frames)
    
    # Wall scaling factor (same as Cell._scale)
    factor = CELL_SIZE / 60
    
    # Draw on each key tile - scaled like walls
    for r, c in gamestate.keys:
        try:
            frame = gamestate.key_frames[gamestate.key_anim_idx]
            # Scale like wall
            if hasattr(pygame.transform, "smoothscale_by"):
                frame = pygame.transform.smoothscale_by(frame, factor)
            else:
                w, h = frame.get_size()
                frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
            
            # Center in cell
            x = OFFSET_X + c * CELL_SIZE + CELL_SIZE / 2 - frame.get_width() / 2
            y = OFFSET_Y + r * CELL_SIZE + CELL_SIZE / 2 - frame.get_height() / 2
            surface.blit(frame, (x, y))
        except Exception as e:
            pass  # print(f"[draw_key] Error drawing key at ({r},{c}): {e}")


def draw_gates(surface, gamestate, dt):
    """Draw gate animations on gate tiles (Phase 2). Scaled like walls."""
    if not gamestate.gate_frames:
        return
    
    # Wall scaling factor (same as Cell._scale)
    factor = CELL_SIZE / 60
    
    # Update gate animations
    for gate_pos, is_open in gamestate.gates_h.items():
        rh, c = gate_pos
        
        if gate_pos not in gamestate.gate_anim_state:
            # Initialize gate animation state
            gamestate.gate_anim_state[gate_pos] = {
                "frame": 0 if not is_open else 7,
                "time": 0.0,
                "is_closing": False
            }
        
        state = gamestate.gate_anim_state[gate_pos]
        
        # Determine animation direction based on gate state
        if is_open and state["frame"] < 7 and not state["is_closing"]:
            # Open: animate forward (0 -> 7)
            state["time"] += dt
            if state["time"] >= 0.08:
                state["time"] -= 0.08
                state["frame"] = min(state["frame"] + 1, 7)
        elif not is_open and state["frame"] > 0 and state["is_closing"]:
            # Close: animate backward (7 -> 0)
            state["time"] += dt
            if state["time"] >= 0.08:
                state["time"] -= 0.08
                state["frame"] = max(state["frame"] - 1, 0)
        
        # Mark closing state transition
        if is_open and state["frame"] == 7:
            state["is_closing"] = False
        elif not is_open and state["frame"] == 0:
            state["is_closing"] = True
        
        # Draw gate (only if in range) - scaled like wall
        if rh - 1 >= 0 and rh - 1 < ROWS:
            try:
                frame = gamestate.gate_frames[state["frame"]]
                # Scale like wall
                if hasattr(pygame.transform, "smoothscale_by"):
                    frame = pygame.transform.smoothscale_by(frame, factor)
                else:
                    w, h = frame.get_size()
                    frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                x = OFFSET_X + c * CELL_SIZE
                y = OFFSET_Y + (rh - 1) * CELL_SIZE + CELL_SIZE - wall_gap
                surface.blit(frame, (x, y))
            except Exception as e:
                pass  # print(f"[draw_gates] Error drawing gate at {gate_pos}: {e}")


def draw_traps(surface, gamestate):
    """Draw trap tiles - scaled like walls, centered in cell (Phase 2)."""
    if not gamestate.trap_frames:
        return
    
    # Wall scaling factor (same as Cell._scale)
    factor = CELL_SIZE / 60
    
    for r, c in gamestate.traps:
        try:
            frame = gamestate.trap_frames[0]  # Only 1 frame for trap
            # Scale like wall
            if hasattr(pygame.transform, "smoothscale_by"):
                frame = pygame.transform.smoothscale_by(frame, factor)
            else:
                w, h = frame.get_size()
                frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
            
            # Center in cell
            x = OFFSET_X + c * CELL_SIZE + CELL_SIZE / 2 - frame.get_width() / 2
            y = OFFSET_Y + r * CELL_SIZE + CELL_SIZE / 2 - frame.get_height() / 2
            surface.blit(frame, (x, y))
        except Exception as e:
            pass  # print(f"[draw_traps] Error drawing trap at ({r},{c}): {e}")

# ===== Phase 3: Key/Gate/Trap Logic =====

def check_special_tiles(player, grid, gamestate):
    """Check if player stepped on key or trap (Phase 3)."""
    pr, pc = player.row, player.col
    
    # Check if player is on a key - toggle gates but keep the key
    if (pr, pc) in gamestate.keys:
        toggle_gates(grid, gamestate)
        # Play key pickup sound
        if gamestate.sfx.get("opentreasure") is not None:
            try:
                gamestate.sfx["opentreasure"].play()
            except: pass
        # print(f"[Key] Player stepped on key at ({pr},{pc}), gates toggled")
    
    # Check if player is on a trap -> start death animation
    if (pr, pc) in gamestate.traps:
        start_trap_death(player, gamestate)
        # print(f"[Trap] Player stepped on trap at ({pr},{pc})")

def toggle_gates(grid, gamestate):
    """Toggle all gates between open/closed (Phase 3)."""
    for gate_pos in gamestate.gates_h:
        rh, c = gate_pos
        current_state = gamestate.gates_h[gate_pos]
        new_state = not current_state
        
        gamestate.gates_h[gate_pos] = new_state
        
        # Sync with Cell.down: 2=closed, 3=open
        if 0 <= rh - 1 < ROWS and 0 <= c < COLS:
            cell = grid[rh - 1][c]
            cell.down = 3 if new_state else 2
            
            # Mark animation state for visual transition
            if gate_pos in gamestate.gate_anim_state:
                gamestate.gate_anim_state[gate_pos]["is_closing"] = not new_state
    
    # Play gate sound when toggling
    if gamestate.sfx.get("gate") is not None:
        try:
            gamestate.sfx["gate"].play()
        except Exception as e:
            debug_log(f"[Sound] gate play failed: {e}")


# ===== Phase 4: Death animations =====

def start_trap_death(player, gamestate):
    """Initialize trap death animation state."""
    gamestate.state = "DEATH_ANIM"
    gamestate.gameover = True
    
    # Randomize trap outcome: pit fall or block hit
    # 50/50 by default; adjust probability if desired
    is_block = random.random() < 0.5

    if is_block and getattr(gamestate, "block_frames", None):
        # Block death animation (falling block + player freakout)
        if gamestate.sfx.get("block") is not None:
            try:
                gamestate.sfx["block"].play()
            except Exception as e:
                debug_log(f"[Sound] block play failed: {e}")
        gamestate.death_state = {
            "cause": "block",
            "row": player.row,
            "col": player.col,
            "stage": "freakout",  # freakout -> drop -> done
            "timer": 0.0,
            # Block animation frames/timing
            "block_idx": 0,
            "block_timer": 0.0,
            "block_fps": 12,
            # Player freakout frames/timing
            "freak_idx": 0,
            "freak_timer": 0.0,
            "freak_fps": 12,
            "freak_dur": 0.6,
            # Vertical drop duration and offset from sky
            "drop_dur": 0.8,
            "drop_offset": CELL_SIZE * 1.5,
        }
    else:
        # Pit fall (original trap death)
        if gamestate.sfx.get("pit") is not None:
            try:
                gamestate.sfx["pit"].play()
            except Exception as e:
                debug_log(f"[Sound] pit play failed: {e}")
        gamestate.death_state = {
            "cause": "trap",
            "row": player.row,
            "col": player.col,
            "stage": "slide",  # slide -> fall -> done
            "timer": 0.0,
            "slide_dur": 0.35,
            "fall_dur": 0.35,
            "exp_idx": 0,
            "exp_timer": 0.0,
            "exp_fps": 12,
        }


def update_death_anim(dt, gamestate):
    """Advance death animation; return True when finished."""
    d = getattr(gamestate, "death_state", None)
    if not d:
        return True

    if d["cause"] == "trap":
        if d["stage"] == "slide":
            d["timer"] += dt
            if d["timer"] >= d["slide_dur"]:
                d["stage"] = "fall"
                d["timer"] = 0.0
            return False

        if d["stage"] == "fall":
            d["timer"] += dt
            d["exp_timer"] += dt
            step = 1.0 / d["exp_fps"]
            if gamestate.expfall_frames:
                while d["exp_timer"] >= step:
                    d["exp_timer"] -= step
                    d["exp_idx"] = min(d["exp_idx"] + 1, len(gamestate.expfall_frames) - 1)
            if d["timer"] >= d["fall_dur"]:
                d["stage"] = "done"
            return False

        if d["stage"] == "done":
            return True

    elif d["cause"] == "block":
        # Stage 1: freakout (player looks up, no block yet)
        if d["stage"] == "freakout":
            d["timer"] += dt
            d["freak_timer"] += dt
            f_step = 1.0 / d.get("freak_fps", 12)
            if getattr(gamestate, "freakout_frames", None):
                while d["freak_timer"] >= f_step:
                    d["freak_timer"] -= f_step
                    d["freak_idx"] = min(d["freak_idx"] + 1, len(gamestate.freakout_frames) - 1)
            # After freakout duration, begin block drop
            if d["timer"] >= d.get("freak_dur", 0.6):
                d["stage"] = "drop"
                d["timer"] = 0.0
            return False

        # Stage 2: block drop (block falls; optionally keep freakout anim)
        if d["stage"] == "drop":
            d["timer"] += dt
            d["block_timer"] += dt
            b_step = 1.0 / d.get("block_fps", 12)
            if getattr(gamestate, "block_frames", None):
                while d["block_timer"] >= b_step:
                    d["block_timer"] -= b_step
                    d["block_idx"] = min(d["block_idx"] + 1, len(gamestate.block_frames) - 1)
            if d["timer"] >= d.get("drop_dur", 0.8):
                d["stage"] = "done"
            return False

        if d["stage"] == "done":
            return True

    else:
        # red / white / stung
        if d["stage"] == "dust":
            d["dust_timer"] += dt
            step = 1.0 / d.get("dust_fps", 20)
            if gamestate.dust_frames:
                while d["dust_timer"] >= step:
                    d["dust_timer"] -= step
                    d["dust_idx"] = min(d["dust_idx"] + 1, len(gamestate.dust_frames) - 1)
            d["timer"] += dt
            if d["timer"] >= 0.6 or d["cause"] == "stung":  # stung skips dust duration
                d["stage"] = "fight"
                d["timer"] = 0.0
            return False

        if d["stage"] == "fight":
            d["fight_timer"] += dt
            d["fight_anim_timer"] += dt
            step = 1.0 / d.get("fight_fps", 12)
            fight_frames = None
            if d["cause"] == "red":
                fight_frames = gamestate.red_fight_frames
            elif d["cause"] == "white":
                fight_frames = gamestate.white_fight_frames
            elif d["cause"] == "stung":
                fight_frames = gamestate.stung_frames
            if fight_frames:
                while d["fight_anim_timer"] >= step:
                    d["fight_anim_timer"] -= step
                    d["fight_idx"] = (d["fight_idx"] + 1) % len(fight_frames)
            if d["fight_timer"] >= d.get("fight_dur", 0.6):
                d["stage"] = "done"
            return False

        if d["stage"] == "done":
            return True

    return True
