"""
@brief  Python module for creating and manipulating Trellis objects, with
        options for printing the state to the terminal.
@file   trellis.py
@author Cem Adatepe, Joseph Chan
"""

import sys
import copy
from itertools import product
from collections import Counter
from blessed import Terminal
import argparse
from colorama import Style, Fore

"""
GLOBAL VARIABLES
"""
verbose = False

"""Trellis state & string representation: use bools"""
LEFT, LEFT_CHAR = True, Fore.RED + "o"
RIGHT, RIGHT_CHAR = False, Fore.GREEN + "x"


"""
HELPER FUNCTIONS 
 - charToSlot : Converts 'a' to 0, 'b' to 1, etc.
 - slotToChar : Inverse of charToSlot
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
        self.visited_states = []
        return

    def __str__(self):
        """String representation of row 'i' in the trellis."""
        chars = [[stateToChar(state) for state in row] for row in self.trellis]
        for row, col in self.visited_states:
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
        Expects a string 'char' as input: char is a single (upper- or lower-case) char.

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
        Resets to the original state, i.e. all LEFT, and clears visited_states.
        Note: doesn't change the ball_position.
        """
        self.trellis = [
            [LEFT for j in range(self.cols - i % 2)] for i in range(self.rows)
        ]
        self.visited_states = []

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
            self.visited_states = []
            return False

        self.visited_states.append(self.ball_position)
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

    """COMPUTATIONAL FUNCTIONS"""

    def getPeriod(self, element):
        """
        Given an element (represented as a string of atomic actions), returns
        the period of the element by iteratively applying its action until the
        state returns to the identity state.

        This always halts: there are finitely many states, and the trellis
        action is injective (Lemma 3.2), so periodicity is guaranteed (which
        also guaranteed that atomic actions on any trellis generate a group!).
        """
        self.reset()
        self.ball_position = None
        rewrites = getRewrites(chars=self.atomic, period=self.period)

        count = 0
        orbit = []

        """Add balls until we go back to the identity."""
        while True:
            count += 1
            orbit.append(reduce(element * count, rewrites, self.atomic))
            self.drop_balls(element)
            if self.isIdentity():
                break

        if verbose:
            print(orbit)
        return count

    def getOrbit(self, element: str, start: str = ""):
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
        orbit, count = [reduce(start + element, ["a", "b", "c"])], 1
        while self.trellis != initial_config:
            self.drop_balls(element)
            count += 1
            orbit.append(reduce(start + element * count, ["a", "b", "c"]))
        return orbit


"""
STRING LIBRARY
Functions for generating strings of actions.
"""


def charsToN(chars, n=8):
    """Returns the set {chars}^n of strings over {chars}."""
    return list(map("".join, product(chars, repeat=n)))


def upToCount(actions):
    """
    Since atomic actions commute, filter `actions` to remove identical elements
    (by commuting atomic actions).
    """
    return list(set(map(lambda str: "".join(sorted(str)), actions)))


def allActions(chars, n=8):
    """
    Generates all actions over the alphabet {chars}.
    If n is given as the period of any atomic element in chars, we return
      n^|{chars}| many elements in a list.
    """
    index_tuples = product(range(n), repeat=len(chars))
    actions = [
        "".join(["".join(tupl[j] * chars[j] for j in range(len(chars)))])
        for tupl in index_tuples
    ]
    return actions


