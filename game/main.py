import pygame, sys, random
import os, json
import time
from typing import Tuple
from pygame.locals import *
from pathlib import Path

from variable import *
from module import *
from entity import Player, Enemy, Cell
from screen.button import Undobutton, Restartbutton, Newgamebutton, Exitbutton, StartButton, Button
from screen.login import LoginScreen, LeaderboardScreen, RegisterScreen, GuestLoadScreen, SaveDialog
from module.gamestate import Gamestate, load_frames_with_mask
from saveload import *

# Explicit imports for map I/O (single source of truth in module/module.py)
from module.module import read_map_json, apply_map_to_grid

# NEW: import module objects to sync runtime constants after changing difficulty / loading maps
import variable as V
import module.module as module_mod
import entity.entity as entity_mod
import module.gamestate as gamestate_mod

# Snapshot helper (Phase 0/1)
from module.module import make_snapshot


class TextButton:
    def __init__(
        self,
        text: str,
        center_xy: Tuple[int, int],
        font: pygame.font.Font,
        idle_color=(0, 0, 0),
        hover_color=(255, 0, 0),
        min_size=(280, 100),
    ):
        self.text = text
        self.font = font
        self.idle_color = idle_color
        self.hover_color = hover_color

        self._surf_idle = self.font.render(self.text, True, self.idle_color)
        self._surf_hover = self.font.render(self.text, True, self.hover_color)

        w = max(self._surf_idle.get_width(), self._surf_hover.get_width(), min_size[0])
        h = max(self._surf_idle.get_height(), self._surf_hover.get_height(), min_size[1])
        # Click area is 80% of visual size
        click_w = int(w * 0.8)
        click_h = int(h * 0.8)
        self.rect = pygame.Rect(0, 0, click_w, click_h)
        self.rect.center = center_xy

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        hovered = self.rect.collidepoint(mouse_pos)
        surf = self._surf_hover if hovered else self._surf_idle
        surface.blit(surf, surf.get_rect(center=self.rect.center))
        return hovered

    def draw_at(self, surface, new_pos, mouse_pos):
        self.rect.center = new_pos
        self.draw(surface, mouse_pos)

    def is_clicked(self, mouse_pos: tuple[int, int]):
        return self.rect.collidepoint(mouse_pos)


