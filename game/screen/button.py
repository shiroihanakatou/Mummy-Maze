import pygame, sys, random
from pygame.locals import *
from variable import *
from module import generate_game

# NEW: snapshot helper để restart/undo đúng với multi-enemy (Phase 1)
from module.module import make_snapshot, apply_snapshot


def _iter_enemies(enemy_or_list):
    if enemy_or_list is None:
        return []
    if isinstance(enemy_or_list, (list, tuple)):
        return list(enemy_or_list)
    return [enemy_or_list]


def reset_actor_animation(actor):
    # dừng clip animation
    if hasattr(actor, "animation_container"):
        actor.animation_container.clear()
    if hasattr(actor, "anim_idx"):
        actor.anim_idx = 0
    if hasattr(actor, "anim_timer"):
        actor.anim_timer = 0.0

    # dừng tween/trượt
    if hasattr(actor, "render_dx"):
        actor.render_dx = 0.0
    if hasattr(actor, "render_dy"):
        actor.render_dy = 0.0

    if hasattr(actor, "is_moving"):
        actor.is_moving = False

    # enemy chain 2 bước
    if hasattr(actor, "pending_steps"):
        actor.pending_steps.clear()

    # idle timer (player)
    if hasattr(actor, "inactive_timer"):
        actor.inactive_timer = 0.0
    if hasattr(actor, "idle_delay"):
        actor.idle_delay = random.uniform(8, 12)


def reset_gamestate_anim_flags(gamestate):
    if hasattr(gamestate, "turn"):
        gamestate.turn = "PLAYER_INPUT"

    if hasattr(gamestate, "was_player_moving"):
        gamestate.was_player_moving = False

    gamestate.cancel_animation = True

    # Phase 1: snapshot append theo turn trong main
    if hasattr(gamestate, "pending_snapshot"):
        gamestate.pending_snapshot = False


class Newgamebutton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/NEW_GAME_BUTTON.png").convert()
        self.image = pygame.transform.smoothscale(self.image, (245, 72))
        self.rect = self.image.get_rect(topleft=(110, 486))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            surface.blit(self.image, self.rect)
        else:
            temp_img = self.image.copy()
            temp_img.set_alpha(200)
            surface.blit(temp_img, self.rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    # giữ API gốc: (event, grid, player, enemy, gamestate)
    # nhưng enemy có thể là list
    def newgame_game(self, event, grid, player, enemy, gamestate):

        # cắt ngang mọi animation
        reset_actor_animation(player)
        enemies_list = _iter_enemies(enemy)
        for en in enemies_list:
            reset_actor_animation(en)
        reset_gamestate_anim_flags(gamestate)

        gamestate.storedmove.clear()

        # Clear enemies and regenerate from scratch
        # Must clear the original enemy list passed in, not a copy
        if isinstance(enemy, list):
            enemy.clear()
        else:
            # If single enemy, wrap in list for clearing
            enemies_list.clear()
        
        gamestate.keys.clear()
        gamestate.traps.clear()
        gamestate.gates_h.clear()
        gamestate.gate_anim_state.clear()
        
        # generate_game Phase 1 đã nhận enemies list và regenerate
        # Pass the original enemy list so it gets populated
        if isinstance(enemy, list):
            generate_game(grid, player, enemy, gamestate)
            snap = make_snapshot(player, enemy, gamestate)
        else:
            generate_game(grid, player, enemies_list, gamestate)
            snap = make_snapshot(player, enemies_list, gamestate)

        # init snapshot chuẩn
        gamestate.initpos = snap
        gamestate.storedmove.clear()
        gamestate.storedmove.append(snap)

        gamestate.gameover = False
        gamestate.result = None


class Restartbutton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/RESTART_BUTTON.png").convert()
        self.image = pygame.transform.smoothscale(self.image, (245, 72))
        self.rect = self.image.get_rect(topleft=(110, 306))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            surface.blit(self.image, self.rect)
        else:
            temp_img = self.image.copy()
            temp_img.set_alpha(200)
            surface.blit(temp_img, self.rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    # giữ API gốc: (event, gamestate, player, enemy)
    # enemy có thể là list
    def restart_game(self, event, player, enemy, gamestate, grid):

        # cắt ngang mọi animation
        reset_actor_animation(player)
        for en in _iter_enemies(enemy):
            reset_actor_animation(en)
        reset_gamestate_anim_flags(gamestate)
        #print("Restart to:", gamestate.initpos)
        if getattr(gamestate, "initpos", None) is None:
            return
        
        # apply snapshot (multi enemy) on the original list reference
        enemies_ref = enemy if isinstance(enemy, list) else _iter_enemies(enemy)
        apply_snapshot(gamestate.initpos, player, enemies_ref, grid, gamestate)
        gamestate.storedmove.clear()
        gamestate.storedmove.append(gamestate.initpos)
        gamestate.gameover = False
        gamestate.result = None
        
        # Clear death state and reset to PLAYING
        gamestate.death_state = None
        gamestate.state = "PLAYING"


class Undobutton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/UNDO_BUTTON.png").convert()
        self.image = pygame.transform.smoothscale(self.image, (245, 72))
        self.rect = self.image.get_rect(topleft=(110, 396))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            surface.blit(self.image, self.rect)
        else:
            temp_img = self.image.copy()
            temp_img.set_alpha(200)
            surface.blit(temp_img, self.rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    # giữ API gốc: (event, player, enemy, gamestate)
    # enemy có thể là list
    def undo_move(self, event, player, enemy, gamestate, grid):

        reset_actor_animation(player)
        for en in _iter_enemies(enemy):
            reset_actor_animation(en)
        reset_gamestate_anim_flags(gamestate)

        # phải có ít nhất 2 state mới undo được
        if len(gamestate.storedmove) < 2:
            return

        # bỏ state hiện tại
        gamestate.storedmove.pop()

        # apply state trước đó
        prev = gamestate.storedmove[-1]
        enemies_ref = enemy if isinstance(enemy, list) else _iter_enemies(enemy)
        apply_snapshot(prev, player, enemies_ref, grid, gamestate)
        gamestate.gameover = False
        gamestate.result = None
        
        # Clear death state and reset to PLAYING
        gamestate.death_state = None
        gamestate.state = "PLAYING"


class Exitbutton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/EXIT_BUTTON.png").convert()
        self.image = pygame.transform.smoothscale(self.image, (245, 72))
        self.rect = self.image.get_rect(topleft=(110, 667))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            surface.blit(self.image, self.rect)
        else:
            temp_img = self.image.copy()
            temp_img.set_alpha(200)
            surface.blit(temp_img, self.rect)

    def is_clicked(self, mouse_pos):
        return self.rect.collidepoint(mouse_pos)

    def exit_game(self, event, gamestate):
        gamestate.state = "SELECTION"


class StartButton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/start_button_4.png").convert_alpha()
        self.height = 127
        self.width = 307
        self.image = pygame.transform.smoothscale(self.image, (self.width, self.height))
        self.rect = self.image.get_rect(center=((SCREEN_WIDTH + 73) // 2, 686))

    def draw(self, surface):
        surface.blit(self.image, self.rect)

    def is_clicked(self, pos):
        return self.rect.collidepoint(pos)


class Button:
    def __init__(self, image, x, y):
        self.image = image
        self.rect = self.image.get_rect(topleft=(x, y))

    def draw(self, screen):
        screen.blit(self.image, self.rect)

    def is_clicked(self, e):
        if e.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(e.pos):
            return True
        return False
