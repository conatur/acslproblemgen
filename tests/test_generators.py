"""Contract tests for every registered generator, plus bitstring invariants."""
import random
import re

import pytest

from generators import REGISTRY, bitstring

GENERATORS = list(REGISTRY.items())
GEN_IDS = [name for name, _ in GENERATORS]
SEEDS = list(range(30))


@pytest.mark.parametrize("gen", [g for _, g in GENERATORS], ids=GEN_IDS)
@pytest.mark.parametrize("seed", SEEDS)
def test_four_distinct_choices(gen, seed):
    item = gen(seed=seed)
    wrongs = [w for w, _ in item.distractors]
    assert len(wrongs) == 3, "exactly three distractors"
    assert len(set(wrongs)) == 3, f"distractors collide: {wrongs}"
    assert item.answer not in wrongs, "the answer leaked into the distractors"
    assert all(tag for _, tag in item.distractors), "every distractor is tagged"


@pytest.mark.parametrize("gen", [g for _, g in GENERATORS], ids=GEN_IDS)
@pytest.mark.parametrize("seed", SEEDS)
def test_stem_mentions_only_used_variables(gen, seed):
    item = gen(seed=seed)
    expr = item.stem.split("\n\n")[-1]
    for var in re.findall(r"\b([A-Z])\s*=", item.stem):
        assert re.search(rf"\b{var}\b", expr), (
            f"{var} is given in the stem but never used:\n{item.stem}")


@pytest.mark.parametrize("gen", [g for _, g in GENERATORS], ids=GEN_IDS)
@pytest.mark.parametrize("seed", SEEDS)
def test_seed_reproduces_identical_item(gen, seed):
    first = gen(seed=seed)
    again = gen(seed=seed)
    assert first == again, "same seed must reproduce the identical item"
    assert first.params.get("seed") == seed, "the seed must be stored in params"


# --- bitstring invariants (moved out of generators/bitstring.py __main__) ---

def test_bitstring_operation_invariants():
    rng = random.Random(0)
    for _ in range(500):
        s = "".join(rng.choice("01") for _ in range(rng.randint(4, 12)))
        n = rng.randint(0, 5)
        env, A = {"A": s}, bitstring.Var("A")
        # every operation preserves length
        for op in bitstring.SHIFT_OPS:
            assert len(bitstring.evaluate(bitstring.Un(op, A, n), env)) == len(s), op
        # circulating n left then n right is the identity
        back = bitstring.evaluate(
            bitstring.Un("RCIRC", bitstring.Un("LCIRC", A, n), n), env)
        assert back == s, (s, n, back)
        # NOT twice is the identity
        assert bitstring.evaluate(
            bitstring.Un("NOT", bitstring.Un("NOT", A)), env) == s


@pytest.mark.parametrize("seed", SEEDS)
def test_bitstring_item_quality(seed):
    item = bitstring.generate(seed=seed)
    assert len(set(item.answer)) > 1, "answer must not be all zeros / all ones"
    for wrong, _ in item.distractors:
        assert len(wrong) == len(item.answer), "choices must share a length"


# TODO(golden): hand-verified golden tests from past ACSL contests.
# Transcribe a handful of official problems, verify the published answers by
# hand, then pin each one here so refactors can't silently change semantics:
#
#   def test_golden_bitstring_2019_intermediate_r1():
#       # official stem: "RSHIFT-2 (LCIRC-3 10110)" -> official answer "00101"
#       assert bitstring.evaluate(<transcribed tree>, <env>) == "<official>"
#
# Cover at minimum: one bitstring shift/circulate chain, one notation
# postfix->infix requiring parentheses, one base-16 arithmetic with a carry.
