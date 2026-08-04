import random
from dataclasses import dataclass, replace
 
from items import Item
 
CATEGORY = "Bit-String Flicking"
 

PREC = {"OR": 1, "XOR": 2, "AND": 3}
 
BINARY_OPS = list(PREC)
SHIFT_OPS = ["LSHIFT", "RSHIFT", "LCIRC", "RCIRC"]
 
 

@dataclass(frozen=True)
class Var:
    """A leaf: a named variable like A, whose value comes from the env."""
    name: str
 
 
@dataclass(frozen=True)
class Un:
    """A unary node: NOT, a shift, a circulate, or ID (identity, used to model
    the 'student forgot to apply the operator' mistake)."""
    op: str
    child: object
    n: int = 0          # shift/circulate distance; unused by NOT and ID
 
 
@dataclass(frozen=True)
class Bin:
    """A binary node: AND, OR, or XOR."""
    op: str
    left: object
    right: object
 
 

def evaluate(node, env):
    if isinstance(node, Var):
        return env[node.name]
 
    if isinstance(node, Un):
        s = evaluate(node.child, env)
        L = len(s)
        if node.op == "ID":
            return s
        if node.op == "NOT":
            return "".join("1" if c == "0" else "0" for c in s)
        n = node.n % L if node.op in ("LCIRC", "RCIRC") else min(node.n, L)
        if node.op == "LSHIFT":
            return s[n:] + "0" * n
        if node.op == "RSHIFT":
            return "0" * n + s[: L - n]
        if node.op == "LCIRC":
            return s[n:] + s[:n]
        if node.op == "RCIRC":
            return s[L - n:] + s[: L - n]
        raise ValueError(f"unknown unary op {node.op}")
 
    if isinstance(node, Bin):
        a, b = evaluate(node.left, env), evaluate(node.right, env)
        pairs = zip(a, b)
        if node.op == "AND":
            return "".join("1" if x == y == "1" else "0" for x, y in pairs)
        if node.op == "OR":
            return "".join("0" if x == y == "0" else "1" for x, y in pairs)
        if node.op == "XOR":
            return "".join("1" if x != y else "0" for x, y in pairs)
        raise ValueError(f"unknown binary op {node.op}")
 
    raise TypeError(f"not a node: {node!r}")
 
 

def render(node, parent_prec=0):
    if isinstance(node, Var):
        return node.name
 
    if isinstance(node, Un):
        inner = render(node.child, 99)      # unary binds tightest
        if node.op == "ID":
            return inner
        if node.op == "NOT":
            return f"NOT {inner}"
        return f"{node.op}-{node.n} {inner}"
 
    prec = PREC[node.op]
    text = f"{render(node.left, prec)} {node.op} {render(node.right, prec)}"
    return f"({text})" if prec < parent_prec else text
 
 

def build_tree(rng, var_names, ops, use_shifts=True):
    tree = Var(rng.choice(var_names))
    for _ in range(ops):
        if rng.random() < 0.5:
            other = Var(rng.choice(var_names))
            if rng.random() < 0.5:
                tree = Bin(rng.choice(BINARY_OPS), tree, other)
            else:
                tree = Bin(rng.choice(BINARY_OPS), other, tree)
        elif use_shifts and rng.random() < 0.6:
            tree = Un(rng.choice(SHIFT_OPS), tree, rng.randint(1, 3))
        else:
            tree = Un("NOT", tree)
    return tree
 
 

