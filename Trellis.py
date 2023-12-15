"""
TRELLIS MODULE
@brief  Python module for creating and manipulating Trellis objects, with
        options for printing the state to the terminal.
@file   trellis.py
@author Cem Adatepe, Joseph Chan    
"""

import GroupActions  # allActions, getRewrites, reduce

import sys  # Checks for interactive mode
from tqdm import tqdm  # Cosmetic progress bar
from colorama import Style, Fore  # Pretty-printing with color
from itertools import chain  # Encoding trellis state

"""
GLOBAL VARIABLES
"""
verbose = False

"""Trellis state & string representation: use bools"""
LEFT = True
RIGHT = False

LEFT_CHAR = Fore.RED + "●"
RIGHT_CHAR = Fore.GREEN + "●"

"""
HELPER FUNCTIONS 
 - state_to_char : Returns string representation of a state
 - print_subset : Highlight subset of a set/list
"""


def state_to_char(isLeft):
    return LEFT_CHAR if isLeft else RIGHT_CHAR


def print_subset(universe: list[str], subset: list[str]):
    """Prints the full set (universe) and highlights the subset."""

    for s in universe:
        print(
            f"{Style.BRIGHT + Fore.GREEN}'{s}'" if s in subset else f"'{s}'",
            end=f" {Style.RESET_ALL}",
        )
    print()
    return


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
        self.atomic = [self.int_to_char(i) for i in range(self.cols)]
        self.ball_path = []
        return

    def __str__(self):
        """String representation of row 'i' in the trellis."""
        chars = [[state_to_char(state) for state in row] for row in self.trellis]
        for row, col in self.ball_path:
            chars[row][col] = Style.BRIGHT + chars[row][col] + Style.RESET_ALL
        rows = ["       ".join(row) for row in chars]
        for i, row in enumerate(rows):
            if i % 2 == 1:
                rows[i] = "    " + row + "    "
        return "\n\n".join(rows) + Style.RESET_ALL

    def __repr__(self):
        """A representation of the configuration (C x S)."""
        return f"<Trellis C={self.trellis}, S={self.ball_position}>"

    def char_to_int(self, char: str):
        """
        Expects a string 'char' as input: 'char' is a single (upper- or lower-
        case) alphabet.

        It returns its corresponding slot number: mapping
        'A' == 'a' == 0
        'B' == 'b' == 1, etc.
        """
        assert self.is_valid_action(char), f"Action '{char}' is not in range"
        return ord(char.lower()) - ord("a")

    def int_to_char(self, int: int):
        if int not in range(ord("z") - ord("a") + 1):
            raise ValueError(f"int_to_char: int {int} not between 0 and 25")
        return chr(int + ord("a"))

    def is_valid_action(self, char: str):
        """Checks if slot (single char) is in range."""
        return char.lower() in self.atomic

    def is_valid_element(self, chars: str):
        """Checks if sequence of atomic actions are all in range."""
        return all(self.is_valid_action(char) for char in chars)

    def goes_left(self):
        """Returns true iff ball goes left from current ball_position"""
        row, col = self.ball_position
        return self.trellis[row][col]

    def is_identity(self):
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

    def flip_state(self, i: int, j: int):
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
            if self.goes_left():
                self.ball_position = (row + 1, col)
            else:
                self.ball_position = (row + 1, col + 1)

        # Even layer
        else:
            # Left-most slot
            if col == 0:
                if self.goes_left():
                    self.ball_position = (row + 2, col)
                else:
                    self.ball_position = (row + 1, col)
            # Right-most slot
            elif col == self.cols - 1:
                if self.goes_left():
                    self.ball_position = (row + 1, col - 1)
                else:
                    self.ball_position = (row + 2, col)
            # Non-edge slot
            else:
                if self.goes_left():
                    self.ball_position = (row + 1, col - 1)
                else:
                    self.ball_position = (row + 1, col)

        self.flip_state(row, col)
        return True

    def drop_ball(self, char: str):
        """
        Iterates the basic action 'update'.
        Slot is a valid single-letter action (in self.atomic).
        """
        assert self.ball_position == None, "drop_ball: There's already a ball"
        assert self.is_valid_action(char), f"drop_ball: Invalid action '{char}'"
        slot = self.char_to_int(char)

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

     - get_orbit     : returns the orbit of a group element (from any position)
     - get_period    : finds the period of an element (by calling get_orbit on 1)
    
    Most of these are defined in GroupActions.py. We define them here with
    trellis variables as function input to simplify their usage.

     - allActions   : returns a list of all possible actions, up to rewrite rules
     - getRewrites  : computes rewrite rules for the trellis
     - reduce       : reduce an action, according to rewrite rules
     - allReducedActions    : computes all actions, modulo SOME reduction rules
    """

    def get_period(self, chars: str, strictly_weight_reducing=True):
        """
        Finds the period of an element 'chars' by finding the orbit of its
        action on the identity trellis.

        This always halts: there are finitely many states, and the trellis
        action is injective (Lemma 3.2), so periodicity is guaranteed (which
        also guaranteed that atomic actions on any trellis generate a group!).
        """
        orbit = self.get_orbit(chars, strictly_weight_reducing=strictly_weight_reducing)
        if verbose:
            print("Orbit:", orbit), print()
        return len(orbit)

    def get_orbit(self, chars: str, start: str = "", strictly_weight_reducing=True):
        """
        Returns the orbit of an element, represented as a list of (reduced)
        elements. Optionally, begins at a starting element indicated by start.

        Version 1: only works with trellises of width=2.
        Currently, getRewrites isn't guaranteed to halt for larger trellises...
        """
        assert self.is_valid_element(chars), f"get_orbit: invalid element '{chars}'"
        assert self.is_valid_element(start), f"get_orbit: invalid start '{start}'"

        # Initialise trellis to 'start' state; get rewrite rules
        self.reset()
        self.ball_position = None
        self.drop_balls(start)
        initial_state = self.encoded_trellis()

        count = 0
        orbit = []

        # Drop balls until we return to initial config
        while True:
            orbit.append(self.reduce(start + chars * count, strictly_weight_reducing))
            self.drop_balls(chars)
            count += 1
            if self.encoded_trellis() == initial_state:
                break

        return orbit

    def all_actions(self):
        """Generates all trellis actions, up to 'self.period'-many of each."""
        return GroupActions.allActions(chars=self.atomic, period=self.period)

    def get_rewrites(self, strictly_weight_reducing=True):
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
        return GroupActions.getRewrites(
            chars=self.atomic,
            period=self.period,
            strictly_weight_reducing=strictly_weight_reducing,
        )

    def reduce(self, action: str, strictly_weight_reducing=True):
        """Reduces an action (a string) using trelli's rewrite rules."""
        return GroupActions.reduce(
            action=action,
            rewrites=self.get_rewrites(strictly_weight_reducing),
            chars=self.atomic,
        )

    def all_reduced_actions(self, strictly_weight_reducing=True):
        """Filters output of 'self.allActions()' using trellis' rewrite rules."""
        reduced = [
            self.reduce(action, strictly_weight_reducing)
            for action in tqdm(self.all_actions(), desc="Calculating reduced elements")
        ]
        return list(set(reduced))

    def encoded_trellis(self):
        """
        Returns 'self.trellis' encoded as an int. We convert our trellis into a
        (flattened) bool array and then into a bitstring, and return the integer
        that the bitstring represents.
        """
        flattened = chain.from_iterable(self.trellis)
        return sum(map(lambda x: x[1] << x[0], enumerate(flattened)))

    def decode_trellis_states(self):
        pass

    def all_group_elements(self):
        """
        Wrapper around 'find_equivalent_actions' which returns the trellis group
        as a list of elements.
        """
        group = [
            elements[0]
            for state, elements in self.find_equivalent_actions(
                elements=self.all_actions()
            ).items()
        ]
        return group

    def find_equivalent_actions(self, elements=None):
        """
        Finds equivalent actions from 'elements' by comparing their action on
        the identity state (this works because trellis actions are free), i.e.
        if they have the same effect on the identity state, they have the same
        effect on all trellis states.

        This induces an equivalence relation on 'items' : they are equivalent if
        they take the identity state to the same result state.

        From each 'item' in 'elements, we compute a dictionary, 'visited' with
            keys   : encoded trellis state of 'item' on the identity state
            values : a list of equivalent 'items'
        """
        visited = {}

        if elements is None:
            elements = self.all_reduced_actions()

        for item in tqdm(elements, desc="Computing equivalent actions"):
            self.reset()
            self.drop_balls(item)
            encoded = self.encoded_trellis()
            if encoded not in visited:
                visited[encoded] = [item]
            else:
                visited[encoded] += [item]

        return visited


