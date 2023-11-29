class Trellis:
    def __init__(self, h = 1, w = 2):
        self.height = h
        self.width = w
        self.rows = 2 * self.height + 1
        self.cols = self.width + 1
        self.trellis = [[False for j in range (self.cols - i % 2) ] for i in range(self.rows)]
        self.ball_position = None
    def print(self):        
        for i in range(len(self.trellis)):
            if i % 2 == 1:
                print("  ", end= "")
            for j in range(len(self.trellis[i])):
                print("x" if self.getState(i,j) else "o", end="   ")
            print("")
    def flipState(self, i, j):
        self.trellis[i][j] = not self.trellis[i][j]
    def getState(self, i, j):
        return self.trellis[i][j]
    def isStateRight(self):
        row, col = self.ball_position
        return self.trellis[row][col]
    def update(self):
        if self.ball_position == None:
            return False
        
        row,col = self.ball_position

        if row == self.rows -1:
            self.flipState(row,col)
            self.ball_position = None
            return False
        if row % 2 == 1: #odd layer
            if self.isStateRight():
                self.ball_position = (row+1, col+1)
            else:
                self.ball_position = (row+1, col)
        else: #even layer
            if col == 0:
                if self.isStateRight():
                    self.ball_position = (row+1, col)
                else:
                    self.ball_position = (row+2, col)
            elif col == self.cols - 1:
                if self.isStateRight():
                    self.ball_position = (row+2, col)
                else:
                    self.ball_position = (row+1, col-1)
            else:
                if self.isStateRight():
                    self.ball_position = (row+1, col)
                else:
                    self.ball_position = (row+1, col-1)
        
        self.flipState(row,col)
        return True
    
    def drop_ball(self, slot):
        if self.ball_position != None:
            print("There's already a ball")
            return
        if slot not in range(self.cols):
            print("Invalid slot")
            return
        self.ball_position = (0,slot)
        while self.update():
            self.print()
            print("-------------------------------------------")
        return
        
            


trellis = Trellis()
trellis.print()