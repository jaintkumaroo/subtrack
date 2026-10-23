"""Dashboard page: totals, charts, upcoming renewals and plain-language insights."""

import plotly.graph_objects as go
import streamlit as st

import api
import ui


def render(base: str) -> None:
    data = api.dashboard(base)
    source = "Live exchange rates" if data["rate_source"] == "live" else "Offline exchange rates"
    ui.page_header("Dashboard", f"Where your money goes every month. Amounts shown in {base} · {source}.")

    if data["total_count"] == 0:
        _empty()
        return

    # ------------------------------------------------------------- KPI row
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        ui.kpi_card("Monthly spend", f"{data['monthly_total']:,.{_dec(base)}f}",
                    f"about {ui.money(data['daily_total'], base)} per day", ui.INDIGO, prefix=base)
    with k2:
        ui.kpi_card("Yearly projection", f"{data['yearly_total']:,.{_dec(base)}f}",
                    "if nothing changes", ui.VIOLET, prefix=base)
    with k3:
        ui.kpi_card("Active subscriptions", str(data["active_count"]),
                    f"{data['paused_count']} paused", ui.CYAN)
    with k4:
        sub = f"{data['due_7_count']} renewal{'s' if data['due_7_count'] != 1 else ''} this week"
        ui.kpi_card("Due in 7 days", f"{data['due_7_total']:,.{_dec(base)}f}", sub, ui.AMBER, prefix=base)

    ui.gap()

    # ------------------------------------------------------- charts: row 1
    left, right = st.columns([1, 1.25])
    with left:
        with st.container(border=True):
            ui.section("Spending by category", "Share of your monthly total")
            _category_donut(data, base)
    with right:
        with st.container(border=True):
            ui.section("Upcoming charges", "Money leaving your account over the next 5 weeks")
            _timeline_chart(data, base)

    ui.gap(0.4)

    # ------------------------------------------------------------- row 2
    left, right = st.columns([1.15, 1])
    with left:
        with st.container(border=True):
            ui.section("Renewing soon", "Next 30 days")
            _upcoming_list(data, base)
    with right:
        with st.container(border=True):
            ui.section("Insights", "Generated from your own numbers")
            for text in data["insights"]:
                st.markdown(f'<div class="insight"><span class="ico">💡</span><span>{ui.esc(text)}</span></div>',
                            unsafe_allow_html=True)

    ui.gap(0.4)

    # ------------------------------------------------------------- row 3
    left, right = st.columns([1.3, 1])
    with left:
        with st.container(border=True):
            ui.section("Most expensive subscriptions", "Cost per month")
            _top_chart(data, base)
    with right:
        with st.container(border=True):
            ui.section("Billing cycles", "Monthly cost split by how you pay")
            _cycle_chart(data, base)


def _dec(currency: str) -> int:
    return 0 if currency in ui.ZERO_DECIMAL else 2


def _empty() -> None:
    ui.empty_state("💳", "No subscriptions yet",
                   "Add your first one, or load sample data to explore the dashboard.")
    ui.gap(0.8)
    a, b, c, d = st.columns([1, 1.4, 1.4, 1])
    with b:
        st.button("Add a subscription", type="primary", width="stretch", icon=":material/add:",
                  on_click=ui.go_to, args=("add",))
    with c:
        if st.button("Load sample data", width="stretch", icon=":material/auto_awesome:"):
            added = api.seed_demo()
            st.session_state.flash = ("success", f"Loaded {added} sample subscriptions.")
            st.rerun()


def _category_donut(data: dict, base: str) -> None:
    cats = data["by_category"]
    fig = go.Figure(
        go.Pie(
            labels=[c["name"] for c in cats],
            values=[c["monthly_cost"] for c in cats],
            hole=0.66,
            marker=dict(colors=[c["color"] for c in cats], line=dict(color="#0f1630", width=3)),
            textinfo="none",
            sort=False,
            customdata=[[c["share"], c["count"]] for c in cats],
            hovertemplate="<b>%{label}</b><br>" + base + " %{value:,.0f} / month<br>"
                          "%{customdata[0]}% · %{customdata[1]} subscription(s)<extra></extra>",
        )
    )
    fig.add_annotation(text=f"<b>{data['monthly_total']:,.{_dec(base)}f}</b>", showarrow=False,
                       x=0.5, y=0.54, xref="paper", yref="paper", font=dict(size=22, color="#ffffff"))
    fig.add_annotation(text="per month", showarrow=False, x=0.5, y=0.42, xref="paper", yref="paper",
                       font=dict(size=12, color=ui.MUTED))
    fig.update_layout(legend=dict(orientation="v", x=1.0, y=0.5, font=dict(color=ui.INK, size=12)))
    ui.show_chart(ui.style_figure(fig, 310))


