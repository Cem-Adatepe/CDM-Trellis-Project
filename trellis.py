"""
@brief  Python module for creating and manipulating Trellis objects, with
        options for printing the state to the terminal.
@file   trellis.py
@author Cem Adatepe, Joseph Chan
"""

import sys
import copy
import itertools
from collections import Counter
from blessed import Terminal
import argparse

"""
GLOBAL VARIABLES
"""
verbose = False

"""Trellis state & string representation: use bools"""
LEFT,  LEFT_CHAR  = True,  'o'
RIGHT, RIGHT_CHAR = False, 'x'

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
        """Checks if slot (single char, or int) is in range."""
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
        assert self.ball_position == None, "drop_ball: There's already a ball"
        if isinstance(slot, (str)):
            slot = charToSlot(slot)
        if not self.isValidAction(slot):
            raise ValueError(f"drop_ball: slot '{slotToChar(slot)}' not "
                             f"between 'a' and '{slotToChar(self.cols - 1)}'")

        # Add the ball, and iterate update
        self.ball_position = (0,slot)
        while self.update():
            if verbose:
                print(self)
                print('-' * len(self.rowToString(0)))

    def drop_balls(self, slots):
        """Iterates the 'drop_ball' action."""
        if slots != "" and not slots.isalpha():
            raise ValueError(f'drop_balls: slots must be a string of letters')
        if verbose:
            print(self)
            print('-' * len(self.rowToString(0)))
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
        self.ball_position = None
        self.drop_balls(element)
        count = 1
        orbit = []
        if verbose:
            orbit.append(reduce(element, ['a','b','c']))
        while not self.isIdentity():
            self.drop_balls(element)
            count += 1
            if verbose:
                orbit.append(reduce(element * count, ['a','b','c']))
        if verbose:
            print(orbit)
        return count
    
    def getOrbit(self, element: str, start: str=''):
        """
        Returns the orbit of an element, represented as a list of (reduced) 
        elements. Optionally, begins at a starting element indicated by start.

        Version 1: only works with trellises of width=2.
        """
        assert all(map(self.isValidAction, list(element))), "getOrbit: invalid element"
        assert all(map(self.isValidAction, list(element))), "getOrbit: invalid start"

        self.reset()
        self.ball_position = None
        self.drop_balls(start)
        initial_config = copy.deepcopy(self.trellis)

        self.drop_balls(element)
        orbit, count = [reduce(start + element, ['a','b','c'])], 1
        while self.trellis != initial_config:
            self.drop_balls(element)
            count += 1
            orbit.append(reduce(start + element * count, ['a','b','c']))
        return orbit

"""
HELPER FUNCTIONS 
 - charToSlot : Converts 'a' to 0, 'b' to 1, etc.
 - slotToChar : Inverse of charToSlot
 - stateToString : Returns string repr'n of states
"""
def charToSlot(char):
    """
    Expects a string 'char' as input: char is a single (upper- or lower-case) 
    char.
    
    It returns its corresponding slot number: mapping
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
    return LEFT_CHAR if stateIsLeft else RIGHT_CHAR

"""
STRING LIBRARY
Functions for generating strings of actions.
"""
def charsToN(chars, n=8):
    """Returns the set {chars}^n of strings over {chars}."""
    return list(map(''.join, itertools.product(chars, repeat=n)))

def upToCount(actions):
    """
    Since atomic actions commute, filter `actions` to remove identical elements
    (by commuting atomic actions).
    """
    return list(set(map(lambda str: ''.join(sorted(str)), actions)))

def allActions(chars, n=8):
    """
    Generates all actions over the alphabet {chars}.
    If n is given as the period of any atomic element in chars, we return
      n^|{chars}| many elements in a list.
    """
    index_tuples = itertools.product(range(n), repeat=len(chars))
    actions = [ 
        ''.join([
            ''.join(tupl[j] * chars[j] for j in range(len(chars)))
        ]) for tupl in index_tuples
    ]
    return actions

# def getRewrites(chars, period=8):

def reduceStep(action, chars):
    """
    Given an action over {chars}, tries to apply one of the reduction rules.

    Version 1: only works for trellises (height=1, width=2).
    """
    # print(f"reduceStep('{action}', {chars})")

    action, chars = action.lower(), list(map(str.lower, chars))
    if set(list(action)) - set(chars):
        raise ValueError(f"Action '{action}' contains chars not in '{chars}'")
    
    # Re-write as a Counter object:
    action = Counter(action)

    # Re-write rules
    rewrites = [
        Counter(a= 2, b=2,  c=2),
        Counter(a= 4, b=4,  c=-4),
        Counter(a= 4, b=-4, c=4),
        Counter(a=-4, b=4,  c=4),
        Counter(a= 6, b=-2, c=-2),
        Counter(a=-2, b=6,  c=-2),
        Counter(a=-2, b=-2, c=6)
    ]

    for rewrite in rewrites:
        if all(rewrite[char] <= action[char] for char in chars):
            res = ''.join(sorted((action - rewrite).elements()))
            # print(f"Reducing by rule: {list(rewrite.items())} to '{res}'.")
            return res
    # print(f"No more reductions!\n")
    return ''.join(sorted(action.elements()))

def reduce(action, chars):
    """
    Iterates the 'reduceStep' action until we've hit a fixed point.
    
    Version 1: only works for trellises of (height=1, width=2).
    """
    while True:
        new_action = reduceStep(action, chars)
        if Counter(new_action) == Counter(action):
            return new_action
        else:
            action = new_action

def allReducedActions(chars=None, n=8):
    """
    Version 1: only works for vanilla trellises (height=1, width=2).
    """
    chars = ['a','b','c']
    return list(set(reduce(action, chars) for action in allActions(chars, n)))

"""
Run this section only if 'trellis.py' is run directly, not as an import.
"""
if __name__ == "__main__":
    if sys.flags.interactive:
        print(f"Verbose mode: {verbose}")
        print(f"Set bool 'verbose' to toggle verbose mode.\n")
        print("trellis =")
    trellis = Trellis()
    print(trellis)
    print()

    """Quick script for trellis.py to brute-force periods"""
    if not sys.flags.interactive:
        chars = ['a','b','c']
        actions = {
            action: trellis.getPeriod(action) for action in
            map(lambda elt: reduce(elt, chars), allActions(chars, n=8))
        }
        irreducibles = list(actions.keys())
        print(f"Number of irreducible group elements: {len(irreducibles)}")
        print()
        print(irreducibles)
        print()

        for p in range(1, 8+1):
            print(f"Period {p}:")
            print([action for action, period in actions.items() if period == p])
            print()
