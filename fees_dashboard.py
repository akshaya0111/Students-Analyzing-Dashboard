"""
╔══════════════════════════════════════════════════════╗
║       STUDENT FEES ANALYTICS DASHBOARD               ║
║       Run:  python fees_dashboard.py                 ║
║       Open: http://127.0.0.1:8050                    ║
╚══════════════════════════════════════════════════════╝

Requirements:
    pip install dash dash-bootstrap-components plotly pandas openpyxl

Place this file in the SAME folder as:
    student_fees_only.xlsx
"""

import pandas as pd
import dash
from dash import dcc, html, Input, Output, dash_table
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import warnings
warnings.filterwarnings("ignore")

# ──────────────────────────────────────────────────────────
# 1.  LOAD & PREPARE DATA
# ──────────────────────────────────────────────────────────
import pandas as pd

FILE = r"C:\Users\acer\Downloads\student_fees_only.xlsx"

df = pd.read_excel(FILE, sheet_name="Fees Dataset")

# ── KPIs ──────────────────────────────────────────────────
total_students   = len(df)
total_revenue    = df["Total Paid"].sum()
total_balance    = df["Balance Due"].sum()
total_fees_billed= df["Total Fees"].sum()
collection_rate  = round(total_revenue / total_fees_billed * 100, 1)
avg_total_fee    = round(df["Total Fees"].mean(), 0)
avg_paid         = round(df["Total Paid"].mean(), 0)
avg_balance      = round(df["Balance Due"].mean(), 0)

status_counts    = df["Fee Status"].value_counts()
full_pct         = round(status_counts.get("Full Payment", 0)    / total_students * 100, 1)
partial_pct      = round(status_counts.get("Partial Payment", 0) / total_students * 100, 1)
enrolled_pct     = round(status_counts.get("Enrolled", 0)        / total_students * 100, 1)

# ── Fee-tier segmentation ─────────────────────────────────
df["Fee Tier"] = pd.cut(
    df["Total Fees"],
    bins=[0, 45000, 50000, 75000],
    labels=["₹45K", "₹50K", "₹75K"]
)

# ── Payment Progress bucket ───────────────────────────────
df["Pay%"] = (df["Total Paid"] / df["Total Fees"] * 100).round(1)
df["Progress Band"] = pd.cut(
    df["Pay%"],
    bins=[-1, 25, 50, 75, 100],
    labels=["0–25%", "26–50%", "51–75%", "76–100%"]
)

# ──────────────────────────────────────────────────────────
# 2.  THEME  (deep teal / gold editorial palette)
# ─────────────────────────────────────────────────────────
C = {
    "bg":      "#071422",
    "surface": "#0f2633",
    "card":    "#112b3b",
    "border":  "#1f4252",
    "text":    "#e8f4f8",
    "muted":   "#9fb8c4",
    "teal":    "#2ac4b3",
    "gold":    "#f8c56d",
    "rose":    "#f2718b",
    "sky":     "#72c8f8",
    "purple":  "#9b79ff",
}

def AX(**kw):
    return dict(showgrid=True, gridcolor=C["border"], gridwidth=1,
                zeroline=False, tickfont=dict(color=C["muted"], size=11),
                title_font=dict(color=C["muted"]), **kw)

# ← ADD THIS RIGHT HERE (line ~73)
def G(fig, h=360):
    return dcc.Graph(figure=fig, config={"displayModeBar": False},
                     style={"height": f"{h}px"})
CHART_COLORS = [C["teal"], C["gold"], C["rose"], C["sky"], C["purple"]]

CARD_STYLE = {
    "background":   C["card"],
    "border":       f"1px solid {C['border']}",
    "borderRadius": "14px",
    "boxShadow":    "0 4px 24px rgba(0,0,0,0.4)",
    "padding":      "20px",
    "marginBottom": "20px",
}

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font=dict(family="'IBM Plex Mono', monospace", color=C["text"], size=12),
    margin=dict(t=48, b=32, l=16, r=16),
    legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color=C["muted"])),
)

