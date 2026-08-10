"""ACSL practice trainer.  Run with:  streamlit run app.py"""
import inspect
import io
import json
import random
import sqlite3
import time
import uuid
import zipfile
from pathlib import Path

import streamlit as st

from generators import REGISTRY
from render.latex import render_worksheet_set, worksheet_items

DB_PATH = Path("data") / "responses.db"


def init_db():
    DB_PATH.parent.mkdir(exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS responses (
                ts         TEXT NOT NULL,
                session_id TEXT NOT NULL,
                category   TEXT NOT NULL,
                params     TEXT NOT NULL,
                error_tag  TEXT,
                correct    INTEGER NOT NULL,
                seconds    REAL NOT NULL
            )""")


def log_response(session_id, item, error_tag, correct, seconds):
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute(
            "INSERT INTO responses VALUES (?, ?, ?, ?, ?, ?, ?)",
            (time.strftime("%Y-%m-%dT%H:%M:%S"), session_id, item.category,
             json.dumps(item.params), error_tag, int(correct), round(seconds, 2)))


def top_errors(session_id):
    with sqlite3.connect(DB_PATH) as conn:
        return conn.execute(
            """SELECT error_tag, COUNT(*) AS n FROM responses
               WHERE session_id = ? AND correct = 0 AND error_tag IS NOT NULL
               GROUP BY error_tag ORDER BY n DESC""",
            (session_id,)).fetchall()


def new_item(generator, settings):
    
    accepted = inspect.signature(generator).parameters
    item = generator(**{k: v for k, v in settings.items() if k in accepted})
    st.session_state.item = item
   
    st.session_state.choices = item.choices(random.Random())
    st.session_state.picked = None           
    st.session_state.shown_at = time.time()  


def record_answer(choice):
    
    if st.session_state.picked is not None:  
        return
    st.session_state.picked = choice
    item = st.session_state.item
    correct = choice == item.answer
    st.session_state.score[0] += int(correct)
    st.session_state.score[1] += 1
    log_response(st.session_state.session_id, item, item.error_for(choice),
                 correct, time.time() - st.session_state.shown_at)


st.set_page_config(page_title="ACSL Trainer", page_icon="🎯")
init_db()

if "session_id" not in st.session_state:
    st.session_state.session_id = uuid.uuid4().hex
    st.session_state.score = [0, 0]         

with st.sidebar:
    category = st.selectbox("Category", list(REGISTRY))
    st.caption("Difficulty — applies from the next question on")
    settings = {
        "length": st.slider("Bit-string length", 4, 16, 8),
        "ops": st.slider("Operations", 1, 6, 3),
    }

generator = REGISTRY[category]

if "item" not in st.session_state:           
    new_item(generator, settings)

quiz, stats, sheets = st.tabs(["Quiz", "Session stats", "Worksheets"])

with quiz:
    item = st.session_state.item
    st.caption(item.category)
    st.code(item.stem)
    answered = st.session_state.picked is not None
    for i, choice in enumerate(st.session_state.choices):
        st.button(choice, key=f"choice_{i}", disabled=answered,
                  use_container_width=True, on_click=record_answer,
                  args=(choice,))
    if answered:
        picked = st.session_state.picked
        if picked == item.answer:
            st.success("Correct!")
        else:
            tag = item.error_for(picked)
            st.error(f"Not quite — looks like you {tag}."
                     if tag else "Not quite.")
            st.info(f"Correct answer: `{item.answer}`")
        st.button("Next question →", type="primary",
                  on_click=new_item, args=(generator, settings))
    right, total = st.session_state.score
    st.metric("Score", f"{right} / {total}")

with stats:
    rows = top_errors(st.session_state.session_id)
    if not rows:
        st.write("No wrong answers this session — nothing to show yet.")
    else:
        st.subheader("Most frequent mistakes this session")
        for tag, n in rows:
            st.write(f"**{n}×** — {tag}")

with sheets:
    c1, c2 = st.columns(2)
    ws_cat = c1.selectbox("Category", list(REGISTRY), key="ws_cat")
    ws_title = c2.text_input("Worksheet title", "ACSL Practice", key="ws_title")
    ws_n = c1.number_input("Problems per worksheet", 1, 20, 5, key="ws_n")
    ws_v = c2.number_input("Versions", 1, 40, 1, key="ws_v")
    ws_seed = c1.number_input("Master seed", value=1, step=1, key="ws_seed")
    ws_mc = c2.toggle("Multiple choice (off = free response)", True, key="ws_mc")
    st.caption("Difficulty comes from the sidebar sliders. Same seed and "
               "settings always regenerate the identical worksheets.")

    versions = render_worksheet_set(ws_cat, int(ws_n), int(ws_v), settings,
                                    int(ws_seed), title=ws_title,
                                    show_choices=ws_mc)

    with st.expander("Preview — version 1 stems"):
        for i, it in enumerate(
                worksheet_items(ws_cat, int(ws_n), 1, settings, int(ws_seed))[0], 1):
            st.text(f"{i}. {it.stem}\n")

    if len(versions) == 1:
        _, ws_tex, key_tex = versions[0]
        d1, d2 = st.columns(2)
        d1.download_button("Download worksheet.tex", ws_tex, "worksheet.tex",
                           mime="text/x-tex", key="ws_dl")
        d2.download_button("Download key.tex", key_tex, "key.tex",
                           mime="text/x-tex", key="key_dl")
    else:
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w") as zf:
            for v, (_, ws_tex, key_tex) in enumerate(versions, 1):
                zf.writestr(f"worksheet_v{v}.tex", ws_tex)
                zf.writestr(f"key_v{v}.tex", key_tex)
        st.download_button(f"Download {len(versions)} worksheets + keys (.zip)",
                           buf.getvalue(), "worksheets.zip",
                           mime="application/zip", key="zip_dl")
