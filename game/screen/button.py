import pygame, sys, random
from pygame.locals import *
from variable import *
from module import generate_game


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


class Newgamebutton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/NEW_GAME_BUTTON.png").convert()
        self.image = pygame.transform.smoothscale(self.image, (271, 91))
        self.rect = self.image.get_rect(topleft=(100, 253))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            surface.blit(self.image, self.rect)
        else:
            temp_img = self.image.copy()
            temp_img.set_alpha(200)
            surface.blit(temp_img, self.rect)

    def newgame_game(self, event, grid, player, enemy, gamestate):
        if self.rect.collidepoint(event.pos):
            # cắt ngang mọi animation
            reset_actor_animation(player)
            reset_actor_animation(enemy)
            reset_gamestate_anim_flags(gamestate)

            gamestate.storedmove.clear()
            generate_game(grid, player, enemy, gamestate)
            gamestate.gameover = False


class Restartbutton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/RESTART_BUTTON.png").convert()
        self.image = pygame.transform.smoothscale(self.image, (271, 91))
        self.rect = self.image.get_rect(topleft=(100, 361))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            surface.blit(self.image, self.rect)
        else:
            temp_img = self.image.copy()
            temp_img.set_alpha(200)
            surface.blit(temp_img, self.rect)

    def restart_game(self, event, gamestate, player, enemy):
        if self.rect.collidepoint(event.pos):
            # cắt ngang mọi animation
            reset_actor_animation(player)
            reset_actor_animation(enemy)
            reset_gamestate_anim_flags(gamestate)

            # gán vị trí ban đầu
            player.row, player.col, enemy.row, enemy.col = gamestate.initpos

            gamestate.storedmove.clear()
            gamestate.storedmove.append(
                (player.row, player.col, player.direction, enemy.row, enemy.col, enemy.direction)
            )
            gamestate.gameover = False


class Undobutton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/UNDO_BUTTON.png").convert()
        self.image = pygame.transform.smoothscale(self.image, (271, 91))
        self.rect = self.image.get_rect(topleft=(100, 469))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            surface.blit(self.image, self.rect)
        else:
            temp_img = self.image.copy()
            temp_img.set_alpha(200)
            surface.blit(temp_img, self.rect)

    def undo_move(self, event, player, enemy, gamestate):
        if not self.rect.collidepoint(event.pos):
            return

        reset_actor_animation(player)
        reset_actor_animation(enemy)
        reset_gamestate_anim_flags(gamestate)

        # phải có ít nhất 2 state mới undo được
        if len(gamestate.storedmove) < 2:
            return

        print(gamestate.storedmove)
        # bỏ state hiện tại
        gamestate.storedmove.pop()

        # apply state trước đó
        prev = gamestate.storedmove[-1]
        player.row, player.col, player.direction, enemy.row, enemy.col, enemy.direction = prev
        gamestate.gameover = False



class Exitbutton:
    def __init__(self):
        self.image = pygame.image.load("game/assets/screen/EXIT_BUTTON.png").convert()
        self.image = pygame.transform.smoothscale(self.image, (271, 91))
        self.rect = self.image.get_rect(topleft=(100, 577))

    def draw(self, surface):
        mouse_pos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mouse_pos):
            surface.blit(self.image, self.rect)
        else:
            temp_img = self.image.copy()
            temp_img.set_alpha(200)
            surface.blit(temp_img, self.rect)

    def exit_game(self, event,gamestate):
        if self.rect.collidepoint(event.pos):
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
