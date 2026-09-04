Check out the [website](https://conatur.github.io/acslproblemgen/)

Generates practice problems for the ACSL MCQ categories: Bit-String Flicking,
Prefix/Infix/Postfix Notation, and Computer Number Systems.

## The idea

Every problem starts from a seed. The generator builds a random expression
tree (or a pair of numbers) from that seed and evaluates it to get the
answer, so the same seed always reproduces the same problem. Wrong answers
come from making a specific student mistake on purpose and working out what
it produces. Each wrong choice carries a tag naming that mistake, so picking
it tells you what you likely did wrong.

## Layout

The website (`index.html`) is a single static file. It contains the
generators ported to JavaScript along with practice, stats, and printable
worksheets. The Python package (`items.py`, `generators/`) is the original
version and has the test suite. Run `python -m pytest` after changing any
generator logic.

Any change to a generator has to be made in both places: `generators/` on
the Python side and the matching `CATEGORIES` entry in `index.html`.

## Add another category

Write `generators/yourtopic.py` with a `CATEGORY` string and
`generate(rng=None, ..., seed=None) -> Item`. Follow
`generators/bitstring.py`: exactly three distinct distractors, each tagged
with the mistake in plain language, and every difficulty knob plus the seed
stored in `Item.params`. Register it with one line in
`generators/__init__.py` and the tests pick it up automatically. Then port
it to `CATEGORIES` in `index.html`.