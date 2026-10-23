"""SubTrack web interface (Streamlit).  Start it with:  streamlit run frontend/app.py"""

import streamlit as st

import api
import ui
from views import add, dashboard, reports, subscriptions

st.set_page_config(page_title="SubTrack", page_icon="💳", layout="wide", initial_sidebar_state="expanded")
ui.inject_css()

PAGES = {
    "dashboard": "📊  Dashboard",
    "subscriptions": "🗂️  Subscriptions",
    "add": "➕  Add subscription",
    "reports": "📄  Reports",
}


def backend_down(error: api.ApiError) -> None:
    ui.page_header("Backend not running", "The interface needs the SubTrack API to be started first.")
    st.error(str(error))
    st.markdown(
        "**How to start it**\n\n"
        "1. Open a second terminal in the project folder.\n"
        "2. Run `run_backend.bat` (or `uvicorn app.main:app --reload`).\n"
        "3. Wait for *Application startup complete*, then refresh this page.\n\n"
        "If the backend prints a database error, run `python -m app.database.diagnose` "
        "and check the SQL Server settings in the `.env` file."
    )
    st.button("Try again", icon=":material/refresh:")


# ------------------------------------------------------------------ backend check
try:
    st.session_state.meta = api.meta()
except api.ApiError as error:
    backend_down(error)
    st.stop()

meta = st.session_state.meta
st.session_state.setdefault("page", "dashboard")
st.session_state.setdefault("base", meta["base_currency"])

# ------------------------------------------------------------------------ sidebar
with st.sidebar:
    st.markdown(
        '<div class="brand"><div class="brand-mark">💳</div>'
        '<div><div class="brand-name">SubTrack</div>'
        '<div class="brand-sub">SUBSCRIPTION MANAGER</div></div></div>',
        unsafe_allow_html=True,
    )

    st.radio("Navigation", list(PAGES), key="page", format_func=PAGES.get, label_visibility="collapsed")

    st.markdown('<div class="side-label">Display currency</div>', unsafe_allow_html=True)
    codes = list(meta["currencies"])
    st.selectbox("Currency", codes, key="base", label_visibility="collapsed",
                 format_func=lambda c: f"{c} · {meta['currencies'][c]}")

    st.markdown('<div class="side-label">System</div>', unsafe_allow_html=True)
    live = meta["rate_source"] == "live"
    st.markdown(
        f'<div class="status-pill"><span class="dot"></span>{ui.esc(meta["database"])} connected</div>'
        f'<div style="height:.45rem"></div>'
        f'<div class="status-pill {"" if live else "warn"}"><span class="dot"></span>'
        f'{"Live exchange rates" if live else "Offline rates"}</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div class="side-label">Demo tools</div>', unsafe_allow_html=True)
    with st.expander("Sample data"):
        if st.button("Load sample data", width="stretch", icon=":material/auto_awesome:"):
            added = api.seed_demo()
            st.session_state.flash = (
                ("success", f"Loaded {added} sample subscriptions.") if added
                else ("info", "Sample data loads only when there are no subscriptions.")
            )
            st.rerun()
        confirm = st.checkbox("I want to delete everything")
        if st.button("Delete all subscriptions", width="stretch", disabled=not confirm,
                     icon=":material/delete_forever:"):
            removed = api.clear_all()
            st.session_state.flash = ("success", f"Deleted {removed} subscriptions.")
            st.rerun()

# ------------------------------------------------------------------- flash message
if "flash" in st.session_state:
    kind, text = st.session_state.pop("flash")
    st.toast(text, icon="✅" if kind == "success" else "ℹ️")

# ---------------------------------------------------------------------------- page
base = st.session_state.base
page = st.session_state.page

try:
    if page == "dashboard":
        dashboard.render(base)
    elif page == "subscriptions":
        subscriptions.render(base, meta)
    elif page == "add":
        add.render(base, meta)
    else:
        reports.render(base)
except api.ApiError as error:
    if error.offline:
        backend_down(error)
    else:
        st.error(str(error))
