"""Reports page: downloadable CSV, a full table, yearly cost chart and exchange rates."""

from datetime import date

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import api
import ui


def render(base: str) -> None:
    ui.page_header("Reports", f"Export your data or look at the full picture. Amounts shown in {base}.")

    items = api.subscriptions(base, sort="name")
    if not items:
        ui.empty_state("📄", "Nothing to report yet", "Add a few subscriptions and your report will appear here.")
        return

    active = [s for s in items if s["is_active"]]
    yearly = sum(s["yearly_cost"] for s in active)

    left, right = st.columns([2.2, 1])
    with left:
        st.markdown(
            f'<div class="section-sub" style="margin-top:.5rem">{len(items)} subscriptions in total · '
            f'{ui.esc(ui.money(yearly, base))} per year across the {len(active)} active ones.</div>',
            unsafe_allow_html=True,
        )
    with right:
        st.download_button(
            "Download CSV report",
            data=api.export_csv(base),
            file_name=f"subtrack-report-{date.today().isoformat()}.csv",
            mime="text/csv",
            type="primary",
            width="stretch",
            icon=":material/download:",
        )

    ui.gap(0.3)

    with st.container(border=True):
        ui.section("Yearly cost per subscription", "Active subscriptions, highest first")
        _yearly_chart(active, base)

    ui.gap(0.3)

    with st.container(border=True):
        ui.section("All subscriptions")
        frame = pd.DataFrame(
            {
                "Name": [s["name"] for s in items],
                "Category": [s["category_name"] or "Uncategorized" for s in items],
                "Status": ["Active" if s["is_active"] else "Paused" for s in items],
                "Price": [s["price"] for s in items],
                "Currency": [s["currency"] for s in items],
                "Cycle": [ui.CYCLE_LABEL[s["billing_cycle"]] for s in items],
                "Next renewal": [ui.parse_date(s["next_renewal"]) for s in items],
                f"Monthly ({base})": [s["monthly_cost"] for s in items],
                f"Yearly ({base})": [s["yearly_cost"] for s in items],
            }
        )
        st.dataframe(
            frame,
            hide_index=True,
            width="stretch",
            column_config={
                "Price": st.column_config.NumberColumn(format="%.2f"),
                "Next renewal": st.column_config.DateColumn(format="MMM D, YYYY"),
                f"Monthly ({base})": st.column_config.NumberColumn(format="%,.2f"),
                f"Yearly ({base})": st.column_config.NumberColumn(format="%,.2f"),
            },
        )

    ui.gap(0.3)

    with st.expander("Exchange rates used for conversion"):
        info = api.rates()
        source = ("Live rates from open.er-api.com" + (f", updated {info['updated']}" if info["updated"] else "")
                  if info["source"] == "live" else "Offline approximate rates (no internet or LIVE_RATES=false)")
        st.caption(source)
        names = st.session_state.meta["currencies"]
        table = pd.DataFrame(
            {
                "Currency": [f"{code} · {names[code]}" for code in names],
                "Units per 1 USD": [info["rates"].get(code) for code in names],
            }
        )
        st.dataframe(table, hide_index=True, width="stretch")


def _yearly_chart(active: list[dict], base: str) -> None:
    if not active:
        st.caption("No active subscriptions.")
        return
    ordered = sorted(active, key=lambda s: s["yearly_cost"])
    fig = go.Figure(
        go.Bar(
            y=[s["name"] for s in ordered],
            x=[s["yearly_cost"] for s in ordered],
            orientation="h",
            marker=dict(color=[s["category_color"] or "#94a3b8" for s in ordered], line=dict(width=0)),
            text=[f"{s['yearly_cost']:,.0f}" for s in ordered],
            textposition="outside",
            textfont=dict(color=ui.INK, size=12),
            hovertemplate="<b>%{y}</b><br>" + base + " %{x:,.0f} / year<extra></extra>",
        )
    )
    peak = max(s["yearly_cost"] for s in ordered)
    fig.update_xaxes(showgrid=True, gridcolor=ui.GRID, zeroline=False, tickfont=dict(color=ui.MUTED),
                     range=[0, peak * 1.18])
    fig.update_yaxes(showgrid=False, tickfont=dict(color=ui.INK, size=12))
    fig.update_layout(bargap=0.3)
    ui.show_chart(ui.style_figure(fig, max(260, 34 * len(ordered) + 40)))
