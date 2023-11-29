"""
@brief  Python module for creating and manipulating Trellis objects, with
        options for printing the state to the terminal.
@file   trellis.py
@author Cem Adatepe, Joseph Chan
"""

from blessed import Terminal
import argparse

class Trellis:
    """
    Defines a Trellis class.
     - Following the handout, a Trellis is a grid of 'X's, so the default trellis
       (the 1x2 trellis) has 3 'rows' and 3 'columns'.
     - STATE : left == False, right == True
    """
    def __init__(self, h=1, w=2):
        self.height, self.width = h, w
        self.rows = 2*self.height + 1
        self.cols = self.width + 1
        self.trellis = [[False for j in range(self.cols - i % 2)] for i in range(self.rows)]
        self.ball_position = None

    def __str__(self):
        str = ""
        for i in range(len(self.trellis)):
            if i % 2 == 1: str += "  " 
            for j in range(len(self.trellis[i])):
                str += 'o' if self.trellis[i][j] else 'x'
                str += "   "
            str += '\n'
        str = str[:-1]
        return str

    def isStateRight(self):
        """Returns true iff ball goes right"""
        row, col = self.ball_position
        return self.trellis[row][col]

    def flipState(self, i, j):
        """Flips the state at (i,j)"""
        self.trellis[i][j] = not self.trellis[i][j]
    
    def update(self):
        """
        Implements the 'basic action': updates the state and ball position.
        Returns True if there's still a ball in the trellis (i.e. we should
          continue updating.)
        """
        if self.ball_position == None:
            return False
        
        row, col = self.ball_position

        # Last (even) layer : remove ball
        if row == self.rows -1:
            self.ball_position = None

        # Odd layer
        elif row % 2 == 1:
            if self.isStateRight():
                self.ball_position = (row+1, col+1)
            else:
                self.ball_position = (row+1, col)

        # Even layer
        else:
            # Left-most slot
            if col == 0:
                if self.isStateRight():
                    self.ball_position = (row+1, col)
                else:
                    self.ball_position = (row+2, col)
            # Right-most slot
            elif col == self.cols - 1:
                if self.isStateRight():
                    self.ball_position = (row+2, col)
                else:
                    self.ball_position = (row+1, col-1)
            # Non-edge slot
            else:
                if self.isStateRight():
                    self.ball_position = (row+1, col)
                else:
                    self.ball_position = (row+1, col-1)
        
        self.flipState(row,col)
        return True
    
    def drop_ball(self, slot):
        """Iterates the basic action 'update'."""
        if self.ball_position != None:
            print("There's already a ball")
            return
        if slot not in range(self.cols):
            print("Invalid slot")
            return
        
        # Add the ball, and iterate update
        self.ball_position = (0,slot)
        while self.update():
            print(self)
            print('---' * self.cols)

if __name__ == "__main__":
    """Run this only if 'trellis.py' is run directly, not as an import"""
    trellis = Trellis()
    print(trellis)