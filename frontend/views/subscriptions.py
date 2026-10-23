"""Subscriptions page: search, filter, edit, pause/resume and delete."""

import streamlit as st

import api
import ui

SORT_OPTIONS = {"Next renewal": "renewal", "Highest price": "price", "Name (A-Z)": "name"}
STATUS_OPTIONS = {"All": "all", "Active": "active", "Paused": "paused"}
CYCLES = ["weekly", "monthly", "quarterly", "yearly"]


def render(base: str, meta: dict) -> None:
    ui.page_header("Subscriptions", "Everything you pay for, in one place. Pause, edit or remove anything.")

    cats = api.categories()
    cat_by_name = {c["name"]: c["id"] for c in cats}

    f1, f2, f3, f4 = st.columns([2.2, 1.4, 1.1, 1.3])
    search = f1.text_input("Search", placeholder="Search by name...", label_visibility="collapsed")
    cat_choice = f2.selectbox("Category", ["All categories"] + list(cat_by_name),
                              label_visibility="collapsed")
    status_choice = f3.selectbox("Status", list(STATUS_OPTIONS), label_visibility="collapsed")
    sort_choice = f4.selectbox("Sort by", list(SORT_OPTIONS), label_visibility="collapsed")

    items = api.subscriptions(
        base,
        status=STATUS_OPTIONS[status_choice],
        category_id=cat_by_name.get(cat_choice),
        search=search.strip(),
        sort=SORT_OPTIONS[sort_choice],
    )

    total = len(api.subscriptions(base)) if (search or cat_choice != "All categories"
                                           or status_choice != "All") else len(items)
    if total == 0:
        ui.empty_state("🗂️", "Nothing here yet", "Add your first subscription to start tracking.")
        ui.gap(0.8)
        _, mid, _ = st.columns([1.2, 1, 1.2])
        mid.button("Add a subscription", type="primary", width="stretch", icon=":material/add:",
                   on_click=ui.go_to, args=("add",))
        return

    monthly = sum(s["monthly_cost"] for s in items if s["is_active"])
    st.markdown(
        f'<div class="section-sub" style="margin:.4rem 0 .8rem 0">{len(items)} subscription'
        f'{"s" if len(items) != 1 else ""} · {ui.esc(ui.money(monthly, base))} per month (active only)</div>',
        unsafe_allow_html=True,
    )

    if not items:
        ui.empty_state("🔍", "No matches", "Try a different search or clear the filters.")
        return

    for sub in items:
        _row(sub, base, cats)