def run_game():
    global menu_y
    pygame.init()
    screen_main = ScreenManager(SCREEN_WIDTH, SCREEN_HEIGHT)

    GAME_DIR = Path(__file__).resolve().parent
    ASSETS_DIR = GAME_DIR / "assets"

    # ===== music loop from open =====
    try:
        pygame.mixer.init(frequency=22050, size=-16, channels=8, buffer=512)
        music_path = ASSETS_DIR / "music" / "game.it"
        pygame.mixer.music.load(str(music_path))
        pygame.mixer.music.play(-1)
        pygame.mixer.music.set_volume(BASE_MUSIC_VOLUME)
    except Exception as ex:
        debug_log("[music] load failed:", ex)

    # runtime objects (sẽ rebuild khi đổi size / load adventure map)
    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
    player = Player()
    enemies: list[Enemy] = []  # Phase 1

    font = pygame.font.SysFont("Verdana", 60)
    menu_font = pygame.font.Font(str(ASSETS_DIR / "font" / "romeo.ttf"), 64)

    start_button = StartButton()
    undobutton = Undobutton()
    restartbutton = Restartbutton()
    newgamebutton = Newgamebutton()
    exitbutton = Exitbutton()

    gamestate = Gamestate()
    gamestate.state = "Home"
    gamestate.mode = "classic"      # "classic" | "adventure"
    gamestate.chapter = 1
    gamestate.level = 1
    progress_mgr = ProgressManager(ASSETS_DIR)

    # User session
    user_session = {
        "username": None,
        "password": None,
        "is_guest": False,
        "score": 0,
        "level_start_time": None,
        "level_start_moves": 0
    }
    
    # Track state transitions for level initialization
    previous_state = None
    
    # State hierarchy tree for navigation
    state_tree = {
        "LOGIN": None,
        "REGISTER": "LOGIN",
        "LEADERBOARD": "LOGIN",
        "GUEST_LOAD": "LOGIN",
        "SELECTION": None,
        "PLAYING": "SELECTION",
    }

    # Save dialog - new class-based implementation
    save_dialog_screen = SaveDialog()
    
    # Old save dialog state (keeping for backward compatibility during transition)
    save_dialog = {
        "active": False,
        "dialog_type": "save_before_exit",
        "mode_to_save": None,
        "pending_state": None,
        "profiles": [],
        "selected_profile": None,
        "message": "",
        "is_guest": False,
        "phase": "confirm",
    }

    # Loading screen state
    loading_state = {
        "active": False,
        "image": None,
        "progress": 0.0,
        "timer": 0.0,
        "generating": False,
        "start_time": 0.0
    }
    
    # Win animation state (player walking to stair)
    win_anim_state = {
        "active": False,
        "target_x": 0.0,
        "target_y": 0.0,
        "start_x": 0.0,
        "start_y": 0.0,
        "progress": 0.0,
        "duration": 0.5,  # seconds
        "pending_state": None,  # "NEXTLEVEL" or "WIN_SCREEN"
    }

    # default classic: size hiện tại (variable default) + generate
    gamestate.enemy_count = 3 if ROWS >= 10 else (2 if ROWS >= 8 else 1)
    generate_game(grid, player, enemies, gamestate)

    start_bg = pygame.image.load(str(ASSETS_DIR / "images" / "bg_start_1.jpg")).convert_alpha()
    start_bg = pygame.transform.smoothscale(start_bg, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    modeSelect_bg = pygame.image.load(str(ASSETS_DIR / "images" / "mode_bg.jpg")).convert_alpha()
    modeSelect_bg = pygame.transform.smoothscale(modeSelect_bg, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    # Loading screen assets
    loading_images = [
        pygame.image.load(str(ASSETS_DIR / "images" / "beach.gif")).convert(),
        pygame.image.load(str(ASSETS_DIR / "images" / "findtreasure.jpg")).convert()
    ]

    # Score font (digits 0-9 in one row)
    score_font_sheet = pygame.image.load(str(ASSETS_DIR / "images" / "scorefont.png")).convert_alpha()
    digit_w = score_font_sheet.get_width() // 10
    digit_h = score_font_sheet.get_height()
    score_digits = [score_font_sheet.subsurface(pygame.Rect(i * digit_w, 0, digit_w, digit_h)).copy() for i in range(10)]

    def render_score(surface, value: int, center_pos: tuple[int, int], scale: float = 1.0):
        """Render numeric score using sprite font."""
        digits = list(str(max(0, value)))
        frames = [score_digits[int(d)] for d in digits]
        w = int(digit_w * scale)
        h = int(digit_h * scale)
        total_w = len(frames) * w
        start_x = center_pos[0] - total_w // 2
        y = center_pos[1] - h // 2
        for i, frame in enumerate(frames):
            surf = pygame.transform.smoothscale(frame, (w, h)) if scale != 1.0 else frame
            surface.blit(surf, (start_x + i * w, y))

    # Save dialog assets
    dialog_bg = pygame.image.load(str(ASSETS_DIR / "images" / "dialog.gif")).convert_alpha()
    dialog_button = pygame.image.load(str(ASSETS_DIR / "images" / "dbutton.jpg")).convert_alpha()
    
    # Scale dialog to fit screen nicely
    dialog_size = min(400, SCREEN_WIDTH // 3)
    dialog_bg = pygame.transform.smoothscale(dialog_bg, (dialog_size, dialog_size))
    
    # Dialog buttons (yes/no)
    button_width = int(dialog_size * 0.8)
    button_height = int(dialog_size * 0.15)
    dialog_button = pygame.transform.smoothscale(dialog_button, (button_width, button_height))

    # Selection screen buttons
    classic_button = TextButton("CLASSIC MODE", (465, 492), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    tutorial_button = TextButton("TUTORIAL", (835, 492), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    adventure_button = TextButton("ADVENTURE", (465, 605), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    quit_button = TextButton("OPTIONS", (835, 605), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    leaderboard_button = TextButton("LEADERBOARD", (650, 720), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    logout_button = TextButton("LOGOUT", (SCREEN_WIDTH * 3 // 4, 720), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))

    # Difficulty screen UI
    choose_diff_text = menu_font.render("CHOOSE DIFFICULTY", True, (0, 0, 0))
    choose_diff_rect = choose_diff_text.get_rect(center=(SCREEN_WIDTH // 2, 420))

    easy_button   = TextButton("Easy",       (SCREEN_WIDTH // 2, 500), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    medium_button = TextButton("Medium",     (SCREEN_WIDTH // 2, 560), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    hard_button   = TextButton("Hard",       (SCREEN_WIDTH // 2, 620), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    impossible_button = TextButton("Impossible", (SCREEN_WIDTH // 2, 680), menu_font, idle_color=(200, 0, 0), hover_color=(255, 100, 0))
    back_button   = TextButton("Back",       (SCREEN_WIDTH // 4, 720), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    continue_button = TextButton("Continue Last Game", (SCREEN_WIDTH * 3 // 4, 720), menu_font, idle_color=(0, 100, 0), hover_color=(0, 200, 0))

    # Login and Leaderboard screens
    login_screen = LoginScreen()
    leaderboard_screen = LeaderboardScreen()
    register_screen = RegisterScreen()
    guest_load_screen = GuestLoadScreen()
    guest_profile_buttons: list[TextButton] = []

    def _refresh_guest_profiles():
        names = list_local_saves(5)
        guest_load_screen.set_profiles(names)

    # Game Over overlay
    lose_bg = pygame.image.load(str(ASSETS_DIR / "images/menufront.png")).convert_alpha()
    lose_bg = pygame.transform.smoothscale(lose_bg, (SCREEN_WIDTH - 100, SCREEN_HEIGHT - 100))

    btn_try_again = TextButton("TRY AGAIN", (360, 630), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    btn_world_map = TextButton("WORLD MAP", (900, 630), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    btn_undo_move = TextButton("UNDO MOVE", (360, 720), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    btn_save_quit = TextButton("SAVE AND QUIT", (900, 720), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    btn_abandon_hope = TextButton("ABANDON HOPE", (630, 630), menu_font, idle_color=(200, 0, 0), hover_color=(255, 100, 0))

    world_map = AdventureWorldMap(ASSETS_DIR, SCREEN_WIDTH, SCREEN_HEIGHT)
    btn_back_map = TextButton("BACK", (234, 680), menu_font, idle_color=(50, 234, 0))
    btn_save_quit_map = TextButton("SAVE AND QUIT", (234, 750), menu_font, idle_color=(50, 234, 0))

    # Auto-play state for solution replay
    auto_play = {
        "enabled": False,
        "solution_idx": 0,
        "move_timer": 0.0,
        "move_delay": 0.5,  # seconds between moves
    }

    img_options = pygame.image.load("game/assets/images/OPTIONS_BUTTON.png").convert_alpha()
    img_options = pygame.transform.smoothscale(img_options, (245, 72))
    options_button = Button(img_options, 110, 216)

    img_done = pygame.image.load("game/assets/images/DONE_BUTTON.png").convert_alpha()
    img_done = pygame.transform.smoothscale(img_done, (180, 54))
    done_button = TextButton("DONE", (650, 500), menu_font, min_size=(270, 90))
    options_panel_bg = pygame.image.load("game/assets/images/OPTIONS_BG.png").convert_alpha()
    options_panel_bg = pygame.transform.smoothscale(options_panel_bg, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    ankh_img = pygame.image.load("game/assets/images/sliderankh.png").convert_alpha()

    s_music = OptionsSlider("Music", 540, 320, 300, 0.5)
    s_sound = OptionsSlider("Sound Fx", 540, 370, 300, 0.7)
    s_speed = OptionsSlider("Speed", 540, 420, 300, 0.0)  # 0.0 = 1x, 1.0 = 5x
    font_path = str(ASSETS_DIR / "font" / "romeo.ttf")
    font_medium = pygame.font.Font(font_path, 32)
    menu_y = SCREEN_HEIGHT
    
    # ===== Arrow sprites for mouse click movement =====
    # Arrows are VERTICAL spritesheets with 4 frames: down, right, left, up (in order)
    arrow_frames = {6: [], 8: [], 10: []}  # Keyed by grid size
    
    def _load_arrow_frames_vertical(color_path, mask_path, frame_count):
        """Load frames from vertical spritesheet with alpha mask."""
        color_sheet = pygame.image.load(color_path).convert_alpha()
        mask_sheet = pygame.image.load(mask_path).convert_alpha()
        
        # Vertical spritesheet: width is frame width, height / frame_count is frame height
        w = color_sheet.get_width()
        h = color_sheet.get_height()
        fh = h // frame_count  # frame height
        
        out_frames = []
        for i in range(frame_count):
            # Slice vertically
            c_frame = color_sheet.subsurface(pygame.Rect(0, i * fh, w, fh)).copy()
            m_frame = mask_sheet.subsurface(pygame.Rect(0, i * fh, w, fh)).copy()
            
            c_frame = c_frame.convert_alpha()
            m_frame = m_frame.convert_alpha()
            
            out = pygame.Surface(c_frame.get_size(), pygame.SRCALPHA, 32)
            out.blit(c_frame, (0, 0))
            
            # Apply mask
            a = pygame.surfarray.array3d(m_frame)[:, :, 0]
            out_a = pygame.surfarray.pixels_alpha(out)
            out_a[:, :] = a
            del out_a
            
            out_frames.append(out)
        
        return out_frames
    
    def _load_arrow_frames():
        """Load arrow sprites for all grid sizes."""
        for size in [6, 8, 10]:
            try:
                color_path = str(ASSETS_DIR / "images" / f"arrows{size}.gif")
                mask_path = str(ASSETS_DIR / "images" / f"_arrows{size}.gif")
                frames = _load_arrow_frames_vertical(color_path, mask_path, 4)
                arrow_frames[size] = frames  # [down, right, left, up]
            except Exception as e:
                debug_log(f"[Arrows] Failed to load arrows{size}: {e}")
                arrow_frames[size] = []
    
    _load_arrow_frames()
    
    def _get_arrow_frame(direction: str):
        """Get arrow frame for current grid size and direction."""
        size = ROWS if ROWS in arrow_frames else 10
        frames = arrow_frames.get(size, [])
        if not frames:
            return None
        # Order in spritesheet: down=0, right=1, left=2, up=3
        idx_map = {"down": 0, "right": 1, "left": 2, "up": 3}
        idx = idx_map.get(direction, 0)
        if idx < len(frames):
            return frames[idx]
        return None
    
    def _get_valid_moves(p_row: int, p_col: int, g: list) -> dict:
        """Return dict of valid move directions with their (row, col) targets."""
        valid = {}
        cell = g[p_row][p_col]
        
        # UP: Check if row > 0 AND cell ABOVE doesn't have wall/gate on its BOTTOM
        if p_row > 0 and g[p_row - 1][p_col].down not in (1, 2):
            valid["up"] = (p_row - 1, p_col)
        
        # DOWN: Check if row < ROWS-1 AND current cell doesn't have wall/gate on its BOTTOM
        if p_row < ROWS - 1 and cell.down not in (1, 2):
            valid["down"] = (p_row + 1, p_col)
        
        # LEFT: Check if current cell has no left wall AND col > 0
        if p_col > 0 and not cell.left:
            valid["left"] = (p_row, p_col - 1)
        
        # RIGHT: Check if current cell has no right wall AND col < COLS-1
        if p_col < COLS - 1 and not cell.right:
            valid["right"] = (p_row, p_col + 1)
        
        return valid
    
    def _mouse_to_grid(mx: int, my: int) -> tuple:
        """Convert mouse screen coordinates to grid (row, col). Returns None if outside grid."""
        grid_x = mx - OFFSET_X
        grid_y = my - OFFSET_Y
        
        col = int(grid_x // CELL_SIZE)
        row = int(grid_y // CELL_SIZE)
        
        if 0 <= row < ROWS and 0 <= col < COLS:
            return (row, col)
        return None

    def _load_floor():
        # floor6.jpg / floor8.jpg / floor10.jpg now under images/
        try:
            img = pygame.image.load(str(ASSETS_DIR / "images" / f"floor{ROWS}.jpg")).convert_alpha()
        except Exception:
            img = pygame.image.load(str(ASSETS_DIR / "images" / "floor10.jpg")).convert_alpha()
        return pygame.transform.smoothscale(img, (int(COLS * CELL_SIZE), int(ROWS * CELL_SIZE)))

    background = _load_floor()

    backdrop = pygame.image.load(str(ASSETS_DIR / "images" / "backdrop_1.png")).convert_alpha()
    backdrop = pygame.transform.smoothscale(backdrop, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    backdrop_s = pygame.image.load(str(ASSETS_DIR / "images" / "backdrop.png")).convert_alpha()
    backdrop_s = pygame.transform.smoothscale(backdrop_s, (X, Y))

    # ===== Next level overlay =====
    nextlevel_img = None
    for p in (
        ASSETS_DIR / "nextlevel.jpg",
        ASSETS_DIR / "images" / "nextlevel.jpg",
        ASSETS_DIR / "screen" / "nextlevel.jpg",
    ):
        if p.exists():
            nextlevel_img = pygame.image.load(str(p)).convert_alpha()
            break
    if nextlevel_img is not None:
        nextlevel_img = pygame.transform.smoothscale(nextlevel_img, (SCREEN_WIDTH - OFFSET_X_1, SCREEN_HEIGHT))

    nextlevel_btn_font = pygame.font.Font(str(ASSETS_DIR / "font" / "romeo.ttf"), 52)
    nextlevel_button = TextButton(
        "Next Level",
        (OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 520),
        nextlevel_btn_font,
        idle_color=(255, 255, 0),
        hover_color=(255, 255, 255),
        min_size=(540, 90),
    )
    
    # Back button for adventure mode NEXTLEVEL screen
    nextlevel_back_button = TextButton(
        "Back to Menu",
        (OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 650),
        nextlevel_btn_font,
        idle_color=(255, 255, 0),
        hover_color=(255, 255, 255),
        min_size=(540, 90),
    )
    
    # Return to Menu button for auto-play completion
    return_menu_button = TextButton(
        "Return to Menu",
        (OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 600),
        nextlevel_btn_font,
        idle_color=(255, 255, 0),
        hover_color=(255, 255, 255),
        min_size=(540, 90),
    )
    
    # Classic mode win screen buttons
    win_newgame_button = TextButton(
        "Play New Game",
        (OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 520),
        nextlevel_btn_font,
        idle_color=(255, 255, 0),
        hover_color=(255, 255, 255),
        min_size=(540, 90),
    )
    
    win_back_button = TextButton(
        "Back",
        (OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 650),
        nextlevel_btn_font,
        idle_color=(255, 255, 0),
        hover_color=(255, 255, 255),
        min_size=(540, 90),
    )

    # Loading screen button (non-functional, just for display)
    loading_button = TextButton(
        "Please wait",
        (0, 0),  # Will be repositioned dynamically
        menu_font,
        idle_color=(0, 0, 0),
        hover_color=(0, 0, 0),  # Same color since it's non-interactive
        min_size=(300, 80),
    )

    # ===== sync constants after changing ROWS/COLS =====
    def _sync_dynamic_vars():
        names = [
            "ROWS", "COLS", "CELL_SIZE",
            "maze_width", "maze_height",
            "stair_padding", "OFFSET_X", "OFFSET_Y", "wall_gap",
        ]
        targets = [globals(), module_mod.__dict__, entity_mod.__dict__, gamestate_mod.__dict__]
        for n in names:
            val = getattr(V, n)
            for t in targets:
                t[n] = val

    def _rebuild_by_size(size: int):
        nonlocal grid, player, enemies, gamestate, background, killed_uids, collision_fx, current_turn, enemy_turn_idx

        V.apply_grid_size(size)
        _sync_dynamic_vars()

        grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
        player = Player()
        # Clear all old enemies and their states
        enemies.clear()
        killed_uids.clear()
        killed_this_turn.clear()
        collision_fx.clear()
        
        # Reset turn state to player's turn
        current_turn = "player"
        enemy_turn_idx = 0
        
        gamestate = Gamestate()
        gamestate.mode = "classic"
        gamestate.state = "PLAYING"
        gamestate.chapter = 1
        gamestate.level = 1

        background = _load_floor()

    def _start_classic(size: int, impossible: bool = False):
        nonlocal gamestate
        _rebuild_by_size(size)
        gamestate.mode = "classic"
        gamestate.state = "PLAYING"
        gamestate.impossible_mode = impossible  # Set after rebuild creates new gamestate

        # Phase 1: enemy count theo difficulty
        if impossible:
            gamestate.enemy_count = 5  # 2 scorpions + 3 random mummies
        elif size <= 6:
            gamestate.enemy_count = 1
        elif size <= 8:
            gamestate.enemy_count = 2
        else:
            gamestate.enemy_count = 3

        generate_game(grid, player, enemies, gamestate)

    def _load_adventure_level(chapter: int, level: int) -> bool:
        """Adventure: load level JSON tại assets/map/level{chapter}-{level}.json."""
        nonlocal grid, player, enemies, gamestate, background, current_turn, enemy_turn_idx

        path = ASSETS_DIR / "map" / f"level{chapter}-{level}.json"
        if not path.exists():
            debug_log("[adventure] missing:", path)
            return False

        try:
            rows, cols, tiles, walls_v, walls_h, exit_pos = read_map_json(str(path))
        except Exception as ex:
            debug_log("[adventure] read_map_json failed:", ex)
            return False

        # validate shapes (defensive)
        if len(tiles) != rows or any(len(s) != cols for s in tiles):
            debug_log("[adventure] tiles shape mismatch")
            return False
        if len(walls_v) != rows or any(len(s) != cols + 1 for s in walls_v):
            debug_log("[adventure] walls_v shape mismatch")
            return False
        if len(walls_h) != rows + 1 or any(len(s) != cols for s in walls_h):
            debug_log("[adventure] walls_h shape mismatch")
            return False

        # rebuild everything to match map size
        V.apply_grid_size(rows)
        _sync_dynamic_vars()

        grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
        player = Player()
        # Clear all old enemies and their states
        enemies.clear()
        killed_uids.clear()
        killed_this_turn.clear()
        collision_fx.clear()
        
        # Reset turn state to player's turn
        current_turn = "player"
        enemy_turn_idx = 0
        
        gamestate = Gamestate()
        gamestate.mode = "adventure"
        gamestate.state = "PLAYING"
        gamestate.chapter = chapter
        gamestate.level = level
        gamestate.gameover = False

        background = _load_floor()

        apply_map_to_grid(rows, cols, tiles, walls_v, walls_h, grid, player, enemies, gamestate, exit_pos=exit_pos)
        return True

    def _advance_level(chapter: int, level: int):
        level += 1
        if level > 15:
            chapter += 1
            level = 1
        if chapter > 3:
            return None
        return chapter, level

    # ===== Save/Load helpers =====
    def _can_continue_classic() -> bool:
        """Check if there is a valid classic save with map_data to continue."""
        username = user_session.get("username")
        if not username:
            return False
        
        save_data = None
        if user_session.get("is_guest"):
            save_data = load_local(username)
        else:
            save_data = load_firebase(username) or load_local(username)
        
        if save_data and save_data.get("classic"):
            map_info = save_data["classic"].get("map_data")
            return map_info is not None
        
        return False

    def _show_save_dialog(mode: str, next_state: str):
        """Show save dialog before transitioning to next_state (for PLAYING state exits)"""
        debug_log(f"[DIALOG] _show_save_dialog called: mode={mode}, next_state={next_state}")
        save_dialog["active"] = True
        save_dialog["dialog_type"] = "save_before_exit"
        save_dialog["mode_to_save"] = mode
        save_dialog["pending_state"] = next_state
        save_dialog["is_guest"] = user_session.get("is_guest", False)
        debug_log(f"[DIALOG] Dialog activated - type: save_before_exit, is_guest: {save_dialog['is_guest']}")
        
        # Configure SaveDialog screen - no profile selection needed, use profile from login
        save_dialog_screen.dialog_type = "save_before_exit"
        save_dialog_screen.phase = "confirm"
        save_dialog_screen.message = "Save progress?"
        save_dialog["profiles"] = []

    def _show_quit_dialog():
        """Show quit dialog with save option"""
        debug_log(f"[DIALOG] _show_quit_dialog called")
        save_dialog["active"] = True
        save_dialog["dialog_type"] = "quit_confirm"
        save_dialog["mode_to_save"] = None
        save_dialog["pending_state"] = None
        save_dialog["is_guest"] = user_session.get("is_guest", False)
        debug_log(f"[DIALOG] Dialog activated - type: quit_confirm, is_guest: {save_dialog['is_guest']}")
        
        # Configure SaveDialog screen - no profile selection needed, use profile from login
        save_dialog_screen.dialog_type = "quit_confirm"
        save_dialog_screen.phase = "confirm"
        save_dialog_screen.message = "Save progress before quitting?"
        save_dialog_screen.profiles = []

    def _show_back_dialog(next_state: str):
        """Show back confirmation dialog (no save)"""
        debug_log(f"[DIALOG] _show_back_dialog called: next_state={next_state}")
        save_dialog["active"] = True
        save_dialog["dialog_type"] = "back_confirm"
        save_dialog["mode_to_save"] = None
        save_dialog["pending_state"] = next_state
        save_dialog["is_guest"] = False
        debug_log(f"[DIALOG] Dialog activated - type: back_confirm")
        
        # Configure SaveDialog screen
        save_dialog_screen.dialog_type = "back_confirm"
        save_dialog_screen.phase = "confirm"
        save_dialog_screen.message = "Go back without saving?"
        save_dialog_screen.profiles = []

    def _perform_save(mode: str, profile: str = None):
        """Save current game state for the specified mode"""
        debug_log(f"[SAVE] _perform_save called: mode={mode}, profile={profile}")
        
        if mode is None:
            debug_log(f"[SAVE] ERROR: mode is None! Cannot save without mode.")
            return False
            
        try:
            # Serialize per mode (classic includes map_data; adventure does not)
            if mode == "classic":
                state, map_data, move_history = serialize_classic(player, enemies, gamestate, grid)
            else:
                state, move_history = serialize_adventure(player, enemies, gamestate, grid)
                map_data = None
            
            # Determine target username/profile
            if user_session.get("is_guest"):
                username = profile or save_dialog.get("selected_profile") or user_session.get("username") or "guest"
            else:
                username = user_session["username"]
            
            debug_log(f"[SAVE] Saving to username: {username}, mode: {mode}, map_data={'yes' if map_data else 'no'}")

            # Load existing save or create new one
            save_data = load_local(username) or (None if user_session.get("is_guest") else load_firebase(username))
            
            if not save_data:
                save_data = create_save_data(
                    username,
                    user_session["password"],
                    user_session["is_guest"],
                    user_session["score"]
                )
            
            # Update the appropriate mode section
            if mode == "adventure":
                save_data["adventure"] = {
                    "game_state": state,
                    "move_history": move_history
                }
            else:  # classic
                save_data["classic"] = {
                    "game_state": state,
                    "map_data": map_data,
                    "move_history": move_history
                }
            
            # Update player info
            save_data["player_info"]["score"] = user_session["score"]
            
            # Save to both local and (if not guest) Firebase
            save_local(username, save_data)
            if not user_session.get("is_guest"):
                save_firebase(username, save_data)
            
            debug_log(f"[SAVE] Save completed successfully for {username}")
            return True
        except Exception as e:
            debug_log(f"[SAVE] Failed to save: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _create_guest_profile_name():
        existing = set(list_local_saves(20))
        for i in range(1, 6):
            cand = f"guest{i}"
            if cand not in existing:
                return cand
        return None

    def _calculate_level_score():
        """Calculate score for completed level"""
        if user_session["level_start_time"] is None:
            return 0
        
        elapsed = time.time() - user_session["level_start_time"]
        minutes = max(0.1, elapsed / 60.0)  # Minimum 0.1 to avoid division by zero
        
        # Determine difficulty for scoring
        if gamestate.impossible_mode:
            difficulty = "impossible"
        elif gamestate.enemy_count == 1:
            difficulty = "easy"
        elif gamestate.enemy_count == 2:
            difficulty = "medium"
        else:
            difficulty = "hard"
        
        actual_moves = len(gamestate.storedmove) - user_session["level_start_moves"]
        solution_len = len(gamestate.solution) if gamestate.solution else actual_moves
        
        return calculate_score(difficulty, minutes, max(1, actual_moves), max(1, solution_len))

    # ===== Phase 1: enemy hooks + collision resolver =====
    # Rule: If an enemy moves into a tile occupied by another enemy that is standing still,
    # then the standing enemy dies. The moving enemy survives.
    killed_uids: set[int] = set()
    killed_this_turn: list[tuple] = []  # Stores (row, col, direction, type) of enemies killed this turn
    collision_fx: list[dict] = []  # dust effects for enemy-enemy collision

    def _ensure_enemy_hooks():
        """
        Attach on_step callback to each enemy for collision detection.
        When a moving enemy enters a tile, check if there's a standing enemy there.
        If yes, mark standing enemy as dead (killed_uids).
        """
        def on_enemy_step(mover: Enemy):
            # mover just committed to new tile (row, col)
            mr, mc = mover.row, mover.col
            
            # Play footstep sound for each step
            if hasattr(mover, 'type') and mover.type:
                if "scorpion" in mover.type:
                    sound = gamestate.sfx.get("scorpwalk")
                else:
                    # Use mummy walk sound based on grid size
                    if ROWS <= 6:
                        sound = gamestate.sfx.get("mumwalk_small")
                    elif ROWS <= 8:
                        sound = gamestate.sfx.get("mumwalk_medium")
                    else:
                        sound = gamestate.sfx.get("mumwalk_large")
                if sound:
                    try:
                        sound.play()
                    except: pass
            
            # Check for collision with other enemies
            for other in enemies:
                if other is mover:
                    continue
                if other.uid in killed_uids:
                    continue
                # "standing still enemy dies when moving enemy enters"
                # Check: same tile AND not moving AND no pending steps
                if (other.row == mr and other.col == mc) and (not other.is_moving) and (not getattr(other, "pending_steps", [])):
                    killed_uids.add(other.uid)
                    # Save the killed enemy's state for undo to restore
                    enemy_state = (other.row, other.col, getattr(other, "direction", "down"), getattr(other, "type", None))
                    killed_this_turn.append(enemy_state)
                    print(f"[COLLISION] Enemy {other.uid} ({other.type}) killed! killed_this_turn now has {len(killed_this_turn)} entries: {killed_this_turn}")
                    # Play a collision sound when an enemy kills another (avoid block.wav)
                    hit_snd = gamestate.sfx.get("mummyhowl")
                    if hit_snd:
                        try:
                            hit_snd.play()
                        except: pass
                    collision_fx.append({
                        "row": mr,
                        "col": mc,
                        "dust_idx": 0,
                        "dust_timer": 0.0,
                        "dust_fps": 20,
                        "timer": 0.0,
                        "duration": 0.6,
                    })
                    break

        # Ensure all enemies have the collision callback
        for e in enemies:
            if getattr(e, "on_step", None) is not on_enemy_step:
                e.on_step = on_enemy_step

    def _actors_idle():
        """Check if all actors (player + enemies) are idle (not moving, no pending actions)."""
        if player.is_moving:
            return False
        for e in enemies:
            # Skip dead enemies
            if e.uid in killed_uids:
                continue
            if e.is_moving:
                return False
            if getattr(e, "pending_steps", []):
                return False
        return True

    # Turn order tracking
    current_turn = "player"  # "player" or enemy index (0, 1, 2, ...)
    enemy_turn_idx = 0
    
    # Track state before OPTIONS (to return to correct state)
    options_return_state = "PLAYING"

    # ===== MAIN LOOP =====
    while True:
        dt = FramePerSec.tick(FPS) / 1000.0
        # Apply game speed multiplier (1x to 5x based on slider)
        game_speed = 1.0 + s_speed.val * 4.0  # s_speed.val 0->1 maps to 1x->5x
        dt *= game_speed

        mouse_pos = screen_main.get_mouse_pos()
        hover_any_button = False

        if gamestate.state == "Home":
            if start_button.rect.collidepoint(mouse_pos):
                hover_any_button = True

        elif gamestate.state == "SELECTION":
            for r in [classic_button, adventure_button, tutorial_button, quit_button, leaderboard_button, logout_button]:
                if r.rect.collidepoint(mouse_pos):
                    hover_any_button = True
                    break

        elif gamestate.state == "DIFFICULTY":
            for r in [easy_button, medium_button, hard_button, impossible_button, back_button]:
                if r.rect.collidepoint(mouse_pos):
                    hover_any_button = True
                    break

        elif gamestate.state == "NEXTLEVEL":
            if nextlevel_button.rect.collidepoint(mouse_pos):
                hover_any_button = True
            elif nextlevel_back_button.rect.collidepoint(mouse_pos):
                hover_any_button = True
        
        elif gamestate.state == "AUTOPLAY_COMPLETE":
            if return_menu_button.rect.collidepoint(mouse_pos):
                hover_any_button = True

        elif gamestate.state == "LOSE_MENU":
            for r in [btn_try_again, btn_undo_move, btn_save_quit, btn_abandon_hope]:
                if r.rect.collidepoint(mouse_pos):
                    hover_any_button = True
                    break

        elif gamestate.state == "WORLD_MAP":
            if btn_save_quit_map.rect.collidepoint(mouse_pos):
                hover_any_button = True
            if btn_back_map.rect.collidepoint(mouse_pos):
                hover_any_button = True

        elif gamestate.state == "OPTIONS":
            if done_button.rect.collidepoint(mouse_pos):
                hover_any_button = True

        pygame.mouse.set_cursor(
            pygame.SYSTEM_CURSOR_HAND if hover_any_button else pygame.SYSTEM_CURSOR_ARROW
        )

        for e in pygame.event.get():
            if e.type == QUIT:
                # Only show save dialog if in an active game state
                if gamestate.state == "PLAYING":
                    _show_save_dialog(gamestate.mode, None)  # None means exit game
                elif gamestate.state == "SELECTION":
                    # From SELECTION, show quit dialog with save option
                    _show_quit_dialog()
                else:
                    # From login/home/other screens, just quit directly
                    pygame.quit()
                    sys.exit()

            if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                if hasattr(screen_main, "toggle_fullscreen"):
                    screen_main.toggle_fullscreen()

            if gamestate.state == "DIFFICULTY":
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    gamestate.state = "SELECTION"

            if gamestate.state == "Home":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.is_clicked(mouse_pos):
                        gamestate.state = "LOGIN"
                        login_screen.reset()

            # Save dialog handling - new class-based implementation
            if save_dialog["active"]:
                if e.type == pygame.MOUSEBUTTONDOWN:
                    button_rects = save_dialog_screen._calculate_button_rects(SCREEN_WIDTH, SCREEN_HEIGHT)
                    clicked = save_dialog_screen.get_clicked(mouse_pos, button_rects)
                    
                    debug_log(f"[DIALOG EVENT] Clicked: {clicked}, Type: {save_dialog['dialog_type']}, Phase: {save_dialog_screen.phase}")
                    
                    if clicked == "yes":
                        if save_dialog["dialog_type"] == "back_confirm":
                            # Back without saving
                            save_dialog["active"] = False
                            save_dialog_screen.phase = "confirm"
                            gamestate.state = save_dialog["pending_state"]
                            previous_state = gamestate.state  # Prevent re-interception
                            break
                        elif save_dialog["dialog_type"] == "quit_confirm":
                            # Save then quit - use profile from login (both guest and account)
                            _perform_save(gamestate.mode if hasattr(gamestate, 'mode') else None)
                            pygame.quit()
                            sys.exit()
                        elif save_dialog["dialog_type"] == "save_before_exit":
                            # Save and transition/exit - use profile from login
                            _perform_save(save_dialog["mode_to_save"])
                            save_dialog["active"] = False
                            save_dialog_screen.phase = "confirm"
                            if save_dialog["pending_state"] is None:
                                # Exit game
                                pygame.quit()
                                sys.exit()
                            else:
                                gamestate.state = save_dialog["pending_state"]
                                previous_state = gamestate.state  # Prevent re-interception
                                break
                    elif clicked == "no":
                        if save_dialog["dialog_type"] == "save_before_exit":
                            # Don't save, just transition or exit
                            save_dialog["active"] = False
                            save_dialog_screen.phase = "confirm"
                            if save_dialog["pending_state"] is None:
                                # Exit game without saving
                                pygame.quit()
                                sys.exit()
                            else:
                                gamestate.state = save_dialog["pending_state"]
                                previous_state = gamestate.state  # Prevent re-interception
                                break
                        elif save_dialog["dialog_type"] == "quit_confirm":
                            # Quit without saving
                            pygame.quit()
                            sys.exit()
                        elif save_dialog["dialog_type"] == "back_confirm":
                            # No - stay in current state
                            save_dialog["active"] = False
                            save_dialog_screen.phase = "confirm"
                    elif clicked == "back":
                        if save_dialog_screen.phase == "select_profile":
                            save_dialog_screen.phase = "confirm"
                    elif clicked and clicked not in ["yes", "no", "back"]:
                        # Profile selected - only process if in select_profile phase
                        if save_dialog_screen.phase == "select_profile":
                            save_dialog_screen.selected_profile = clicked
                            
                            # Perform save with selected profile
                            mode_to_save = save_dialog["mode_to_save"]
                            dialog_type = save_dialog["dialog_type"]
                            pending_state = save_dialog["pending_state"]
                            
                            _perform_save(mode_to_save, clicked)
                            
                            # Close dialog immediately
                            save_dialog["active"] = False
                            save_dialog_screen.phase = "confirm"
                            
                            # Execute action based on dialog type
                            if dialog_type == "quit_confirm":
                                pygame.quit()
                                sys.exit()
                            elif dialog_type == "save_before_exit" and pending_state is None:
                                # save_before_exit with None pending_state means exit game
                                pygame.quit()
                                sys.exit()
                            else:
                                # Transition to target state immediately
                                gamestate.state = pending_state
                                previous_state = gamestate.state  # Prevent re-interception
                                break
                        continue  # Skip if not in correct phase
                    continue  # Skip other state event handling while dialog is active

            elif gamestate.state == "SELECTION":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if classic_button.is_clicked(mouse_pos):
                        # print(f"[Click] classic_button clicked, sfx['click'] = {gamestate.sfx.get('click')}")
                        if gamestate.sfx.get("click") is not None:
                            try:
                                # print("[Click] Playing click sound...")
                                gamestate.sfx["click"].play()
                                # print("[Click] Click sound played successfully")
                            except Exception as ex:
                                pass  # print(f"[Click] Error playing click: {ex}")
                        gamestate.state = "DIFFICULTY"

                    elif adventure_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        
                        # Load adventure progress from save if available
                        username = user_session.get("username")
                        loaded_chapter, loaded_level = 1, 1
                        if username:
                            save_data = None
                            if user_session.get("is_guest"):
                                save_data = load_local(username)
                            else:
                                save_data = load_firebase(username) or load_local(username)
                            
                            if save_data and save_data.get("adventure", {}).get("game_state"):
                                adv_state = save_data["adventure"]["game_state"]
                                loaded_chapter = adv_state.get("chapter", 1)
                                loaded_level = adv_state.get("level", 1)
                        
                        progress_mgr.current_chapter = loaded_chapter
                        progress_mgr.current_level = loaded_level
                        gamestate.chapter = loaded_chapter
                        gamestate.level = loaded_level
                        gamestate.impossible_mode = False  # Adventure mode doesn't use impossible AI
                        ok = _load_adventure_level(progress_mgr.current_chapter, progress_mgr.current_level)
                        if ok:
                            gamestate.mode = "adventure"
                            gamestate.state = "WORLD_MAP"
                            gamestate.gameover = False

                    elif tutorial_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        gamestate.state = "TUTORIAL"

                    elif leaderboard_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Fetch leaderboard from Firebase
                        leaderboard_data = get_leaderboard(10)
                        leaderboard_screen.set_leaderboard(leaderboard_data)
                        gamestate.state = "LEADERBOARD"

                    elif quit_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Open options menu from SELECTION
                        options_return_state = "SELECTION"
                        gamestate.state = "OPTIONS"
                    
                    elif logout_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Clear user session and return to Home page
                        user_session.clear()
                        user_session["is_guest"] = False
                        user_session["username"] = None
                        user_session["password"] = None
                        login_screen.reset()
                        gamestate.state = "Home"

            elif gamestate.state == "LOGIN":
                if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                    action = login_screen.handle_event(e)
                    
                    if action == "login":
                        # Attempt login
                        username, password = login_screen.get_credentials()
                        if username and password:
                            # Verify login against local/Firebase saves
                            if verify_login(username, password):
                                user_session["username"] = username
                                user_session["password"] = password
                                user_session["is_guest"] = False
                                # Load player data from save
                                player_data = load_local(username)
                                if player_data:
                                    user_session["score"] = player_data.get("player_info", {}).get("score", 0)
                                gamestate.state = "SELECTION"
                            else:
                                login_screen.set_error("Invalid username or password")
                        else:
                            login_screen.set_error("Username and password required")
                    
                    # Mouse clicks for buttons
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        button_rects = login_screen._calculate_button_rects(SCREEN_WIDTH, SCREEN_HEIGHT)
                        
                        # Login button
                        if button_rects["login_btn"].collidepoint(mouse_pos):
                            username, password = login_screen.get_credentials()
                            if username and password:
                                if verify_login(username, password):
                                    user_session["username"] = username
                                    user_session["password"] = password
                                    user_session["is_guest"] = False
                                    player_data = load_local(username)
                                    if player_data:
                                        user_session["score"] = player_data.get("player_info", {}).get("score", 0)
                                    gamestate.state = "SELECTION"
                                else:
                                    login_screen.set_error("Invalid username or password")
                            else:
                                login_screen.set_error("Username and password required")
                        
                        # Register button (goes to REGISTER state)
                        elif button_rects["create_btn"].collidepoint(mouse_pos):
                            gamestate.state = "REGISTER"
                            register_screen.reset()
                        
                        # Play as Guest button -> go to guest load screen
                        elif button_rects["guest_btn"].collidepoint(mouse_pos):
                            user_session["username"] = "Guest"
                            user_session["is_guest"] = True
                            user_session["score"] = 0
                            _refresh_guest_profiles()
                            gamestate.state = "GUEST_LOAD"

                        # Load Local Save (guest)
                        elif button_rects.get("load_guest_btn") and button_rects["load_guest_btn"].collidepoint(mouse_pos):
                            user_session["is_guest"] = True
                            _refresh_guest_profiles()
                            gamestate.state = "GUEST_LOAD"

            elif gamestate.state == "REGISTER":
                if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                    action = register_screen.handle_event(e)
                    
                    if action == "register":
                        # Attempt registration
                        username, password, confirm = register_screen.get_credentials()
                        if username and password and confirm:
                            if len(username) < 3:
                                register_screen.set_error("Username must be at least 3 characters")
                            elif len(password) < 4:
                                register_screen.set_error("Password must be at least 4 characters")
                            elif password != confirm:
                                register_screen.set_error("Passwords do not match")
                            else:
                                # Create new account
                                save_data = {
                                    "player_info": {
                                        "username": username,
                                        "password": password,
                                        "score": 0
                                    },
                                    "classic": {},
                                    "adventure": {}
                                }
                                save_local(username, save_data)
                                user_session["username"] = username
                                user_session["password"] = password
                                user_session["is_guest"] = False
                                user_session["score"] = 0
                                gamestate.state = "SELECTION"
                        else:
                            register_screen.set_error("All fields required")
                    
                    # Mouse clicks for buttons
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        button_rects = register_screen._calculate_button_rects(SCREEN_WIDTH, SCREEN_HEIGHT)
                        
                        # Register button
                        if button_rects["register_btn"].collidepoint(mouse_pos):
                            username, password, confirm = register_screen.get_credentials()
                            if username and password and confirm:
                                if len(username) < 3:
                                    register_screen.set_error("Username must be at least 3 characters")
                                elif len(password) < 4:
                                    register_screen.set_error("Password must be at least 4 characters")
                                elif password != confirm:
                                    register_screen.set_error("Passwords do not match")
                                else:
                                    # Create new account
                                    save_data = {
                                        "player_info": {
                                            "username": username,
                                            "password": password,
                                            "score": 0
                                        },
                                        "classic": {},
                                        "adventure": {}
                                    }
                                    save_local(username, save_data)
                                    user_session["username"] = username
                                    user_session["password"] = password
                                    user_session["is_guest"] = False
                                    user_session["score"] = 0
                                    gamestate.state = "SELECTION"
                            else:
                                register_screen.set_error("All fields required")
                        
                        # Back button
                        elif button_rects["back_btn"].collidepoint(mouse_pos):
                            gamestate.state = "LOGIN"
                            login_screen.reset()

            elif gamestate.state == "LEADERBOARD":
                if e.type == pygame.KEYDOWN or e.type == pygame.MOUSEBUTTONDOWN:
                    action = leaderboard_screen.handle_event(e)
                    if action == "back":
                        gamestate.state = "SELECTION"
                    # Mouse click: check back button rect
                    if e.type == pygame.MOUSEBUTTONDOWN:
                        rects = leaderboard_screen._calculate_button_rects(SCREEN_WIDTH, SCREEN_HEIGHT)
                        if rects.get("back_btn") and rects["back_btn"].collidepoint(mouse_pos):
                            debug_log("[LEADERBOARD] Back clicked")
                            gamestate.state = "SELECTION"

            elif gamestate.state == "GUEST_LOAD":
                if e.type == pygame.MOUSEBUTTONDOWN or e.type == pygame.KEYDOWN:
                    action = guest_load_screen.handle_event(e)
                    
                    if action == "back":
                        gamestate.state = "LOGIN"
                        login_screen.reset()
                    elif e.type == pygame.MOUSEBUTTONDOWN:
                        profile_rects = guest_load_screen.draw(surface, SCREEN_WIDTH, SCREEN_HEIGHT)
                        clicked = guest_load_screen.get_clicked_profile(mouse_pos)
                        
                        if clicked == "_new_profile":
                            name = _create_guest_profile_name() or "guest"
                            user_session["username"] = name
                            user_session["password"] = None
                            user_session["is_guest"] = True
                            user_session["score"] = 0
                            gamestate.state = "SELECTION"
                        elif clicked == "_back":
                            gamestate.state = "LOGIN"
                            login_screen.reset()
                        elif clicked and clicked.startswith("_"):
                            pass  # Skip internal keys
                        elif clicked:
                            # Regular profile selected
                            data = load_local(clicked)
                            if data:
                                user_session["username"] = clicked
                                user_session["password"] = None
                                user_session["is_guest"] = True
                                user_session["score"] = data.get("player_info", {}).get("score", 0)
                            gamestate.state = "SELECTION"

            elif gamestate.state == "TUTORIAL":
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    gamestate.state = "SELECTION"
                elif e.type == pygame.MOUSEBUTTONDOWN:
                    gamestate.state = "SELECTION"

            elif gamestate.state == "DIFFICULTY":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if easy_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        _start_classic(6, impossible=False)
                    elif medium_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        _start_classic(8, impossible=False)
                    elif hard_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        _start_classic(10, impossible=False)
                    elif impossible_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        _start_classic(10, impossible=True)  # Same grid size as hard mode
                    elif back_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        gamestate.state = "SELECTION"
                    elif continue_button.is_clicked(mouse_pos) and _can_continue_classic():
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Load last saved classic game
                        username = user_session.get("username")
                        if username:
                            save_data = None
                            if user_session.get("is_guest"):
                                save_data = load_local(username)
                            else:
                                save_data = load_firebase(username) or load_local(username)
                            
                            if save_data and save_data.get("classic"):
                                classic_data = save_data["classic"]
                                map_info = classic_data.get("map_data")
                                game_state_info = classic_data.get("game_state", {})
                                debug_log(f"[CONTINUE][CLASSIC] map_data={'yes' if map_info else 'no'} grid_size={game_state_info.get('grid_size')} diff={game_state_info.get('difficulty')}")
                                
                                if map_info:
                                    # Load map using saved map data
                                    grid_size = map_info.get("size", {}).get("rows", 10)
                                    _rebuild_by_size(grid_size)
                                    
                                    rows = map_info["size"]["rows"]
                                    cols = map_info["size"]["cols"]
                                    tiles = map_info["tiles"]
                                    walls_v = map_info["walls_v"]
                                    walls_h = map_info["walls_h"]
                                    # Handle both old (rows/cols) and new (row/col) format
                                    exit_pos = None
                                    if "exit" in map_info:
                                        exit_info = map_info["exit"]
                                        if "row" in exit_info:
                                            exit_pos = (exit_info["row"], exit_info["col"])
                                        elif "rows" in exit_info:
                                            exit_pos = (exit_info["rows"], exit_info["cols"])
                                    debug_log(f"[CONTINUE][CLASSIC] rows={rows} cols={cols} tiles_len={len(tiles)} vwalls_len={len(walls_v)} hwalls_len={len(walls_h)} exit_pos={exit_pos}")
                                    
                                    apply_map_to_grid(rows, cols, tiles, walls_v, walls_h, grid, player, enemies, gamestate, exit_pos)
                                elif game_state_info:
                                    # Fallback: use game state to recreate the game (less accurate but works)
                                    grid_size = game_state_info.get("grid_size", 10)
                                    _rebuild_by_size(grid_size)
                                    gamestate.mode = "classic"
                                    gamestate.impossible_mode = game_state_info.get("impossible_mode", False)
                                    gamestate.enemy_count = 3 if gamestate.impossible_mode else (1 if game_state_info.get("difficulty") == "easy" else (2 if game_state_info.get("difficulty") == "medium" else 3))
                                    generate_game(grid, player, enemies, gamestate)
                                    debug_log(f"[CONTINUE][CLASSIC] Fallback regenerate grid_size={grid_size} enemies={gamestate.enemy_count} impossible={gamestate.impossible_mode}")
                                else:
                                    gamestate.state = "SELECTION"
                                    return
                                
                                # Restore game state
                                gamestate.mode = "classic"
                                gamestate.impossible_mode = game_state_info.get("impossible_mode", False)
                                gamestate.state = "PLAYING"
                                gamestate.gameover = False
                                
                                # Generate solution for the loaded map
                                from module.module import is_playable
                                is_playable(player, enemies, grid, gamestate)

            elif gamestate.state == "NEXTLEVEL":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if nextlevel_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        if gamestate.mode == "adventure":
                            progress_mgr.current_chapter = gamestate.chapter
                            progress_mgr.current_level = gamestate.level
                            status = progress_mgr.update_progress()

                            if status == "FINISH_GAME":
                                gamestate.state = "SELECTION"
                                gamestate.mode = "classic"
                            else:
                                gamestate.chapter = progress_mgr.current_chapter
                                gamestate.level = progress_mgr.current_level
                                ok = _load_adventure_level(gamestate.chapter, gamestate.level)
                                gamestate.state = "PLAYING" if ok else "SELECTION"
                        else:
                            nxt = _advance_level(gamestate.chapter, gamestate.level)
                            if nxt is None:
                                gamestate.state = "SELECTION"
                                gamestate.mode = "classic"
                            else:
                                ch, lv = nxt
                                ok = _load_adventure_level(ch, lv)
                                gamestate.state = "PLAYING" if ok else "SELECTION"
                    elif nextlevel_back_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Save adventure progress before going back
                        _perform_save(gamestate.mode)
                        gamestate.state = "SELECTION"
                        gamestate.mode = "classic"
                        gamestate.gameover = False
            
            elif gamestate.state == "AUTOPLAY_COMPLETE":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if return_menu_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Save progress before going back
                        _perform_save(gamestate.mode)
                        gamestate.state = "SELECTION"
                        gamestate.mode = "classic"
                        gamestate.gameover = False
            
            elif gamestate.state == "WIN_SCREEN":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if win_newgame_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Start loading screen
                        loading_state["active"] = True
                        loading_state["image"] = random.choice(loading_images)
                        loading_state["progress"] = 0.0
                        loading_state["timer"] = 0.0
                        loading_state["generating"] = False
                        loading_state["start_time"] = pygame.time.get_ticks() / 1000.0
                        # Will generate in update loop
                        killed_uids.clear()
                        killed_this_turn.clear()
                        collision_fx.clear()
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.state = "PLAYING"
                        gamestate.gameover = False

            elif gamestate.state == "PLAYING":
                if e.type == MOUSEBUTTONDOWN and options_button.is_clicked(e):
                    options_return_state = "PLAYING"
                    gamestate.state = "OPTIONS"

                # INPUT chỉ khi player turn và tất cả idle (Phase 1)
                # AUTO-PLAY: disable manual input if auto-play is active
                if (e.type == KEYDOWN) and (not gamestate.gameover) and (e.key in ALLOWED_BUTTON) and (not auto_play["enabled"]):
                    if current_turn == "player" and _actors_idle():
                        moved = player.move(e.key, grid)
                        if moved:
                            # Play player footstep sound based on grid size
                            if ROWS <= 6:
                                sound = gamestate.sfx.get("expwalk_small")
                            elif ROWS <= 8:
                                sound = gamestate.sfx.get("expwalk_medium")
                            else:
                                sound = gamestate.sfx.get("expwalk_large")
                            if sound:
                                try:
                                    sound.play()
                                except: pass
                            # Phase 3: Check for key/trap interactions
                            check_special_tiles(player, grid, gamestate)
                            if gamestate.state != "DEATH_ANIM":
                                # Check for collision with enemies after player moves
                                losing_check(None, None, player, enemies, gamestate)
                            if gamestate.state != "DEATH_ANIM":
                                gamestate.pending_snapshot = True
                                _ensure_enemy_hooks()
                                # Move to first enemy turn
                                current_turn = 0
                                enemy_turn_idx = 0

                if e.type == MOUSEBUTTONDOWN:
                    # Check mouse click movement (only when player's turn and all idle)
                    if current_turn == "player" and _actors_idle() and not gamestate.gameover and not auto_play["enabled"]:
                        clicked_grid = _mouse_to_grid(mouse_pos[0], mouse_pos[1])
                        if clicked_grid:
                            click_row, click_col = clicked_grid
                            # Check if clicked on player (skip turn)
                            if click_row == player.row and click_col == player.col:
                                moved = player.move(K_SPACE, grid)
                                if moved:
                                    check_special_tiles(player, grid, gamestate)
                                    if gamestate.state != "DEATH_ANIM":
                                        losing_check(None, None, player, enemies, gamestate)
                                    if gamestate.state != "DEATH_ANIM":
                                        gamestate.pending_snapshot = True
                                        _ensure_enemy_hooks()
                                        current_turn = 0
                                        enemy_turn_idx = 0
                            else:
                                # Check if clicked on valid adjacent cell
                                valid_moves = _get_valid_moves(player.row, player.col, grid)
                                for direction, (target_row, target_col) in valid_moves.items():
                                    if click_row == target_row and click_col == target_col:
                                        # Map direction to key
                                        key_map = {"up": K_UP, "down": K_DOWN, "left": K_LEFT, "right": K_RIGHT}
                                        move_key = key_map[direction]
                                        moved = player.move(move_key, grid)
                                        if moved:
                                            # Play footstep sound
                                            if ROWS <= 6:
                                                sound = gamestate.sfx.get("expwalk_small")
                                            elif ROWS <= 8:
                                                sound = gamestate.sfx.get("expwalk_medium")
                                            else:
                                                sound = gamestate.sfx.get("expwalk_large")
                                            if sound:
                                                try:
                                                    sound.play()
                                                except: pass
                                            check_special_tiles(player, grid, gamestate)
                                            if gamestate.state != "DEATH_ANIM":
                                                losing_check(None, None, player, enemies, gamestate)
                                            if gamestate.state != "DEATH_ANIM":
                                                gamestate.pending_snapshot = True
                                                _ensure_enemy_hooks()
                                                current_turn = 0
                                                enemy_turn_idx = 0
                                        break
                    
                    # Check undo button - only allow when all actors are idle
                    if undobutton.is_clicked(e.pos) and _actors_idle():
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        undobutton.undo_move(e, player, enemies, gamestate, grid)
                        # Clear killed_uids to ensure restored enemies aren't filtered out
                        killed_uids.clear()
                        killed_this_turn.clear()
                        collision_fx.clear()
                        # Reset turn to player's turn after undo
                        current_turn = "player"
                        enemy_turn_idx = 0
                    # Check restart button
                    elif restartbutton.is_clicked(e.pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        restartbutton.restart_game(e, player, enemies, gamestate, grid)
                        killed_uids.clear()  # Respawn all dead enemies
                        killed_this_turn.clear()
                        collision_fx.clear()  # Clear collision effects
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.state = "PLAYING"
                        # Reset level timer on restart
                        user_session["level_start_time"] = time.time()
                        user_session["level_start_moves"] = len(gamestate.storedmove)
                    # Check new game button
                    elif gamestate.mode != "adventure" and newgamebutton.is_clicked(e.pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Start loading screen
                        loading_state["active"] = True
                        loading_state["image"] = random.choice(loading_images)
                        loading_state["progress"] = 0.0
                        loading_state["timer"] = 0.0
                        loading_state["generating"] = False
                        loading_state["start_time"] = pygame.time.get_ticks() / 1000.0
                    # Check exit button
                    elif exitbutton.is_clicked(e.pos):
                        debug_log(f"[PLAYING] EXIT button clicked, mode: {gamestate.mode}")
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        # Show save dialog before exiting - save current mode, then go to SELECTION
                        target_state = "SELECTION"
                        _show_save_dialog(gamestate.mode, target_state)

            elif gamestate.state == "DEATH_ANIM":
                # Lock input during death animation
                pass

            elif gamestate.state == "OPTIONS":
                s_music.handle_event(e, mouse_pos)
                s_sound.handle_event(e, mouse_pos)
                s_speed.handle_event(e, mouse_pos)
                pygame.mixer.music.set_volume(s_music.val)

                if e.type == pygame.MOUSEBUTTONDOWN and done_button.is_clicked(mouse_pos):
                    gamestate.state = options_return_state
                elif e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    gamestate.state = options_return_state

            elif gamestate.state == "LOSE_MENU":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    dy = menu_y - target_y
                    # Create adjusted mouse position for buttons drawn with offset
                    adjusted_mouse_pos = (mouse_pos[0], mouse_pos[1] - dy)
                    
                    if btn_try_again.is_clicked(adjusted_mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        if gamestate.mode == "adventure":
                            _load_adventure_level(gamestate.chapter, gamestate.level)
                        else:
                            restartbutton.restart_game(e, player, enemies, gamestate, grid)
                        killed_uids.clear()
                        killed_this_turn.clear()
                        collision_fx.clear()
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.state = "PLAYING"
                        gamestate.gameover = False
                        gamestate.death_state = None
                        menu_y = SCREEN_HEIGHT
                        # Reset level timer on retry
                        user_session["level_start_time"] = time.time()
                        user_session["level_start_moves"] = len(gamestate.storedmove)
                    elif btn_undo_move.is_clicked(adjusted_mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                                # print("[Click] Undo button clicked")
                            except Exception as ex:
                                pass  # print(f"[Click] Undo sound error: {ex}")
                        undobutton.undo_move(e, player, enemies, gamestate, grid)
                        killed_uids.clear()
                        killed_this_turn.clear()
                        collision_fx.clear()
                        menu_y = SCREEN_HEIGHT
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.state = "PLAYING"
                        gamestate.gameover = False
                        gamestate.death_state = None
                        player.update(0)
                        for en in enemies:
                            en.update(0)
                    elif btn_abandon_hope.is_clicked(adjusted_mouse_pos):
                        # Available in both modes; functional in both
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        if gamestate.solution:
                            # Reset to initial position
                            if gamestate.initpos:
                                from module.module import apply_snapshot
                                apply_snapshot(gamestate.initpos, player, enemies, grid, gamestate)
                                # print(f"[AutoPlay] Starting with {len(gamestate.solution)} moves")
                            # Start auto-play
                            auto_play["enabled"] = True
                            auto_play["solution_idx"] = 0
                            auto_play["move_timer"] = 0.0
                            # Set to AUTOPLAY state
                            current_turn = "player"
                            enemy_turn_idx = 0
                            killed_uids.clear()  # Reset dead enemies
                            killed_this_turn.clear()
                            collision_fx.clear()  # Clear collision effects
                            gamestate.state = "AUTOPLAY"
                            gamestate.gameover = False
                            menu_y = SCREEN_HEIGHT
                        else:
                            pass
                            # print("[AutoPlay] No solution available")
                    elif btn_save_quit.is_clicked(adjusted_mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        pygame.quit()
                        sys.exit()

            elif gamestate.state == "WORLD_MAP":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    chapter_selected = world_map.get_clicked_chapter(mouse_pos, progress_mgr)
                    if chapter_selected:
                        gamestate.chapter = chapter_selected
                        if chapter_selected < progress_mgr.current_chapter:
                            gamestate.level = 1
                        else:
                            gamestate.level = progress_mgr.current_level

                        progress_mgr.current_chapter = gamestate.chapter
                        progress_mgr.current_level = gamestate.level

                        _load_adventure_level(gamestate.chapter, gamestate.level)
                        gamestate.state = "PLAYING"
                        gamestate.gameover = False

                    if btn_back_map.is_clicked(mouse_pos):
                        # Save adventure progress before going back to menu
                        _perform_save(gamestate.mode)
                        gamestate.state = "SELECTION"

        # ===== Track state transitions for level initialization =====
        if gamestate.state != previous_state:
            if gamestate.state == "PLAYING" and previous_state != "PLAYING":
                # Entering PLAYING state: initialize level timer
                user_session["level_start_time"] = time.time()
                user_session["level_start_moves"] = len(gamestate.storedmove) if gamestate.storedmove else 0
            previous_state = gamestate.state

        # ===== update actors =====
        if gamestate.state == "PLAYING" and (not gamestate.gameover):
            _ensure_enemy_hooks()

            # If a trap death requested an immediate snapshot, do it now
            if getattr(gamestate, "_force_snapshot_now", False):
                gamestate.storedmove.append(make_snapshot(player, enemies, gamestate, killed_this_turn, killed_uids))
                try:
                    delattr(gamestate, "_force_snapshot_now")
                except Exception:
                    gamestate._force_snapshot_now = False

            player.update(dt)
            for en in enemies:
                # Skip updating dead enemies
                if en.uid not in killed_uids:
                    en.update(dt)

            # Handle enemy turns sequentially
            if current_turn != "player" and _actors_idle():
                # All previous actors idle, execute current enemy turn
                if current_turn < len(enemies):
                    en = enemies[current_turn]
                    # Skip dead enemies during turn processing
                    if en.uid in killed_uids:
                        print(f"[TURN] Skipping dead enemy {current_turn} (uid={en.uid})")
                        current_turn += 1
                    else:
                        print(f"[TURN] Enemy {current_turn} ({en.type}) moving...")
                        en.move(player, grid, gamestate)
                        # Check collision after this enemy moves
                        if gamestate.state != "DEATH_ANIM":
                            losing_check(None, None, player, enemies, gamestate)
                        # Move to next enemy or back to player
                        current_turn += 1
                else:
                    # All enemies done, wait for all animations to finish then back to player
                    if _actors_idle():
                        print(f"[TURN] All enemies done, back to player")
                        current_turn = "player"

            # Append snapshot when turn fully settled - only when it's player's turn again
            # This ensures all enemies have moved before we snapshot
            if getattr(gamestate, "pending_snapshot", False) and current_turn == "player" and _actors_idle():
                snapshot = make_snapshot(player, enemies, gamestate, killed_this_turn, killed_uids)
                gamestate.storedmove.append(snapshot)
                gamestate.pending_snapshot = False
                
                # DEBUG: Print snapshot info
                enemies_in_snap = snapshot[3] if len(snapshot) > 3 else []
                killed_in_snap = snapshot[6] if len(snapshot) > 6 else []
                print(f"[SNAPSHOT] Added snapshot #{len(gamestate.storedmove)}: player=({snapshot[0]},{snapshot[1]}), enemies={len(enemies_in_snap)}, killed_this_turn={len(killed_in_snap)}")
                print(f"  killed_uids={killed_uids}, killed_this_turn={killed_this_turn}")

                # Remove dead enemies from list AFTER taking snapshot (only when turn is complete)
                if killed_uids:
                    enemies[:] = [en for en in enemies if en.uid not in killed_uids]
                    killed_uids.clear()
                    killed_this_turn.clear()

            # Update enemy-enemy collision dust effects
            if gamestate.dust_frames:
                alive_fx = []
                for fx in collision_fx:
                    fx["timer"] += dt
                    fx["dust_timer"] += dt
                    step = 1.0 / fx.get("dust_fps", 20)
                    while fx["dust_timer"] >= step:
                        fx["dust_timer"] -= step
                        fx["dust_idx"] = min(fx["dust_idx"] + 1, len(gamestate.dust_frames) - 1)
                    if fx["timer"] < fx.get("duration", 0.6):
                        alive_fx.append(fx)
                collision_fx[:] = alive_fx

        elif gamestate.state == "DEATH_ANIM":
            finished = update_death_anim(dt, gamestate)
            if finished:
                gamestate.state = "LOSE_MENU"
                gamestate.gameover = True

        elif gamestate.state == "WIN_ANIM":
            # Update win animation - player walks toward stair
            win_anim_state["progress"] += dt / win_anim_state["duration"]
            
            # Update player animation
            player.update(dt)
            
            if win_anim_state["progress"] >= 1.0:
                win_anim_state["progress"] = 1.0
                win_anim_state["active"] = False
                # Save progress when level is completed
                _perform_save(gamestate.mode)
                # Transition to win screen
                gamestate.state = win_anim_state["pending_state"]

        elif gamestate.state == "AUTOPLAY":
            # Auto-play state: game has restarted and is replaying solution
            _ensure_enemy_hooks()
            
            player.update(dt)
            for en in enemies:
                # Skip updating dead enemies
                if en.uid not in killed_uids:
                    en.update(dt)

            # Handle enemy turns sequentially
            if current_turn != "player" and _actors_idle():
                # All previous actors idle, execute current enemy turn
                if current_turn < len(enemies):
                    en = enemies[current_turn]
                    if en.uid not in killed_uids:
                        en.move(player, grid, gamestate)
                        # Check collision after this enemy moves
                        if gamestate.state != "DEATH_ANIM":
                            losing_check(None, None, player, enemies, gamestate)
                        if gamestate.state == "DEATH_ANIM":
                            auto_play["enabled"] = False
                            return
                    if _actors_idle():
                        if current_turn >= len(enemies):
                            current_turn = len(enemies)
                    current_turn += 1
                else:
                    # All enemies done, wait for all animations to finish then back to player
                    if _actors_idle():
                        current_turn = "player"
            
            # AUTO-PLAY: Execute next move from solution only when it's player turn and all idle
            if auto_play["enabled"] and current_turn == "player" and _actors_idle():
                auto_play["move_timer"] += dt
                if auto_play["move_timer"] >= auto_play["move_delay"]:
                    auto_play["move_timer"] = 0.0
                    if auto_play["solution_idx"] < len(gamestate.solution):
                        move_dir = gamestate.solution[auto_play["solution_idx"]]
                        # print(f"[AutoPlay] Step {auto_play['solution_idx'] + 1}/{len(gamestate.solution)}: {move_dir}")
                        # Convert direction string to key code
                        key_map = {
                            "up": pygame.K_UP,
                            "down": pygame.K_DOWN,
                            "left": pygame.K_LEFT,
                            "right": pygame.K_RIGHT,
                        }
                        if move_dir in key_map:
                            moved = player.move(key_map[move_dir], grid)
                            if moved:
                                # Play player footstep sound
                                if ROWS <= 6:
                                    sound = gamestate.sfx.get("expwalk_small")
                                elif ROWS <= 8:
                                    sound = gamestate.sfx.get("expwalk_medium")
                                else:
                                    sound = gamestate.sfx.get("expwalk_large")
                                if sound:
                                    try:
                                        sound.play()
                                    except: pass
                                check_special_tiles(player, grid, gamestate)
                                if gamestate.state != "DEATH_ANIM":
                                    # Check for collision with enemies after player moves
                                    losing_check(None, None, player, enemies, gamestate)
                                if gamestate.state != "DEATH_ANIM":
                                    _ensure_enemy_hooks()
                                    # Move to first enemy turn
                                    current_turn = 0
                                    enemy_turn_idx = 0
                                else:
                                    # Death during autoplay, stop
                                    auto_play["enabled"] = False
                                    return
                        auto_play["solution_idx"] += 1
                    else:
                        # Solution finished
                        # print(f"[AutoPlay] Solution completed! Player at ({player.row}, {player.col})")
                        auto_play["enabled"] = False
                        # Reset to a fresh state after autoplay
                        if gamestate.initpos:
                            apply_snapshot(gamestate.initpos, player, enemies, grid, gamestate)
                        killed_uids.clear()
                        killed_this_turn.clear()
                        collision_fx.clear()
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.gameover = False
                        gamestate.state = "AUTOPLAY_COMPLETE"

            # apply enemy-vs-enemy kills after updates
            if killed_uids:
                enemies[:] = [en for en in enemies if en.uid not in killed_uids]
                killed_uids.clear()
                killed_this_turn.clear()

            # Update enemy-enemy collision dust effects
            if gamestate.dust_frames:
                alive_fx = []
                for fx in collision_fx:
                    fx["timer"] += dt
                    fx["dust_timer"] += dt
                    step = 1.0 / fx.get("dust_fps", 20)
                    while fx["dust_timer"] >= step:
                        fx["dust_timer"] -= step
                        fx["dust_idx"] = min(fx["dust_idx"] + 1, len(gamestate.dust_frames) - 1)
                    if fx["timer"] < fx.get("duration", 0.6):
                        alive_fx.append(fx)
                collision_fx[:] = alive_fx
            
            # Win check during auto-play
            if (player.row == gamestate.goal_row and player.col == gamestate.goal_col):
                gamestate.gameover = True
                gamestate.state = "AUTOPLAY_COMPLETE"
                auto_play["enabled"] = False
                # Fresh reset after autoplay goal
                if gamestate.initpos:
                    apply_snapshot(gamestate.initpos, player, enemies, grid, gamestate)
                killed_uids.clear()
                killed_this_turn.clear()
                collision_fx.clear()
                current_turn = "player"
                enemy_turn_idx = 0
                gamestate.gameover = False
                # print("[AutoPlay] Goal reached during auto-play!")

        # Win detection (skip if loading screen is active - new game being generated)
        if gamestate.state == "PLAYING" and (not gamestate.gameover) and (not loading_state["active"]):
            if player.row == gamestate.goal_row and player.col == gamestate.goal_col:
                gamestate.gameover = True
                
                # Calculate and add score for completed level
                level_score = _calculate_level_score()
                user_session["score"] += level_score
                
                # Play win sound
                if gamestate.sfx.get("finishedlevel") is not None:
                    try:
                        gamestate.sfx["finishedlevel"].play()
                    except: pass
                
                # Start win animation - player walks to stair
                # Calculate stair target position based on direction
                goal_x = OFFSET_X + gamestate.goal_col * CELL_SIZE
                goal_y = OFFSET_Y + gamestate.goal_row * CELL_SIZE
                
                # Determine stair direction and target position
                if gamestate.goal_row == 0:
                    # Stair is up
                    stair_target_x = goal_x + CELL_SIZE / 2
                    stair_target_y = goal_y - CELL_SIZE / 2 + stair_padding
                    player.direction = "up"
                elif gamestate.goal_row == ROWS - 1:
                    # Stair is down
                    stair_target_x = goal_x + CELL_SIZE / 2
                    stair_target_y = goal_y + CELL_SIZE + CELL_SIZE / 2 - stair_padding
                    player.direction = "down"
                elif gamestate.goal_col == 0:
                    # Stair is left
                    stair_target_x = goal_x - CELL_SIZE / 2 + stair_padding
                    stair_target_y = goal_y + CELL_SIZE / 2
                    player.direction = "left"
                else:
                    # Stair is right
                    stair_target_x = goal_x + CELL_SIZE + CELL_SIZE / 2 - stair_padding
                    stair_target_y = goal_y + CELL_SIZE / 2
                    player.direction = "right"
                
                # Setup win animation
                win_anim_state["active"] = True
                win_anim_state["start_x"] = goal_x + CELL_SIZE / 2
                win_anim_state["start_y"] = goal_y + CELL_SIZE / 2
                win_anim_state["target_x"] = stair_target_x
                win_anim_state["target_y"] = stair_target_y
                win_anim_state["progress"] = 0.0
                win_anim_state["pending_state"] = "NEXTLEVEL" if gamestate.mode == "adventure" else "WIN_SCREEN"
                
                # Play walk animation
                player.play_animation("move", speed=0.1, loop=False, reset=True)
                
                gamestate.state = "WIN_ANIM"

        # ===== render =====
        surface = screen_main.virtual_surface

        if gamestate.state == "Home":
            surface.blit(start_bg, (0, 0))
            start_button.draw(surface)
            if start_button.rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (255, 255, 0), start_button.rect, 2)

        elif gamestate.state == "LOGIN":
            surface.blit(start_bg, (0, 0))
            login_screen.draw(surface, SCREEN_WIDTH, SCREEN_HEIGHT)

        elif gamestate.state == "REGISTER":
            surface.blit(start_bg, (0, 0))
            register_screen.draw(surface, SCREEN_WIDTH, SCREEN_HEIGHT)

        elif gamestate.state == "LEADERBOARD":
            surface.blit(start_bg, (0, 0))
            leaderboard_screen.draw(surface, SCREEN_WIDTH, SCREEN_HEIGHT)

        elif gamestate.state == "GUEST_LOAD":
            guest_load_screen.draw(surface, SCREEN_WIDTH, SCREEN_HEIGHT)

        elif gamestate.state == "SELECTION":
            surface.blit(modeSelect_bg, (0, 0))
            classic_button.draw(surface, mouse_pos)
            tutorial_button.draw(surface, mouse_pos)
            adventure_button.draw(surface, mouse_pos)
            quit_button.draw(surface, mouse_pos)
            leaderboard_button.draw(surface, mouse_pos)
            logout_button.draw(surface, mouse_pos)

        elif gamestate.state == "DIFFICULTY":
            surface.blit(modeSelect_bg, (0, 0))
            surface.blit(choose_diff_text, choose_diff_rect)
            easy_button.draw(surface, mouse_pos)
            medium_button.draw(surface, mouse_pos)
            hard_button.draw(surface, mouse_pos)
            impossible_button.draw(surface, mouse_pos)
            back_button.draw(surface, mouse_pos)
            # Only show continue button if valid map_data exists
            if _can_continue_classic():
                continue_button.draw(surface, mouse_pos)

        elif gamestate.state == "TUTORIAL":
            # Simple text-only tutorial screen
            surface.blit(modeSelect_bg, (0, 0))
            
            # Semi-transparent overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
            overlay.set_alpha(200)
            overlay.fill((20, 20, 40))
            surface.blit(overlay, (0, 0))
            
            tutorial_font = pygame.font.SysFont("Verdana", 28)
            title_font = pygame.font.SysFont("Verdana", 48, bold=True)
            
            # Title
            title = title_font.render("HOW TO PLAY", True, (255, 200, 100))
            title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
            surface.blit(title, title_rect)
            
            # Tutorial text
            tutorial_lines = [
                "",
                "CONTROLS:",
                "  Arrow Keys / WASD - Move the explorer",
                "  SPACE - Skip your turn (stay in place)",
                "  ESC - Open options / Go back",
                "",
                "OBJECTIVE:",
                "  Reach the exit staircase to complete the level",
                "  Avoid mummies and scorpions!",
                "",
                "RULES:",
                "  - You move first, then enemies move",
                "  - Mummies move 2 steps per turn (vertical first)",
                "  - Scorpions move 1 step per turn (horizontal first)",
                "  - Lure enemies into walls or each other to defeat them",
                "  - Collect keys to open gates",
                "",
                "BUTTONS:",
                "  UNDO - Go back one move",
                "  RESTART - Reset the current level",
                "  NEW GAME - Generate a new random level (Classic mode)",
                "",
                "Click anywhere or press ESC to go back"
            ]
            
            y_offset = 130
            for line in tutorial_lines:
                if line.startswith("CONTROLS:") or line.startswith("OBJECTIVE:") or line.startswith("RULES:") or line.startswith("BUTTONS:"):
                    color = (255, 200, 100)  # Yellow for headers
                else:
                    color = (220, 220, 220)  # White for content
                text = tutorial_font.render(line, True, color)
                surface.blit(text, (100, y_offset))
                y_offset += 32

        elif gamestate.state == "NEXTLEVEL":
            # Adventure mode level complete screen (similar to classic WIN_SCREEN)
            if nextlevel_img is not None:
                surface.blit(nextlevel_img, (OFFSET_X_1, 0))
            else:
                surface.blit(modeSelect_bg, (0, 0))
            
            # Draw "Level Complete!" text
            win_text = nextlevel_btn_font.render("Level Complete!", True, (255, 255, 0))
            win_rect = win_text.get_rect(center=(OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 300))
            surface.blit(win_text, win_rect)
            
            # Display level score using sprite font, centered
            render_score(surface, user_session.get("score", 0), (OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, SCREEN_HEIGHT // 2), scale=1.4)
            
            nextlevel_button.draw(surface, mouse_pos)
            nextlevel_back_button.draw(surface, mouse_pos)
        
        elif gamestate.state == "WIN_SCREEN":
            # Classic mode win screen
            if nextlevel_img is not None:
                surface.blit(nextlevel_img, (OFFSET_X_1, 0))
            else:
                surface.blit(modeSelect_bg, (0, 0))
            
            # Draw "You Win!" text
            win_text = nextlevel_btn_font.render("You Win!", True, (255, 255, 0))
            win_rect = win_text.get_rect(center=(OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 300))
            surface.blit(win_text, win_rect)
            
            # Display level score using sprite font, centered on win image
            render_score(surface, user_session.get("score", 0), (OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, SCREEN_HEIGHT // 2), scale=1.4)
            
            win_newgame_button.draw(surface, mouse_pos)
        
        elif gamestate.state == "AUTOPLAY_COMPLETE":
            # Show completion screen with same background as NEXTLEVEL
            if nextlevel_img is not None:
                surface.blit(nextlevel_img, (OFFSET_X_1, 0))
            else:
                surface.blit(modeSelect_bg, (0, 0))
            # Draw "Auto-Play Complete!" text
            complete_text = nextlevel_btn_font.render("Auto-Play Complete!", True, (255, 255, 0))
            complete_rect = complete_text.get_rect(center=(OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 300))
            surface.blit(complete_text, complete_rect)
            return_menu_button.draw(surface, mouse_pos)

        elif gamestate.state in ("PLAYING", "DEATH_ANIM", "AUTOPLAY", "WIN_ANIM"):
            surface.blit(backdrop, (0, 0))
            surface.blit(backdrop_s, (OFFSET_X_1, OFFSET_Y_1))
            surface.blit(background, (OFFSET_X, OFFSET_Y))

            if gamestate.mode == "adventure":
                progress_mgr.draw_sidebar_map(surface, 93, 478)
            options_button.draw(surface)

            death_active = gamestate.state == "DEATH_ANIM" and getattr(gamestate, "death_state", None)
            death_cause = gamestate.death_state.get("cause") if death_active else None
            death_pos = (gamestate.death_state.get("row"), gamestate.death_state.get("col")) if death_active else (-1, -1)

            # Top-down, row-based rendering: walls (DOWN/LEFT) have priority
            # Build enemy lookup for quick access
            pos_to_enemy = {}
            for en in enemies:
                if en.uid not in killed_uids:
                    pos_to_enemy[(en.row, en.col)] = en
            
            # Track which gates have been drawn (to avoid duplicate)
            drawn_gates = set()
            
            # Draw row by row from top to bottom
            for row in grid:
                for cell in row:
                    # 1. Draw floor/background first
                    x = OFFSET_X + cell.col * CELL_SIZE
                    y = OFFSET_Y + cell.row * CELL_SIZE
                    
                    # 2. Draw keys in this cell
                    if (cell.row, cell.col) in gamestate.keys:
                        if gamestate.key_frames:
                            try:
                                factor = CELL_SIZE / 60
                                frame = gamestate.key_frames[gamestate.key_anim_idx]
                                if hasattr(pygame.transform, "smoothscale_by"):
                                    frame = pygame.transform.smoothscale_by(frame, factor)
                                else:
                                    w, h = frame.get_size()
                                    frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                                kx = x + CELL_SIZE / 2 - frame.get_width() / 2
                                ky = y + CELL_SIZE / 2 - frame.get_height() / 2
                                surface.blit(frame, (kx, ky))
                            except: pass
                    
                    # 3. Draw traps in this cell (skip if death anim owns this trap)
                    if (cell.row, cell.col) in gamestate.traps:
                        if death_active and death_cause == "trap" and (cell.row, cell.col) == death_pos:
                            pass
                        elif gamestate.trap_frames:
                            try:
                                factor = CELL_SIZE / 60
                                frame = gamestate.trap_frames[0]
                                if hasattr(pygame.transform, "smoothscale_by"):
                                    frame = pygame.transform.smoothscale_by(frame, factor)
                                else:
                                    w, h = frame.get_size()
                                    frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                                tx = x + CELL_SIZE / 2 - frame.get_width() / 2
                                ty = y + CELL_SIZE / 2 - frame.get_height() / 2
                                surface.blit(frame, (tx, ty))
                            except: pass
                    
                    # 4. Check if entity is in this cell
                    entity_in_cell = None
                    if not gamestate.gameover or gamestate.state == "WIN_ANIM":
                        if cell.row == player.row and cell.col == player.col:
                            entity_in_cell = player
                        else:
                            entity_in_cell = pos_to_enemy.get((cell.row, cell.col), None)
                        if death_active and (cell.row, cell.col) == death_pos:
                            entity_in_cell = None
                    
                    # 5. Gate render moved to same priority as walls (after entity)
                    
                    # 6. Draw entity
                    if entity_in_cell:
                        if entity_in_cell is player and gamestate.state == "WIN_ANIM" and win_anim_state["active"]:
                            # Draw player at interpolated position during win animation
                            progress = win_anim_state["progress"]
                            interp_x = win_anim_state["start_x"] + (win_anim_state["target_x"] - win_anim_state["start_x"]) * progress
                            interp_y = win_anim_state["start_y"] + (win_anim_state["target_y"] - win_anim_state["start_y"]) * progress
                            
                            # Get player frame
                            if player.animation_container:
                                anim_name = player.animation_container[0]["name"]
                                seq = player.anim_sequences[anim_name]
                                frame_idx = seq[player.anim_idx]
                            else:
                                frame_idx = 0
                            frame = player._scale_frame(player.frames[player.direction][frame_idx])
                            rect = frame.get_rect(center=(int(interp_x), int(interp_y)))
                            surface.blit(frame, rect)
                        else:
                            entity_in_cell.draw(surface)
                    
                    # 7. Draw walls
                    cell.draw(surface, grid)
                    # 7b. Draw gate for this cell at the same priority as walls
                    if gamestate.gate_frames:
                        rh = cell.row + 1
                        c = cell.col
                        gate_pos = (rh, c)
                        if gate_pos in gamestate.gates_h:
                            drawn_gates.add(gate_pos)
                            is_open = gamestate.gates_h[gate_pos]
                            if gate_pos not in gamestate.gate_anim_state:
                                gamestate.gate_anim_state[gate_pos] = {
                                    "frame": 0 if not is_open else 7,
                                    "time": 0.0,
                                    "is_closing": False
                                }
                            state = gamestate.gate_anim_state[gate_pos]
                            try:
                                factor = CELL_SIZE / 60
                                frame = gamestate.gate_frames[state["frame"]]
                                if hasattr(pygame.transform, "smoothscale_by"):
                                    frame = pygame.transform.smoothscale_by(frame, factor)
                                else:
                                    w, h = frame.get_size()
                                    frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                                gx = OFFSET_X + c * CELL_SIZE
                                gy = OFFSET_Y + (rh - 1) * CELL_SIZE + CELL_SIZE - wall_gap
                                surface.blit(frame, (gx, gy))
                            except: pass
            
            # Remaining gates pass removed; gates are drawn per cell with walls
            
            # ===== Draw movement arrows around player =====
            # Only show when it's player's turn, all actors idle, game not over, and not auto-playing
            if current_turn == "player" and _actors_idle() and not gamestate.gameover and not auto_play["enabled"] and not loading_state["active"]:
                valid_moves = _get_valid_moves(player.row, player.col, grid)
                player_cx = OFFSET_X + player.col * CELL_SIZE + CELL_SIZE / 2
                player_cy = OFFSET_Y + player.row * CELL_SIZE + CELL_SIZE / 2
                
                for direction, (target_row, target_col) in valid_moves.items():
                    arrow_frame = _get_arrow_frame(direction)
                    if arrow_frame:
                        # Scale arrow smaller than cell (60% of cell size)
                        target_size = CELL_SIZE * 0.6
                        factor = target_size / arrow_frame.get_width()
                        if hasattr(pygame.transform, "smoothscale_by"):
                            scaled_arrow = pygame.transform.smoothscale_by(arrow_frame, factor)
                        else:
                            w, h = arrow_frame.get_size()
                            scaled_arrow = pygame.transform.smoothscale(arrow_frame, (int(w * factor), int(h * factor)))
                        
                        # Position arrow between player and target cell
                        aw, ah = scaled_arrow.get_width(), scaled_arrow.get_height()
                        offset = CELL_SIZE * 0.75  # Distance from player center
                        
                        if direction == "up":
                            ax = player_cx - aw / 2
                            ay = player_cy - offset - ah / 2
                        elif direction == "down":
                            ax = player_cx - aw / 2
                            ay = player_cy + offset - ah / 2
                        elif direction == "left":
                            ax = player_cx - offset - aw / 2
                            ay = player_cy - ah / 2
                        elif direction == "right":
                            ax = player_cx + offset - aw / 2
                            ay = player_cy - ah / 2
                        
                        surface.blit(scaled_arrow, (ax, ay))
            
            # Update gate animations
            if gamestate.gate_frames:
                for gate_pos, is_open in gamestate.gates_h.items():
                    if gate_pos in gamestate.gate_anim_state:
                        state = gamestate.gate_anim_state[gate_pos]
                        if is_open and state["frame"] < 7 and not state["is_closing"]:
                            state["time"] += dt
                            if state["time"] >= 0.08:
                                state["time"] -= 0.08
                                state["frame"] = min(state["frame"] + 1, 7)
                        elif not is_open and state["frame"] > 0 and state["is_closing"]:
                            state["time"] += dt
                            if state["time"] >= 0.08:
                                state["time"] -= 0.08
                                state["frame"] = max(state["frame"] - 1, 0)
                        if is_open and state["frame"] == 7:
                            state["is_closing"] = False
                        elif not is_open and state["frame"] == 0:
                            state["is_closing"] = True
            
            # Update key animation
            if gamestate.key_frames:
                gamestate.key_anim_timer += dt
                if gamestate.key_anim_timer >= 0.05:
                    gamestate.key_anim_timer -= 0.05
                    gamestate.key_anim_idx = (gamestate.key_anim_idx + 1) % len(gamestate.key_frames)

            # Update loading screen progress
            if loading_state["active"]:
                loading_state["timer"] += dt
                current_time = pygame.time.get_ticks() / 1000.0
                elapsed_time = current_time - loading_state["start_time"]
                
                # Randomly increment progress every 0.05-0.15 seconds
                if loading_state["timer"] >= random.uniform(0.05, 0.15):
                    loading_state["timer"] = 0.0
                    if loading_state["progress"] < 0.95:  # Don't fill completely until generation done
                        loading_state["progress"] += random.uniform(0.05, 0.15)
                
                # Start actual generation after a brief visual delay
                if not loading_state["generating"] and loading_state["progress"] > 0.1:
                    loading_state["generating"] = True
                    # Perform the actual generation
                    newgamebutton.newgame_game(None, grid, player, enemies, gamestate)
                    killed_uids.clear()
                    killed_this_turn.clear()
                    collision_fx.clear()
                    # Mark as complete
                    loading_state["progress"] = 1.0
                
                # Clear loading screen only after 2 seconds minimum AND generation complete
                if loading_state["progress"] >= 1.0 and loading_state["generating"] and elapsed_time >= 2.0:
                    loading_state["active"] = False
                    loading_state["generating"] = False

            # Death overlay: trap or fight sequence
            if death_active:
                dr, dc = death_pos
                x = OFFSET_X + dc * CELL_SIZE
                y = OFFSET_Y + dr * CELL_SIZE
                factor = CELL_SIZE / 60

                if death_cause == "trap":
                    # Floor dark mask
                    if gamestate.floor_dark_frames:
                        try:
                            frame = gamestate.floor_dark_frames[0]
                            if hasattr(pygame.transform, "smoothscale_by"):
                                frame = pygame.transform.smoothscale_by(frame, factor)
                            else:
                                w, h = frame.get_size()
                                frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                            surface.blit(frame, (x, y))
                        except: pass

                    # Trap sliding to the right
                    slide_progress = 0.0
                    if gamestate.death_state["stage"] == "slide":
                        slide_progress = min(1.0, gamestate.death_state["timer"] / gamestate.death_state["slide_dur"])
                    else:
                        slide_progress = 1.0
                    trap_dx = slide_progress * (CELL_SIZE * 0.6)
                    if gamestate.trap_frames:
                        try:
                            frame = gamestate.trap_frames[0]
                            if hasattr(pygame.transform, "smoothscale_by"):
                                frame = pygame.transform.smoothscale_by(frame, factor)
                            else:
                                w, h = frame.get_size()
                                frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                            tx = x + CELL_SIZE / 2 - frame.get_width() / 2 + trap_dx
                            ty = y + CELL_SIZE / 2 - frame.get_height() / 2
                            surface.blit(frame, (tx, ty))
                        except: pass

                    # Expfall animation (player falls)
                    if gamestate.expfall_frames and gamestate.death_state["stage"] in ("fall", "done"):
                        try:
                            idx = min(gamestate.death_state.get("exp_idx", 0), len(gamestate.expfall_frames) - 1)
                            frame = gamestate.expfall_frames[idx]
                            if hasattr(pygame.transform, "smoothscale_by"):
                                frame = pygame.transform.smoothscale_by(frame, factor)
                            else:
                                w, h = frame.get_size()
                                frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                            fx = x + CELL_SIZE / 2 - frame.get_width() / 2
                            fy = y + CELL_SIZE / 2 - frame.get_height() / 2
                            surface.blit(frame, (fx, fy))
                        except: pass

                elif death_cause == "block":
                    stage = gamestate.death_state.get("stage")
                    # Stage-specific render: freakout first, then block drop
                    if stage == "freakout":
                        try:
                            if gamestate.freakout_frames:
                                idx = min(gamestate.death_state.get("freak_idx", 0), len(gamestate.freakout_frames) - 1)
                                frame = gamestate.freakout_frames[idx]
                                if hasattr(pygame.transform, "smoothscale_by"):
                                    frame = pygame.transform.smoothscale_by(frame, factor)
                                else:
                                    w, h = frame.get_size()
                                    frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                                fx = x + CELL_SIZE / 2 - frame.get_width() / 2
                                fy = y + CELL_SIZE / 2 - frame.get_height() / 2
                                surface.blit(frame, (fx, fy))
                        except: pass
                    else:
                        # drop or done
                        try:
                            # Falling block above the player
                            if gamestate.block_frames:
                                bidx = min(gamestate.death_state.get("block_idx", 0), len(gamestate.block_frames) - 1)
                                bframe = gamestate.block_frames[bidx]
                                if hasattr(pygame.transform, "smoothscale_by"):
                                    bframe = pygame.transform.smoothscale_by(bframe, factor)
                                else:
                                    w, h = bframe.get_size()
                                    bframe = pygame.transform.smoothscale(bframe, (int(w * factor), int(h * factor)))
                                # Compute vertical drop
                                drop_dur = gamestate.death_state.get("drop_dur", 0.8)
                                progress = min(1.0, gamestate.death_state.get("timer", 0.0) / drop_dur)
                                offset = gamestate.death_state.get("drop_offset", CELL_SIZE * 1.5)
                                by = y - offset * (1.0 - progress)
                                bx = x + CELL_SIZE / 2 - bframe.get_width() / 2
                                surface.blit(bframe, (bx, by))
                        except: pass

                else:
                    # Dust first for red/white (skip for stung)
                    if death_cause != "stung" and gamestate.dust_frames:
                        try:
                            idx = min(gamestate.death_state.get("dust_idx", 0), len(gamestate.dust_frames) - 1)
                            frame = gamestate.dust_frames[idx]
                            if hasattr(pygame.transform, "smoothscale_by"):
                                frame = pygame.transform.smoothscale_by(frame, factor)
                            else:
                                w, h = frame.get_size()
                                frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                            fx = x + CELL_SIZE / 2 - frame.get_width() / 2
                            fy = y + CELL_SIZE / 2 - frame.get_height() / 2
                            surface.blit(frame, (fx, fy))
                        except: pass

                    # Fight frame after dust
                    if gamestate.death_state.get("stage") in ("fight", "done"):
                        fight_frames = None
                        if death_cause == "red":
                            fight_frames = gamestate.red_fight_frames
                        elif death_cause == "white":
                            fight_frames = gamestate.white_fight_frames
                        elif death_cause == "stung":
                            fight_frames = gamestate.stung_frames
                        if fight_frames:
                            try:
                                idx = min(gamestate.death_state.get("fight_idx", 0), len(fight_frames) - 1)
                                frame = fight_frames[idx]
                                if hasattr(pygame.transform, "smoothscale_by"):
                                    frame = pygame.transform.smoothscale_by(frame, factor)
                                else:
                                    w, h = frame.get_size()
                                    frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                                fx = x + CELL_SIZE / 2 - frame.get_width() / 2
                                fy = y + CELL_SIZE / 2 - frame.get_height() / 2
                                surface.blit(frame, (fx, fy))
                            except: pass

            # Enemy-enemy collision dust overlay
            if collision_fx and gamestate.dust_frames:
                factor = CELL_SIZE / 60
                for fx in collision_fx:
                    try:
                        idx = min(fx.get("dust_idx", 0), len(gamestate.dust_frames) - 1)
                        frame = gamestate.dust_frames[idx]
                        if hasattr(pygame.transform, "smoothscale_by"):
                            frame = pygame.transform.smoothscale_by(frame, factor)
                        else:
                            w, h = frame.get_size()
                            frame = pygame.transform.smoothscale(frame, (int(w * factor), int(h * factor)))
                        fx_x = OFFSET_X + fx["col"] * CELL_SIZE + CELL_SIZE / 2 - frame.get_width() / 2
                        fx_y = OFFSET_Y + fx["row"] * CELL_SIZE + CELL_SIZE / 2 - frame.get_height() / 2
                        surface.blit(frame, (fx_x, fx_y))
                    except: pass

            undobutton.draw(surface)
            restartbutton.draw(surface)
            if gamestate.mode != "adventure":
                newgamebutton.draw(surface)
            exitbutton.draw(surface)

            gamestate.draw_stairs(surface)
            losing_check(surface, font, player, enemies, gamestate)
            winning_check(surface, font, player, gamestate)
            
            # Render loading screen overlay
            if loading_state["active"]:
                # Use backdrop_s position and size (X, Y at OFFSET_X_1, OFFSET_Y_1)
                backdrop_width = int(X)
                backdrop_height = int(Y)
                backdrop_x = int(OFFSET_X_1)
                backdrop_y = int(OFFSET_Y_1)
                
                # Scale and draw loading image to match backdrop exactly
                scaled_img = pygame.transform.smoothscale(loading_state["image"], (backdrop_width, backdrop_height))
                surface.blit(scaled_img, (backdrop_x, backdrop_y))
                
                # Draw "Please wait" button near bottom of image
                button_y = backdrop_y + backdrop_height - 100  # 100 pixels from bottom
                button_x = backdrop_x + backdrop_width // 2
                loading_button.draw_at(surface, (button_x, button_y), mouse_pos)

        elif gamestate.state == "LOSE_MENU":
            if menu_y > target_y:
                menu_y -= slide_speed
                if menu_y < target_y:
                    menu_y = target_y

            surface.blit(lose_bg, (100, menu_y))
            dy = menu_y - target_y
            btn_try_again.draw_at(surface, (360, 630 + dy), mouse_pos)
            btn_undo_move.draw_at(surface, (360, 720 + dy), mouse_pos)
            btn_save_quit.draw_at(surface, (900, 720 + dy), mouse_pos)
            # Show abandon hope in both modes (disabled in classic via click handling)
            btn_abandon_hope.draw_at(surface, (900, 630 + dy), mouse_pos)

        elif gamestate.state == "WORLD_MAP":
            world_map.draw(surface, progress_mgr, mouse_pos)
            btn_back_map.draw(surface, mouse_pos)

        elif gamestate.state == "OPTIONS":
            surface.blit(options_panel_bg, (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4))
            s_music.draw(surface, font_medium, ankh_img)
            s_sound.draw(surface, font_medium, ankh_img)
            s_speed.draw(surface, font_medium, ankh_img)
            done_button.draw(surface, mouse_pos)

        # Render save dialog overlay (on top of everything) - using new SaveDialog class
        if save_dialog["active"]:
            save_dialog_screen.draw(surface, SCREEN_WIDTH, SCREEN_HEIGHT, mouse_pos)

        screen_main.render()


if __name__ == "__main__":
    run_game()
