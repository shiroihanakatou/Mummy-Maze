import pygame, sys, random
import os, json
from pygame.locals import *
from pathlib import Path

from variable import *
from module import *
from entity import Player, Enemy, Cell
from screen.button import Undobutton, Restartbutton, Newgamebutton, Exitbutton, StartButton, Button,TextButton
from module.gamestate import Gamestate

from module.module import read_map_json, apply_map_to_grid

import variable as V
import module.module as module_mod
import entity.entity as entity_mod
import module.gamestate as gamestate_mod

from module.module import create_tuple




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
        print("[music] load failed:", ex)

    # init entities and gamestate
    grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
    player = Player()
    enemies: list[Enemy] = []  # enemies lists

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

    # Loading screen (ads)
    loading_state = {
        "active": False,
        "image": None,
        "progress": 0.0,
        "timer": 0.0,
        "generating": False,
        "start_time": 0.0
    }

    # số lượng quái
    gamestate.enemy_count = 3 if ROWS >= 10 else (2 if ROWS >= 8 else 1)
    generate_game(grid, player, enemies, gamestate)

    start_bg = pygame.image.load(str(ASSETS_DIR / "screen" / "bg_start_1.jpg")).convert_alpha()
    start_bg = pygame.transform.smoothscale(start_bg, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    modeSelect_bg = pygame.image.load(str(ASSETS_DIR / "screen" / "mode_bg.jpg")).convert_alpha()
    modeSelect_bg = pygame.transform.smoothscale(modeSelect_bg, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    # Loading screen images
    loading_images = [
        pygame.image.load(str(ASSETS_DIR / "images" / "beach.gif")).convert(),
        pygame.image.load(str(ASSETS_DIR / "images" / "findtreasure.jpg")).convert()
    ]

    # Selection screen buttons
    classic_button = TextButton("CLASSIC MODE", (465, 492), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    tutorial_button = TextButton("TUTORIAL", (835, 492), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    adventure_button = TextButton("ADVENTURE", (465, 605), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    quit_button = TextButton("QUIT GAME", (835, 605), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))

    # Difficulty screen UI
    choose_diff_text = menu_font.render("CHOOSE DIFFICULTY", True, (0, 0, 0))
    choose_diff_rect = choose_diff_text.get_rect(center=(SCREEN_WIDTH // 2, 450))

    easy_button   = TextButton("Easy",   (SCREEN_WIDTH // 2, 550), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    medium_button = TextButton("Medium", (SCREEN_WIDTH // 2, 620), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    hard_button   = TextButton("Hard",   (SCREEN_WIDTH // 2, 690), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))
    back_button   = TextButton("Back",   (SCREEN_WIDTH // 4, 720), menu_font, idle_color=(0, 0, 0), hover_color=(255, 0, 0))

    # Game Over screen
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

    # Auto-play time setting
    auto_play = {
        "enabled": False,
        "solution_idx": 0,
        "move_timer": 0.0,
        "move_delay": 0.5,  
    }

    img_options = pygame.image.load("game/assets/screen/OPTIONS_BUTTON.png").convert_alpha()
    img_options = pygame.transform.smoothscale(img_options, (245, 72))
    options_button = Button(img_options, 110, 216)

    img_done = pygame.image.load("game/assets/screen/DONE_BUTTON.png").convert_alpha()
    img_done = pygame.transform.smoothscale(img_done, (180, 54))
    done_button = TextButton("DONE", (650, 500), menu_font, min_size=(270, 90))
    options_panel_bg = pygame.image.load("game/assets/screen/OPTIONS_BG.png").convert_alpha()
    options_panel_bg = pygame.transform.smoothscale(options_panel_bg, (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
    ankh_img = pygame.image.load("game/assets/images/sliderankh.png").convert_alpha()

    s_music = OptionsSlider("Music", 540, 320, 300, 0.5)
    s_sound = OptionsSlider("Sound Fx", 540, 370, 300, 0.7)
    s_speed = OptionsSlider("Speed", 540, 420, 300, 0.4)
    font_path = str(ASSETS_DIR / "font" / "romeo.ttf")
    font_medium = pygame.font.Font(font_path, 32)
    menu_y = SCREEN_HEIGHT

    def _load_floor():
        # floor6/8/10.jpg
        img = pygame.image.load(str(ASSETS_DIR / f"floor{ROWS}.jpg")).convert_alpha()
        return pygame.transform.smoothscale(img, (int(COLS * CELL_SIZE), int(ROWS * CELL_SIZE)))

    background = _load_floor()

    backdrop = pygame.image.load(str(ASSETS_DIR / "backdrop_1.png")).convert_alpha()
    backdrop = pygame.transform.smoothscale(backdrop, (SCREEN_WIDTH + 10, SCREEN_HEIGHT + 60))

    backdrop_s = pygame.image.load(str(ASSETS_DIR / "backdrop.png")).convert_alpha()
    backdrop_s = pygame.transform.smoothscale(backdrop_s, (X, Y))

    # ===== Next level =====
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
        "Go to next level",
        (OFFSET_X_1 + (SCREEN_WIDTH - OFFSET_X_1) // 2, 600),
        nextlevel_btn_font,
        idle_color=(255, 255, 0),
        hover_color=(255, 255, 255),
        min_size=(540, 90),
    )
    
    # Return to Menu button autoplay
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

    # Loading screen button
    loading_button = TextButton(
        "Please wait",
        (0, 0),  
        menu_font,
        idle_color=(255, 255, 255),
        hover_color=(255,255,255), 
        min_size=(300, 80),
    )

    # ===== reset vaiable sau khi đổi mode =====
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
        nonlocal grid, player, enemies, gamestate, background, killed_uids, collision_fx

        V.apply_grid_size(size)
        _sync_dynamic_vars()

        grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
        player = Player()
        # Clear enemies 
        enemies.clear()
        killed_uids.clear()
        collision_fx.clear()
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

        if size <= 6:
            gamestate.enemy_count = 1
        elif size <= 8:
            gamestate.enemy_count = 2
        else:
            gamestate.enemy_count = 3

        generate_game(grid, player, enemies, gamestate)

    def _load_adventure_level(chapter: int, level: int) -> bool:
        """Adventure: load level JSON tại assets/map/level{chapter}-{level}.json."""
        nonlocal grid, player, enemies, gamestate, background

        path = ASSETS_DIR / "map" / f"level{chapter}-{level}.json"
        if not path.exists():
            print("[adventure] missing:", path)
            return False

        try:
            rows, cols, tiles, walls_v, walls_h, exit_pos = read_map_json(str(path))
        except Exception as ex:
            print("[adventure] read_map_json failed:", ex)
            return False

        # validate shapes (defensive)
        if len(tiles) != rows or any(len(s) != cols for s in tiles):
            print("[adventure] tiles shape mismatch")
            return False
        if len(walls_v) != rows or any(len(s) != cols + 1 for s in walls_v):
            print("[adventure] walls_v shape mismatch")
            return False
        if len(walls_h) != rows + 1 or any(len(s) != cols for s in walls_h):
            print("[adventure] walls_h shape mismatch")
            return False

        # rebuild everything to match map size
        V.apply_grid_size(rows)
        _sync_dynamic_vars()

        grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
        player = Player()
        # Clear quái
        enemies.clear()
        killed_uids.clear()
        collision_fx.clear()
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

    # ===== enemy fight =====
    # Rule: If an enemy moves into a tile occupied by another enemy that is standing still,
    # then the standing enemy dies. The moving enemy survives.
    killed_uids: set[int] = set()
    collision_fx: list[dict] = []  # dust effects 

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
                    # Play a collision sound when an enemy kills another
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
                    # print(f"[Collision] Enemy {other.uid} ({other.type}) killed by Enemy {mover.uid}")
                    break

        for e in enemies:
            if getattr(e, "on_step", None) is not on_enemy_step:
                e.on_step = on_enemy_step

    def _actors_idle():
        """Check if all actors (player + enemies) are idle (not moving, no pending actions)."""
        if player.is_moving:
            return False
        for e in enemies:
            if e.is_moving:
                return False
            if getattr(e, "pending_steps", []):
                return False
        return True
    
    current_turn = "player"  
    enemy_turn_idx = 0

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
        
        elif gamestate.state == "AUTOPLAY_COMPLETE":
            if return_menu_button.rect.collidepoint(mouse_pos):
                hover_any_button = True

        elif gamestate.state == "LOSE_MENU":
            for r in [btn_try_again, btn_world_map, btn_undo_move, btn_save_quit, btn_abandon_hope]:
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
                        gamestate.state = "SELECTION"

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
                        progress_mgr.current_chapter = 1
                        progress_mgr.current_level = 1
                        gamestate.chapter = 1
                        gamestate.level = 1
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
                        print("Chọn Tutorial (chưa làm)")

                    elif quit_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        pygame.quit()
                        sys.exit()

            elif gamestate.state == "DIFFICULTY":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if easy_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        _start_classic(6)
                    elif medium_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        _start_classic(8)
                    elif hard_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        _start_classic(10)
                    elif back_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        gamestate.state = "SELECTION"

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
            
            elif gamestate.state == "AUTOPLAY_COMPLETE":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    if return_menu_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
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
                        collision_fx.clear()
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.state = "PLAYING"
                        gamestate.gameover = False
                    elif win_back_button.is_clicked(mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        gamestate.state = "SELECTION"
                        gamestate.mode = "classic"
                        gamestate.gameover = False

            elif gamestate.state == "PLAYING":
                if e.type == MOUSEBUTTONDOWN and options_button.is_clicked(e):
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
                    # Check undo button
                    if undobutton.is_clicked(e.pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        undobutton.undo_move(e, player, enemies, gamestate, grid)
                        killed_uids.clear()  # Hồi sinh quái khi undo
                        collision_fx.clear()
                    # Check restart button
                    elif restartbutton.is_clicked(e.pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        restartbutton.restart_game(e, player, enemies, gamestate, grid)
                        killed_uids.clear()  # Hồi sinh quái khi restart
                        collision_fx.clear()  
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.state = "PLAYING"
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
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        exitbutton.exit_game(e, gamestate)

            elif gamestate.state == "DEATH_ANIM":
                # Lock input during death animation
                pass

            elif gamestate.state == "OPTIONS":
                s_music.handle_event(e, mouse_pos)
                s_sound.handle_event(e, mouse_pos)
                s_speed.handle_event(e, mouse_pos)
                pygame.mixer.music.set_volume(s_music.val)

                if e.type == pygame.MOUSEBUTTONDOWN and done_button.is_clicked(mouse_pos):
                    gamestate.state = "PLAYING"

            elif gamestate.state == "LOSE_MENU":
                if e.type == pygame.MOUSEBUTTONDOWN:
                    dy = menu_y - target_y
                   
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
                        collision_fx.clear()
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.state = "PLAYING"
                        gamestate.gameover = False
                        gamestate.death_state = None
                        menu_y = SCREEN_HEIGHT
                    elif btn_undo_move.is_clicked(adjusted_mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                                # print("[Click] Undo button clicked")
                            except Exception as ex:
                                pass  # print(f"[Click] Undo sound error: {ex}")
                        undobutton.undo_move(e, player, enemies, gamestate, grid)
                        killed_uids.clear()
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
                        #autoplay mode
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        if gamestate.solution:
                            # Reset to initial position
                            if gamestate.initpos:
                                from module.module import apply_tuple
                                apply_tuple(gamestate.initpos, player, enemies, grid, gamestate)
                                # print(f"[AutoPlay] Starting with {len(gamestate.solution)} moves")
                            # Start auto-play
                            auto_play["enabled"] = True
                            auto_play["solution_idx"] = 0
                            auto_play["move_timer"] = 0.0
                            # Set to AUTOPLAY state
                            current_turn = "player"
                            enemy_turn_idx = 0
                            killed_uids.clear()  # Reset dead enemies
                            collision_fx.clear()  # Clear collision effects
                            gamestate.state = "AUTOPLAY"
                            gamestate.gameover = False
                            menu_y = SCREEN_HEIGHT
                        else:
                            pass
                            # print("[AutoPlay] No solution available")
                    elif btn_world_map.is_clicked(adjusted_mouse_pos):
                        if gamestate.sfx.get("click") is not None:
                            try:
                                gamestate.sfx["click"].play()
                            except: pass
                        gamestate.state = "WORLD_MAP"
                        gamestate.gameover = False
                        menu_y = SCREEN_HEIGHT
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
                        gamestate.state = "SELECTION"
                        
                    if btn_save_quit_map.is_clicked(mouse_pos):
                        pygame.quit()
                        sys.exit()

        # ===== update animation =====
        if gamestate.state == "PLAYING" and (not gamestate.gameover):
            _ensure_enemy_hooks()

            if getattr(gamestate, "_force_snapshot_now", False):
                gamestate.storedmove.append(create_tuple(player, enemies, gamestate))
                try:
                    delattr(gamestate, "_force_snapshot_now")
                except Exception:
                    gamestate._force_snapshot_now = False

            player.update(dt)
            for en in enemies:
                if en.uid not in killed_uids:
                    en.update(dt)

            # Handle enemy turns theo lượt
            if current_turn != "player" and _actors_idle():
                if current_turn < len(enemies):
                    en = enemies[current_turn]
                    en.move(player, grid)
                    # Check collision after this enemy moves
                    if gamestate.state != "DEATH_ANIM":
                        losing_check(None, None, player, enemies, gamestate)
                    # Xóa quái khi bị giết
                    if killed_uids:
                        enemies[:] = [e for e in enemies if e.uid not in killed_uids]
                        killed_uids.clear()
                        
                        if current_turn >= len(enemies):
                            current_turn = len(enemies)
                    # Move to next enemy or back to player
                    current_turn += 1
                else:
                    # All enemies done, wait for all animations to finish then back to player
                    if _actors_idle():
                        current_turn = "player"

            # apply enemy-vs-enemy kills after updates
            if killed_uids:
                enemies[:] = [en for en in enemies if en.uid not in killed_uids]
                killed_uids.clear()

            #dust effects
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

            # append snapshot when turn fully settled
            if getattr(gamestate, "pending_snapshot", False) and _actors_idle():
                gamestate.storedmove.append(create_tuple(player, enemies, gamestate))
                gamestate.pending_snapshot = False

        elif gamestate.state == "DEATH_ANIM":
            finished = update_death_anim(dt, gamestate)
            if finished:
                gamestate.state = "LOSE_MENU"
                gamestate.gameover = True

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
            
                if current_turn < len(enemies):
                    en = enemies[current_turn]
                    if en.uid not in killed_uids:
                        en.move(player, grid)
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
                    if _actors_idle():
                        current_turn = "player"
            
            # AUTO-PLAY
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
    
                                    auto_play["enabled"] = False
                                    return
                        auto_play["solution_idx"] += 1
                    else:
                        # Solution finished
                        # print(f"[AutoPlay] Solution completed! Player at ({player.row}, {player.col})")
                        auto_play["enabled"] = False
                        # Reset to a fresh state after autoplay
                        if gamestate.initpos:
                            apply_tuple(gamestate.initpos, player, enemies, grid, gamestate)
                        killed_uids.clear()
                        collision_fx.clear()
                        current_turn = "player"
                        enemy_turn_idx = 0
                        gamestate.gameover = False
                        gamestate.state = "AUTOPLAY_COMPLETE"

            if killed_uids:
                enemies[:] = [en for en in enemies if en.uid not in killed_uids]
                killed_uids.clear()

            #dust effects
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
                    apply_tuple(gamestate.initpos, player, enemies, grid, gamestate)
                killed_uids.clear()
                collision_fx.clear()
                current_turn = "player"
                enemy_turn_idx = 0
                gamestate.gameover = False
                # print("[AutoPlay] Goal reached during auto-play!")

        # Win check 
        if gamestate.state == "PLAYING" and (not gamestate.gameover):
            if player.row == gamestate.goal_row and player.col == gamestate.goal_col:
                gamestate.gameover = True
                if gamestate.mode == "adventure":
                    gamestate.state = "NEXTLEVEL"
                else:
                    # Classic mode -> WIN_SCREEN
                    gamestate.state = "WIN_SCREEN"
                    # Play win sound
                    if gamestate.sfx.get("finishedlevel") is not None:
                        try:
                            gamestate.sfx["finishedlevel"].play()
                        except: pass

        # ===== render =====
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
            if nextlevel_img is not None:
                surface.blit(nextlevel_img, (OFFSET_X_1, 0))
            else:
                surface.blit(modeSelect_bg, (0, 0))
            nextlevel_button.draw(surface, mouse_pos)
        
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
            
            win_newgame_button.draw(surface, mouse_pos)
            win_back_button.draw(surface, mouse_pos)
        
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

        elif gamestate.state in ("PLAYING", "DEATH_ANIM", "AUTOPLAY"):
            surface.blit(backdrop, (0, 0))
            surface.blit(backdrop_s, (OFFSET_X_1, OFFSET_Y_1))
            surface.blit(background, (OFFSET_X, OFFSET_Y))

            if gamestate.mode == "adventure":
                progress_mgr.draw_sidebar_map(surface, 93, 478)
            options_button.draw(surface)

            death_active = gamestate.state == "DEATH_ANIM" and getattr(gamestate, "death_state", None)
            death_cause = gamestate.death_state.get("cause") if death_active else None
            death_pos = (gamestate.death_state.get("row"), gamestate.death_state.get("col")) if death_active else (-1, -1)
            pos_to_enemy = {}
            for en in enemies:
                if en.uid not in killed_uids:
                    pos_to_enemy[(en.row, en.col)] = en
            
            # Track which gates have been drawn (to avoid duplicate)
            drawn_gates = set()
            
            # Draw theo từng ô tránh đè nhau
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
                    if not gamestate.gameover:
                        if cell.row == player.row and cell.col == player.col:
                            entity_in_cell = player
                        else:
                            entity_in_cell = pos_to_enemy.get((cell.row, cell.col), None)
                        if death_active and (cell.row, cell.col) == death_pos:
                            entity_in_cell = None
                    
                    # 5. Gate render moved to same priority as walls (after entity)
                    
                    # 6. Draw entity
                    if entity_in_cell:
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
                
                # Start actual generation after a brief visual delay
                if not loading_state["generating"] :
                    loading_state["generating"] = True
                    # Perform the actual generation
                    newgamebutton.newgame_game(None, grid, player, enemies, gamestate)
                    killed_uids.clear()
                    collision_fx.clear()
                
                # Clear loading screen only after 2 seconds minimum AND generation complete
                if loading_state["generating"] and elapsed_time >= 2.0:
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
            btn_world_map.draw_at(surface, (900, 630 + dy), mouse_pos)
            btn_undo_move.draw_at(surface, (360, 720 + dy), mouse_pos)
            btn_save_quit.draw_at(surface, (900, 720 + dy), mouse_pos)
            # Show abandon hope in both modes (disabled in classic via click handling)
            btn_abandon_hope.draw_at(surface, (630, 630 + dy), mouse_pos)

        elif gamestate.state == "WORLD_MAP":
            world_map.draw(surface, progress_mgr, mouse_pos)
            btn_back_map.draw(surface, mouse_pos)
            btn_save_quit_map.draw(surface, mouse_pos)

        elif gamestate.state == "OPTIONS":
            surface.blit(options_panel_bg, (SCREEN_WIDTH // 4, SCREEN_HEIGHT // 4))
            s_music.draw(surface, font_medium, ankh_img)
            s_sound.draw(surface, font_medium, ankh_img)
            s_speed.draw(surface, font_medium, ankh_img)
            done_button.draw(surface, mouse_pos)

        screen_main.render()


if __name__ == "__main__":
    run_game()
