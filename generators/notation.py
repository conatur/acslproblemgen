"""ACSL Prefix/Infix/Postfix Notation.

Same architecture as bitstring.py: build a random expression tree, render it
for the stem, traverse it for the answer, and make distractors by breaking
exactly one thing in the tree and re-deriving the requested form.
No parsing anywhere — every string is rendered from a tree we already hold.
"""
import random
from dataclasses import dataclass, replace

from items import Item

CATEGORY = "Prefix/Infix/Postfix"

# Infix precedence: higher binds tighter. Operators are rendered as
# left-associative, and a right-hand child of equal precedence is always
# parenthesized, so every tree has exactly one infix spelling.
# TODO: verify this table and the associativity convention against the
# official ACSL Prefix/Infix/Postfix Notation reference.
PREC = {"+": 1, "-": 1, "*": 2, "/": 2}

OPS = list(PREC)
COMMUTATIVE = ("+", "*")
OP_NAMES = {"+": "addition", "-": "subtraction",
            "*": "multiplication", "/": "division"}
QTYPES = ("in2post", "in2pre", "post2in", "evalpost")


@dataclass(frozen=True)
class Leaf:
    """An operand: a single uppercase letter or a single decimal digit."""
    sym: str


@dataclass(frozen=True)
class Node:
    """A binary operator application."""
    op: str
    left: object
    right: object


def to_postfix(node):
    if isinstance(node, Leaf):
        return node.sym
    return to_postfix(node.left) + to_postfix(node.right) + node.op


def to_prefix(node):
    if isinstance(node, Leaf):
        return node.sym
    return node.op + to_prefix(node.left) + to_prefix(node.right)


def to_infix(node, parent_prec=0, is_right=False):
    """Minimal-parentheses infix, driven by PREC the way bitstring.render is:
    parenthesize a child that binds looser than its parent, or one sitting on
    the right of an equal-precedence parent (left-associativity elsewhere)."""
    if isinstance(node, Leaf):
        return node.sym
    p = PREC[node.op]
    text = (f"{to_infix(node.left, p, False)} {node.op} "
            f"{to_infix(node.right, p, True)}")
    if p < parent_prec or (p == parent_prec and is_right):
        return f"({text})"
    return text


def eval_tree(node):
    """Integer value, or None on a symbolic leaf, division by zero, or a
    division that doesn't come out exact."""
    if isinstance(node, Leaf):
        return int(node.sym) if node.sym.isdigit() else None
    a, b = eval_tree(node.left), eval_tree(node.right)
    if a is None or b is None:
        return None
    if node.op == "+":
        return a + b
    if node.op == "-":
        return a - b
    if node.op == "*":
        return a * b
    if b == 0 or a % b != 0:
        return None
    return a // b


def all_nodes(node):
    yield node
    if isinstance(node, Node):
        yield from all_nodes(node.left)
        yield from all_nodes(node.right)


def graft(tree, target, new):
    """Rebuild the tree with `target` replaced by `new` (nodes are frozen)."""
    if tree is target:
        return new
    if isinstance(tree, Node):
        return replace(tree, left=graft(tree.left, target, new),
                             right=graft(tree.right, target, new))
    return tree


def mirror(node):
    """Swap the operands of every operator — the 'read it backwards' student."""
    if isinstance(node, Leaf):
        return node
    return Node(node.op, mirror(node.right), mirror(node.left))


def capacity(depth):
    return (1 << depth) - 1     # most operators a tree of this depth can hold


def build_tree(rng, n_ops, max_depth, leaves):
    """Random tree with exactly n_ops operators, no deeper than max_depth.
    Consumes symbols from `leaves` (pass a copy)."""
    if n_ops == 0:
        return Leaf(leaves.pop())
    cap = capacity(max_depth - 1)
    n_left = rng.randint(max(0, n_ops - 1 - cap), min(n_ops - 1, cap))
    return Node(rng.choice(OPS),
                build_tree(rng, n_left, max_depth - 1, leaves),
                build_tree(rng, n_ops - 1 - n_left, max_depth - 1, leaves))


def drop_paren(s):
    """Remove the first parenthesis pair, or None if there is none to drop."""
    i = s.find("(")
    if i < 0:
        return None
    depth = 0
    for j in range(i, len(s)):
        if s[j] == "(":
            depth += 1
        elif s[j] == ")":
            depth -= 1
            if depth == 0:
                return s[:i] + s[i + 1:j] + s[j + 1:]
    return None


def _tree_mistakes(node):
    """All the ways a student could plausibly mishandle this one operator."""
    out = []
    swapped = Node(node.op, node.right, node.left)
    if node.op in COMMUTATIVE:
        out.append((swapped, "took the operands in right-to-left order"))
    else:
        out.append((swapped,
                    f"reversed the operands of the {OP_NAMES[node.op]}"))
    r = node.right
    if isinstance(r, Node) and PREC[r.op] == PREC[node.op]:
        out.append((Node(r.op, Node(node.op, node.left, r.left), r.right),
                    "applied left-associativity where the expression "
                    "groups to the right"))
    l = node.left
    if isinstance(l, Node) and PREC[l.op] == PREC[node.op]:
        out.append((Node(l.op, l.left, Node(node.op, l.right, node.right)),
                    "grouped from the right where the operators associate left"))
    return out