def _row(sub: dict, base: str, cats: list[dict]) -> None:
    color = sub["category_color"] or "#94a3b8"
    active = sub["is_active"]
    with st.container(border=True):
        c_main, c_price, c_cost, c_when, c_actions = st.columns([3.1, 1.7, 1.7, 1.6, 1.5], vertical_alignment="center")

        c_main.markdown(
            '<div class="row-main">'
            f'<div class="avatar" style="--c:{ui.esc(color)}">{ui.esc(sub["name"][:1].upper())}</div>'
            '<div>'
            f'<div class="row-name{"" if active else " dim"}">{ui.esc(sub["name"])}</div>'
            f'<div class="row-sub">{ui.category_badge(sub["category_name"], sub["category_color"])}'
            f'<span class="badge b-cycle">{ui.esc(ui.CYCLE_LABEL[sub["billing_cycle"]])}</span></div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
        c_price.markdown(
            '<div class="cell-label">Price</div>'
            f'<div class="cell-value">{ui.esc(ui.money(sub["price"], sub["currency"]))}</div>'
            f'<div class="cell-note">per {ui.esc(_per(sub["billing_cycle"]))}</div>',
            unsafe_allow_html=True,
        )
        c_cost.markdown(
            '<div class="cell-label">Monthly cost</div>'
            f'<div class="cell-value">{ui.esc(ui.money(sub["monthly_cost"], base))}</div>'
            f'<div class="cell-note">{ui.esc(ui.money(sub["yearly_cost"], base))} / year</div>',
            unsafe_allow_html=True,
        )
        due = ui.parse_date(sub["next_renewal"])
        c_when.markdown(
            '<div class="cell-label">Next renewal</div>'
            f'<div class="cell-value">{due.strftime("%b")} {due.day}, {due.year}</div>'
            f'<div style="margin-top:.25rem">{ui.renewal_badge(sub["days_until_renewal"], active)}</div>',
            unsafe_allow_html=True,
        )

        with c_actions:
            a1, a2, a3 = st.columns(3)
            with a1:
                if st.button("", key=f"edit_{sub['id']}", icon=":material/edit:", help="Edit", width="stretch"):
                    edit_dialog(sub, base, cats)
            with a2:
                _toggle_button(sub, base)
            with a3:
                if st.button("", key=f"delete_{sub['id']}", icon=":material/delete:", help="Delete", width="stretch"):
                    delete_dialog(sub)

        if sub.get("notes"):
            st.markdown(f'<div class="cell-note" style="margin-top:.2rem">📝 {ui.esc(sub["notes"])}</div>',
                        unsafe_allow_html=True)


def _per(cycle: str) -> str:
    return {"weekly": "week", "monthly": "month", "quarterly": "quarter", "yearly": "year"}[cycle]


def _toggle_button(sub: dict, base: str) -> None:
    if sub["is_active"]:
        clicked = st.button("", key=f"toggle_{sub['id']}", icon=":material/pause:", help="Pause (stop counting it)",
                            width="stretch")
        message = f"Paused {sub['name']}. It no longer counts towards your spending."
    else:
        clicked = st.button("", key=f"toggle_{sub['id']}", icon=":material/play_arrow:", help="Resume",
                            width="stretch")
        message = f"Resumed {sub['name']}."
    if clicked:
        try:
            api.toggle_subscription(sub["id"], base)
            st.session_state.flash = ("success", message)
            st.rerun()
        except api.ApiError as error:
            st.error(str(error))


@st.dialog("Delete subscription")
def delete_dialog(sub: dict) -> None:
    st.markdown(f"Delete **{sub['name']}** permanently?")
    st.caption("If you only want to stop counting it in your totals, pause it instead.")
    yes, no = st.columns(2)
    if yes.button("Yes, delete", type="primary", width="stretch"):
        try:
            api.delete_subscription(sub["id"])
        except api.ApiError as error:
            st.error(str(error))
            return
        st.session_state.flash = ("success", f"Deleted {sub['name']}.")
        st.rerun()
    if no.button("Cancel", width="stretch"):
        st.rerun()


@st.dialog("Edit subscription")
def edit_dialog(sub: dict, base: str, cats: list[dict]) -> None:
    currencies = list(st.session_state.meta["currencies"])
    cat_names = [c["name"] for c in cats]
    cat_ids = {c["name"]: c["id"] for c in cats}
    current_cat = sub["category_name"] if sub["category_name"] in cat_names else cat_names[-1]

    with st.form(f"edit_form_{sub['id']}", border=False):
        name = st.text_input("Name", value=sub["name"], max_chars=100)
        p1, p2 = st.columns(2)
        price = p1.number_input("Price", min_value=0.01, value=float(sub["price"]), step=1.0, format="%.2f")
        currency = p2.selectbox("Currency", currencies, index=currencies.index(sub["currency"]))
        c1, c2 = st.columns(2)
        cycle = c1.selectbox("Billing cycle", CYCLES, index=CYCLES.index(sub["billing_cycle"]),
                             format_func=lambda c: ui.CYCLE_LABEL[c])
        renewal = c2.date_input("Next renewal", value=ui.parse_date(sub["next_renewal"]))
        category = st.selectbox("Category", cat_names, index=cat_names.index(current_cat))
        notes = st.text_input("Notes", value=sub.get("notes") or "", max_chars=300)
        saved = st.form_submit_button("Save changes", type="primary", width="stretch")

    if saved:
        payload = {
            "name": name,
            "price": price,
            "currency": currency,
            "billing_cycle": cycle,
            "next_renewal": renewal.isoformat(),
            "category_id": cat_ids[category],
            "notes": notes.strip() or None,
        }
        try:
            api.update_subscription(sub["id"], payload, base)
        except api.ApiError as error:
            st.error(str(error))
            return
        st.session_state.flash = ("success", f"Saved changes to {name}.")
        st.rerun()
