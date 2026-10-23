"""Look and feel: the stylesheet and the small HTML building blocks used by every page."""

import html
from datetime import date

import plotly.graph_objects as go
import streamlit as st

ZERO_DECIMAL = {"PKR", "JPY", "INR", "BDT", "EGP"}
CYCLE_LABEL = {"weekly": "Weekly", "monthly": "Monthly", "quarterly": "Quarterly", "yearly": "Yearly"}

# Palette (kept in one place so the charts match the CSS)
INK = "#e8ebf7"
MUTED = "#8b95b8"
GRID = "#1f2a4d"
INDIGO = "#6366f1"
VIOLET = "#8b5cf6"
CYAN = "#22d3ee"
GREEN = "#34d399"
AMBER = "#fbbf24"
RED = "#f87171"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* Do NOT use a wildcard here: it would also override the icon font and show icon names as text. */
html, body, .stApp, .stApp p, .stApp label, .stApp li, .stApp h1, .stApp h2, .stApp h3,
.stApp input, .stApp textarea, .stApp button, .stApp [data-baseweb="select"] div,
.stApp [data-testid="stMarkdownContainer"], .stApp [data-testid="stCaptionContainer"] {
  font-family: 'Inter', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
.stApp {
  background:
    radial-gradient(1100px 560px at 8% -12%, rgba(99,102,241,.20), transparent 60%),
    radial-gradient(900px 520px at 100% -5%, rgba(139,92,246,.15), transparent 55%),
    #0b1020;
}
[data-testid="stHeader"] { background: transparent; }
#MainMenu, footer, [data-testid="stDecoration"] { visibility: hidden; }
.block-container { padding-top: 2.4rem; padding-bottom: 4rem; max-width: 1240px; }

/* ---------- sidebar ---------- */
section[data-testid="stSidebar"] {
  background: linear-gradient(180deg, #0f1733 0%, #0a1126 100%);
  border-right: 1px solid #1b2548;
}
section[data-testid="stSidebar"] .block-container { padding-top: 1.4rem; }
.brand { display:flex; align-items:center; gap:.7rem; margin: .2rem 0 1.4rem 0; }
.brand-mark {
  width:40px; height:40px; border-radius:12px; display:grid; place-items:center;
  background: linear-gradient(135deg, #6366f1, #8b5cf6 60%, #22d3ee);
  box-shadow: 0 8px 22px rgba(99,102,241,.45); font-size:1.15rem;
}
.brand-name { font-size:1.3rem; font-weight:800; letter-spacing:-.02em; color:#fff; line-height:1.1; }
.brand-sub { font-size:.72rem; color:#8b95b8; letter-spacing:.04em; }
.side-label {
  font-size:.68rem; font-weight:700; letter-spacing:.12em; text-transform:uppercase;
  color:#6f7aa3; margin:1.2rem 0 .5rem 0;
}
section[data-testid="stSidebar"] div[role="radiogroup"] { gap:.25rem; }
section[data-testid="stSidebar"] div[role="radiogroup"] > div { width:100%; }
section[data-testid="stSidebar"] div[role="radiogroup"] label {
  padding:.62rem .85rem; border-radius:12px; border:1px solid transparent;
  transition: background .15s, border-color .15s; cursor:pointer; width:100%; box-sizing:border-box;
}
section[data-testid="stSidebar"] div[role="radiogroup"] label:hover { background: rgba(99,102,241,.10); }
section[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {
  background: linear-gradient(90deg, rgba(99,102,241,.28), rgba(139,92,246,.12));
  border-color: rgba(129,140,248,.45);
}
/* hide the round radio indicator; keep only the label text */
section[data-testid="stSidebar"] div[role="radiogroup"] label > div > div:not([data-testid="stMarkdownContainer"]) { display:none; }
section[data-testid="stSidebar"] div[role="radiogroup"] label p { font-weight:600; font-size:.95rem; }
.status-pill {
  display:inline-flex; align-items:center; gap:.45rem; padding:.35rem .75rem; border-radius:999px;
  font-size:.76rem; font-weight:600; background:rgba(52,211,153,.10); color:#6ee7b7;
  border:1px solid rgba(52,211,153,.28);
}
.status-pill .dot { width:7px; height:7px; border-radius:50%; background:#34d399; box-shadow:0 0 8px #34d399; }
.status-pill.warn { background:rgba(251,191,36,.10); color:#fcd34d; border-color:rgba(251,191,36,.28); }
.status-pill.warn .dot { background:#fbbf24; box-shadow:0 0 8px #fbbf24; }

/* ---------- page header ---------- */
.page-head { display:flex; align-items:flex-end; justify-content:space-between; gap:1rem; margin-bottom:1.4rem; }
.page-title { font-size:2rem; font-weight:800; letter-spacing:-.03em; color:#fff; margin:0; line-height:1.15; }
.page-sub { color:#8b95b8; font-size:.98rem; margin-top:.3rem; }
.section-title { font-size:1.02rem; font-weight:700; color:#f3f5ff; margin:0 0 .15rem 0; }
.section-sub { font-size:.8rem; color:#8b95b8; margin-bottom:.6rem; }
.gap { height:1.1rem; }

/* ---------- KPI cards ---------- */
.kpi {
  position:relative; overflow:hidden; border-radius:18px; padding:1.15rem 1.25rem 1.1rem 1.25rem;
  background: linear-gradient(160deg, #141d3e 0%, #101834 100%);
  border:1px solid #222d55; min-height:128px;
}
.kpi::before {
  content:""; position:absolute; left:0; top:0; bottom:0; width:4px; background:var(--accent);
  box-shadow: 0 0 18px var(--accent);
}
.kpi::after {
  content:""; position:absolute; right:-40px; top:-40px; width:140px; height:140px; border-radius:50%;
  background: var(--accent); opacity:.10; filter: blur(8px);
}
.kpi-label { font-size:.72rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#8b95b8; }
.kpi-value { font-size:1.95rem; font-weight:800; letter-spacing:-.03em; color:#fff; margin:.35rem 0 .15rem 0; line-height:1.1; }
.kpi-value small { font-size:.95rem; font-weight:600; color:#8b95b8; margin-right:.3rem; letter-spacing:0; }
.kpi-sub { font-size:.82rem; color:#8b95b8; }

/* ---------- bordered containers become cards ---------- */
[data-testid="stVerticalBlockBorderWrapper"]:has(> div > [data-testid="stVerticalBlock"]) {
  border-radius:18px;
}
div[data-testid="stVerticalBlockBorderWrapper"] {
  background: linear-gradient(160deg, #121a38 0%, #0f1630 100%);
  border-color:#222d55 !important; border-radius:18px;
}

/* ---------- badges ---------- */
.badge {
  display:inline-block; padding:.18rem .6rem; border-radius:999px; font-size:.72rem; font-weight:700;
  letter-spacing:.01em; white-space:nowrap;
}
.b-cat { color:var(--c); background:color-mix(in srgb, var(--c) 16%, transparent); border:1px solid color-mix(in srgb, var(--c) 40%, transparent); }
.b-today { color:#fecaca; background:rgba(248,113,113,.16); border:1px solid rgba(248,113,113,.4); }
.b-soon  { color:#fde68a; background:rgba(251,191,36,.14); border:1px solid rgba(251,191,36,.38); }
.b-ok    { color:#a5b4fc; background:rgba(99,102,241,.14); border:1px solid rgba(129,140,248,.35); }
.b-paused{ color:#aab3d1; background:rgba(148,163,184,.12); border:1px solid rgba(148,163,184,.3); }
.b-cycle { color:#c4b5fd; background:rgba(139,92,246,.12); border:1px solid rgba(139,92,246,.3); }

/* ---------- upcoming list ---------- */
.up-item {
  display:flex; align-items:center; gap:.9rem; padding:.7rem .8rem; margin-bottom:.55rem;
  border-radius:14px; background:rgba(255,255,255,.025); border:1px solid #1f2a4d;
}
.up-date {
  width:48px; min-width:48px; text-align:center; border-radius:12px; padding:.3rem 0 .35rem 0;
  background:linear-gradient(160deg, rgba(99,102,241,.30), rgba(139,92,246,.18)); border:1px solid rgba(129,140,248,.35);
}
.up-date .d { display:block; font-size:1.15rem; font-weight:800; color:#fff; line-height:1.1; }
.up-date .m { display:block; font-size:.62rem; font-weight:700; letter-spacing:.1em; color:#a5b4fc; }
.up-main { flex:1; min-width:0; }
.up-name { font-weight:700; color:#fff; font-size:.98rem; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.up-meta { font-size:.78rem; color:#8b95b8; margin-top:.1rem; }
.up-right { text-align:right; }
.up-amount { font-weight:700; color:#fff; font-size:.95rem; }
.up-when { margin-top:.2rem; }

/* ---------- subscription rows ---------- */
.avatar {
  width:46px; height:46px; min-width:46px; border-radius:14px; display:grid; place-items:center;
  font-weight:800; font-size:1.15rem; color:#fff;
  background: linear-gradient(135deg, var(--c), color-mix(in srgb, var(--c) 55%, #0b1020));
  box-shadow: 0 6px 16px color-mix(in srgb, var(--c) 35%, transparent);
}
.row-main { display:flex; align-items:center; gap:.9rem; }
.row-name { font-weight:700; color:#fff; font-size:1.02rem; line-height:1.2; }
.row-name.dim { color:#8b95b8; text-decoration: line-through; text-decoration-color:#4a547a; }
.row-sub { margin-top:.3rem; display:flex; gap:.4rem; flex-wrap:wrap; }
.cell-label { font-size:.66rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#6f7aa3; }
.cell-value { font-size:1rem; font-weight:700; color:#fff; margin-top:.1rem; }
.cell-note { font-size:.76rem; color:#8b95b8; }

/* ---------- insights ---------- */
.insight {
  display:flex; gap:.7rem; padding:.75rem .9rem; margin-bottom:.55rem; border-radius:14px;
  background:rgba(99,102,241,.07); border:1px solid rgba(99,102,241,.2); font-size:.9rem; color:#dfe4f8; line-height:1.45;
}
.insight .ico { font-size:1.05rem; line-height:1.4; }

/* ---------- empty state ---------- */
.empty {
  text-align:center; padding:3.2rem 1rem 2.2rem 1rem; border-radius:20px;
  background: linear-gradient(160deg, rgba(99,102,241,.10), rgba(139,92,246,.05));
  border:1px dashed rgba(129,140,248,.35);
}
.empty .big { font-size:2.6rem; margin-bottom:.4rem; }
.empty h3 { color:#fff; margin:.2rem 0 .3rem 0; font-size:1.3rem; }
.empty p { color:#8b95b8; margin:0; }

/* ---------- preview card on the Add page ---------- */
.preview {
  border-radius:16px; padding:1rem 1.15rem; background:linear-gradient(160deg, rgba(34,211,238,.10), rgba(99,102,241,.10));
  border:1px solid rgba(34,211,238,.28);
}
.preview .p-label { font-size:.7rem; font-weight:700; letter-spacing:.1em; text-transform:uppercase; color:#67e8f9; }
.preview .p-value { font-size:1.45rem; font-weight:800; color:#fff; margin-top:.2rem; }
.preview .p-note { font-size:.8rem; color:#9fb0d6; margin-top:.15rem; }

/* ---------- widgets ---------- */
div[data-testid="stButton"] > button, div[data-testid="stDownloadButton"] > button, div[data-testid="stFormSubmitButton"] > button {
  border-radius:12px; font-weight:600; border:1px solid #2b3868; background:#141d3e; color:#e8ebf7;
  transition: transform .08s ease, border-color .15s, background .15s;
}
div[data-testid="stButton"] > button:hover, div[data-testid="stDownloadButton"] > button:hover {
  border-color:#6366f1; background:#19234c; color:#fff;
}
div[data-testid="stButton"] > button:active { transform: scale(.98); }
button[kind="primary"], button[data-testid="stBaseButton-primary"] {
  background: linear-gradient(135deg, #6366f1, #8b5cf6) !important; border:none !important; color:#fff !important;
  box-shadow: 0 8px 20px rgba(99,102,241,.35);
}
button[kind="primary"]:hover, button[data-testid="stBaseButton-primary"]:hover { filter: brightness(1.08); }
div[data-baseweb="input"], div[data-baseweb="select"] > div, div[data-baseweb="textarea"], div[data-baseweb="base-input"] {
  border-radius:12px !important;
}
.stTextInput input, .stNumberInput input, .stDateInput input, .stTextArea textarea { color:#fff; }
label[data-testid="stWidgetLabel"] p { font-size:.82rem; font-weight:600; color:#aab3d1; }
hr { border-color:#1f2a4d; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


# ------------------------------------------------------------------ formatting
def money(value: float, currency: str) -> str:
    decimals = 0 if currency in ZERO_DECIMAL else 2
    return f"{currency} {value:,.{decimals}f}"


def esc(text: str) -> str:
    return html.escape(str(text), quote=True)


def renewal_badge(days: int, active: bool = True) -> str:
    if not active:
        return '<span class="badge b-paused">Paused</span>'
    if days <= 0:
        return '<span class="badge b-today">Renews today</span>'
    if days == 1:
        return '<span class="badge b-today">Tomorrow</span>'
    if days <= 7:
        return f'<span class="badge b-soon">In {days} days</span>'
    return f'<span class="badge b-ok">In {days} days</span>'


def category_badge(name: str | None, color: str | None) -> str:
    label = esc(name or "Uncategorized")
    return f'<span class="badge b-cat" style="--c:{esc(color or "#94a3b8")}">{label}</span>'


# ------------------------------------------------------------------- components
def page_header(title: str, subtitle: str) -> None:
    st.markdown(
        f'<div class="page-head"><div><h1 class="page-title">{esc(title)}</h1>'
        f'<div class="page-sub">{esc(subtitle)}</div></div></div>',
        unsafe_allow_html=True,
    )


def section(title: str, subtitle: str = "") -> None:
    sub = f'<div class="section-sub">{esc(subtitle)}</div>' if subtitle else ""
    st.markdown(f'<div class="section-title">{esc(title)}</div>{sub}', unsafe_allow_html=True)


def gap(rem: float = 1.1) -> None:
    st.markdown(f'<div class="gap" style="height:{rem}rem"></div>', unsafe_allow_html=True)


def kpi_card(label: str, value: str, sub: str, accent: str, prefix: str = "") -> None:
    prefix_html = f"<small>{esc(prefix)}</small>" if prefix else ""
    st.markdown(
        f'<div class="kpi" style="--accent:{accent}">'
        f'<div class="kpi-label">{esc(label)}</div>'
        f'<div class="kpi-value">{prefix_html}{esc(value)}</div>'
        f'<div class="kpi-sub">{esc(sub)}</div></div>',
        unsafe_allow_html=True,
    )


def empty_state(icon: str, title: str, text: str) -> None:
    st.markdown(
        f'<div class="empty"><div class="big">{icon}</div><h3>{esc(title)}</h3><p>{esc(text)}</p></div>',
        unsafe_allow_html=True,
    )


def style_figure(fig: go.Figure, height: int = 320) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=8, r=8, t=8, b=8),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color=INK, size=12),
        hoverlabel=dict(bgcolor="#1a2347", font_color="#fff", bordercolor="#3a4a85"),
        legend=dict(font=dict(color=MUTED)),
    )
    return fig


def show_chart(fig: go.Figure) -> None:
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})


def go_to(page: str) -> None:
    """Button callback that switches the sidebar page (callbacks run before the page redraws)."""
    st.session_state.page = page


def parse_date(value: str | date) -> date:
    return value if isinstance(value, date) else date.fromisoformat(value)
