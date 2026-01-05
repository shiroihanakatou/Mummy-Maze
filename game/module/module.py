import pygame, sys, random
import json
from collections import deque
from pygame.locals import *
from variable import *
from module.gamestate import Gamestate

def wait(seconds):
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < seconds * 1000:
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()
        FramePerSec.tick(FPS)

###scale màn
class ScreenManager:
    def __init__(self, virtual_w, virtual_h):
        self.virtual_w = virtual_w
        self.virtual_h = virtual_h
        
        # Tạo màn hình ảo
        self.virtual_surface = pygame.Surface((self.virtual_w, self.virtual_h))
        
        # Màn hình thật (mặc định mở bằng kích thước ảo)
        self.real_screen = pygame.display.set_mode((self.virtual_w, self.virtual_h), pygame.RESIZABLE)
        
    def get_mouse_pos(self):
        """Chuyển tọa độ chuột thật về tọa độ trong game (600x660)"""
        real_w, real_h = self.real_screen.get_size()
        raw_x, raw_y = pygame.mouse.get_pos()
        
        ratio_w = real_w / self.virtual_w
        ratio_h = real_h / self.virtual_h
        
        return (raw_x / ratio_w, raw_y / ratio_h)

    def toggle_fullscreen(self):
        """Bật/tắt Fullscreen"""
        if self.real_screen.get_flags() & pygame.FULLSCREEN:
            pygame.display.set_mode((self.virtual_w, self.virtual_h), pygame.RESIZABLE)
        else:
            pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

    def render(self):
        """Phóng to màn hình ảo lên màn hình thật và cập nhật hiển thị"""
        real_w, real_h = self.real_screen.get_size()
        # Phóng to toàn bộ màn hình ảo lấp đầy màn hình thật
        scaled_surface = pygame.transform.smoothscale(self.virtual_surface, (real_w, real_h))
        self.real_screen.blit(scaled_surface, (0, 0))
        
        pygame.display.update()
        
def add_sprite_frames(entity):
        entity.sprite_sheet = pygame.image.load(f"game/assets/{entity.type}6.png").convert_alpha()
        sheet_rect = entity.sprite_sheet.get_rect()

        # Sprite sheet: 4 hàng, 5 cột
        entity.frame_w = sheet_rect.width // 5
        entity.frame_h = sheet_rect.height // 4

        # Lưu các frame cho từng hướng
        entity.frames = {
            "up": [],
            "right": [],
            "down": [],
            "left": []
        }

        for row in range(4):
            tmp = []
            for col in range(5):
                rect = pygame.Rect(col * entity.frame_w, row * entity.frame_h, entity.frame_w, entity.frame_h)
                frame = entity.sprite_sheet.subsurface(rect)
                tmp.append(frame)

            if row == 0:
                entity.frames["up"] = tmp
            elif row == 1:
                entity.frames["right"] = tmp
            elif row == 2:
                entity.frames["down"] = tmp
            elif row == 3:
                entity.frames["left"] = tmp
def new_enemy_position(e_row,e_col,p_row,p_col,grid,type):
    new_row,new_col = e_row,e_col
    directions = [('up', -1, 0), ('down', 1, 0), 
                ('left', 0, -1), ('right', 0, 1)]
    if type=="red_mummy":
        directions = [('left', 0, -1), ('right', 0, 1),('up', -1, 0), ('down', 1, 0)]

    best_dist = abs(e_row - p_row) + abs(e_col - p_col)
    cell = grid[e_row][e_col]
    for d in directions:
        if not getattr(cell,d[0]) and 0 <= e_row + d[1] < ROWS and 0 <= e_col + d[2] < COLS:
            new_row = e_row + d[1]
            new_col = e_col + d[2]
            dist = abs(new_row - p_row) + abs(new_col - p_col)
            if dist < best_dist:
                best_dist = dist
                e_row = new_row
                e_col = new_col
                break


    return e_row,e_col


def get_actor_center(actor):
    dx = int(getattr(actor, "render_dx", 0))
    dy = int(getattr(actor, "render_dy", 0))
    x = OFFSET_X + actor.col * CELL_SIZE + CELL_SIZE // 2 + dx
    y = OFFSET_Y + actor.row * CELL_SIZE + CELL_SIZE // 2 + dy
    return x, y


