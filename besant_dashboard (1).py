"""
Besant Courses Analytics Dashboard
====================================
Run:  python besant_dashboard.py
Open: http://127.0.0.1:8050

Requirements:
    pip install dash plotly pandas openpyxl
"""

import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
from pathlib import Path
import threading
import webbrowser

# ── Load & Clean Data ──────────────────────────────────────────────────────────
DATA_PATH = Path(__file__).resolve().parent / "besant_courses_1000_updated.xlsx"
if not DATA_PATH.exists():
    raise FileNotFoundError(
        f"Could not find the data file at {DATA_PATH}.\n"
        "Make sure besant_courses_1000_updated.xlsx is located in the same folder as this script."
    )

_raw = pd.read_excel(DATA_PATH, sheet_name="Course_Data", header=None)
_raw.columns = _raw.iloc[0]
df = _raw[1:].reset_index(drop=True)

for col in ["fee", "duration_hrs", "full_completion", "partial_completion"]:
    df[col] = pd.to_numeric(df[col], errors="coerce")

df["total_completion"] = df["full_completion"] + df["partial_completion"]
df["completion_rate"]  = (df["full_completion"] / (df["full_completion"] + df["partial_completion"])
                          .replace(0, pd.NA) * 100).round(1)

# ── Design Tokens ──────────────────────────────────────────────────────────────
C = {
    "bg":      "#0a0f1e",
    "card":    "#111827",
    "border":  "#1f2d3d",
    "a1":      "#7c3aed",   # violet
    "a2":      "#06b6d4",   # cyan
    "a3":      "#f59e0b",   # amber
    "a4":      "#10b981",   # emerald
    "a5":      "#f43f5e",   # rose
    "text":    "#f9fafb",
    "sub":     "#9ca3af",
}

CAT_COLORS  = [C["a1"], C["a2"], C["a3"], C["a4"], C["a5"], "#a855f7", "#0ea5e9", "#84cc16", "#fb923c", "#e879f9", "#38bdf8"]
MODE_COLORS = [C["a2"], C["a1"], C["a3"]]

CHART_BASE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor ="rgba(0,0,0,0)",
    font_color   = C["text"],
    font_family  = "'Inter','Segoe UI',sans-serif",
    margin       = dict(t=46, b=32, l=36, r=20),
    legend       = dict(bgcolor="rgba(0,0,0,0)", font_color=C["sub"], orientation="h", y=-0.18),
)

CATEGORIES = sorted(df["category"].unique().tolist())
MODES      = sorted(df["mode"].unique().tolist())
COURSES    = sorted(df["course_name"].unique().tolist())

# ── KPI card helper ────────────────────────────────────────────────────────────
def kpi(title, value, color, icon):
    return html.Div([
        html.Div(icon, style={"fontSize": "28px", "marginBottom": "6px"}),
        html.P(title, style={"margin": "0 0 4px", "color": C["sub"], "fontSize": "12px", "fontWeight": "600", "textTransform": "uppercase", "letterSpacing": "0.06em"}),
        html.H2(str(value), style={"margin": 0, "color": color, "fontSize": "30px", "fontWeight": "800"}),
    ], style={
        "background": C["card"],
        "border": f"1px solid {C['border']}",
        "borderLeft": f"4px solid {color}",
        "borderRadius": "14px",
        "padding": "18px 22px",
        "flex": "1",
        "minWidth": "155px",
    })

# ── Dropdown style ─────────────────────────────────────────────────────────────
DD = {"background": C["card"], "color": "#111", "borderRadius": "8px"}

# ── App Layout ─────────────────────────────────────────────────────────────────
app = Dash(__name__)
app.title = "Besant Courses Dashboard"