def axis_style():
    return dict(
        showgrid=True,
        gridcolor=C["border"],
        gridwidth=1,
        zeroline=False,
        tickfont=dict(color=C["muted"], size=11),
        title_font=dict(color=C["muted"]),
    )

# ──────────────────────────────────────────────────────────
# 3.  CHART BUILDERS
# ──────────────────────────────────────────────────────────

def fig_status_donut():
    sc = df["Fee Status"].value_counts().reset_index()
    sc.columns = ["Status", "Count"]
    fig = px.pie(
        sc, names="Status", values="Count",
        hole=0.62,
        color_discrete_sequence=CHART_COLORS,
        title="Fee Status Breakdown"
    )
    fig.update_traces(textfont_size=12, textfont_color=C["text"],
                      marker=dict(line=dict(color=C["bg"], width=2)))
    fig.update_layout(**CHART_LAYOUT)
    return fig


def fig_revenue_waterfall():
    categories = ["Total Billed", "Enroll Fee", "Partial Payments",
                  "Full Payments", "Total Collected", "Balance Due"]
    values = [
        total_fees_billed / 1e6,
        df["Enroll Fee"].sum()       / 1e6,
        df["Partial Payment"].sum()  / 1e6,
        df["Full Payment"].sum()     / 1e6,
        total_revenue                / 1e6,
        total_balance                / 1e6,
    ]
    measure = ["absolute", "relative", "relative", "relative", "total", "total"]
    colors  = [C["sky"], C["teal"], C["gold"], C["purple"], C["teal"], C["rose"]]
    fig = go.Figure(go.Waterfall(
        orientation="v",
        measure=measure,
        x=categories,
        y=values,
        connector=dict(line=dict(color=C["border"], width=1)),
        decreasing=dict(marker=dict(color=C["rose"])),
        increasing=dict(marker=dict(color=C["teal"])),
        totals=dict(marker=dict(color=C["gold"])),
        text=[f"₹{v:.2f}M" for v in values],
        textposition="outside",
        textfont=dict(color=C["text"], size=11),
    ))
    fig.update_layout(title="Revenue Waterfall (₹ Millions)",
                      yaxis=dict(title="Amount (₹M)", **axis_style()),
                      xaxis=dict(**axis_style()),
                      **CHART_LAYOUT)
    return fig


def fig_total_fees_dist():
    fig = px.histogram(
        df, x="Total Fees", nbins=3,
        color="Fee Status",
        color_discrete_sequence=CHART_COLORS,
        barmode="overlay",
        title="Total Fees Distribution by Status",
        labels={"Total Fees": "Total Fees (₹)", "count": "Students"}
    )
    fig.update_layout(xaxis=axis_style(), yaxis=axis_style(), **CHART_LAYOUT)
    return fig


def fig_payment_progress():
    pb = df["Progress Band"].value_counts().reindex(
        ["0–25%", "26–50%", "51–75%", "76–100%"]).reset_index()
    pb.columns = ["Band", "Count"]
    fig = px.bar(
        pb, x="Band", y="Count",
        color="Band",
        color_discrete_sequence=CHART_COLORS,
        title="Students by Payment Progress",
        text="Count",
        labels={"Band": "Payment Progress", "Count": "# Students"}
    )
    fig.update_traces(textposition="outside", textfont=dict(color=C["text"]))
    fig.update_layout(showlegend=False,
                      xaxis=axis_style(), yaxis=axis_style(),
                      **CHART_LAYOUT)
    return fig


def fig_balance_by_status():
    bd = df.groupby("Fee Status")[["Total Paid", "Balance Due"]].mean().reset_index()
    fig = go.Figure()
    fig.add_trace(go.Bar(name="Avg Paid",    x=bd["Fee Status"], y=bd["Total Paid"],
                         marker_color=C["teal"],   text=bd["Total Paid"].map(lambda v: f"₹{v:,.0f}"),
                         textposition="auto", textfont=dict(color=C["text"])))
    fig.add_trace(go.Bar(name="Avg Balance", x=bd["Fee Status"], y=bd["Balance Due"],
                         marker_color=C["rose"],   text=bd["Balance Due"].map(lambda v: f"₹{v:,.0f}"),
                         textposition="auto", textfont=dict(color=C["text"])))
    fig.update_layout(barmode="group", title="Avg Paid vs Balance by Fee Status",
                      xaxis=dict(title="", **axis_style()),
                      yaxis=dict(title="Amount (₹)", **axis_style()),
                      **CHART_LAYOUT)
    return fig


