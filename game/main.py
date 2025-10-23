import pygame, sys, random
from pygame.locals import *
from variable import *
from module import *
from entity import Player, Enemy, Cell
from button import Undobutton, Restartbutton, Newgamebutton, Exitbutton
from gamestate import Gamestate

pygame.init()
storedmove=[]
gameover = False
grid = [[Cell(r, c) for c in range(COLS)] for r in range(ROWS)]
player = Player()
enemy = Enemy()
font = pygame.font.SysFont("Verdana", 60)
undobutton=Undobutton()
restartbutton=Restartbutton() 
newgamebutton=Newgamebutton()
exitbutton=Exitbutton()
gamestate=Gamestate()
gamestate.initpos=(player.row,player.col,enemy.row,enemy.col)
generate_game(grid,player,enemy,gamestate)
while True:
    for e in pygame.event.get():
        if e.type == QUIT:
            pygame.quit()
            sys.exit()

        if e.type == KEYDOWN and not gamestate.gameover:
            player.move(e.key, grid)
            enemy.move(player, grid)
            gamestate.storedmove.append((player.row,player.col,enemy.row,enemy.col))
            
        if e.type == MOUSEBUTTONDOWN :
            undobutton.undo_move(e,player,enemy,gamestate)
            restartbutton.restart_game(e,gamestate,player,enemy)
            newgamebutton.newgame_game(e,grid,player,enemy,gamestate)
            exitbutton.exit_game(e)
            

    DISPLAYSURF.fill(BLACK)

    for row in grid:
        for cell in row:
            cell.draw(DISPLAYSURF)

    player.draw(DISPLAYSURF)
    enemy.draw(DISPLAYSURF)
    undobutton.draw(DISPLAYSURF)
    restartbutton.draw(DISPLAYSURF)
    newgamebutton.draw(DISPLAYSURF)
    exitbutton.draw(DISPLAYSURF)
    
    losing_check(player,enemy,gamestate)
    winning_check(player)

    
    pygame.display.update()
    FramePerSec.tick(FPS)
