"""Generator registry.

To add a category: write generators/<name>.py exposing CATEGORY and
generate(rng=None, ...) -> Item, then add one line to REGISTRY below.
app.py reads only this dict and never changes.
"""
from . import bitstring

REGISTRY = {
    bitstring.CATEGORY: bitstring.generate,
}
