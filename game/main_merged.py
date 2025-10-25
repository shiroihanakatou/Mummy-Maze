import pygame, sys, random
from pygame.locals import *

pygame.init()
FPS = 60
FramePerSec = pygame.time.Clock()


WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
GRAY  = (150, 150, 150)
NGRAY = (165, 165, 165)
GREEN = (0, 255, 0)
CYAN  = (0, 255, 255)
YELLOW=(255,255,0)
ORANGE=(255,165,0)
PINK  = (255,192,203)
DARKGREEN=(0,100,0)
ROWS = 8
COLS = 8
CELL_SIZE = 60
BUTTON_SIZE = 60
SCREEN_WIDTH = COLS * CELL_SIZE 
SCREEN_HEIGHT = ROWS * CELL_SIZE + BUTTON_SIZE

DISPLAYSURF = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Mummy Maze")


storedmove=[]
gameover = False

def wait(seconds):
    start = pygame.time.get_ticks()
    while pygame.time.get_ticks() - start < seconds * 1000:
        for e in pygame.event.get():
            if e.type == QUIT:
                pygame.quit()
                sys.exit()
        pygame.display.update()
        FramePerSec.tick(FPS)
def new_enemy_position(e_row,e_col,p_row,p_col,grid):
    new_row,new_col = e_row,e_col
    directions = [('up', -1, 0), ('down', 1, 0), 
                ('left', 0, -1), ('right', 0, 1)]
    for _ in range(2):
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

            if e_row == p_row and e_col == p_col:
                break
    return e_row,e_col
def winning_check(player):
    if player.row == ROWS-1 and player.col == COLS-1:
        text = font.render("You Win", True, GREEN)
        DISPLAYSURF.blit(
            text,
            (
                SCREEN_WIDTH // 2 - text.get_width() // 2,
                SCREEN_HEIGHT // 2 - text.get_height() // 2,
            ),
        )
        pygame.display.update()
        # wait(2)
        # pygame.quit()
        # sys.exit()
        
def losing_check(player,enemy,gameover):
        if player.row == enemy.row and player.col == enemy.col:
            gameover = True
            text = font.render("Game Over", True, RED)
            DISPLAYSURF.blit(
                text,
                (
                    SCREEN_WIDTH // 2 - text.get_width() // 2,
                    SCREEN_HEIGHT // 2 - text.get_height() // 2,
                ),
            )
            pygame.display.update()
            return gameover
            # wait(2)
            # pygame.quit()
            # sys.exit()
def is_playable(player, enemy, grid,gamestate):
    directions = [('up', -1, 0), ('down', 1, 0), ('left', 0, -1), ('right', 0, 1)]
    
    queue = [(player.row, player.col, enemy.row, enemy.col)]
    visited = [[[[0] * COLS for _ in range(ROWS)] for _ in range(COLS)] for _ in range(ROWS)]
    prev = [[[[(0,0,0,0)] * COLS for _ in range(ROWS)] for _ in range(COLS)] for _ in range(ROWS)]
    visited[player.row][player.col][enemy.row][enemy.col] = 1  
    while queue:
        curr = queue.pop(0)
        p_row, p_col, e_row, e_col = curr
        cell = grid[p_row][p_col]
        
        for d in directions:
            if not getattr(cell, d[0]) and 0 <= p_row + d[1] < ROWS and 0 <= p_col + d[2] < COLS:
                new_p_row = p_row + d[1]
                new_p_col = p_col + d[2]
                new_e_row, new_e_col = new_enemy_position(e_row, e_col, new_p_row, new_p_col, grid)

                if visited[new_p_row][new_p_col][new_e_row][new_e_col] == 0 and not (new_p_row == new_e_row and new_p_col == new_e_col):
                    prev[new_p_row][new_p_col][new_e_row][new_e_col] = (p_row, p_col, e_row, e_col)
                    visited[new_p_row][new_p_col][new_e_row][new_e_col] = 1
                    queue.append((new_p_row, new_p_col, new_e_row, new_e_col))
                    
                    if new_p_row == ROWS - 1 and new_p_col == COLS - 1:
                        print("Path found!")
                        path=[]
                        directions = [('up', -1, 0), ('down', 1, 0), ('left', 0, -1), ('right', 0, 1)]
                        curr_p_row, curr_p_col, curr_e_row, curr_e_col = new_p_row, new_p_col, new_e_row, new_e_col
                        while (new_p_row, new_p_col, new_e_row, new_e_col) != (player.row, player.col, enemy.row, enemy.col):
                            new_p_row, new_p_col, new_e_row, new_e_col = prev[curr_p_row][curr_p_col][curr_e_row][curr_e_col]
                            for d in directions:
                                if curr_p_row == new_p_row + d[1] and curr_p_col == new_p_col   + d[2]:
                                    path.append(d[0])
                                    break
                            curr_p_row, curr_p_col, curr_e_row, curr_e_col = new_p_row, new_p_col, new_e_row, new_e_col
                        path.reverse()
                        gamestate.solution = path
                        return True
    return False