def mutations(node):
    """All the ways a student could plausibly misread this single node."""
    out = []
    if isinstance(node, Un):
        if node.op in ("LSHIFT", "RSHIFT"):
            circ = "LCIRC" if node.op == "LSHIFT" else "RCIRC"
            out.append((replace(node, op=circ), "wrapped bits around instead of discarding them"))
            flipped = "RSHIFT" if node.op == "LSHIFT" else "LSHIFT"
            out.append((replace(node, op=flipped), "shifted in the wrong direction"))
        if node.op in ("LCIRC", "RCIRC"):
            shift = "LSHIFT" if node.op == "LCIRC" else "RSHIFT"
            out.append((replace(node, op=shift), "discarded bits instead of wrapping them around"))
            flipped = "RCIRC" if node.op == "LCIRC" else "LCIRC"
            out.append((replace(node, op=flipped), "circulated in the wrong direction"))
        if node.op in SHIFT_OPS:
            out.append((replace(node, n=node.n + 1), "shifted one position too far"))
        if node.op == "NOT":
            out.append((replace(node, op="ID"), "skipped the NOT"))
    if isinstance(node, Bin):
        if node.op == "XOR":
            out.append((replace(node, op="OR"), "treated XOR as OR (1 XOR 1 is 0, not 1)"))
        if node.op == "OR":
            out.append((replace(node, op="XOR"), "treated OR as XOR"))
        if node.op == "AND":
            out.append((replace(node, op="OR"), "treated AND as OR"))
    return out
 
 
def all_nodes(node):
    yield node
    if isinstance(node, Un):
        yield from all_nodes(node.child)
    elif isinstance(node, Bin):
        yield from all_nodes(node.left)
        yield from all_nodes(node.right)
 
 
def swap(tree, target, new):
    """Rebuild the tree with `target` replaced by `new`. Nodes are frozen, so
    we build a new tree rather than mutating in place."""
    if tree is target:
        return new
    if isinstance(tree, Un):
        return replace(tree, child=swap(tree.child, target, new))
    if isinstance(tree, Bin):
        return replace(tree, left=swap(tree.left, target, new),
                             right=swap(tree.right, target, new))
    return tree
 
 

def generate(rng=None, length=8, ops=3, n_vars=2, use_shifts=True, seed=None):
    if rng is None:
        seed = random.randrange(2**31) if seed is None else seed
        rng = random.Random(seed)
 
    for _ in range(50):                     # retry until the item is usable
        var_names = ["A", "B", "C"][:n_vars]
        env = {v: "".join(rng.choice("01") for _ in range(length)) for v in var_names}
        tree = build_tree(rng, var_names, ops, use_shifts)
        answer = evaluate(tree, env)
 
        # Collect distractors: break one node, re-evaluate the whole tree.
        seen, distractors = {answer}, []
        candidates = [(node, m, tag)
                      for node in all_nodes(tree)
                      for m, tag in mutations(node)]
        rng.shuffle(candidates)
        for node, mutated, tag in candidates:
            value = evaluate(swap(tree, node, mutated), env)
            if value in seen:               # collision: this mistake happens to
                continue                    # give the right answer here
            seen.add(value)
            distractors.append((value, tag))
            if len(distractors) == 3:
                break
 
        if len(distractors) < 3:            # this expression can't support four
            continue                        # distinct choices — start over
 
        given = ", ".join(f"{v} = {env[v]}" for v in var_names)
        return Item(
            category=CATEGORY,
            stem=f"If {given}, evaluate:\n\n{render(tree)}",
            answer=answer,
            distractors=distractors,
            params={"length": length, "ops": ops, "use_shifts": use_shifts,
                    "seed": seed},
        )
 
    raise RuntimeError("could not build an item; try more ops or a longer string")
 
 

def _self_test():
    rng = random.Random(0)
    for _ in range(500):
        s = "".join(rng.choice("01") for _ in range(rng.randint(4, 12)))
        n = rng.randint(0, 5)
        env, A = {"A": s}, Var("A")
        # every operation preserves length
        for op in SHIFT_OPS:
            assert len(evaluate(Un(op, A, n), env)) == len(s), op
        # circulating n left then n right is the identity
        back = evaluate(Un("RCIRC", Un("LCIRC", A, n), n), env)
        assert back == s, (s, n, back)
        # NOT twice is the identity
        assert evaluate(Un("NOT", Un("NOT", A)), env) == s
    print("invariants hold")
 
 
if __name__ == "__main__":
    _self_test()
    rng = random.Random(42)
    for _ in range(3):
        item = generate(rng, length=8, ops=3)
        print("\n" + item.stem)
        print(f"  answer: {item.answer}")
        for wrong, tag in item.distractors:
            print(f"  {wrong}  <- {tag}")
 
