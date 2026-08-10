"""Generator registry.

To add a category: write generators/<name>.py exposing CATEGORY and
generate(rng=None, ..., seed=None) -> Item, then add one line to REGISTRY
below. app.py reads only this dict and never changes.
"""
from . import bitstring, notation, numbersys

REGISTRY = {
    bitstring.CATEGORY: bitstring.generate,
    notation.CATEGORY: notation.generate,
    numbersys.CATEGORY: numbersys.generate,
}
