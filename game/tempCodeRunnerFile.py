URF)
        enemy.draw(DISPLAYSURF)
        for row in grid:
            for cell in row:
                cell.draw(DISPLAYSURF,grid)


        undobutton.draw(DISPLAYSURF)
        restartbutton.draw(DIS