_RENDER = {"in2post": to_postfix, "in2pre": to_prefix, "post2in": to_infix}


def _candidates(tree, qtype):
    """Distractors from named mistakes: break one thing, re-derive the answer."""
    render = _RENDER.get(qtype)
    out = []
    for node in all_nodes(tree):
        if not isinstance(node, Node):
            continue
        for mutated, tag in _tree_mistakes(node):
            broken = graft(tree, node, mutated)
            if qtype == "evalpost":
                v = eval_tree(broken)
                if v is not None:
                    out.append((str(v), tag))
            else:
                out.append((render(broken), tag))

    if qtype == "in2post":
        out.append((to_prefix(tree), "gave the prefix form when postfix was asked"))
        out.append((to_postfix(tree)[::-1], "wrote the postfix string in reverse order"))
    elif qtype == "in2pre":
        out.append((to_postfix(tree), "gave the postfix form when prefix was asked"))
        out.append((to_prefix(tree)[::-1], "wrote the prefix string in reverse order"))
    elif qtype == "post2in":
        out.append((to_infix(mirror(tree)), "read the postfix operands right-to-left"))
        dropped = drop_paren(to_infix(tree))
        if dropped:
            out.append((dropped, "dropped a parenthesis the grouping requires"))
    else:  # evalpost
        v = eval_tree(mirror(tree))
        if v is not None:
            out.append((str(v), "took every operand pair in reverse order"))
    return out


def _backfill(tree, qtype):
    """Weaker misread-an-operator slips, used only when the principled
    mistakes above collide and can't fill three distinct choices."""
    render = _RENDER.get(qtype)
    out = []
    if qtype == "evalpost":
        v = eval_tree(tree)
        if v is not None:
            out.append((str(v + 1), "slipped one too high in the arithmetic"))
            out.append((str(v - 1), "slipped one too low in the arithmetic"))
    for node in all_nodes(tree):
        if not isinstance(node, Node):
            continue
        for op in OPS:
            if op == node.op:
                continue
            broken = graft(tree, node, replace(node, op=op))
            tag = f"misread the {OP_NAMES[node.op]} as {OP_NAMES[op]}"
            if qtype == "evalpost":
                v = eval_tree(broken)
                if v is not None:
                    out.append((str(v), tag))
            else:
                out.append((render(broken), tag))
    return out


def generate(rng=None, ops=3, depth=3, use_parens=True, seed=None):
    if rng is None:
        seed = random.randrange(2**31) if seed is None else seed
        rng = random.Random(seed)

    ops = max(1, min(int(ops), 7))          # 8 distinct letters available
    depth = int(depth)
    while capacity(depth) < ops:            # deep enough to hold `ops` operators
        depth += 1

    for _ in range(200):                    # retry until the item is usable
        qtype = rng.choice(QTYPES)
        if qtype == "evalpost":
            leaves = [str(rng.randint(1, 9)) for _ in range(ops + 1)]
        else:
            leaves = [s if rng.random() < 0.8 else str(rng.randint(2, 9))
                      for s in rng.sample("ABCDEFGH", ops + 1)]
        tree = build_tree(rng, ops, depth, leaves)

        if qtype != "evalpost" and not use_parens and "(" in to_infix(tree):
            continue                        # knob says: no parentheses on screen

        if qtype == "evalpost":
            value = eval_tree(tree)
            if value is None or not 0 <= value <= 200:
                continue
            stem = f"Evaluate this postfix expression:\n\n{to_postfix(tree)}"
            answer = str(value)
        elif qtype == "post2in":
            stem = ("Convert this postfix expression to infix, using only the "
                    f"parentheses you need:\n\n{to_postfix(tree)}")
            answer = to_infix(tree)
        elif qtype == "in2post":
            stem = f"Convert this infix expression to postfix:\n\n{to_infix(tree)}"
            answer = to_postfix(tree)
        else:
            stem = f"Convert this infix expression to prefix:\n\n{to_infix(tree)}"
            answer = to_prefix(tree)

        principled = _candidates(tree, qtype)
        weak = _backfill(tree, qtype)
        rng.shuffle(principled)
        rng.shuffle(weak)

        seen, distractors = {answer}, []
        for wrong, tag in principled + weak:
            if wrong is None or wrong in seen:
                continue
            seen.add(wrong)
            distractors.append((wrong, tag))
            if len(distractors) == 3:
                break
        if len(distractors) < 3:            # can't fill four distinct choices
            continue

        return Item(
            category=CATEGORY,
            stem=stem,
            answer=answer,
            distractors=distractors,
            params={"ops": ops, "depth": depth, "use_parens": use_parens,
                    "seed": seed},
        )

    raise RuntimeError("could not build an item; try more operators or depth")


if __name__ == "__main__":
    rng = random.Random(42)
    for _ in range(3):
        item = generate(rng)
        print("\n" + item.stem)
        print(f"  answer: {item.answer}")
        for wrong, tag in item.distractors:
            print(f"  {wrong}  <- {tag}")
