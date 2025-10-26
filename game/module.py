import pygame, sys, random
from pygame.locals import *
from variable import *

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


def winning_check(player,gamestate):#Kiểm nếu người chơi đến góc
    if not gamestate.gameover and player.row == ROWS-1 and player.col == COLS-1:
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
        
        
def losing_check(player,enemy,gamestate):#Kiểm nếu quái trúng người chơi
        if player.row == enemy.row and player.col == enemy.col:
            gamestate.gameover = True
            text = font.render("Game Over", True, RED)
            DISPLAYSURF.blit(
                text,
                (
                    SCREEN_WIDTH // 2 - text.get_width() // 2,
                    SCREEN_HEIGHT // 2 - text.get_height() // 2,
                ),
            )
            image = pygame.image.load("assets/whitefight6.png").convert_alpha()
            image = pygame.transform.scale(image, (CELL_SIZE,CELL_SIZE))
            rect = image.get_rect(center=(player.col* CELL_SIZE + CELL_SIZE // 2, player.row* CELL_SIZE + CELL_SIZE // 2))
            DISPLAYSURF.blit(image, rect)
            pygame.display.update()
            # wait(2)
            # pygame.quit()
            # sys.exit()
            
            
def is_playable(player, enemy, grid,gamestate):#Xài BFS kiểm nếu có đường đi
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

def is_not_too_easy(player, enemy, grid):#Kiểm tra nếu quái có thể bắt được người chơi
    directions = [('up', -1, 0), ('down', 1, 0), ('left', 0, -1), ('right', 0, 1)]
    visited = [[False] * COLS for _ in range(ROWS)]

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
    
    return visited[enemy.row][enemy.col]


def generate_game(grid,player,enemy,gamestate):
    print("Generating new game...")

    while True:#Generate tường đến khi có đường đi
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
        if is_playable(player, enemy, grid,gamestate) and is_not_too_easy(player, enemy, grid):
            break
    gamestate.initpos=(player.row,player.col,enemy.row,enemy.col) #Lưu vị trí ban đầu
    gamestate.storedmove.append((player.row,player.col,enemy.row,enemy.col))
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
            if 0 <= r + d[2] < ROWS and 0 <= c + d[3] < COLS and not getattr(grid[r][c],d[0]):#Tường trong lưới và chưa có
                setattr(grid[r][c],d[0], 1)  
                setattr(grid[r + d[2]][c + d[3]],d[1], 1)  
                no_wall = False
                
    print("Walls generated.")