app.layout = html.Div([

    # Header
    html.Div([
        html.Div([
            html.H1("📚 Besant Courses Analytics", style={"margin": 0, "fontSize": "24px", "fontWeight": "800", "color": C["text"]}),
            html.P("1,000 Enrolments · 50 Courses · 11 Categories", style={"margin": "4px 0 0", "color": C["sub"], "fontSize": "13px"}),
        ]),
        html.Div("LIVE DASHBOARD", style={
            "background": C["a1"], "color": "#fff",
            "padding": "4px 14px", "borderRadius": "20px",
            "fontSize": "11px", "fontWeight": "700", "letterSpacing": "0.08em",
            "alignSelf": "center",
        }),
    ], style={"display": "flex", "justifyContent": "space-between", "alignItems": "center",
               "padding": "24px 32px 18px", "borderBottom": f"1px solid {C['border']}"}),

    # Filters
    html.Div([
        html.Div([
            html.Label("Category", style={"color": C["sub"], "fontSize": "12px", "marginBottom": "5px", "display": "block", "fontWeight": "600"}),
            dcc.Dropdown(
                id="cat-filter",
                options=[{"label": "All Categories", "value": "All"}] + [{"label": c, "value": c} for c in CATEGORIES],
                value="All", clearable=False, style=DD,
            ),
        ], style={"flex": "2", "minWidth": "180px"}),

        html.Div([
            html.Label("Mode", style={"color": C["sub"], "fontSize": "12px", "marginBottom": "5px", "display": "block", "fontWeight": "600"}),
            dcc.Dropdown(
                id="mode-filter",
                options=[{"label": "All Modes", "value": "All"}] + [{"label": m, "value": m} for m in MODES],
                value="All", clearable=False, style=DD,
            ),
        ], style={"flex": "1", "minWidth": "150px"}),

        html.Div([
            html.Label("Fee Range (₹)", style={"color": C["sub"], "fontSize": "12px", "marginBottom": "5px", "display": "block", "fontWeight": "600"}),
            dcc.RangeSlider(
                id="fee-slider",
                min=int(df["fee"].min()), max=int(df["fee"].max()),
                value=[int(df["fee"].min()), int(df["fee"].max())],
                step=500,
                marks={v: {"label": f"₹{v//1000}k", "style": {"color": C["sub"], "fontSize": "10px"}}
                       for v in [9500, 15000, 20000, 25000, 30000, 35500]},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], style={"flex": "3", "minWidth": "240px"}),

        html.Div([
            html.Label("Duration (hrs)", style={"color": C["sub"], "fontSize": "12px", "marginBottom": "5px", "display": "block", "fontWeight": "600"}),
            dcc.RangeSlider(
                id="dur-slider",
                min=int(df["duration_hrs"].min()), max=int(df["duration_hrs"].max()),
                value=[int(df["duration_hrs"].min()), int(df["duration_hrs"].max())],
                step=5,
                marks={v: {"label": f"{v}h", "style": {"color": C["sub"], "fontSize": "10px"}}
                       for v in [25, 40, 55, 70, 90]},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], style={"flex": "2", "minWidth": "200px"}),
    ], style={
        "display": "flex", "gap": "24px", "alignItems": "flex-end",
        "padding": "18px 32px",
        "background": "#0d1526",
        "borderBottom": f"1px solid {C['border']}",
        "flexWrap": "wrap",
    }),

    # KPIs
    html.Div(id="kpi-row", style={"display": "flex", "gap": "14px", "padding": "24px 32px 10px", "flexWrap": "wrap"}),

    # Row 1
    html.Div([
        dcc.Graph(id="cat-bar",     style={"flex": "2", "minWidth": "320px"}),
        dcc.Graph(id="mode-donut",  style={"flex": "1", "minWidth": "240px"}),
        dcc.Graph(id="fee-hist",    style={"flex": "1", "minWidth": "240px"}),
    ], style={"display": "flex", "gap": "14px", "padding": "10px 32px", "flexWrap": "wrap"}),

    # Row 2
    html.Div([
        dcc.Graph(id="completion-bar",  style={"flex": "2", "minWidth": "320px"}),
        dcc.Graph(id="scatter-fee-dur", style={"flex": "2", "minWidth": "320px"}),
    ], style={"display": "flex", "gap": "14px", "padding": "10px 32px", "flexWrap": "wrap"}),

    # Row 3
    html.Div([
        dcc.Graph(id="top-courses",    style={"flex": "2", "minWidth": "320px"}),
        dcc.Graph(id="mode-cat-heat",  style={"flex": "2", "minWidth": "320px"}),
    ], style={"display": "flex", "gap": "14px", "padding": "10px 32px 32px", "flexWrap": "wrap"}),

], style={"background": C["bg"], "minHeight": "100vh", "fontFamily": "'Inter','Segoe UI',sans-serif"})


# ── Callback ───────────────────────────────────────────────────────────────────
@app.callback(
    Output("kpi-row",        "children"),
    Output("cat-bar",        "figure"),
    Output("mode-donut",     "figure"),
    Output("fee-hist",       "figure"),
    Output("completion-bar", "figure"),
    Output("scatter-fee-dur","figure"),
    Output("top-courses",    "figure"),
    Output("mode-cat-heat",  "figure"),
    Input("cat-filter",  "value"),
    Input("mode-filter", "value"),
    Input("fee-slider",  "value"),
    Input("dur-slider",  "value"),
)
def update(cat, mode, fee_range, dur_range):
    d = df.copy()
    if cat  != "All": d = d[d["category"] == cat]
    if mode != "All": d = d[d["mode"]     == mode]
    d = d[(d["fee"]          >= fee_range[0]) & (d["fee"]          <= fee_range[1])]
    d = d[(d["duration_hrs"] >= dur_range[0]) & (d["duration_hrs"] <= dur_range[1])]

    total      = len(d)
    avg_fee    = f"₹{int(d['fee'].mean()):,}"       if total else "₹0"
    avg_full   = f"{d['full_completion'].mean():.1f}%" if total else "0%"
    avg_dur    = f"{d['duration_hrs'].mean():.1f} hrs" if total else "0"
    top_cat    = d["category"].value_counts().idxmax() if total else "-"

    kpis = [
        kpi("Total Enrolments", f"{total:,}",  C["a1"], "🎓"),
        kpi("Avg Course Fee",    avg_fee,       C["a2"], "💰"),
        kpi("Avg Full Completion", avg_full,    C["a4"], "✅"),
        kpi("Avg Duration",      avg_dur,       C["a3"], "⏱️"),
        kpi("Top Category",      top_cat,       C["a5"], "🏆"),
    ]

    # ── 1. Enrolments by Category (horizontal bar) ──
    cat_cnt = d["category"].value_counts().reset_index()
    cat_cnt.columns = ["category", "count"]
    fig_cat = px.bar(cat_cnt.sort_values("count"), x="count", y="category",
                     orientation="h", title="Enrolments by Category",
                     color="count", color_continuous_scale=["#7c3aed","#06b6d4"],
                     labels={"count": "Enrolments", "category": ""})
    fig_cat.update_layout(**CHART_BASE, coloraxis_showscale=False)
    fig_cat.update_xaxes(gridcolor=C["border"])
    fig_cat.update_yaxes(gridcolor="rgba(0,0,0,0)")

    # ── 2. Mode Donut ──
    mode_cnt = d["mode"].value_counts().reset_index()
    fig_mode = px.pie(mode_cnt, names="mode", values="count", title="Delivery Mode",
                      color_discrete_sequence=MODE_COLORS, hole=0.50)
    fig_mode.update_layout(**CHART_BASE)
    fig_mode.update_traces(textfont_color=C["text"])

    # ── 3. Fee Distribution ──
    fig_fee = px.histogram(d, x="fee", nbins=25, title="Fee Distribution",
                           color_discrete_sequence=[C["a3"]],
                           labels={"fee": "Fee (₹)", "count": "Courses"})
    fig_fee.update_layout(**CHART_BASE)
    fig_fee.update_traces(marker_line_color=C["bg"], marker_line_width=0.6)
    fig_fee.update_xaxes(gridcolor=C["border"])
    fig_fee.update_yaxes(gridcolor=C["border"])

    # ── 4. Avg Full vs Partial Completion by Category ──
    comp = d.groupby("category")[["full_completion","partial_completion"]].mean().round(1).reset_index()
    comp = comp.sort_values("full_completion", ascending=False)
    fig_comp = go.Figure()
    fig_comp.add_bar(name="Full Completion",    x=comp["category"], y=comp["full_completion"],
                     marker_color=C["a4"])
    fig_comp.add_bar(name="Partial Completion", x=comp["category"], y=comp["partial_completion"],
                     marker_color=C["a3"])
    fig_comp.update_layout(barmode="group", title="Avg Completion by Category", **CHART_BASE)
    fig_comp.update_xaxes(gridcolor=C["border"], tickangle=-30)
    fig_comp.update_yaxes(gridcolor=C["border"], title="Avg Count")

    # ── 5. Scatter: Fee vs Duration, colored by mode ──
    fig_scat = px.scatter(d, x="duration_hrs", y="fee", color="mode",
                          size="full_completion", hover_name="course_name",
                          color_discrete_sequence=MODE_COLORS,
                          title="Fee vs Duration (bubble = full completions)",
                          labels={"duration_hrs": "Duration (hrs)", "fee": "Fee (₹)", "mode": "Mode"})
    fig_scat.update_layout(**CHART_BASE)
    fig_scat.update_xaxes(gridcolor=C["border"])
    fig_scat.update_yaxes(gridcolor=C["border"])

    # ── 6. Top 10 Courses by Total Enrolments ──
    top = d.groupby("course_name").size().reset_index(name="count").nlargest(10, "count").sort_values("count")
    fig_top = px.bar(top, x="count", y="course_name", orientation="h",
                     title="Top 10 Courses by Enrolments",
                     color="count", color_continuous_scale=["#7c3aed","#f43f5e"],
                     labels={"count": "Enrolments", "course_name": ""})
    fig_top.update_layout(**CHART_BASE, coloraxis_showscale=False)
    fig_top.update_xaxes(gridcolor=C["border"])
    fig_top.update_yaxes(gridcolor="rgba(0,0,0,0)")

    # ── 7. Heatmap: Avg Full Completion — Mode × Category ──
    pivot = d.groupby(["mode","category"])["full_completion"].mean().round(1).reset_index()
    pt = pivot.pivot(index="mode", columns="category", values="full_completion")
    fig_heat = go.Figure(go.Heatmap(
        z=pt.values, x=pt.columns.tolist(), y=pt.index.tolist(),
        colorscale="Viridis",
        text=pt.values.round(1), texttemplate="%{text}",
        textfont={"size": 10, "color": "white"},
        colorbar=dict(title="Avg Full<br>Completion", tickfont=dict(color=C["sub"])),
    ))
    fig_heat.update_layout(title="Avg Full Completion — Mode × Category", **CHART_BASE)
    fig_heat.update_xaxes(tickangle=-30, gridcolor=C["border"])
    fig_heat.update_yaxes(gridcolor=C["border"])

    return kpis, fig_cat, fig_mode, fig_fee, fig_comp, fig_scat, fig_top, fig_heat


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    url = "http://127.0.0.1:8050"
    threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    print(f"\n✅ Besant Dashboard → {url}\n")
    app.run(debug=True)
