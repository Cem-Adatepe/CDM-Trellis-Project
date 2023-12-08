"""
TRELLIS MODULE
@brief  Python module for creating and manipulating Trellis objects, with
        options for printing the state to the terminal.
@file   trellis.py
@author Cem Adatepe, Joseph Chan
"""

from GroupActions import allActions, getRewrites, reduce

import sys  # Checks for interactive mode
import copy  # Deep-copy functionality
from tqdm import tqdm  # Cosmetic progress bar
from colorama import Style, Fore

from blessed import Terminal
import argparse

"""
GLOBAL VARIABLES
"""
verbose = False

"""Trellis state & string representation: use bools"""
LEFT, LEFT_CHAR = True, Fore.RED + "o"
RIGHT, RIGHT_CHAR = False, Fore.GREEN + "x"


"""
HELPER FUNCTIONS 
 - stateToChar : Returns string representation of a state
"""


def stateToChar(isLeft):
    return LEFT_CHAR if isLeft else RIGHT_CHAR


class Trellis:
    """
    Defines a Trellis class.
     - Following the handout, a Trellis is a grid of 'X's, so the default
       trellis (the 1x2 trellis) has 3 'rows' and 3 'columns'.
    """

    def __init__(self, h=1, w=2):
        self.height, self.width = h, w
        self.rows = 2 * self.height + 1
        self.cols = self.width + 1
        self.period = 2**self.rows
        self.trellis = [
            [LEFT for j in range(self.cols - i % 2)] for i in range(self.rows)
        ]
        self.ball_position = None
        self.atomic = [self.slotToChar(i) for i in range(self.cols)]
        self.ball_path = []
        return

    def __str__(self):
        """String representation of row 'i' in the trellis."""
        chars = [[stateToChar(state) for state in row] for row in self.trellis]
        for row, col in self.ball_path:
            chars[row][col] = Style.BRIGHT + chars[row][col] + Style.RESET_ALL
        rows = ["   ".join(row) for row in chars]
        for i in range(len(rows)):
            if i % 2 == 1:
                rows[i] = "  " + rows[i] + "  "
        return "\n".join(rows) + Style.RESET_ALL

    def __repr__(self):
        """A representation of the configuration (C x S)."""
        return f"<Trellis C={self.trellis}, S={self.ball_position}>"

    def charToSlot(self, char: str):
        """
        Expects a string 'char' as input: 'char' is a single (upper- or lower-
        case) alphabet.

        It returns its corresponding slot number: mapping
        'A' == 'a' == 0
        'B' == 'b' == 1, etc.
        """
        assert self.isValidAction(char), f"Action '{char}' is not in range"
        return ord(char.lower()) - ord("a")

    def slotToChar(self, int: int):
        if int not in range(ord("z") - ord("a") + 1):
            raise ValueError(f"slotToChar: int {int} not between 0 and 25")
        return chr(int + ord("a"))

    def isValidAction(self, char: str):
        """Checks if slot (single char) is in range."""
        return char.lower() in self.atomic

    def isValidElement(self, chars: str):
        """Checks if sequence of atomic actions are all in range."""
        return all(self.isValidAction(char) for char in chars)

    def goesLeft(self):
        """Returns true iff ball goes left from current ball_position"""
        row, col = self.ball_position
        return self.trellis[row][col]

    def isIdentity(self):
        """
        Returns true if trellis returns to initial state, i.e. all left.
        Note: assumes here that LEFT == True.
        """
        return all(all(row) for row in self.trellis)

    def reset(self):
        """
        Resets to the original state, i.e. all LEFT, and clears ball_path.
        Note: doesn't change the ball_position.
        """
        self.trellis = [
            [LEFT for j in range(self.cols - i % 2)] for i in range(self.rows)
        ]
        self.ball_path = []

    def flipState(self, i: int, j: int):
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
            if verbose:
                print(self), print()
            self.ball_path = []
            return False

        self.ball_path.append(self.ball_position)
        row, col = self.ball_position

        # Last (even) layer : remove ball
        if row == self.rows - 1:
            self.ball_position = None

        # Odd layer
        elif row % 2 == 1:
            if self.goesLeft():
                self.ball_position = (row + 1, col)
            else:
                self.ball_position = (row + 1, col + 1)

        # Even layer
        else:
            # Left-most slot
            if col == 0:
                if self.goesLeft():
                    self.ball_position = (row + 2, col)
                else:
                    self.ball_position = (row + 1, col)
            # Right-most slot
            elif col == self.cols - 1:
                if self.goesLeft():
                    self.ball_position = (row + 1, col - 1)
                else:
                    self.ball_position = (row + 2, col)
            # Non-edge slot
            else:
                if self.goesLeft():
                    self.ball_position = (row + 1, col - 1)
                else:
                    self.ball_position = (row + 1, col)

        self.flipState(row, col)
        return True

    def drop_ball(self, char: str):
        """
        Iterates the basic action 'update'.
        Slot is a valid single-letter action (in self.atomic).
        """
        assert self.ball_position == None, "drop_ball: There's already a ball"
        assert self.isValidAction(char), f"drop_ball: Invalid action '{char}'"
        slot = self.charToSlot(char)

        # Add the ball, and iterate update
        self.ball_position = (0, slot)
        while self.update():
            continue

    def drop_balls(self, chars: str):
        """Iterates the 'drop_ball' action."""
        for char in chars:
            self.drop_ball(char)

    """
    COMPUTATIONAL FUNCTIONS
    These functions use the trellis to do period/orbit calculations.

     - getOrbit     : returns the orbit of a group element (from any position)
     - getPeriod    : finds the period of an element (by calling getOrbit on 1)
    
    Most of these are defined in GroupActions.py. We define them here with
    trellis variables as function input to simplify their usage.

     - allActions   : returns a list of all possible actions, up to rewrite rules
     - getRewrites  : computes rewrite rules for the trellis
     - reduce       : reduce an action, according to rewrite rules
     - allReducedActions    : computes all actions, modulo SOME reduction rules
    """

    def getPeriod(self, chars: str):
        """
        Finds the period of an element 'chars' by finding the orbit of its
        action on the identity trellis.

        This always halts: there are finitely many states, and the trellis
        action is injective (Lemma 3.2), so periodicity is guaranteed (which
        also guaranteed that atomic actions on any trellis generate a group!).
        """
        orbit = self.getOrbit(chars)
        if verbose:
            print("Orbit:", orbit)
        return len(orbit)

    def getOrbit(self, chars: str, start: str = ""):
        """
        Returns the orbit of an element, represented as a list of (reduced)
        elements. Optionally, begins at a starting element indicated by start.

        Version 1: only works with trellises of width=2.
        Currently, getRewrites isn't guaranteed to halt for larger trellises...
        """
        assert self.isValidElement(chars), f"getOrbit: invalid element '{chars}'"
        assert self.isValidElement(start), f"getOrbit: invalid start '{start}'"

        # Initialise trellis to 'start' state; get rewrite rules
        self.reset()
        self.ball_position = None
        self.drop_balls(start)
        initial_config = copy.deepcopy(self.trellis)

        count = 0
        orbit = []

        # Drop balls until we return to initial config
        while True:
            orbit.append(self.reduce(start + chars * count))
            self.drop_balls(chars)
            count += 1
            if self.trellis == initial_config:
                break

        return orbit

    def allActions(self):
        """Generates all trellis actions, up to 'self.period'-many of each."""
        return allActions(chars=self.atomic, period=self.period)

    def getRewrites(self, strictly_weight_reducing=True):
        """
        Rewrite rules for trellis, as Counter objects.
        If strictly_weight_reducing=False, we include some weight-preserving
        rewrites, too. There's still no guarantee we won't loop! e.g.

            a4c6 --> b4c2d4 --> a6c2d2 --> a4c6

        using rules

            a4c4 -> b4d4
            b2c2d2 -> a6
            a2b2d2 -> c6

        in a Trellis(h=1,w=3).
        """
        return getRewrites(
            chars=self.atomic,
            period=self.period,
            strictly_weight_reducing=strictly_weight_reducing,
        )

    def reduce(self, action: str, strictly_weight_reducing=True):
        """Reduces an action (a string) using trelli's rewrite rules."""
        return reduce(
            action=action,
            rewrites=self.getRewrites(strictly_weight_reducing),
            chars=self.atomic,
        )

    def allReducedActions(self, strictly_weight_reducing=True):
        """Filters output of 'self.allActions()' using trellis' rewrite rules."""
        reduced = [
            self.reduce(action, strictly_weight_reducing)
            for action in tqdm(self.allActions(), desc="Calculating reduced elements")
        ]
        return list(set(reduced))


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

    else:
        """
        Quick script for trellis.py to brute-force periods. Some results:

        ---------------------------------------------------------------
        Trellis    Irreducibles   Group                Generators of Cn
        ---------------------------------------------------------------
          1x1           16        (C8  x C2)           <a,ab> (?)
          2x1           64
          3x1          256
        ---------------------------------------------------------------
          1x2          128        (C8  x C8  x C2)     <a,c,abc>
          2x2         2048        (C32 x C32 x C2)     <a,c,abc>
        ---------------------------------------------------------------
          1x3         2096  (?)
          2x3        78608  (?)
        ---------------------------------------------------------------
          1x4        12288
        ---------------------------------------------------------------
          1x5       111488  (?)
        ---------------------------------------------------------------

        For trellises of odd width, we likely have extra irreducibles that are
        congruent (since we're likely overcounting, we mark it with a '?'). One
        idea is to map each action to the state it induces on the trellis, so
        we can 'mod' out by equivalent group action.
        """
        trellis = Trellis(h=2, w=2)
        print("Setting up trellis...")
        print(trellis), print()

        irreducibles = trellis.allReducedActions(strictly_weight_reducing=False)
        print(f"Number of irreducible group elements: {len(irreducibles)}")
        print()

        if True:
            actions = {
                action: trellis.getPeriod(action)
                for action in tqdm(irreducibles, desc="...and getting their periods")
            }
            print(f"Periods: {set(actions.values())}")
            print()

        # for p in range(1, 8+1):
        #     print(f"Period {p}:")
        #     print([action for action, period in actions.items() if period == p])
        #     print()