def _timeline_chart(data: dict, base: str) -> None:
    weeks = data["timeline"]
    peak = max((w["amount"] for w in weeks), default=0)
    fig = go.Figure(
        go.Bar(
            x=[w["label"] for w in weeks],
            y=[w["amount"] for w in weeks],
            marker=dict(
                color=[ui.VIOLET if w["amount"] == peak and peak > 0 else ui.INDIGO for w in weeks],
                line=dict(width=0),
            ),
            text=[f"{w['amount']:,.0f}" if w["amount"] else "" for w in weeks],
            textposition="outside",
            textfont=dict(color=ui.INK, size=12),
            customdata=[w["count"] for w in weeks],
            hovertemplate="<b>%{x}</b><br>" + base + " %{y:,.0f}<br>%{customdata} renewal(s)<extra></extra>",
        )
    )
    fig.update_xaxes(showgrid=False, tickfont=dict(color=ui.MUTED, size=11), linecolor=ui.GRID)
    fig.update_yaxes(showgrid=True, gridcolor=ui.GRID, zeroline=False, tickfont=dict(color=ui.MUTED),
                     range=[0, peak * 1.25 if peak else 1])
    fig.update_layout(bargap=0.38)
    ui.show_chart(ui.style_figure(fig, 310))


def _upcoming_list(data: dict, base: str) -> None:
    items = data["upcoming"]
    if not items:
        st.markdown('<div class="section-sub">Nothing renews in the next 30 days. Enjoy the calm.</div>',
                    unsafe_allow_html=True)
        return
    for s in items:
        due = ui.parse_date(s["next_renewal"])
        original = ""
        if s["currency"] != base:
            original = f' · {ui.esc(ui.money(s["price"], s["currency"]))}'
        st.markdown(
            '<div class="up-item">'
            f'<div class="up-date"><span class="d">{due.day}</span><span class="m">{due.strftime("%b").upper()}</span></div>'
            f'<div class="up-main"><div class="up-name">{ui.esc(s["name"])}</div>'
            f'<div class="up-meta">{ui.esc(s["category_name"] or "Uncategorized")} · '
            f'{ui.esc(ui.CYCLE_LABEL[s["billing_cycle"]].lower())}{original}</div></div>'
            f'<div class="up-right"><div class="up-amount">{ui.esc(ui.money(s["price_base"], base))}</div>'
            f'<div class="up-when">{ui.renewal_badge(s["days_until_renewal"])}</div></div>'
            '</div>',
            unsafe_allow_html=True,
        )


def _top_chart(data: dict, base: str) -> None:
    top = list(reversed(data["top"]))
    fig = go.Figure(
        go.Bar(
            y=[t["name"] for t in top],
            x=[t["monthly_cost"] for t in top],
            orientation="h",
            marker=dict(color=[t["category_color"] or "#94a3b8" for t in top], line=dict(width=0)),
            text=[f"{t['monthly_cost']:,.0f}" for t in top],
            textposition="outside",
            textfont=dict(color=ui.INK, size=12),
            hovertemplate="<b>%{y}</b><br>" + base + " %{x:,.0f} / month<extra></extra>",
        )
    )
    peak = max((t["monthly_cost"] for t in top), default=0)
    fig.update_xaxes(showgrid=True, gridcolor=ui.GRID, zeroline=False, tickfont=dict(color=ui.MUTED),
                     range=[0, peak * 1.2 if peak else 1])
    fig.update_yaxes(showgrid=False, tickfont=dict(color=ui.INK, size=12))
    fig.update_layout(bargap=0.35)
    ui.show_chart(ui.style_figure(fig, 290))


def _cycle_chart(data: dict, base: str) -> None:
    order = ["weekly", "monthly", "quarterly", "yearly"]
    cycles = sorted(data["by_cycle"], key=lambda c: order.index(c["cycle"]))
    palette = {"weekly": ui.CYAN, "monthly": ui.INDIGO, "quarterly": ui.VIOLET, "yearly": ui.GREEN}
    fig = go.Figure(
        go.Bar(
            x=[ui.CYCLE_LABEL[c["cycle"]] for c in cycles],
            y=[c["monthly_cost"] for c in cycles],
            marker=dict(color=[palette[c["cycle"]] for c in cycles], line=dict(width=0)),
            text=[f"{c['count']} plan{'s' if c['count'] != 1 else ''}" for c in cycles],
            textposition="outside",
            textfont=dict(color=ui.INK, size=12),
            hovertemplate="<b>%{x}</b><br>" + base + " %{y:,.0f} / month<extra></extra>",
        )
    )
    peak = max((c["monthly_cost"] for c in cycles), default=0)
    fig.update_xaxes(showgrid=False, tickfont=dict(color=ui.MUTED), linecolor=ui.GRID)
    fig.update_yaxes(showgrid=True, gridcolor=ui.GRID, zeroline=False, tickfont=dict(color=ui.MUTED),
                     range=[0, peak * 1.25 if peak else 1])
    fig.update_layout(bargap=0.45)
    ui.show_chart(ui.style_figure(fig, 290))