def getRewrites(chars: list[str], period: int = 8):
    """
    Generates a list of rewrites for a given set of {char}'s and period.
    WARNING : naively, this is EXPONENTIAL in |{char}| !
    WARNING : as-is, doesn't work for cases as simple as {a,b,c,d} and period=8!

    All rewrite rules are generated ultimately from identity elements, which (we
    conjecture, and can computationally verify for small cases) are of the form
    (abc)^2k. Essentially, we are trying to 'mod' out by the identity elements.

    The key insight is that each identity can be turned into a rewrite rule by
    turning each number into its inverse, e.g. when the period is 8, then

        a^{-2} == a^6     and more generally    r^{-k} == r^{n-k}

    Computationally, each bitstring of length |{char}| corresponds to a rewrite
    rule ('negate' the elements as above when the bit is 1, and leave it when
    the bit is 0). For example, the bitstring '100' corresponds to

            a^{-6} b^2 c^2              (since 2 ~= -6 mod 8)
        ~=  Counter(a=-6, b=2, c=2)     (our representation)

    Also, we want our rewrites to be reducing, so we can simply filter our list.
    We want to exclude 'reversible' rewrites that don't change weight too.
    """

    def reducingTuple(rewriteTuple: tuple):
        """
        Helper: 'flips' the tuple to ensure that the weight doesn't increase.
        For a given rewrite tuple (k,l,m), (-k,-l,-m) is also the identity,
        so we just search for 2k <= period / 2 and choose the tuple that
        decreases weight.

        If both tuples don't change weight (i.e. their sum is 0), we pick the
        first one and discard the second. This way we EXCLUDE reversible
        rewrites.
        """
        weight = sum(rewriteTuple)
        if weight < 0:
            return rewriteTuple
        elif weight > 0:
            return tuple(-elt for elt in rewriteTuple)
        else:
            if rewriteTuple in reversibleTuples:
                return (-2, -2, -2)
            else:
                reversibleTuples.add(tuple(-elt for elt in rewriteTuple))
                return rewriteTuple

    def tupleToCounter(rewriteTuple: tuple):
        """Helper: converts a rewrite tuple to a Counter object."""
        return Counter(dict(zip(chars, rewriteTuple)))

    reversibleTuples = set()
    rewriteRules = []

    """Generate 2k = { 2, 4, 6, ... , period / 2 } ."""
    for n in range(2, period // 2 + 1, 2):
        tuples = map(reducingTuple, product([-n, period - n], repeat=len(chars)))
        rewriteRules += list(map(tupleToCounter, set(tuples)))

    return rewriteRules


def reduce(action, rewrites, chars=["a", "b", "c"]):
    """Iterates 'reduceStep' until we hit a fixed point."""

    # Simple type-checking
    action, chars = action.lower(), list(map(str.lower, chars))
    if set(list(action)) - set(chars):
        raise ValueError(f"Action '{action}' contains chars not in '{chars}'")

    # Helper functions
    def counterToStr(action: Counter):
        """Helper: converts action Counter to string."""
        return "".join(sorted(action.elements()))

    def reduceStep(action: Counter):
        for rewrite in rewrites:
            if all(action[char] + rewrite[char] >= 0 for char in chars):
                action = action + rewrite
                # print(f"Reducing by rule {list(rewrite.items())} to '{counterToStr(action)}'.")
        return action

    # Main function body
    # print(f"reduce('{action}')")
    action = Counter(action)

    while True:
        new_action = reduceStep(action)
        if new_action == action:
            # print("No more reductions!\n")
            break
        else:
            action = new_action

    return counterToStr(action)


def allReducedActions(chars=["a", "b", "c"], period=8):
    """
    Version 1: only works for vanilla trellises (height=1, width=2).
    """
    rewrites = getRewrites(chars, period)
    return list(
        set(reduce(action, rewrites, chars) for action in allActions(chars, period))
    )


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
        """Quick script for trellis.py to brute-force periods."""
        trellis = Trellis(h=2, w=2)
        print("Setting up trellis...")
        print(trellis), print()

        print("Getting rewrite rules...")
        rewrites = getRewrites(trellis.atomic, period=trellis.period)

        print("Calculating irreducible actions and their periods...")
        actions = {
            action: trellis.getPeriod(action)
            for action in map(
                lambda elt: reduce(elt, rewrites, trellis.atomic),
                allActions(trellis.atomic, n=trellis.period),
            )
        }
        irreducibles = list(actions.keys())
        print(f"Number of irreducible group elements: {len(irreducibles)}")
        print()
        print(f"Periods: { set(actions.values()) }")
        print()

        # for p in range(1, 8+1):
        #     print(f"Period {p}:")
        #     print([action for action, period in actions.items() if period == p])
        #     print()