def fig_fee_tier_status():
    ft = df.groupby(["Fee Tier", "Fee Status"]).size().reset_index(name="Count")
    fig = px.bar(
        ft, x="Fee Tier", y="Count", color="Fee Status",
        barmode="stack",
        color_discrete_sequence=CHART_COLORS,
        title="Fee Tier vs Status",
        labels={"Fee Tier": "Fee Tier", "Count": "Students"},
        text="Count"
    )
    fig.update_traces(textposition="inside", textfont=dict(color=C["bg"], size=10))
    fig.update_layout(xaxis=axis_style(), yaxis=axis_style(),
                      legend_title="Status", **CHART_LAYOUT)
    return fig


def fig_enroll_fee_box():
    fig = px.box(
        df, x="Fee Status", y="Enroll Fee",
        color="Fee Status",
        color_discrete_sequence=CHART_COLORS,
        title="Enroll Fee Spread by Status",
        points="outliers"
    )
    fig.update_layout(showlegend=False,
                      xaxis=dict(title="", **axis_style()),
                      yaxis=dict(title="Enroll Fee (₹)", **axis_style()),
                      **CHART_LAYOUT)
    return fig


def fig_scatter_paid_vs_balance():
    sample = df.sample(min(600, len(df)), random_state=42)
    fig = px.scatter(
        sample, x="Total Paid", y="Balance Due",
        color="Fee Status",
        color_discrete_sequence=CHART_COLORS,
        opacity=0.7,
        size_max=8,
        title="Total Paid vs Balance Due",
        labels={"Total Paid": "Total Paid (₹)", "Balance Due": "Balance Due (₹)"},
        hover_data=["Student Id", "Fee Status"]
    )
    fig.update_layout(xaxis=axis_style(), yaxis=axis_style(), **CHART_LAYOUT)
    return fig


# ──────────────────────────────────────────────────────────
# 4.  KPI CARD BUILDER
# ──────────────────────────────────────────────────────────
def kpi(label, value, sub, accent):
    return html.Div([
        html.P(label, style={"color": C["muted"], "fontSize": "0.72rem",
                              "fontWeight": "700", "letterSpacing": "0.12em",
                              "textTransform": "uppercase", "marginBottom": "6px"}),
        html.H3(value, style={"color": accent, "fontSize": "1.7rem",
                               "fontWeight": "800", "fontFamily": "'IBM Plex Mono', monospace",
                               "margin": "0 0 4px 0"}),
        html.P(sub, style={"color": C["muted"], "fontSize": "0.76rem", "margin": 0}),
    ], style={**CARD_STYLE, "borderTop": f"3px solid {accent}"})


# ──────────────────────────────────────────────────────────
# 5.  APP LAYOUT
# ──────────────────────────────────────────────────────────
app = dash.Dash(
    __name__,
    external_stylesheets=[
        dbc.themes.BOOTSTRAP,
        "https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600;700&family=Syne:wght@700;800&display=swap"
    ]
)
app.title = "Student Fees Dashboard"

