"""
@brief  Python module for creating and manipulating Trellis objects, with
        options for printing the state to the terminal.
@file   trellis.py
@author Cem Adatepe, Joseph Chan
"""

from blessed import Terminal
import argparse
import sys

"""
GLOBAL VARIABLES
"""
verbose = True

"""Trellis state representation: use bools"""
LEFT = True
RIGHT = False

class Trellis:
    """
    Defines a Trellis class.
     - Following the handout, a Trellis is a grid of 'X's, so the default 
       trellis (the 1x2 trellis) has 3 'rows' and 3 'columns'.
    """
    def __init__(self, h=1, w=2):
        self.height, self.width = h, w
        self.rows = 2*self.height + 1
        self.cols = self.width + 1
        self.trellis = [[LEFT for j in range(self.cols - i % 2)] for i in range(self.rows)]
        self.ball_position = None

    def rowToString(self, i):
        """Returns string repr'n of row 'i' in the trellis."""
        row = self.trellis[i]
        res = '   '.join([stateToString(row[j]) for j in range(len(row))])
        if i % 2 == 1:
            res = '  ' + res + '  '
        return res

    def __str__(self):
        """String repr'n of the trellis in its current state"""
        return '\n'.join([self.rowToString(i) for i in range(self.rows)])

    def __repr__(self):
        """A repr'n of the configuration C x S."""
        return f'<Trellis C={self.trellis}, S={self.ball_position}>'

    def isValidAction(self, slot):
        if isinstance(slot, (str)):
            slot = charToSlot(slot)
        return slot in range(self.cols)

    def isStateLeft(self):
        """Returns true iff ball goes left from current ball_position"""
        row, col = self.ball_position
        return self.trellis[row][col]

    def isIdentity(self):
        """
        Returns true if trellis returns to initial state, i.e. all left.
        Note: assumes here that LEFT == True.
        """
        return all(map(all, self.trellis))

    def reset(self):
        """
        Resets to the original state, i.e. all LEFT.
        """
        for row in range(len(self.trellis)):
            for col in range(len(self.trellis[row])):
                self.trellis[row][col] = LEFT

    def flipState(self, i, j):
        """
        Flips the state at (i,j).
        Note: assumes here that states are represented by bool's.
        """
        self.trellis[i][j] = not self.trellis[i][j]

    def update(self):
        """
        Implements the 'basic action': updates the state and ball position.
        Returns True if there's still a ball in the trellis (i.e. we should
          continue updating).
        """
        if self.ball_position == None:
            return False

        row, col = self.ball_position

        # Last (even) layer : remove ball
        if row == self.rows -1:
            self.ball_position = None

        # Odd layer
        elif row % 2 == 1:
            if self.isStateLeft():
                self.ball_position = (row+1, col)
            else:
                self.ball_position = (row+1, col+1)

        # Even layer
        else:
            # Left-most slot
            if col == 0:
                if self.isStateLeft():
                    self.ball_position = (row+2, col)
                else:
                    self.ball_position = (row+1, col)
            # Right-most slot
            elif col == self.cols - 1:
                if self.isStateLeft():
                    self.ball_position = (row+1, col-1)
                else:
                    self.ball_position = (row+2, col)
            # Non-edge slot
            else:
                if self.isStateLeft():
                    self.ball_position = (row+1, col-1)
                else:
                    self.ball_position = (row+1, col)

        self.flipState(row,col)
        return True

    def drop_ball(self, slot):
        """
        Iterates the basic action 'update'.
        Slot can either be
          an integer, 0 <= slot < self.cols; or
          a letter, such that 0 <= charToSlot(slot) < self.cols.
        """
        if self.ball_position != None:
            raise AssertionError("drop_ball: There's already a ball")

        if isinstance(slot, (str)):
            slot = charToSlot(slot)

        if not self.isValidAction(slot):
            raise ValueError(f"drop_ball: slot '{slotToChar(slot)}' not "
                             f"between 'a' and '{slotToChar(self.cols - 1)}'")

        # Add the ball, and iterate update
        self.ball_position = (0,slot)
        if verbose:
            print(self)
            print('-' * len(self.rowToString(0)))

        while self.update():
            if verbose:
                print(self)
                print('-' * len(self.rowToString(0)))

    def drop_balls(self, slots):
        """Iterates the 'drop_ball' action."""
        if slots != "" and not slots.isalpha():
            raise ValueError(f'drop_balls: slots must be a string of letters')
        for slot in slots:
            self.drop_ball(slot)

    """
    COMPUTATIONAL FUNCTIONS
    """
    def getPeriod(self, element):
        """
        Given an element (repr'd as a string of atomic actions), returns the
        period of the element by iteratively applying its action until the state
        returns to the identity state.

        This always halts: there are finitely many states, and the trellis
        action is injective (Lemma 3.2), so periodicity is guaranteed (which
        also guaranteed that atomic actions on any trellis generate a group!).
        """
        self.reset()
        self.drop_balls(element)
        count = 1
        while not self.isIdentity():
            self.drop_balls(element)
            count += 1
        return count

"""
HELPER FUNCTIONS 
 - charToSlot : Converts 'a' to 0, 'b' to 1, etc.
 - slotToChar : Inverse of charToSlot
 - stateToString : Returns string repr'n of states
"""
def charToSlot(char):
    """
    char is a single (upper- or lower-case) char.
    It returns its corresponding slot: mapping
      'A' == 'a' == 0
      'B' == 'b' == 1, etc.
    """
    if len(char) != 1 or not char.isalpha():
        raise ValueError(f'charToSlot: expected an single letter, got: {char}')
    if char.isupper():
        return ord(char) - ord('A')
    return ord(char) - ord('a')

def slotToChar(int):
    if int not in range(ord('z') - ord('a') + 1):
        raise ValueError(f'slotToChar: int {int} not between 0 and 25')
    return chr(int + ord('a'))

def stateToString(stateIsLeft):
    return 'o' if stateIsLeft else 'x'


if __name__ == "__main__":
    """Run this only if 'trellis.py' is run directly, not as an import."""
    if sys.flags.interactive:
        print(f"Verbose mode: {verbose}")
        print(f"Set bool 'verbose' to toggle verbose mode.")

    trellis = Trellis()
    print(trellis)