"""
Run this section only if 'trellis.py' is run directly, not as an import.
"""
if __name__ == "__main__":
    if sys.flags.interactive:
        print(f"Verbose mode: {verbose}")
        print(f"Set bool 'verbose' to toggle verbose mode.\n")
        print("trellis =")
        trellis = Trellis()
        print(trellis), print()

    else:
        """
        Quick script for trellis.py to brute-force periods. Some results:

        ---------------------------------------------------------------
        Trellis    Irreducibles   Group                Generators of Cn
        ---------------------------------------------------------------
          1x1             16      (C8  x C2)           <a,ab>
          2x1             32
          3x1             64
          4x1            128       patterns are 2x
        ---------------------------------------------------------------
          1x2            128      (C8  x C8  x C2)     <a,c,abc>
          2x2           2048      (C32 x C32 x C2)     <a,c,abc>
          3x2          32768 wtf?  patterns are x16
        ---------------------------------------------------------------
          1x3           1024         
          2x3          16384       patterns are x16  
        ---------------------------------------------------------------
          1x4           8192
        ---------------------------------------------------------------
          1x5          65536
        ---------------------------------------------------------------
          1x6         524288
        ---------------------------------------------------------------
        recursive rules:    
        a x b - > size
        (a x b+1) - > size * 8  
        """
        trellis = Trellis(h=2, w=1)
        print("Setting up trellis...")
        print(trellis), print()
        irreducibles = trellis.all_group_elements()

        if False:
            actions = {
                action: trellis.get_period(action)
                for action in tqdm(irreducibles, desc="...and getting their periods")
            }

            print()
            for p in range(1, trellis.period + 1):
                period_p_actions = [
                    action for action, period in actions.items() if period == p
                ]
                if period_p_actions:
                    print(Style.BRIGHT + f"Period {p}:" + Style.RESET_ALL)
                    print(sorted(period_p_actions, key=len))
                    print()

            print(f"Periods: {set(actions.values())}")

        print(f"Number of irreducible group elements: {len(irreducibles)}")
        print()
