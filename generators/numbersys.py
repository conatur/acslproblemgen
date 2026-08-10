"""ACSL Number Systems.

Conversions between bases 2, 8, 10, 16, plus add/subtract/multiply carried
out inside a non-decimal base. Distractors are produced by actually running
the wrong procedure a student would run (dropping carries, misreading a hex
letter, ...), never by random perturbation.
"""
import random

from items import Item

CATEGORY = "Number Systems"

BASES = (2, 8, 10, 16)
DIGITS = "0123456789ABCDEF"
OP_WORDS = {"+": "addition", "-": "subtraction", "*": "multiplication"}


def to_base(n, b):
    if n == 0:
        return "0"
    digits = []
    while n:
        n, d = divmod(n, b)
        digits.append(DIGITS[d])
    return "".join(reversed(digits))


def from_base(s, b):
    """int(s, b), or None when s isn't a valid base-b numeral."""
    try:
        return int(s, b)
    except ValueError:
        return None


def add_dropping_carries(xs, ys, b):
    """Column-by-column addition that throws every carry away."""
    w = max(len(xs), len(ys))
    xs, ys = xs.zfill(w), ys.zfill(w)
    out = "".join(DIGITS[(DIGITS.index(dx) + DIGITS.index(dy)) % b]
                  for dx, dy in zip(xs, ys))
    return out.lstrip("0") or "0"


def sub_borrow_as_carry(xs, ys, b):
    """Subtraction where each borrow is *added* to the next column instead of
    being paid back — the borrow-treated-as-carry mistake."""
    w = max(len(xs), len(ys))
    xs, ys = xs.zfill(w), ys.zfill(w)
    out, borrow = [], 0
    for dx, dy in zip(reversed(xs), reversed(ys)):
        d = DIGITS.index(dx) - DIGITS.index(dy) + borrow  # should be - borrow
        borrow = 0
        if d < 0:
            d += b
            borrow = 1
        out.append(DIGITS[d % b])
    return "".join(reversed(out)).lstrip("0") or "0"


def shift_hex_letter(s, rng):
    """Nudge one hex letter's value by one (D read as 12 gives C), or None
    if the string has no letters."""
    idxs = [i for i, c in enumerate(s) if c in "ABCDEF"]
    if not idxs:
        return None
    i = rng.choice(idxs)
    nv = DIGITS.index(s[i]) + rng.choice((-1, 1))
    if nv > 15:
        nv = 14
    return s[:i] + DIGITS[nv] + s[i + 1:]


def _conversion_candidates(rng, value, src, from_b, to_b, answer):
    out = []
    for wb in BASES:
        if wb in (from_b, to_b):
            continue
        if wb == 8 and {from_b, to_b} == {2, 16}:
            tag = ("converted through the wrong intermediate base "
                   "(grouped bits in threes, giving octal)")
        else:
            tag = f"converted correctly, but to base {wb} instead of base {to_b}"
        out.append((to_base(value, wb), tag))
        misread = from_base(src, wb)
        if misread is not None and misread != value:
            cand = to_base(misread, to_b)
            # keep only misreads of believable magnitude — a 7-digit option
            # next to a 2-digit answer is a free elimination
            if abs(len(cand) - len(answer)) <= 2:
                out.append((cand,
                            f"read the given number as if it were base {wb}"))
    if len(answer) > 1:
        out.append((answer[::-1], "reversed the digit order"))
    shifted = shift_hex_letter(answer, rng)
    if shifted:
        out.append((shifted, "mapped a hex letter off by one (D read as 12)"))
    if from_b == 16:
        mis = shift_hex_letter(src, rng)
        if mis:
            out.append((to_base(from_base(mis, 16), to_b),
                        "misread a hex letter in the problem as its neighbour"))
    return out


def _arith_candidates(rng, b, xs, ys, op, value, answer):
    out = []
    if op == "+":
        out.append((add_dropping_carries(xs, ys, b), "dropped a carry"))
    if op == "-":
        out.append((sub_borrow_as_carry(xs, ys, b),
                    "treated a subtraction borrow as a carry"))
    # Face-value slip: do the arithmetic as if the numerals were base 10.
    fx, fy = from_base(xs, 10), from_base(ys, 10)
    if fx is not None and fy is not None:
        dec = {"+": fx + fy, "-": fx - fy, "*": fx * fy}[op]
        if dec > 0:
            out.append((str(dec), "did the column arithmetic in base 10"))
    out.append((str(value), "computed correctly but left the answer in base 10"))
    if len(answer) > 1:
        out.append((answer[::-1], "reversed the digit order"))
    shifted = shift_hex_letter(answer, rng)
    if shifted:
        out.append((shifted, "mapped a hex letter off by one (D read as 12)"))
    # Last-resort one-column slips.
    out.append((to_base(value + 1, b), "slipped one too high in the last column"))
    if value > 1:
        out.append((to_base(value - 1, b), "slipped one too low in the last column"))
    return out


def _conversion_item(rng, magnitude, pair):
    if pair and pair[0] != pair[1]:
        from_b, to_b = pair
    else:
        from_b, to_b = rng.sample(BASES, 2)
    value = rng.randint(max(from_b, to_b), magnitude)  # >= 2 digits in from_b
    src = to_base(value, from_b)
    answer = to_base(value, to_b)
    stem = f"Convert {src} (base {from_b}) to base {to_b}."
    return stem, answer, _conversion_candidates(rng, value, src, from_b, to_b, answer)


def _arith_item(rng, magnitude, pair):
    non_decimal = [b for b in (pair or BASES) if b != 10]
    b = rng.choice(non_decimal or [2, 8, 16])
    op = rng.choice("+-*")
    if op == "*":
        hi = max(4, int(magnitude ** 0.5))
        x, y = rng.randint(2, hi), rng.randint(2, hi)
    else:
        x, y = rng.randint(b, magnitude), rng.randint(2, magnitude)
        if op == "-" and x < y:
            x, y = y, x
    value = {"+": x + y, "-": x - y, "*": x * y}[op]
    if value <= 0:
        return None
    xs, ys = to_base(x, b), to_base(y, b)
    stem = f"Working entirely in base {b}, compute:\n\n{xs} {op} {ys}"
    answer = to_base(value, b)
    return stem, answer, _arith_candidates(rng, b, xs, ys, op, value, answer)


def generate(rng=None, magnitude=255, base_pair=None, arithmetic=True, seed=None):
    if rng is None:
        seed = random.randrange(2**31) if seed is None else seed
        rng = random.Random(seed)

    magnitude = max(48, int(magnitude))
    pair = tuple(base_pair) if base_pair else None

    for _ in range(200):                    # retry until the item is usable
        if arithmetic and rng.random() < 0.5:
            built = _arith_item(rng, magnitude, pair)
        else:
            built = _conversion_item(rng, magnitude, pair)
        if built is None:
            continue
        stem, answer, candidates = built

        rng.shuffle(candidates)
        seen, distractors = {answer}, []
        for wrong, tag in candidates:
            if not wrong or wrong in seen:
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
            params={"magnitude": magnitude,
                    "base_pair": list(pair) if pair else None,
                    "arithmetic": arithmetic, "seed": seed},
        )

    raise RuntimeError("could not build an item; try a larger magnitude")


if __name__ == "__main__":
    rng = random.Random(42)
    for _ in range(3):
        item = generate(rng)
        print("\n" + item.stem)
        print(f"  answer: {item.answer}")
        for wrong, tag in item.distractors:
            print(f"  {wrong}  <- {tag}")