app.layout = html.Div(style={"background": C["bg"], "minHeight": "100vh",
                               "fontFamily": "'IBM Plex Mono', monospace",
                               "padding": "0 0 60px 0"}, children=[

    # ── TOP HEADER ────────────────────────────────────────
    html.Div([
        html.Div([
            html.Span("💳", style={"fontSize": "2rem", "marginRight": "14px"}),
            html.Div([
                html.H1("Student Fees Dashboard",
                        style={"fontFamily": "'Syne', sans-serif", "color": C["text"],
                               "fontSize": "1.9rem", "fontWeight": "800", "margin": 0}),
                html.P("Real-time fee collection analytics · 5,000 students",
                       style={"color": C["muted"], "fontSize": "0.82rem", "margin": 0}),
            ])
        ], style={"display": "flex", "alignItems": "center"}),
        html.Div([
            html.Span("● LIVE", style={"color": C["teal"], "fontSize": "0.75rem",
                                        "fontWeight": "700", "letterSpacing": "0.1em"})
        ])
    ], style={
        "background": C["surface"],
        "borderBottom": f"1px solid {C['border']}",
        "padding": "22px 40px",
        "display": "flex",
        "justifyContent": "space-between",
        "alignItems": "center",
        "position": "sticky", "top": 0, "zIndex": 999
    }),

    # ── BODY ─────────────────────────────────────────────
    html.Div(style={"maxWidth": "1400px", "margin": "0 auto", "padding": "30px 24px"}, children=[

        # ── KPI ROW ───────────────────────────────────────
        dbc.Row([
            dbc.Col(kpi("Total Students",     f"{total_students:,}",
                        "enrolled in system",                    C["sky"]),    md=3),
            dbc.Col(kpi("Total Collected",    f"₹{total_revenue/1e6:.2f}M",
                        f"Collection rate {collection_rate}%",  C["teal"]),   md=3),
            dbc.Col(kpi("Outstanding Balance",f"₹{total_balance/1e6:.2f}M",
                        f"Avg ₹{avg_balance:,.0f}/student",      C["rose"]),   md=3),
            dbc.Col(kpi("Fully Paid",         f"{full_pct}%",
                        f"{status_counts.get('Full Payment',0):,} students",  C["gold"]), md=3),
        ], className="g-3 mb-2"),

        dbc.Row([
            dbc.Col(kpi("Avg Total Fee",   f"₹{avg_total_fee:,.0f}",  "per student",         C["purple"]), md=3),
            dbc.Col(kpi("Avg Paid",        f"₹{avg_paid:,.0f}",       "per student",         C["teal"]),   md=3),
            dbc.Col(kpi("Partial Payers",  f"{partial_pct}%",
                        f"{status_counts.get('Partial Payment',0):,} students", C["gold"]), md=3),
            dbc.Col(kpi("Just Enrolled",   f"{enrolled_pct}%",
                        f"{status_counts.get('Enrolled',0):,} students",        C["rose"]), md=3),
        ], className="g-3 mb-4"),

        # ── SECTION LABEL ─────────────────────────────────
        html.P("▸  PAYMENT OVERVIEW", style={"color": C["teal"], "fontSize": "0.72rem",
               "fontWeight": "700", "letterSpacing": "0.15em", "marginBottom": "12px"}),

        # ── ROW 1 CHARTS ──────────────────────────────────
        dbc.Row([
            dbc.Col(html.Div(G(fig_status_donut()), style=CARD_STYLE), md=4),
            dbc.Col(html.Div(G(fig_revenue_waterfall()), style=CARD_STYLE), md=8),
        ], className="g-3 mb-2"),

        # ── ROW 2 CHARTS ──────────────────────────────────
        dbc.Row([
            dbc.Col(html.Div(G(fig_payment_progress()), style=CARD_STYLE), md=4),
            dbc.Col(html.Div(G(fig_balance_by_status()), style=CARD_STYLE), md=8),
        ], className="g-3 mb-2"),

        html.P("▸  DEEP DIVE", style={"color": C["teal"], "fontSize": "0.72rem",
               "fontWeight": "700", "letterSpacing": "0.15em", "marginBottom": "12px",
               "marginTop": "8px"}),

        # ── ROW 3 CHARTS ──────────────────────────────────
        dbc.Row([
            dbc.Col(html.Div(G(fig_fee_tier_status()),   style=CARD_STYLE), md=4),
            dbc.Col(html.Div(G(fig_enroll_fee_box()),    style=CARD_STYLE), md=4),
            dbc.Col(html.Div(G(fig_scatter_paid_vs_balance()), style=CARD_STYLE), md=4),
        ], className="g-3 mb-2"),

        # ── ROW 4 ─────────────────────────────────────────
        dbc.Row([
            dbc.Col(html.Div(G(fig_total_fees_dist()), style=CARD_STYLE), md=12),
        ], className="g-3 mb-4"),

        # ── INTERACTIVE FILTER + TABLE ────────────────────
        html.P("▸  DATA EXPLORER", style={"color": C["teal"], "fontSize": "0.72rem",
               "fontWeight": "700", "letterSpacing": "0.15em", "marginBottom": "12px"}),

        html.Div([
            html.P("Filter by Fee Status:", style={"color": C["muted"], "fontSize": "0.78rem",
                   "marginBottom": "8px", "fontWeight": "600"}),
            dcc.Dropdown(
                id="status-filter",
                options=[{"label": "All", "value": "All"}] +
                        [{"label": s, "value": s} for s in df["Fee Status"].unique()],
                value="All",
                clearable=False,
                style={"background": C["card"], "color": C["text"],
                       "border": f"1px solid {C['border']}", "borderRadius": "8px",
                       "fontFamily": "'IBM Plex Mono', monospace", "width": "280px"},
            ),
        ], style={"marginBottom": "16px"}),

        html.Div(id="table-container"),

        # ── FOOTER ────────────────────────────────────────
        html.Hr(style={"borderColor": C["border"], "marginTop": "40px"}),
        html.P("Student Fees Analytics Dashboard · Besant Technologies · Built with Dash & Plotly",
               style={"color": C["muted"], "fontSize": "0.72rem",
                      "textAlign": "center", "letterSpacing": "0.08em"}),
    ])
])


