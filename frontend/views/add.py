"""Add page: quick-add templates, a live cost preview and the new-subscription form."""

from datetime import date, timedelta

import streamlit as st

import api
import ui

FACTOR = {"weekly": 52 / 12, "monthly": 1.0, "quarterly": 1 / 3, "yearly": 1 / 12}
PER = {"weekly": "week", "monthly": "month", "quarterly": "quarter", "yearly": "year"}

# name, suggested price, currency, billing cycle, category. Prices are only suggestions.
TEMPLATES = [
    ("Netflix", 15.49, "USD", "monthly", "Entertainment"),
    ("YouTube Premium", 13.99, "USD", "monthly", "Entertainment"),
    ("Disney+", 13.99, "USD", "monthly", "Entertainment"),
    ("Spotify Premium", 11.99, "USD", "monthly", "Music"),
    ("ChatGPT Plus", 20.00, "USD", "monthly", "Productivity"),
    ("Microsoft 365", 99.99, "USD", "yearly", "Productivity"),
    ("Notion Plus", 10.00, "USD", "monthly", "Productivity"),
    ("Canva Pro", 14.99, "USD", "monthly", "Productivity"),
    ("GitHub Copilot", 10.00, "USD", "monthly", "Cloud & Dev"),
    ("Google One 2 TB", 9.99, "USD", "monthly", "Cloud & Dev"),
    ("iCloud+", 2.99, "USD", "monthly", "Cloud & Dev"),
    ("Amazon Prime", 14.99, "USD", "monthly", "Shopping"),
]

CYCLES = list(FACTOR)


# The form widgets use keys that end in a version number. Bumping the version after a successful
# save gives the next visit a brand-new, empty form (Streamlit forgets widgets that are not shown).
def _version() -> int:
    return st.session_state.setdefault("add_version", 0)


def _key(field: str) -> str:
    return f"add_{field}_{_version()}"


def _use_template(template: tuple) -> None:
    name, price, currency, cycle, category = template
    s = st.session_state
    s[_key("name")] = name
    s[_key("price")] = float(price)
    s[_key("currency")] = currency
    s[_key("cycle")] = cycle
    if category in s.get("add_cat_names", []):
        s[_key("category")] = category
    s.add_error = None


def _submit(cat_ids: dict, base: str) -> None:
    s = st.session_state
    payload = {
        "name": s[_key("name")],
        "price": s[_key("price")],
        "currency": s[_key("currency")],
        "billing_cycle": s[_key("cycle")],
        "next_renewal": s[_key("renewal")].isoformat(),
        "category_id": cat_ids.get(s[_key("category")]),
        "notes": s[_key("notes")].strip() or None,
    }
    try:
        api.create_subscription(payload, base)
    except api.ApiError as error:
        s.add_error = str(error)
        return
    s.flash = ("success", f"Added {s[_key('name')].strip()}.")
    s.add_version = _version() + 1  # next visit starts with an empty form
    s.add_error = None
    s.page = "subscriptions"


def _create_category() -> None:
    s = st.session_state
    try:
        created = api.create_category(s.new_cat_name, s.new_cat_color)
    except api.ApiError as error:
        s.cat_error = str(error)
        return
    s.cat_error = None
    s[_key("category")] = created["name"]
    s.new_cat_name = ""
    s.flash = ("success", f"Created category {created['name']}.")


def render(base: str, meta: dict) -> None:
    ui.page_header("Add subscription", "Pick a popular service to start fast, or fill in your own.")

    cats = api.categories()
    cat_names = [c["name"] for c in cats]
    cat_ids = {c["name"]: c["id"] for c in cats}
    st.session_state.add_cat_names = cat_names
    st.session_state.setdefault("add_error", None)
    st.session_state.setdefault("cat_error", None)

    # ------------------------------------------------------------ templates
    with st.container(border=True):
        ui.section("Quick add", "Click a service to pre-fill the form. Prices are suggestions, so adjust them.")
        for start in range(0, len(TEMPLATES), 6):
            cols = st.columns(6)
            for col, template in zip(cols, TEMPLATES[start:start + 6]):
                col.button(template[0], key=f"tpl_{template[0]}", width="stretch",
                           on_click=_use_template, args=(template,))

    ui.gap(0.4)

    form_col, side_col = st.columns([1.55, 1])

    # ----------------------------------------------------------------- form
    with form_col:
        with st.container(border=True):
            ui.section("Subscription details")
            st.text_input("Name", key=_key("name"), max_chars=100, placeholder="For example: Netflix")
            c1, c2 = st.columns(2)
            c1.number_input("Price", key=_key("price"), min_value=0.01, value=10.0, step=1.0, format="%.2f")
            codes = list(meta["currencies"])
            c2.selectbox("Currency", codes, key=_key("currency"), index=codes.index("USD"),
                         format_func=lambda c: f"{c} · {meta['currencies'][c]}")
            c3, c4 = st.columns(2)
            c3.selectbox("Billing cycle", CYCLES, key=_key("cycle"), index=CYCLES.index("monthly"),
                         format_func=lambda c: ui.CYCLE_LABEL[c])
            c4.date_input("Next renewal date", key=_key("renewal"), value=date.today() + timedelta(days=30))
            st.selectbox("Category", cat_names, key=_key("category"), index=0)
            st.text_input("Notes (optional)", key=_key("notes"), max_chars=300,
                          placeholder="Shared with family, cancel before December...")

            if st.session_state.add_error:
                st.error(st.session_state.add_error)
            st.button("Add subscription", type="primary", width="stretch", icon=":material/add_circle:",
                      on_click=_submit, args=(cat_ids, base))

    # ---------------------------------------------------------------- side
    with side_col:
        _preview(base)
        ui.gap(0.5)
        with st.container(border=True):
            ui.section("Need another category?")
            st.text_input("Category name", key="new_cat_name", placeholder="For example: Gaming",
                          label_visibility="collapsed")
            st.color_picker("Colour", value="#22c55e", key="new_cat_color")
            if st.session_state.cat_error:
                st.error(st.session_state.cat_error)
            st.button("Create category", width="stretch", icon=":material/label:", on_click=_create_category)


def _preview(base: str) -> None:
    s = st.session_state
    try:
        rates = api.rates()["rates"]
        price, currency, cycle = s[_key("price")], s[_key("currency")], s[_key("cycle")]
        monthly = price / rates[currency] * rates[base] * FACTOR[cycle]
        body = (
            f'<div class="p-label">Live cost preview</div>'
            f'<div class="p-value">{ui.esc(ui.money(monthly, base))} <span style="font-size:.95rem;font-weight:600;color:#9fb0d6">/ month</span></div>'
            f'<div class="p-note">{ui.esc(ui.money(monthly * 12, base))} per year · '
            f'{ui.esc(ui.money(price, currency))} per {PER[cycle]}</div>'
        )
    except (api.ApiError, KeyError, ZeroDivisionError):
        body = '<div class="p-label">Live cost preview</div><div class="p-note">Preview unavailable right now.</div>'
    st.markdown(f'<div class="preview">{body}</div>', unsafe_allow_html=True)