def winning_check(surface, font, player, gamestate):
    if gamestate.gameover:
        return

    if player.row == gamestate.goal_row and player.col == gamestate.goal_col:
        gamestate.gameover = True
        gamestate.result = "win"
        text = font.render("You Win", True, GREEN)
        surface.blit(
            text,
            (
                SCREEN_WIDTH // 2 - text.get_width() // 2,
                SCREEN_HEIGHT // 2 - text.get_height() // 2,
            ),
        )


def losing_check(surface, font, player, enemy, gamestate):
    if gamestate.gameover:
        return

    if player.row == enemy.row and player.col == enemy.col:
        gamestate.gameover = True
        gamestate.result = "lose"

        text = font.render("Game Over", True, RED)
        surface.blit(
            text,
            (
                SCREEN_WIDTH // 2 - text.get_width() // 2,
                SCREEN_HEIGHT // 2 - text.get_height() // 2,
            ),
        )

        image = pygame.image.load("game/assets/whitefight6.png").convert_alpha()
        image = pygame.transform.smoothscale(image, (CELL_SIZE, CELL_SIZE))

        cx, cy = get_actor_center(player)
        rect = image.get_rect(center=(cx, cy))
        surface.blit(image, rect)
        pygame.time.wait(700)

            
            
def path_finding(player, enemy, grid, gamestate):
    """BFS trên state (player_pos, enemy_pos). Trả về list hướng hoặc None."""
    directions = [("up", -1, 0), ("down", 1, 0), ("left", 0, -1), ("right", 0, 1)]

    start = (player.row, player.col, enemy.row, enemy.col)
    q = deque([start])
    visited = [[[[0] * COLS for _ in range(ROWS)] for _ in range(COLS)] for _ in range(ROWS)]
    prev = [[[[(0, 0, 0, 0)] * COLS for _ in range(ROWS)] for _ in range(COLS)] for _ in range(ROWS)]
    visited[player.row][player.col][enemy.row][enemy.col] = 1

    while q:
        p_row, p_col, e_row, e_col = q.popleft()
        cell = grid[p_row][p_col]

        for name, dr, dc in directions:
            if getattr(cell, name):
                continue
            np_r = p_row + dr
            np_c = p_col + dc
            if not (0 <= np_r < ROWS and 0 <= np_c < COLS):
                continue

            ne_r, ne_c = new_enemy_position(e_row, e_col, np_r, np_c, grid, enemy.type)
            if enemy.type != "red_scorpion":
                ne_r, ne_c = new_enemy_position(ne_r, ne_c, np_r, np_c, grid, enemy.type)

            if visited[np_r][np_c][ne_r][ne_c] != 0:
                continue
            if np_r == ne_r and np_c == ne_c:
                continue

            prev[np_r][np_c][ne_r][ne_c] = (p_row, p_col, e_row, e_col)
            visited[np_r][np_c][ne_r][ne_c] = 1
            q.append((np_r, np_c, ne_r, ne_c))

            if np_r == gamestate.goal_row and np_c == gamestate.goal_col:
                path = []
                cur = (np_r, np_c, ne_r, ne_c)
                while cur != start:
                    pr, pc, er, ec = prev[cur[0]][cur[1]][cur[2]][cur[3]]
                    # suy ra bước player
                    for nm, ddr, ddc in directions:
                        if cur[0] == pr + ddr and cur[1] == pc + ddc:
                            path.append(nm)
                            break
                    cur = (pr, pc, er, ec)
                path.reverse()
                return path

    return None


def is_playable(player, enemy, grid, gamestate):
    """Chỉ kiểm tra playable + gán gamestate.solution."""
    path = path_finding(player, enemy, grid, gamestate)
    if path is None:
        return False
    gamestate.solution = path
    return True


