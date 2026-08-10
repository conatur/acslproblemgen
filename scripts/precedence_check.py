#!/usr/bin/env python3
"""Eyeball check for implicit grouping: print each generator's rendered
expression beside a fully-parenthesized rendering of the SAME tree, so any
mismatch with ACSL's precedence rules is visible at a glance.

Run from the repo root:  python scripts/precedence_check.py
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from generators import bitstring, notation


def full_bitstring(node):
    if isinstance(node, bitstring.Var):
        return node.name
    if isinstance(node, bitstring.Un):
        if node.op == "ID":
            return full_bitstring(node.child)
        if node.op == "NOT":
            return f"(NOT {full_bitstring(node.child)})"
        return f"({node.op}-{node.n} {full_bitstring(node.child)})"
    return f"({full_bitstring(node.left)} {node.op} {full_bitstring(node.right)})"


def full_infix(node):
    if isinstance(node, notation.Leaf):
        return node.sym
    return f"({full_infix(node.left)} {node.op} {full_infix(node.right)})"


def bitstring_rows(rng, want=10):
    """Only trees mixing at least two DIFFERENT binary operators — those are
    the ones where the precedence table actually decides anything."""
    rows = []
    for _ in range(100_000):
        if len(rows) == want:
            break
        tree = bitstring.build_tree(rng, ["A", "B", "C"], ops=4)
        bins = [n for n in bitstring.all_nodes(tree)
                if isinstance(n, bitstring.Bin)]
        if len({n.op for n in bins}) < 2:
            continue
        if any(n.left == n.right for n in bins):   # generate() rejects these too
            continue
        rows.append((bitstring.render(tree), full_bitstring(tree)))
    return rows


def notation_rows(rng, want=10):
    rows = []
    while len(rows) < want:
        leaves = list(rng.sample("ABCDEFGH", 5))
        tree = notation.build_tree(rng, 4, 3, leaves)
        rows.append((notation.to_infix(tree), full_infix(tree)))
    return rows


def show(title, rows):
    print(f"\n== {title} ==")
    width = max(len(minimal) for minimal, _ in rows)
    for minimal, full in rows:
        print(f"{minimal:<{width}}   |   {full}")


def main():
    rng = random.Random(2026)
    show("Bit-String Flicking (items mixing two binary ops)", bitstring_rows(rng))
    show("Prefix/Infix/Postfix (minimal vs full parentheses)", notation_rows(rng))
    print("\n(Number Systems has no expression trees — nothing to check there.)")


if __name__ == "__main__":
    main()