def generate_game(grid,player,enemy,gamestate):
    print("Generating new game...")

    while True:
        for row in grid:
            for cell in row:
                cell.up , cell.down ,cell.left,cell.right = 0,0,0,0
        player.row = 0
        player.col = 0  
        while True:
            enemy.row = random.randint(0, ROWS - 1)
            enemy.col = random.randint(0, COLS - 1)
            if not (enemy.row == 0 and enemy.col == 0):
                break
        
        generate_walls(grid, random.randint(ROWS*COLS//4,ROWS*COLS))
        if is_playable(player, enemy, grid,gamestate):
            break
    gamestate.initpos=(player.row,player.col,enemy.row,enemy.col)
    gamestate.storedmove.append((player.row,player.col,enemy.row,enemy.col))
    gamestate.gameover = False
    print("New game generated.")
    print(gamestate.solution)
        
class Cell:
    def __init__(self, row, col):
        self.row = row
        self.col = col
        self.up = 0
        self.down = 0
        self.left = 0
        self.right = 0

    def draw(self, surface):
        x = self.col * CELL_SIZE
        y = self.row * CELL_SIZE
        
        pygame.draw.rect(surface, GRAY, (x, y, CELL_SIZE, CELL_SIZE), 1)

        if self.up:
            pygame.draw.line(surface, WHITE, (x, y), (x + CELL_SIZE, y), 3)
        if self.down:
            pygame.draw.line(surface, WHITE, (x, y + CELL_SIZE),(x + CELL_SIZE, y + CELL_SIZE), 3)
        if self.left:
            pygame.draw.line(surface, WHITE, (x, y), (x, y + CELL_SIZE), 3)
        if self.right:
            pygame.draw.line(surface, WHITE, (x + CELL_SIZE, y),(x + CELL_SIZE, y + CELL_SIZE), 3)


def generate_walls(grid, num_walls):
    directions = [('up', 'down', -1, 0), ('down', 'up', 1, 0), 
                ('left', 'right', 0, -1), ('right', 'left', 0, 1)]
    for _ in range(num_walls):
        no_wall = True
        while (no_wall):
            r = random.randint(1, ROWS - 1)
            c = random.randint(1, COLS - 1)
            d = random.choice(directions)
            if 0 <= r + d[2] < ROWS and 0 <= c + d[3] < COLS and not getattr(grid[r][c],d[0]):
                setattr(grid[r][c],d[0], 1)  
                setattr(grid[r + d[2]][c + d[3]],d[1], 1)  
                no_wall = False
                
    print("Walls generated.")

class Player:
    def __init__(self):
        self.row = 0
        self.col = 0
        self.color = BLUE

    def move(self, key, grid):
        cell = grid[self.row][self.col]

        if key == K_UP and not cell.up and self.row > 0:
            self.row -= 1
        elif key == K_DOWN and not cell.down and self.row < ROWS - 1:
            self.row += 1
        elif key == K_LEFT and not cell.left and self.col > 0:
            self.col -= 1
        elif key == K_RIGHT and not cell.right and self.col < COLS - 1:
            self.col += 1

    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2
        y = self.row * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, self.color, (x, y), CELL_SIZE // 3)


class Enemy:
    def __init__(self):
        self.row = random.randint(0, ROWS - 1)
        self.col = random.randint(0, COLS - 1)
        self.color = RED

    def move(self, player, grid):
        self.row,self.col = new_enemy_position(self.row,self.col,player.row,player.col,grid)

    def draw(self, surface):
        x = self.col * CELL_SIZE + CELL_SIZE // 2
        y = self.row * CELL_SIZE + CELL_SIZE // 2
        pygame.draw.circle(surface, self.color, (x, y), CELL_SIZE // 3)

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
        if self.rect.collidepoint(event.pos) and gamestate.storedmove:
            last_move=gamestate.storedmove.pop()
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
            player.row,player.col,enemy.row,enemy.col = gamestate.initpos
            gamestate.storedmove.clear()
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
            gamestate.storedmove.clear() 
            generate_game(grid,player,enemy,gamestate)
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
            pygame.quit()
            sys.exit()
        
class Gamestate:
    def __init__(self):
        self.gameover = False
        self.storedmove = []
        self.initpos = (0,0,0,0)
        self.solution = []

def main():
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


if __name__ == "__main__":
    main()