def read_map_json(filepath: str):
    """Đọc JSON Option B (chuẩn hoá).

    Schema chuẩn (readable):
      - size: {"rows": R, "cols": C}
      - exit: {"rows": r, "cols": c}  (exit tách riêng để cho phép trùng ô với item/quái)
      - tiles: [R strings length C]
      - walls_v: [R strings length C+1] (| là tường)
      - walls_h: [R+1 strings length C] (- là tường)

    Chuẩn hoá ký tự:
      Tiles (đồ nằm trong ô):
        P player
        W white mummy
        R red mummy
        S scorpion
        K key
        T trap
        . empty
        (E legacy hỗ trợ nhưng không khuyến khích, vì exit đã tách riêng)

      walls_h (tường ngang + gate):
        - wall (chặn)
        . no wall
        = gate closed (chặn)
        ~ gate open (không chặn)
    """
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)

    rows = int(data["size"]["rows"])
    cols = int(data["size"]["cols"])
    tiles = data["tiles"]
    walls_v = data["walls_v"]
    walls_h = data["walls_h"]

    exit_pos = None
    ex = data.get("exit")
    if isinstance(ex, dict):
        er = ex.get("rows", ex.get("row"))
        ec = ex.get("cols", ex.get("col"))
        if er is not None and ec is not None:
            exit_pos = (int(er), int(ec))

    return rows, cols, tiles, walls_v, walls_h, exit_pos

def apply_map_to_grid(rows, cols, tiles, walls_v, walls_h, grid, player, enemy, gamestate, exit_pos=None):
    """Gán tường + entity + items + goal từ map.

    - Exit ưu tiên theo exit_pos (field 'exit' trong JSON).
    - Cho phép exit trùng ô với K/T/quái/player vì exit không nằm trong tiles.
    - Gate được lưu trong walls_h (edge) với ký tự ~/=.
    """
    # reset walls
    for r in range(rows):
        for c in range(cols):
            cell = grid[r][c]
            cell.up = cell.down = cell.left = cell.right = 0

    # init containers in gamestate (để adventure/core dùng được ngay)
    if not hasattr(gamestate, "keys"):
        gamestate.keys = set()
    if not hasattr(gamestate, "traps"):
        gamestate.traps = set()
    if not hasattr(gamestate, "gates_h"):
        # (rh, c) -> True(open) / False(closed), rh in [0..ROWS]
        gamestate.gates_h = {}

    gamestate.keys.clear()
    gamestate.traps.clear()
    gamestate.gates_h.clear()

    # parse gates from walls_h (single source of truth)
    for rh in range(rows + 1):
        line = walls_h[rh]
        for c in range(cols):
            ch = line[c]
            if ch == "~":
                gamestate.gates_h[(rh, c)] = True
                grid[rh - 1][c].down = 2
            elif ch == "=":
                gamestate.gates_h[(rh, c)] = False
                grid[rh - 1][c].down = 3

    # apply walls (walls_v + walls_h with gate semantics)
    for r in range(rows):
        for c in range(cols):   
            cell = grid[r][c]

            # vertical walls: only '|' blocks
            cell.left = 1 if walls_v[r][c] == "|" else 0
            cell.right = 1 if walls_v[r][c + 1] == "|" else 0

            # horizontal walls: '-' or '=' blocks; '.' or '~' open
            up_ch = walls_h[r][c]
            down_ch = walls_h[r + 1][c]
            cell.up = 1 if up_ch in ("-", "=") else 0
            cell.down = 1 if down_ch in ("-", "=") else 0

    # entities + items from tiles (no gate here anymore)
    found_p = False
    found_e = False
    legacy_goal = None

    for r in range(rows):
        line = tiles[r]
        for c in range(cols):
            ch = line[c]

            if ch == "P":
                player.row, player.col = r, c
                found_p = True

            elif ch in ("W", "R", "S"):
                enemy.row, enemy.col = r, c
                enemy.type = {"W": "white_mummy", "R": "red_mummy", "S": "red_scorpion"}[ch]
                found_e = True

            elif ch == "K":
                gamestate.keys.add((r, c))

            elif ch == "T":
                gamestate.traps.add((r, c))

            elif ch == "E":
                # legacy support (không khuyến khích)
                legacy_goal = (r, c)

    # defaults
    if not found_p:
        player.row, player.col = 0, 0
    if not found_e:
        enemy.row, enemy.col = rows - 1, cols - 1
        enemy.type = "white_mummy"

    # goal priority: exit_pos > legacy 'E' > fallback
    if exit_pos is not None:
        gamestate.goal_row, gamestate.goal_col = exit_pos
    elif legacy_goal is not None:
        gamestate.goal_row, gamestate.goal_col = legacy_goal
    else:
        gamestate.goal_row, gamestate.goal_col = rows - 1, cols - 1

    # rebuild enemy sprite if type changed by map
    try:
        enemy.sprite_sheet = pygame.image.load(f"game/assets/{enemy.type}6.png").convert_alpha()
        sheet_rect = enemy.sprite_sheet.get_rect()
        enemy.frame_w = sheet_rect.width // 5
        enemy.frame_h = sheet_rect.height // 4
        enemy.frames = {"up": [], "right": [], "down": [], "left": []}
    except Exception:
        pass

    add_sprite_frames(enemy)

    # reset game state bookkeeping
    gamestate.initpos = (player.row, player.col, enemy.row, enemy.col)
    gamestate.storedmove.clear()
    gamestate.storedmove.append((player.row, player.col, player.direction, enemy.row, enemy.col, enemy.direction))
    gamestate.gameover = False
    gamestate.result = None

