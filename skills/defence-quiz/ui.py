"""Thin Streamlit view over the defence cards.

Reads and writes the same markdown files as cards.py; no second store.
Run:  uv run --with streamlit --with pyyaml streamlit run ui.py
"""

from __future__ import annotations

import datetime as dt
import re
import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent))
import cards as C  # noqa: E402

AREAS = ["sys", "mt", "auth", "cp", "cmp", "ing", "ml", "etl", "dp", "exp", "ops", "ai", "fund", "me"]
AREA_LABELS = {
    "sys": "System shape",
    "mt": "Multi-tenancy",
    "auth": "Identity and auth",
    "cp": "Control plane",
    "cmp": "Compute plane",
    "ing": "Ingestion",
    "ml": "Enrichment and models",
    "etl": "Transformation",
    "dp": "Data plane",
    "exp": "Experience layer",
    "ops": "Infra and delivery",
    "ai": "AI-native engineering",
    "fund": "Fundamentals",
    "me": "Personal projects",
}


def area_name(a: str) -> str:
    return AREA_LABELS.get(a, a)


LEVELS = ["system", "component", "mechanism", "integration", "operational"]
MARKS = ["whiteboard", "shaky", "no"]
MARK_COLOUR = {"whiteboard": "#2e7d32", "shaky": "#f9a825", "no": "#c62828"}

st.set_page_config(page_title="Defence cards", layout="wide")


@st.cache_data(ttl=5)
def load_all() -> list[dict]:
    rows = []
    for p, fm, body in C.iter_cards():
        rows.append({**fm, "body": body, "file": p.name})
    return rows


def refresh() -> None:
    load_all.clear()


def body_lines(body: str) -> dict[str, str]:
    out = {}
    for m in re.finditer(r"\*\*(\w[\w-]*)\.\*\*\s*(.*)", body):
        out[m.group(1)] = m.group(2).strip()
    return out


rows = load_all()
today = dt.date.today()

with st.sidebar:
    st.header("Filter")
    f_area = st.multiselect("Area", AREAS, default=[], format_func=area_name)
    f_level = st.multiselect("Level", LEVELS, default=[])
    f_mark = st.multiselect("Confidence", MARKS, default=[])
    f_portable = st.checkbox("Portable ideas only", value=False)
    f_unreviewed = st.checkbox("Not yet in my words", value=False)
    f_stale = st.checkbox("Stale only", value=False)
    f_due = st.checkbox("Due today", value=False)
    q = st.text_input("Search question")
    if st.button("Reload from disk"):
        refresh()
        st.rerun()

view = rows
if f_area:
    view = [r for r in view if r.get("area") in f_area]
if f_level:
    view = [r for r in view if r.get("level") in f_level]
if f_mark:
    view = [r for r in view if r.get("confidence") in f_mark]
if f_portable:
    view = [r for r in view if r.get("portable")]
if f_unreviewed:
    view = [r for r in view if not r.get("reviewed_by_me")]
if f_stale:
    view = [r for r in view if r.get("stale")]
if f_due:
    view = [r for r in view if (C.as_date(r.get("next_due")) or today) <= today]
if q:
    view = [r for r in view if q.lower() in str(r.get("question", "")).lower()]

tab_browse, tab_quiz, tab_heat = st.tabs(["Browse", "Self-quiz", "Heatmap"])

with tab_heat:
    st.caption(f"{len(rows)} cards, {sum(1 for r in rows if (C.as_date(r.get('next_due')) or today) <= today)} due, "
               f"{sum(1 for r in rows if r.get('stale'))} stale, {sum(1 for r in rows if not r.get('reviewed_by_me'))} not yet in my words")
    grid = {a: {m: 0 for m in MARKS} for a in AREAS}
    for r in rows:
        a, m = r.get("area"), r.get("confidence")
        if a in grid and m in grid[a]:
            grid[a][m] += 1
    html = ["<table style='border-collapse:collapse;font-size:0.95em'>",
            "<tr><th style='text-align:left;padding:4px 12px'>Area</th>"
            + "".join(f"<th style='padding:4px 12px'>{m}</th>" for m in MARKS)
            + "<th style='padding:4px 12px'>total</th></tr>"]
    for a in AREAS:
        n = sum(grid[a].values())
        cells = []
        for m in MARKS:
            k = grid[a][m]
            style = f"background:{MARK_COLOUR[m]};color:white;" if k else "color:#999;"
            cells.append(f"<td style='text-align:center;padding:4px 12px;{style}'>{k or ''}</td>")
        html.append(f"<tr><td style='padding:4px 12px'><b>{area_name(a)}</b></td>{''.join(cells)}"
                    f"<td style='text-align:center;padding:4px 12px'>{n}</td></tr>")
    html.append("</table>")
    st.markdown("".join(html), unsafe_allow_html=True)
    st.subheader("By level")
    lv = {lvl: 0 for lvl in LEVELS}
    for r in rows:
        if r.get("level") in lv:
            lv[r["level"]] += 1
    st.bar_chart(lv)