# ──────────────────────────────────────────────────────────
# 6.  CALLBACKS
# ──────────────────────────────────────────────────────────
@app.callback(Output("table-container", "children"), Input("status-filter", "value"))
def update_table(status):
    filtered = df if status == "All" else df[df["Fee Status"] == status]
    show_cols = ["Student Id", "Fee Status", "Total Fees",
                 "Enroll Fee", "Partial Payment", "Full Payment",
                 "Total Paid", "Balance Due"]
    sample = filtered[show_cols].head(100)

    tbl = dash_table.DataTable(
        data=sample.to_dict("records"),
        columns=[{"name": c, "id": c, "type": "numeric" if c != "Fee Status" and c != "Student Id"
                  else "text",
                  "format": {"specifier": ","} if c not in ("Fee Status", "Student Id") else {}}
                 for c in show_cols],
        page_size=15,
        sort_action="native",
        filter_action="native",
        style_table={"overflowX": "auto", "borderRadius": "10px",
                     "border": f"1px solid {C['border']}"},
        style_header={"backgroundColor": C["surface"], "color": C["teal"],
                       "fontWeight": "700", "fontSize": "0.75rem",
                       "letterSpacing": "0.08em", "textTransform": "uppercase",
                       "border": f"1px solid {C['border']}"},
        style_cell={"backgroundColor": C["card"], "color": C["text"],
                     "fontSize": "0.8rem", "fontFamily": "'IBM Plex Mono', monospace",
                     "padding": "10px 14px",
                     "border": f"1px solid {C['border']}",
                     "textAlign": "right"},
        style_cell_conditional=[
            
            {"if": {"column_id": "Fee Status"}, "textAlign": "center"},
            {"if": {"column_id": "Student Id"}, "textAlign": "center"},
        ],
        style_data_conditional=[
            {"if": {"filter_query": '{Fee Status} = "Full Payment"'},
             "color": C["teal"], "fontWeight": "600"},
            {"if": {"filter_query": '{Fee Status} = "Partial Payment"'},
             "color": C["gold"]},
            {"if": {"filter_query": '{Fee Status} = "Enrolled"'},
             "color": C["rose"]},
            {"if": {"row_index": "odd"}, "backgroundColor": C["surface"]},
        ],
    )

    summary = html.Div([
        html.Span(f"Showing {len(sample)} of {len(filtered):,} records",
                  style={"color": C["muted"], "fontSize": "0.75rem",
                         "fontFamily": "'IBM Plex Mono', monospace"}),
    ], style={"marginBottom": "10px"})

    return html.Div([summary, tbl], style=CARD_STYLE)


# ──────────────────────────────────────────────────────────
# 7.  RUN
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n🚀 Starting Fees Dashboard → http://127.0.0.1:8050\n")
    app.run(debug=True, port=8050)