def is_not_too_easy(player, enemy, grid,gamestate):#Kiểm tra nếu quái có thể bắt được người chơi
    directions = [('up', -1, 0), ('down', 1, 0), ('left', 0, -1), ('right', 0, 1)]
    visited = [[False] * COLS for _ in range(ROWS)]
    if len(gamestate.solution) < (ROWS + COLS-1):#Quá dễ
        return False
    visited[player.row][player.col] = True
    queue = [(player.row, player.col)]
    while queue:
        curr = queue.pop()
        p_row, p_col = curr
        cell = grid[p_row][p_col]

        for d in directions:
            if not getattr(cell, d[0]) and 0 <= p_row + d[1] < ROWS and 0 <= p_col + d[2] < COLS:
                new_p_row = p_row + d[1]
                new_p_col = p_col + d[2]

                if visited[new_p_row][new_p_col]: continue
                visited[new_p_row][new_p_col] = True
                queue.append((new_p_row, new_p_col))
    
    for r in range(ROWS):
        for c in range(COLS):
            if visited[r][c]==0:
                #print("Some cells are unreachable.")
                return False
    return True


def generate_game(grid,player,enemy,gamestate):
    print("Generating new game...")

    while True:#Generate tường đến khi có đường đi
        for row in grid:
            for cell in row:
                cell.up , cell.down ,cell.left,cell.right = 0,0,0,0
        player.row = random.randint(0, ROWS - 1)
        player.col = random.randint(0, ROWS - 1)  
        while True:
            enemy.row = random.randint(0, ROWS - 1)
            enemy.col = random.randint(0, COLS - 1)
            if not (enemy.row == player.row and player.col == enemy.col):
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
            elif side == 'right':
                gamestate.goal_row = random.randint(0, ROWS - 1)
                gamestate.goal_col = COLS - 1

            # Đảm bảo ô đích không phải là ô bắt đầu của player hoặc enemy
            if (gamestate.goal_row, gamestate.goal_col) != (player.row, player.col) and \
                    (gamestate.goal_row, gamestate.goal_col) != (enemy.row, enemy.col):
                break

        enemy.type=random.choice(["red_mummy","white_mummy","red_scorpion"])
        add_sprite_frames(enemy)
        print(f"Enemy type: {enemy.type}")
        generate_walls(grid, random.randint(ROWS*COLS//4,ROWS*COLS))
        if is_playable(player, enemy, grid,gamestate) and is_not_too_easy(player, enemy, grid,gamestate):
            break
    gamestate.initpos=(player.row,player.col,enemy.row,enemy.col) #Lưu vị trí ban đầu
    gamestate.storedmove.append((player.row,player.col,player.direction,enemy.row,enemy.col,enemy.direction))
    gamestate.gameover = False
    print("New game generated.")
    print(gamestate.solution)
    
def generate_walls(grid, num_walls):#Random generate tường
    directions = [('up', 'down', -1, 0), ('down', 'up', 1, 0), 
            ('left', 'right', 0, -1), ('right', 'left', 0, 1)]
    for _ in range(num_walls):
        no_wall = True
        while (no_wall):
            r = random.randint(1, ROWS - 1)
            c = random.randint(1, COLS - 1)
            d = random.choice(directions)
            wall_cnt=0
            for i in range(0):
                wall_cnt+=getattr(grid[r][c],d[0])
            if 0 <= r + d[2] < ROWS and 0 <= c + d[3] < COLS and not getattr(grid[r][c],d[0]) and wall_cnt<=2:#Tường trong lưới và chưa có
                setattr(grid[r][c],d[0], 1)  
                setattr(grid[r + d[2]][c + d[3]],d[1], 1)  
                no_wall = False
                
    print("Walls generated.")
