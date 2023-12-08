"""
GROUP ACTIONS LIBRARY
@brief  Helper functions for generating strings of actions.
"""

from itertools import product
from collections import Counter


def allActions(chars, period: int = 8):
    """
    Generates all actions over an alphabet {chars}, up to 'period'-many of each.
    We return n^|{chars}| many elements in a list.
    """
    index_tuples = product(range(period), repeat=len(chars))
    actions = [
        "".join(["".join(tupl[j] * chars[j] for j in range(len(chars)))])
        for tupl in index_tuples
    ]
    return actions


def _invert(rewrite_tuple: tuple) -> tuple:
    """Helper: 'flips' a tuple, e.g. from (6,-2,-2) to (-6,2,2)."""
    return tuple(-elt for elt in rewrite_tuple)


def getRewrites(chars, period: int = 8, strictly_weight_reducing=True):
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
    We can optionally exclude 'reversible' rewrites that don't change weight
    too.
    """

    # Track reversible tuples we've added: don't add a rewrite AND its inverse
    already_seen_reversible_rewrites = set()
    rewriteRules = []

    def reducingTuple(rewrite_tuple: tuple):
        """
        Helper: 'flips' the tuple to ensure that the weight doesn't increase.
        For a given rewrite tuple (k,l,m), (-k,-l,-m) is also the identity,
        so we just search for 2k <= period / 2 and choose the tuple that
        decreases weight.

        If both tuples don't change weight (i.e. their sum is 0), we pick the
        first one and discard the second. This way we EXCLUDE reversible
        rewrites.
        """
        weight = sum(rewrite_tuple)

        # Add strictly weight-reducing tuples
        if weight < 0:
            return rewrite_tuple

        # If strictly weight-increasing, add its inverse
        elif weight > 0:
            return _invert(rewrite_tuple)

        # Make sure we don't add a rewrite and its inverse: infinite rewrites!
        elif not strictly_weight_reducing:
            if rewrite_tuple not in already_seen_reversible_rewrites:
                already_seen_reversible_rewrites.add(_invert(rewrite_tuple))
                return rewrite_tuple
            return None

        return None

    def tupleToCounter(rewriteTuple: tuple):
        """Helper: converts a rewrite tuple to a Counter object."""
        return Counter(dict(zip(chars, rewriteTuple)))

    # Generate 2k = { 2, 4, 6, ... , period / 2 } .
    for n in range(2, period // 2 + 1, 2):
        all_tuples = list(product([-n, period - n], repeat=len(chars)))
        reducing = set(reducingTuple(index_tuple) for index_tuple in all_tuples)
        reducing.discard(None)
        rewriteRules += [tupleToCounter(index_tuple) for index_tuple in reducing]

    return rewriteRules


def _counterToStr(action: Counter):
    """Helper: converts action Counter to string."""
    return "".join(sorted(action.elements()))


def reduce(action: str, rewrites: list[Counter], chars=["a", "b", "c"]):
    """Iterates 'reduceStep' until we hit a fixed point."""

    # Simple type-checking
    action = action.lower()
    chars = [str.lower(char) for char in chars]
    if set(list(action)) - set(chars):
        raise ValueError(f"Action '{action}' contains chars not in '{chars}'")

    def reduceStep(action: Counter):
        for rewrite in rewrites:
            if all(action[char] + rewrite[char] >= 0 for char in chars):
                action = action + rewrite
                # print(
                #     f"Reducing by rule {list(rewrite.items())} to '{_counterToStr(action)}'."
                # )
        return action

    """Main function body."""
    action = Counter(action)
    # print(f"reduce('{action}')")

    while True:
        new_action = reduceStep(action)
        if new_action == action:
            # print("No more reductions!\n")
            break
        action = new_action

    return _counterToStr(action)


def allReducedActions(
    chars: str,
    rewrites: list[Counter],
    period: int = 8,
    strictly_weight_reducing: bool = True,
):
    """
    Returns all reduced actions by generating all actions (up to period) and
    reducing each one.

     'chars'  The alphabet to reduce over, e.g. ['a','b','c']
     'period' The largest period of any group element (8, for the 1x2 trellis).
     'strictly_weight_reducing' Whether to generate weight-preserving rewrites.

    If we use only strict rewrite rules, we MAY end up with some identical
    elements in the result.
    """
    # rewrites = getRewrites(chars, period, strictly_weight_reducing)
    reduced = [reduce(action, rewrites, chars) for action in allActions(chars, period)]
    return list(set(reduced))
