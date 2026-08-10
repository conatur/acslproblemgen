"""Tests for the LaTeX renderer — the second renderer over the Item contract."""
import re

import pytest

from generators import REGISTRY
from render import latex

NAMES = list(REGISTRY)

SPECIALS = {
    "_": r"\_", "^": r"\textasciicircum{}", "#": r"\#", "$": r"\$",
    "%": r"\%", "&": r"\&", "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}", "\\": r"\textbackslash{}",
}


def test_escape_latex_every_special():
    for ch, escaped in SPECIALS.items():
        assert latex.escape_latex(ch) == escaped
    # mixed text escapes in place, exactly once, and plain text is untouched
    assert latex.escape_latex("a_b^c") == r"a\_b\textasciicircum{}c"
    assert latex.escape_latex("100% & more_") == r"100\% \& more\_"
    assert latex.escape_latex("NOT LCIRC-1 A") == "NOT LCIRC-1 A"


@pytest.mark.parametrize("name", NAMES)
def test_every_generator_renders_and_counts_match(name):
    (label, ws, key), = latex.render_worksheet_set(name, 4, 1, {}, seed=11)
    assert label == "Version 1"
    assert ws.count("% problem ") == 4
    assert key.count("% problem ") == 4
    for doc in (ws, key):
        assert doc.startswith(r"\documentclass")
        assert doc.rstrip().endswith(r"\end{document}")


def test_regenerating_from_seed_is_byte_identical():
    args = ("Bit-String Flicking", 5, 3, {"length": 8, "ops": 3}, 99)
    assert latex.render_worksheet_set(*args) == latex.render_worksheet_set(*args)


@pytest.mark.parametrize("name", NAMES)
def test_key_letter_matches_worksheet_position(name):
    for items in latex.worksheet_items(name, 5, 2, {}, seed=3):
        # helper-level: the letter indexes the answer in the choice order
        for item in items:
            order = latex.choice_order(item)
            assert order[latex.LETTERS.index(latex.correct_letter(item))] == item.answer

        # document-level: key letters line up with the worksheet's choice lists
        ws = latex.render_worksheet(items, "t", "v1")
        key = latex.render_key(items, "t", "v1")
        assert re.findall(r"Answer: \((\w)\)", key) == \
            [latex.correct_letter(it) for it in items]
        for chunk, item in zip(ws.split("% problem ")[1:], items):
            block = chunk.split(r"\begin{enumerate}[label=")[1].split(r"\end{enumerate}")[0]
            rendered = re.findall(r"\\texttt\{(.*?)\}", block)
            assert rendered == [latex.escape_latex(c) for c in latex.choice_order(item)]


@pytest.mark.parametrize("name", NAMES)
def test_free_response_mode(name):
    (_, ws, key), = latex.render_worksheet_set(name, 3, 1, {}, seed=5,
                                               show_choices=False)
    assert r"label=(\Alph*)" not in ws          # no lettered options
    assert r"\vspace{1.5in}" in ws              # room to work instead
    assert "Answer: (" not in key               # key gives answers, not letters
    assert key.count("% problem ") == 3
