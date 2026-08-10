"""LaTeX worksheet renderer — a second renderer over the Item contract.

The Streamlit UI renders Items to screen; these pure functions render the
same Items to print. No Streamlit imports, no file I/O: every function maps
Items to .tex source strings and the caller decides where the bytes go.
Only stock LaTeX (article, geometry, enumitem) is emitted.
"""
import inspect
import random

from generators import REGISTRY

LETTERS = "ABCD"

_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#", "_": r"\_",
    "{": r"\{", "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def escape_latex(text):
    """Escape LaTeX specials. Char-by-char, so nothing is escaped twice."""
    return "".join(_ESCAPES.get(c, c) for c in str(text))


def choice_order(item):
    """Deterministic (A)-(D) order for an item, derived from its stored seed,
    so a regenerated worksheet always matches its key."""
    rng = random.Random(f"choices:{item.params.get('seed')}:{item.stem}")
    return item.choices(rng)


def correct_letter(item):
    return LETTERS[choice_order(item).index(item.answer)]


def _stem_tex(stem):
    """Stem paragraphs; blocks after the first (the expression) in monospace."""
    blocks = [b for b in stem.split("\n\n") if b.strip()]
    out = [escape_latex(blocks[0])]
    for block in blocks[1:]:
        out.append(r"\par\medskip \texttt{" + escape_latex(block) + "}")
    return "\n".join(out)


def _document(title, version_label, body):
    return "\n".join([
        r"\documentclass[11pt]{article}",
        r"\usepackage[margin=1in]{geometry}",
        r"\usepackage{enumitem}",
        r"\setlength{\parindent}{0pt}",
        "",
        r"\begin{document}",
        "",
        r"\begin{center}",
        r"  {\Large \textbf{" + escape_latex(title) + r"}}\\[4pt]",
        r"  {\large " + escape_latex(version_label) + r"}",
        r"\end{center}",
        r"\vspace{0.5em}",
        "",
        body,
        "",
        r"\end{document}",
        "",
    ])


def render_worksheet(items, title, version_label, show_choices=True):
    parts = [
        r"Name: \rule{2.5in}{0.4pt} \hfill Date: \rule{1.5in}{0.4pt}",
        r"\vspace{1em}",
        "",
        r"\begin{enumerate}[itemsep=2em]",
    ]
    for i, item in enumerate(items, 1):
        parts.append(f"% problem {i}")
        parts.append(r"\item " + _stem_tex(item.stem))
        if show_choices:
            parts.append(r"\begin{enumerate}[label=(\Alph*), topsep=0.75em, itemsep=0.4em]")
            for choice in choice_order(item):
                parts.append(r"\item \texttt{" + escape_latex(choice) + "}")
            parts.append(r"\end{enumerate}")
        else:
            parts.append(r"\vspace{1.5in}")   # room to work
        parts.append("")
    parts.append(r"\end{enumerate}")
    return _document(title, version_label, "\n".join(parts))


def render_key(items, title, version_label, show_choices=True):
    parts = [r"\begin{enumerate}[itemsep=1em]"]
    for i, item in enumerate(items, 1):
        parts.append(f"% problem {i}")
        letter = f"({correct_letter(item)}) " if show_choices else ""
        parts.append(r"\item Answer: " + letter
                     + r"\texttt{" + escape_latex(item.answer) + r"}"
                     + r" \hfill {\small seed " + escape_latex(item.params.get("seed")) + "}")
        if show_choices:
            order = choice_order(item)
            wrongs = sorted(item.distractors, key=lambda d: order.index(d[0]))
        else:
            wrongs = item.distractors
        parts.append(r"\begin{itemize}[nosep]")
        for wrong, tag in wrongs:
            label = f"({LETTERS[order.index(wrong)]}) " if show_choices else ""
            parts.append(r"\item " + label + r"\texttt{" + escape_latex(wrong)
                         + r"} --- " + escape_latex(tag))
        parts.append(r"\end{itemize}")
    parts.append(r"\end{enumerate}")
    return _document(title, f"{version_label} --- KEY", "\n".join(parts))


def worksheet_items(generator_name, n_problems, n_versions, params, seed):
    """Item lists for each version, all derived deterministically from `seed`:
    the same arguments always yield the same items (and thus the same .tex)."""
    gen = REGISTRY[generator_name]
    accepted = inspect.signature(gen).parameters
    kwargs = {k: v for k, v in (params or {}).items() if k in accepted}
    master = random.Random(f"worksheets:{seed}")
    versions = []
    for _ in range(n_versions):
        items, seen, tries = [], set(), 0
        while len(items) < n_problems:
            tries += 1
            if tries > 200 * n_problems:
                raise RuntimeError(f"could not fill a worksheet for {generator_name}")
            try:
                item = gen(seed=master.randrange(2**31), **kwargs)
            except RuntimeError:
                continue                      # unlucky seed; draw another
            if item.stem in seen and tries < 30 * n_problems:
                continue                      # best-effort de-dup within a version
            seen.add(item.stem)
            items.append(item)
        versions.append(items)
    return versions


def render_worksheet_set(generator_name, n_problems, n_versions, params, seed,
                         title="ACSL Practice", show_choices=True):
    """n_versions independent worksheets + matched keys: same category, same
    difficulty params, different seeds. Returns [(label, worksheet_tex, key_tex)]."""
    out = []
    all_items = worksheet_items(generator_name, n_problems, n_versions, params, seed)
    for v, items in enumerate(all_items, 1):
        label = f"Version {v}"
        out.append((label,
                    render_worksheet(items, title, label, show_choices),
                    render_key(items, title, label, show_choices)))
    return out
