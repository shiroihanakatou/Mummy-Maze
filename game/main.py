import pygame, sys, random
import os, json
from pygame.locals import *
from pathlib import Path

from variable import *
from module import *
from entity import Player, Enemy, Cell
from screen.button import Undobutton, Restartbutton, Newgamebutton, Exitbutton, StartButton, Button
from module.gamestate import Gamestate

# NEW: import module objects to sync runtime constants after changing difficulty / loading maps
import variable as V
import module.module as module_mod
import entity.entity as entity_mod
import module.gamestate as gamestate_mod


class TextButton:
    def __init__(
        self,
        text: str,
        center_xy: tuple[int, int],
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
        self.rect = pygame.Rect(0, 0, w, h)
        self.rect.center = center_xy

    def draw(self, surface: pygame.Surface, mouse_pos: tuple[int, int]):
        hovered = self.rect.collidepoint(mouse_pos)
        surf = self._surf_hover if hovered else self._surf_idle
        surface.blit(surf, surf.get_rect(center=self.rect.center))
        return hovered

    def is_clicked(self, mouse_pos: tuple[int, int]):
        return self.rect.collidepoint(mouse_pos)


def run_game():
    pygame.init()
    screen_main = ScreenManager(SCREEN_WIDTH, SCREEN_HEIGHT)

    # ===== music loop from open =====
    try:
        pygame.mixer.init()
        music_path = os.path.join("game", "assets", "music", "game.it")
        pygame.mixer.music.load(music_path)
        pygame.mixer.music.play(-1)
    except Exception as ex:
        print("[music] load failed:", ex)

    # runtime objects (sẽ rebuild khi đổi size / load adventure map)
    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
    player = Player()
    enemy = Enemy()

    font = pygame.font.SysFont("Verdana", 60)
    menu_font = pygame.font.Font("game/assets/font/romeo.ttf", 64)

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

    generate_game(grid, player, enemy, gamestate)

    start_bg = pygame.image.load("game/assets/screen/bg_start_1.jpg").convert_alpha()
    start_bg = pygame.transform.smoothscale(start_bg, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    modeSelect_bg = pygame.image.load("game/assets/screen/mode_bg.jpg").convert()
    modeSelect_bg = pygame.transform.smoothscale(modeSelect_bg, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    # Selection screen buttons
    classic_button = TextButton("CLASSIC MODE", (465, 492), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    tutorial_button = TextButton("TUTORIAL", (835, 492), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    adventure_button = TextButton("ADVENTURE", (465, 605), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    quit_button = TextButton("QUIT GAME", (835, 605), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))

    # Difficulty screen UI (the "old" layout you sent)
    choose_diff_text = menu_font.render("CHOOSE DIFFICULTY", True, (0, 0, 0))
    choose_diff_rect = choose_diff_text.get_rect(center=(SCREEN_WIDTH // 2, 450))

    easy_button   = TextButton("Easy",   (SCREEN_WIDTH // 2, 550), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    medium_button = TextButton("Medium", (SCREEN_WIDTH // 2, 620), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    hard_button   = TextButton("Hard",   (SCREEN_WIDTH // 2, 690), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    back_button   = TextButton("Back",   (SCREEN_WIDTH // 4 * 3, 720), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))

    def _load_floor():
        # floor6.jpg / floor8.jpg / floor10.jpg
        try:
            img = pygame.image.load(f"game/assets/floor{ROWS}.jpg").convert()
        except Exception:
            img = pygame.image.load("game/assets/floor10.jpg").convert()
        return pygame.transform.smoothscale(img, (int(COLS * CELL_SIZE), int(ROWS * CELL_SIZE)))

    background = _load_floor()

    backdrop = pygame.image.load("game/assets/backdrop_1.png").convert()
    backdrop = pygame.transform.smoothscale(backdrop, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    backdrop_s = pygame.image.load("game/assets/backdrop.png").convert()
    backdrop_s = pygame.transform.smoothscale(backdrop_s, (X, Y))

    # ===== Next level overlay =====

    nextlevel_img = pygame.image.load("game/assets/images/nextlevel.jpg").convert()


    nextlevel_img = pygame.transform.smoothscale(nextlevel_img, (SCREEN_WIDTH-OFFSET_X_1, SCREEN_HEIGHT))

    nextlevel_btn_font = pygame.font.Font("game/assets/font/romeo.ttf", 52)
    nextlevel_button = TextButton(
        "ENTER THE NEXT CHAMBER",
        (OFFSET_X_1+(SCREEN_WIDTH-OFFSET_X_1) // 2, 600),
        nextlevel_btn_font,
        idle_color=(255, 255, 0),
        hover_color=(255, 255, 255),
        min_size=(540, 90),
    )
    nextlevel_selection_button = TextButton(
        "RETURN TO MODE SELECTION",
        (OFFSET_X_1+(SCREEN_WIDTH-OFFSET_X_1) // 2, 650),
        nextlevel_btn_font,
        idle_color=(255, 255, 0),
        hover_color=(255, 255, 255),
        min_size=(540, 90),
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
        nonlocal grid, player, enemy, gamestate, background

        V.apply_grid_size(size)   # must exist in variable.py
        _sync_dynamic_vars()

        grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
        player = Player()
        enemy = Enemy()
        gamestate = Gamestate()
        gamestate.mode = "classic"
        gamestate.state = "PLAYING"
        gamestate.chapter = 1
        gamestate.level = 1

        background = _load_floor()

    def _start_classic(size: int):
        nonlocal gamestate
        _rebuild_by_size(size)
        gamestate.mode = "classic"
        gamestate.state = "PLAYING"
        generate_game(grid, player, enemy, gamestate)

    def _level_json_path(chapter: int, level: int) -> str:
        return os.path.join("game", "assets", "map", f"level{chapter}-{level}.json")

    def _apply_walls_from_option_b(grid, walls_v, walls_h):
        # walls_v: rows strings, each length cols+1 (| = wall)
        # walls_h: rows+1 strings, each length cols (- = wall)
        for r in range(ROWS):
            for c in range(COLS):
                cell = grid[r][c]
                cell.left  = 1 if walls_v[r][c] == "|" else 0
                cell.right = 1 if walls_v[r][c + 1] == "|" else 0
                cell.up    = 1 if walls_h[r][c] == "-" else 0
                cell.down  = 1 if walls_h[r + 1][c] == "-" else 0

    def _load_adventure_level(chapter: int, level: int) -> bool:
        """Load JSON Option B from game/assets/map/level{chapter}-{level}.json.
        Returns True if loaded, else False.
        """
        nonlocal grid, player, enemy, gamestate, background

        path = _level_json_path(chapter, level)
        if not os.path.exists(path):
            print("[adventure] missing:", path)
            return False

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as ex:
            print("[adventure] json load failed:", ex)
            return False

        size = data.get("size") or {}
        rows = int(size.get("rows", 10))
        cols = int(size.get("cols", 10))

        if rows != cols:
            print("[adventure] only square maps supported right now:", rows, cols)
            return False
        if rows not in (6, 8, 10):
            print("[adventure] size must be 6/8/10 for now:", rows)
            return False

        # rebuild everything to match map size
        V.apply_grid_size(rows)
        _sync_dynamic_vars()

        grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
        player = Player()
        enemy = Enemy()
        gamestate = Gamestate()
        gamestate.mode = "adventure"
        gamestate.state = "PLAYING"
        gamestate.chapter = chapter
        gamestate.level = level
        gamestate.gameover = False

        background = _load_floor()

        tiles = data.get("tiles") or []
        walls_v = data.get("walls_v") or []
        walls_h = data.get("walls_h") or []

        # validate basic shape
        if len(tiles) != ROWS:
            print("[adventure] tiles rows mismatch")
            return False
        if len(walls_v) != ROWS or any(len(s) != COLS + 1 for s in walls_v):
            print("[adventure] walls_v shape mismatch")
            return False
        if len(walls_h) != ROWS + 1 or any(len(s) != COLS for s in walls_h):
            print("[adventure] walls_h shape mismatch")
            return False

        _apply_walls_from_option_b(grid, walls_v, walls_h)

        # parse tiles: place P, enemy (W/R/S), and exit E
        found_enemy = False
        found_exit = False
        for r in range(ROWS):
            row_str = tiles[r]
            if len(row_str) != COLS:
                print("[adventure] tiles cols mismatch")
                return False
            for c in range(COLS):
                ch = row_str[c]
                if ch == "P":
                    player.row, player.col = r, c
                elif ch in ("W", "R", "S"):
                    if not found_enemy:
                        enemy.row, enemy.col = r, c
                        enemy.type = {"W": "white_mummy", "R": "red_mummy", "S": "red_scorpion"}[ch]
                        enemy.frames = {"up": [], "right": [], "down": [], "left": []}
                        add_sprite_frames(enemy)
                        found_enemy = True
                elif ch == "E":
                    gamestate.goal_row, gamestate.goal_col = r, c
                    found_exit = True

        if not found_exit:
            # fallback: default goal
            gamestate.goal_row, gamestate.goal_col = ROWS - 1, COLS - 1

        gamestate.initpos = (player.row, player.col, enemy.row, enemy.col)
        gamestate.storedmove.clear()
        gamestate.storedmove.append((player.row, player.col, player.direction, enemy.row, enemy.col, enemy.direction))
        return True

    def _advance_level(chapter: int, level: int):
        level += 1
        if level > 15:
            chapter += 1
            level = 1
        if chapter > 3:
            return None
        return chapter, level

    # ===== MAIN LOOP =====
    while True:
        dt = FramePerSec.tick(FPS) / 1000.0

        mouse_pos = screen_main.get_mouse_pos()
        hover_any_button = False

        if gamestate.state == "Home":
            if start_button.rect.collidepoint(mouse_pos):
                hover_any_button = True

        elif gamestate.state == "SELECTION":
            for r in [classic_button, adventure_button, tutorial_button, quit_button]:
                if r.rect.collidepoint(mouse_pos):
                    hover_any_button = True
                    break

        elif gamestate.state == "DIFFICULTY":
            for r in [easy_button, medium_button, hard_button, back_button]:
                if r.rect.collidepoint(mouse_pos):
                    hover_any_button = True
                    break

        elif gamestate.state == "NEXTLEVEL":
            if nextlevel_button.rect.collidepoint(mouse_pos):
                hover_any_button = True
            if nextlevel_selection_button.rect.collidepoint(mouse_pos):
                hover_any_button = True

        pygame.mouse.set_cursor(pygame.SYSTEM_CURSOR_HAND if hover_any_button else pygame.SYSTEM_CURSOR_ARROW)

        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                sys.exit()

            if e.type == pygame.KEYDOWN and e.key == pygame.K_F11:
                screen_main.toggle_fullscreen()

            if gamestate.state == "DIFFICULTY":
                if e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE:
                    gamestate.state = "SELECTION"

            if gamestate.state == "Home":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if start_button.is_clicked(mouse_pos):
                        gamestate.state = "SELECTION"

            elif gamestate.state == "SELECTION":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if classic_button.is_clicked(mouse_pos):
                        gamestate.state = "DIFFICULTY"

                    elif adventure_button.is_clicked(mouse_pos):
                        # start at chapter1-level1
                        ok = _load_adventure_level(1, 1)
                        if ok:
                            gamestate.mode = "adventure"
                            gamestate.state = "PLAYING"

                    elif tutorial_button.is_clicked(mouse_pos):
                        print("Chọn Tutorial (chưa làm)")

                    elif quit_button.is_clicked(mouse_pos):
                        pygame.quit()
                        sys.exit()

            elif gamestate.state == "DIFFICULTY":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if easy_button.is_clicked(mouse_pos):
                        _start_classic(6)
                    elif medium_button.is_clicked(mouse_pos):
                        _start_classic(8)
                    elif hard_button.is_clicked(mouse_pos):
                        _start_classic(10)
                    elif back_button.is_clicked(mouse_pos):
                        gamestate.state = "SELECTION"

            elif gamestate.state == "NEXTLEVEL":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if nextlevel_button.is_clicked(mouse_pos):
                        nxt = _advance_level(gamestate.chapter, gamestate.level)
                        if nxt is None:
                            gamestate.state = "SELECTION"
                            gamestate.mode = "classic"
                        else:
                            ch, lv = nxt
                            ok = _load_adventure_level(ch, lv)
                            if ok:
                                gamestate.state = "PLAYING"
                            else:
                                gamestate.state = "SELECTION"
                    elif nextlevel_selection_button.is_clicked(mouse_pos):
                        gamestate.state = "SELECTION"
                        gamestate.mode = "classic"
                        

            elif gamestate.state == "PLAYING":
                if (e.type == KEYDOWN) and (not gamestate.gameover) and (e.key in ALLOWED_BUTTON):
                    moved = player.move(e.key, grid)
                    if moved:
                        remaining_move = enemy.move(player, grid)
                        if remaining_move == 0:
                            gamestate.storedmove.append(
                                (player.row, player.col, player.direction, enemy.row, enemy.col, enemy.direction)
                            )

                if e.type == MOUSEBUTTONDOWN:
                    undobutton.undo_move(e, player, enemy, gamestate)
                    restartbutton.restart_game(e, gamestate, player, enemy)
                    if gamestate.mode != "adventure":
                        newgamebutton.newgame_game(e, grid, player, enemy, gamestate)
                    exitbutton.exit_game(e, gamestate)

        if gamestate.state == "PLAYING" and (not gamestate.gameover):
            player.update(dt)
            enemy.update(dt)

        # Adventure win -> go to NEXTLEVEL screen
        if gamestate.state == "PLAYING" and gamestate.mode == "adventure":
            if (not gamestate.gameover) and (player.row == gamestate.goal_row and player.col == gamestate.goal_col):
                gamestate.gameover = True
                gamestate.state = "NEXTLEVEL"

        surface = screen_main.virtual_surface

        if gamestate.state == "Home":
            surface.blit(start_bg, (0, 0))
            start_button.draw(surface)
            if start_button.rect.collidepoint(mouse_pos):
                pygame.draw.rect(surface, (255, 255, 0), start_button.rect, 2)

        elif gamestate.state == "SELECTION":
            surface.blit(modeSelect_bg, (0, 0))
            classic_button.draw(surface, mouse_pos)
            tutorial_button.draw(surface, mouse_pos)
            adventure_button.draw(surface, mouse_pos)
            quit_button.draw(surface, mouse_pos)

        elif gamestate.state == "DIFFICULTY":
            surface.blit(modeSelect_bg, (0, 0))
            surface.blit(choose_diff_text, choose_diff_rect)
            easy_button.draw(surface, mouse_pos)
            medium_button.draw(surface, mouse_pos)
            hard_button.draw(surface, mouse_pos)
            back_button.draw(surface, mouse_pos)

        elif gamestate.state == "NEXTLEVEL":
            surface.blit(nextlevel_img, (OFFSET_X_1, 0))
            nextlevel_button.draw(surface, mouse_pos)
            nextlevel_selection_button.draw(surface, mouse_pos)

        elif gamestate.state == "PLAYING":
            surface.blit(backdrop, (0, 0))
            surface.blit(backdrop_s, (OFFSET_X_1, OFFSET_Y_1))
            surface.blit(background, (OFFSET_X, OFFSET_Y))

            for row in grid:
                for cell in row:
                    if not gamestate.gameover:
                        if cell.row == player.row and cell.col == player.col:
                            player.draw(surface)
                        elif cell.row == enemy.row and cell.col == enemy.col:
                            enemy.draw(surface)
                    cell.draw(surface, grid)

            undobutton.draw(surface)
            restartbutton.draw(surface)
            if gamestate.mode != "adventure":
                newgamebutton.draw(surface)
            exitbutton.draw(surface)

            gamestate.draw_stairs(surface)
            losing_check(surface, font, player, enemy, gamestate)
            winning_check(surface, font, player, gamestate)

        screen_main.render()


if __name__ == "__main__":
    run_game()
