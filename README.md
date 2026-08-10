# ACSL Trainer

A Streamlit practice-problem trainer for ACSL contest categories.

## Architecture

Three ideas, one contract:

1. **Deterministic, symbolic item generation.** No LLM anywhere. Each
   generator builds a random expression tree (or numeral pair) from a seeded
   `random.Random`, renders the stem from it, and derives the answer by
   evaluating/traversing the same tree. Every difficulty knob **and the seed**
   are stored in `Item.params`, so any item ever shown can be regenerated
   bit-for-bit.
2. **Misconception-tagged distractors.** Wrong choices are never random
   perturbations: each one is produced by deliberately performing a specific
   student mistake (dropping a carry, shifting the wrong direction, giving
   prefix when postfix was asked) and re-deriving the result. The tag rides
   along, so a wrong click shows the student *which mistake they made*, and
   `scripts/calibrate.py` can report which misconceptions dominate.
3. **One `Item` contract, many subject surfaces.** `items.py` defines a frozen
   `Item` (stem, answer, tagged distractors, params). Each module in
   `generators/` exposes `CATEGORY` and `generate(rng=None, ..., seed=None) ->
   Item`; `generators/__init__.py` maps display names to generate functions in
   `REGISTRY`. The app iterates `REGISTRY` and knows nothing else — adding a
   category is one new module plus one registry line, zero app changes.

Current categories: Bit-String Flicking, Prefix/Infix/Postfix, Number Systems.

![App screenshot](docs/screenshot.png)
<!-- TODO: replace with a real capture at docs/screenshot.png -->

## Setup

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Running

```bash
.venv/bin/streamlit run app.py
```

Run from the repo root (imports and the SQLite path are root-relative).
Responses are logged to `data/responses.db`; the "Session stats" tab shows
this session's most frequent error tags.

## Tests

```bash
.venv/bin/python -m pytest
```

Contract tests are parameterised across every generator in `REGISTRY`, so a
newly registered generator is tested automatically.

## Utility scripts

```bash
python scripts/precedence_check.py   # eyeball minimal vs full parenthesization
python scripts/calibrate.py          # accuracy / timing / top error per difficulty group
```

## Adding a generator

1. Create `generators/yourtopic.py` with a `CATEGORY` string and
   `generate(rng=None, <knobs>, seed=None) -> Item`. Follow
   `generators/bitstring.py`: build a structure, derive the answer from it,
   produce **exactly three distinct** distractors by breaking one thing at a
   time, tag each with the mistake in plain language, and put every knob plus
   the seed in `Item.params`.
2. Add one line to `REGISTRY` in `generators/__init__.py`.

The app matches sidebar difficulty settings to generator knobs by parameter
name and drops the rest, so unrelated knobs are simply ignored.

## Verification TODOs

- Operator precedence tables (`PREC` in `bitstring.py` and `notation.py`) are
  flagged with TODO comments — verify them against the official ACSL
  references.
- `tests/test_generators.py` has a marked TODO block for hand-verified golden
  items transcribed from past contests.