with tab_browse:
    st.caption(f"{len(view)} of {len(rows)} cards")
    for r in sorted(view, key=lambda r: (r.get("area"), r.get("id"))):
        mark = r.get("confidence", "no")
        flags = []
        if r.get("stale"):
            flags.append("stale")
        if not r.get("reviewed_by_me"):
            flags.append("generated wording")
        if r.get("portable") is False:
            flags.append("how we do it here")
        label = f"[{r['id']}] {r['question']}"
        with st.expander(label):
            st.markdown(
                f"<span style='background:{MARK_COLOUR.get(mark, '#555')};color:white;padding:2px 8px;border-radius:4px'>{mark}</span> "
                f"&nbsp; {area_name(r.get('area'))} · {r.get('kind')} · {r.get('level')} · due {r.get('next_due')} · tested {r.get('tested', 0)}"
                + (f" · <i>{', '.join(flags)}</i>" if flags else ""),
                unsafe_allow_html=True,
            )
            if r.get("stale_note"):
                st.warning(r["stale_note"])
            edit_key = f"edit-{r['id']}"
            if st.session_state.get(edit_key):
                new_body = st.text_area("Body", value=r["body"], height=320, key=f"body-{r['id']}")
                c1, c2, c3 = st.columns(3)
                if c1.button("Save", key=f"save-{r['id']}"):
                    p = C.CARDS / r["file"]
                    fm, _ = C.load(p)
                    C.dump(p, fm, new_body)
                    st.session_state[edit_key] = False
                    refresh()
                    st.rerun()
                if c2.button("Save and mark as my words", key=f"own-{r['id']}"):
                    p = C.CARDS / r["file"]
                    fm, _ = C.load(p)
                    fm["reviewed_by_me"] = True
                    C.dump(p, fm, new_body)
                    st.session_state[edit_key] = False
                    refresh()
                    st.rerun()
                if c3.button("Cancel", key=f"cancel-{r['id']}"):
                    st.session_state[edit_key] = False
                    st.rerun()
            else:
                st.markdown(r["body"])
                if st.button("Edit", key=f"editbtn-{r['id']}"):
                    st.session_state[edit_key] = True
                    st.rerun()
            with st.expander("Sources"):
                for s in r.get("sources") or []:
                    st.code(str(s), language=None)

with tab_quiz:
    st.caption("Same arithmetic as the chat quiz. Answer out loud or on paper, reveal, then mark yourself honestly.")
    due = sorted(
        [r for r in view if (C.as_date(r.get("next_due")) or today) <= today] or view,
        key=lambda r: (C.as_date(r.get("next_due")) or today, int(r.get("tested") or 0), r["id"]),
    )[:3]
    if not due:
        st.info("Nothing matches the filter.")
    for r in due:
        st.markdown(f"### {r['question']}")
        st.caption(f"{r['id']} · {area_name(r.get('area'))} · {r.get('level')} · last {r.get('confidence')}")
        rk = f"reveal-{r['id']}"
        if not st.session_state.get(rk):
            if st.button("Reveal", key=f"rb-{r['id']}"):
                st.session_state[rk] = True
                st.rerun()
        else:
            parts = body_lines(r["body"])
            for k in ["Claim", "Why", "Rejected", "Where", "Prevents", "Trade-off"]:
                if k in parts:
                    st.markdown(f"**{k}.** {parts[k]}")
            miss = st.text_input("What did you miss?", key=f"miss-{r['id']}")
            b1, b2, b3 = st.columns(3)
            for col, mark in zip((b1, b2, b3), MARKS):
                if col.button(mark, key=f"mark-{mark}-{r['id']}"):
                    class A:  # minimal argparse stand-in for cards.cmd_record
                        pass
                    a = A()
                    a.id, a.mark, a.miss = r["id"], mark, miss or None
                    C.cmd_record(a)
                    st.session_state[rk] = False
                    refresh()
                    st.rerun()
        st.divider()
