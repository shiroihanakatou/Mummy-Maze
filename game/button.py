import pygame, sys, random
from pygame.locals import *
from variable import *
from module import generate_game

class Undobutton:
    def __init__(self):
        self.color = BLUE
        self.hovercolor = CYAN
        self.rect = pygame.Rect( COLS * CELL_SIZE - 2*CELL_SIZE,(ROWS) * CELL_SIZE, BUTTON_SIZE, BUTTON_SIZE)

    def draw(self, surface):
        mousepos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mousepos):
            pygame.draw.rect(surface, self.hovercolor, self.rect)  
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        font = pygame.font.SysFont("Verdana", 11)
        text = font.render("Undo", True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)  
        surface.blit(text, text_rect)
    def undo_move(self, event,player,enemy,gamestate):
        if self.rect.collidepoint(event.pos) and gamestate.storedmove:#Nếu click và nút và có thể undo
            last_move=gamestate.storedmove.pop()#Lấy lại trong stack
            player.row,player.col,enemy.row,enemy.col = last_move
class Restartbutton:
    def __init__(self):
        self.color = YELLOW
        self.hovercolor = ORANGE
        self.rect = pygame.Rect( COLS * CELL_SIZE - CELL_SIZE,(ROWS) * CELL_SIZE, BUTTON_SIZE, BUTTON_SIZE)

    def draw(self, surface):
        mousepos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mousepos):
            pygame.draw.rect(surface, self.hovercolor, self.rect)  
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        font = pygame.font.SysFont("Verdana", 11)
        text = font.render("Restart", True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)  
        surface.blit(text, text_rect)
    def restart_game(self, event,gamestate,player,enemy):
        if self.rect.collidepoint(event.pos):
            player.row,player.col,enemy.row,enemy.col = gamestate.initpos #Gán vị trí ban đầu
            gamestate.storedmove.clear() #Xóa stack
            gamestate.storedmove.append((player.row,player.col,enemy.row,enemy.col))

class Newgamebutton:
    def __init__(self):
        self.color = GREEN
        self.hovercolor = DARKGREEN
        self.rect = pygame.Rect( COLS * CELL_SIZE - 3*CELL_SIZE,(ROWS) * CELL_SIZE, BUTTON_SIZE, BUTTON_SIZE)

    def draw(self, surface):
        mousepos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mousepos):
            pygame.draw.rect(surface, self.hovercolor, self.rect)  
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        font = pygame.font.SysFont("Verdana", 10)
        text = font.render("New Game", True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)  
        surface.blit(text, text_rect)
    def newgame_game(self, event,grid,player,enemy,gamestate):
        if self.rect.collidepoint(event.pos):
            gamestate.storedmove.clear() #Xóa stack
            generate_game(grid,player,enemy,gamestate) #Tạo game mới
            gamestate.gameover = False
        
class Exitbutton:
    def __init__(self):
        self.color = RED
        self.hovercolor = PINK
        self.rect = pygame.Rect( COLS * CELL_SIZE - 4*CELL_SIZE,(ROWS) * CELL_SIZE, BUTTON_SIZE, BUTTON_SIZE)

    def draw(self, surface):
        mousepos = pygame.mouse.get_pos()
        if self.rect.collidepoint(mousepos):
            pygame.draw.rect(surface, self.hovercolor, self.rect)  
        else:
            pygame.draw.rect(surface, self.color, self.rect)
        font = pygame.font.SysFont("Verdana", 11)
        text = font.render("Exit", True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)  
        surface.blit(text, text_rect)
    def exit_game(self, event):
        if self.rect.collidepoint(event.pos):
            pygame.quit() #Thoát tab
            sys.exit()