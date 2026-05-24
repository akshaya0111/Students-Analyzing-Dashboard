"""
Student Placement Analytics Dashboard
=======================================
Run:  python placement_dashboard.py
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
import os, glob
import importlib.util

# ── Load & Prepare Data ────────────────────────────────────────────────────────
def _find_data_file():
    # Look in the script directory first (so running from anywhere still works)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = glob.glob(os.path.join(script_dir, "student_placement_only*"))
    if candidates:
        return candidates[0]

    # Then look in the current working directory
    candidates = glob.glob("student_placement_only*")
    if candidates:
        return candidates[0]

    # Try a few likely filename variations (both script dir and cwd)
    names = [
        "student_placement_only__version_2__xlsb.xlsx",
        "student_placement_only__version_2_.xlsx",
        "student_placement_only__version_2.xlsb",
    ]
    for base in (script_dir, os.getcwd()):
        for n in names:
            p = os.path.join(base, n)
            if os.path.exists(p):
                return p

    raise FileNotFoundError(
        "Could not find the student placement Excel file in the current directory."
        " Place the file next to this script or update the path in the code."
    )

_data_file = _find_data_file()
print(f"Using data file: {_data_file}")

# If the file is an .xlsb, require pyxlsb and pass engine explicitly
_engine = None
if _data_file.lower().endswith(".xlsb"):
    if importlib.util.find_spec("pyxlsb") is None:
        raise ImportError(
            "Reading .xlsb files requires 'pyxlsb'. Install it with: pip install pyxlsb"
        )
    _engine = "pyxlsb"

_raw = pd.read_excel(_data_file, sheet_name="Placement Dataset", header=None, engine=_engine)
_raw.columns = _raw.iloc[0]
df = _raw[1:].reset_index(drop=True)

df["Ctc Lpa"]        = pd.to_numeric(df["Ctc Lpa"], errors="coerce")
df["Placement Date"] = pd.to_datetime(df["Placement Date"], errors="coerce")
df["Year"]           = df["Placement Date"].dt.year.astype("Int64")
df["Month"]          = df["Placement Date"].dt.to_period("M").astype(str)
df["City"]           = df["Branch"].str.split(" - ").str[0]   # Chennai / Bangalore / Online

BRANCHES  = sorted(df["Branch"].dropna().unique())
STATUSES  = sorted(df["Placement Status"].dropna().unique())
COMPANIES = sorted(df["Company Name"].dropna().unique())
YEARS     = sorted(df["Year"].dropna().unique().tolist())

# ── Design ─────────────────────────────────────────────────────────────────────
C = {
    "bg":    "#080d1a",
    "card":  "#0f1729",
    "b":     "#1a2740",
    "a1":    "#3b82f6",   # blue
    "a2":    "#10b981",   # emerald
    "a3":    "#f59e0b",   # amber
    "a4":    "#f43f5e",   # rose
    "a5":    "#a78bfa",   # violet
    "text":  "#f1f5f9",
    "sub":   "#94a3b8",
}

STATUS_COLORS   = {"Placed": C["a2"], "Not Placed": C["a4"], "In Process": C["a3"]}
CITY_COLORS     = [C["a1"], C["a2"], C["a5"]]

CHART_BASE = dict(
    paper_bgcolor = "rgba(0,0,0,0)",
    plot_bgcolor  = "rgba(0,0,0,0)",
    font_color    = C["text"],
    font_family   = "'Inter','Segoe UI',sans-serif",
    margin        = dict(t=46, b=36, l=36, r=20),
    legend        = dict(bgcolor="rgba(0,0,0,0)", font_color=C["sub"]),
)

DD = {"background": C["card"], "color": "#111", "borderRadius": "8px"}

def card_style(border_color):
    return {
        "background": C["card"],
        "border": f"1px solid {C['b']}",
        "borderTop": f"4px solid {border_color}",
        "borderRadius": "14px",
        "padding": "18px 22px",
        "flex": "1",
        "minWidth": "155px",
    }

def kpi(title, value, color, icon):
    return html.Div([
        html.Div(icon, style={"fontSize": "26px", "marginBottom": "5px"}),
        html.P(title, style={
            "margin": "0 0 3px", "color": C["sub"],
            "fontSize": "11px", "fontWeight": "700",
            "textTransform": "uppercase", "letterSpacing": "0.07em",
        }),
        html.H2(str(value), style={"margin": 0, "color": color, "fontSize": "28px", "fontWeight": "800"}),
    ], style=card_style(color))


# ── App ────────────────────────────────────────────────────────────────────────
app = Dash(__name__)
app.title = "Student Placement Dashboard"

app.layout = html.Div([

    # ── Header ──────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.H1("🎯 Student Placement Dashboard",
                    style={"margin": 0, "fontSize": "23px", "fontWeight": "800", "color": C["text"]}),
            html.P("5,000 Students · 19 Branches · 2022 – 2024",
                   style={"margin": "4px 0 0", "color": C["sub"], "fontSize": "13px"}),
        ]),
        html.Div("LIVE", style={
            "background": C["a2"], "color": "#fff",
            "padding": "4px 14px", "borderRadius": "20px",
            "fontSize": "11px", "fontWeight": "800", "letterSpacing": "0.1em",
            "alignSelf": "center",
        }),
    ], style={
        "display": "flex", "justifyContent": "space-between", "alignItems": "center",
        "padding": "24px 32px 16px", "borderBottom": f"1px solid {C['b']}",
    }),

    # ── Filters ─────────────────────────────────────────────────────────────
    html.Div([
        html.Div([
            html.Label("Placement Status", style={"color": C["sub"], "fontSize": "11px", "fontWeight": "700",
                                                   "marginBottom": "5px", "display": "block", "textTransform": "uppercase"}),
            dcc.Dropdown(
                id="status-filter",
                options=[{"label": "All Statuses", "value": "All"}] +
                        [{"label": s, "value": s} for s in STATUSES],
                value="All", clearable=False, style=DD,
            ),
        ], style={"flex": "1", "minWidth": "160px"}),

        html.Div([
            html.Label("City", style={"color": C["sub"], "fontSize": "11px", "fontWeight": "700",
                                       "marginBottom": "5px", "display": "block", "textTransform": "uppercase"}),
            dcc.Dropdown(
                id="city-filter",
                options=[{"label": "All Cities", "value": "All"},
                         {"label": "Chennai", "value": "Chennai"},
                         {"label": "Bangalore", "value": "Bangalore"},
                         {"label": "Online", "value": "Online"}],
                value="All", clearable=False, style=DD,
            ),
        ], style={"flex": "1", "minWidth": "140px"}),

        html.Div([
            html.Label("Year", style={"color": C["sub"], "fontSize": "11px", "fontWeight": "700",
                                       "marginBottom": "5px", "display": "block", "textTransform": "uppercase"}),
            dcc.Dropdown(
                id="year-filter",
                options=[{"label": "All Years", "value": "All"}] +
                        [{"label": str(int(y)), "value": int(y)} for y in YEARS],
                value="All", clearable=False, style=DD,
            ),
        ], style={"flex": "1", "minWidth": "130px"}),

        html.Div([
            html.Label("CTC Range (LPA)", style={"color": C["sub"], "fontSize": "11px", "fontWeight": "700",
                                                   "marginBottom": "5px", "display": "block", "textTransform": "uppercase"}),
            dcc.RangeSlider(
                id="ctc-slider",
                min=2, max=9, step=0.5,
                value=[2, 9],
                marks={v: {"label": f"₹{v}", "style": {"color": C["sub"], "fontSize": "10px"}}
                       for v in [2, 4, 6, 8, 9]},
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], style={"flex": "3", "minWidth": "240px"}),
    ], style={
        "display": "flex", "gap": "24px", "alignItems": "flex-end",
        "padding": "18px 32px",
        "background": "#0b1220",
        "borderBottom": f"1px solid {C['b']}",
        "flexWrap": "wrap",
    }),

    # ── KPI Row ─────────────────────────────────────────────────────────────
    html.Div(id="kpi-row", style={"display": "flex", "gap": "14px", "padding": "22px 32px 8px", "flexWrap": "wrap"}),

    # ── Row 1 ───────────────────────────────────────────────────────────────
    html.Div([
        dcc.Graph(id="status-donut",   style={"flex": "1", "minWidth": "240px"}),
        dcc.Graph(id="branch-bar",     style={"flex": "2", "minWidth": "340px"}),
        dcc.Graph(id="city-bar",       style={"flex": "1", "minWidth": "220px"}),
    ], style={"display": "flex", "gap": "14px", "padding": "8px 32px", "flexWrap": "wrap"}),

    # ── Row 2 ───────────────────────────────────────────────────────────────
    html.Div([
        dcc.Graph(id="ctc-hist",       style={"flex": "2", "minWidth": "340px"}),
        dcc.Graph(id="ctc-box",        style={"flex": "2", "minWidth": "340px"}),
    ], style={"display": "flex", "gap": "14px", "padding": "8px 32px", "flexWrap": "wrap"}),

    # ── Row 3 ───────────────────────────────────────────────────────────────
    html.Div([
        dcc.Graph(id="top-companies",  style={"flex": "2", "minWidth": "340px"}),
        dcc.Graph(id="top-roles",      style={"flex": "2", "minWidth": "340px"}),
    ], style={"display": "flex", "gap": "14px", "padding": "8px 32px", "flexWrap": "wrap"}),

    # ── Row 4 ───────────────────────────────────────────────────────────────
    html.Div([
        dcc.Graph(id="trend-line",     style={"flex": "2", "minWidth": "340px"}),
        dcc.Graph(id="ctc-company",    style={"flex": "2", "minWidth": "340px"}),
    ], style={"display": "flex", "gap": "14px", "padding": "8px 32px 32px", "flexWrap": "wrap"}),

], style={"background": C["bg"], "minHeight": "100vh", "fontFamily": "'Inter','Segoe UI',sans-serif"})


# ── Callback ───────────────────────────────────────────────────────────────────
@app.callback(
    Output("kpi-row",       "children"),
    Output("status-donut",  "figure"),
    Output("branch-bar",    "figure"),
    Output("city-bar",      "figure"),
    Output("ctc-hist",      "figure"),
    Output("ctc-box",       "figure"),
    Output("top-companies", "figure"),
    Output("top-roles",     "figure"),
    Output("trend-line",    "figure"),
    Output("ctc-company",   "figure"),
    Input("status-filter",  "value"),
    Input("city-filter",    "value"),
    Input("year-filter",    "value"),
    Input("ctc-slider",     "value"),
)
def update(status, city, year, ctc_range):

    # ── filter base ──
    d = df.copy()
    if status != "All":
        d = d[d["Placement Status"] == status]
    if city != "All":
        d = d[d["City"] == city]
    if year != "All":
        d = d[d["Year"] == year]

    # CTC filter applies only to placed students subset
    placed = d[d["Placement Status"] == "Placed"]
    placed = placed[(placed["Ctc Lpa"] >= ctc_range[0]) & (placed["Ctc Lpa"] <= ctc_range[1])]

    total        = len(d)
    n_placed     = len(d[d["Placement Status"] == "Placed"])
    n_process    = len(d[d["Placement Status"] == "In Process"])
    placement_rt = f"{100 * n_placed / total:.1f}%" if total else "0%"
    avg_ctc      = f"₹{placed['Ctc Lpa'].mean():.2f} LPA" if len(placed) else "—"
    top_company  = placed["Company Name"].value_counts().idxmax() if len(placed) else "—"

    kpis = [
        kpi("Total Students",   f"{total:,}",       C["a1"], "👥"),
        kpi("Placed",           f"{n_placed:,}",    C["a2"], "✅"),
        kpi("In Process",       f"{n_process:,}",   C["a3"], "⏳"),
        kpi("Placement Rate",   placement_rt,       C["a5"], "📈"),
        kpi("Avg CTC",          avg_ctc,            C["a2"], "💰"),
        kpi("Top Recruiter",    top_company,        C["a1"], "🏢"),
    ]

    # ── 1. Status Donut ──
    sc = d["Placement Status"].value_counts().reset_index()
    sc.columns = ["Status", "Count"]
    fig_donut = px.pie(
        sc, names="Status", values="Count",
        color="Status",
        color_discrete_map=STATUS_COLORS,
        hole=0.52, title="Placement Status Split",
    )
    fig_donut.update_layout(**CHART_BASE)
    fig_donut.update_traces(textfont_color=C["text"])

    # ── 2. Placement Rate by Branch (horizontal bar) ──
    br = d.groupby("Branch")["Placement Status"].apply(
        lambda x: round(100 * (x == "Placed").sum() / len(x), 1)
    ).reset_index()
    br.columns = ["Branch", "Rate"]
    br = br.sort_values("Rate", ascending=True)
    fig_branch = px.bar(
        br, x="Rate", y="Branch", orientation="h",
        title="Placement Rate % by Branch",
        color="Rate", color_continuous_scale=["#f43f5e", "#f59e0b", "#10b981"],
        labels={"Rate": "Placement %", "Branch": ""},
        text=br["Rate"].apply(lambda v: f"{v}%"),
    )
    fig_branch.update_layout(**CHART_BASE, coloraxis_showscale=False, height=520)
    fig_branch.update_traces(textposition="outside", textfont_color=C["sub"])
    fig_branch.update_xaxes(gridcolor=C["b"], range=[0, 75])
    fig_branch.update_yaxes(gridcolor="rgba(0,0,0,0)", tickfont_size=10)

    # ── 3. Placed vs Not Placed by City ──
    city_cnt = d.groupby(["City", "Placement Status"]).size().reset_index(name="Count")
    fig_city = px.bar(
        city_cnt, x="City", y="Count", color="Placement Status",
        color_discrete_map=STATUS_COLORS, barmode="group",
        title="Status by City",
        labels={"Count": "Students", "City": ""},
    )
    fig_city.update_layout(**CHART_BASE)
    fig_city.update_xaxes(gridcolor=C["b"])
    fig_city.update_yaxes(gridcolor=C["b"])

    # ── 4. CTC Distribution ──
    fig_ctc = px.histogram(
        placed, x="Ctc Lpa", nbins=30,
        color_discrete_sequence=[C["a1"]],
        title="CTC Distribution (Placed Students)",
        labels={"Ctc Lpa": "CTC (LPA)", "count": "Students"},
    )
    fig_ctc.update_layout(**CHART_BASE)
    fig_ctc.update_traces(marker_line_color=C["bg"], marker_line_width=0.5)
    fig_ctc.update_xaxes(gridcolor=C["b"])
    fig_ctc.update_yaxes(gridcolor=C["b"])

    # ── 5. CTC Box by Job Role ──
    role_order = (placed.groupby("Job Role")["Ctc Lpa"].median()
                  .sort_values(ascending=False).index.tolist())
    fig_box = px.box(
        placed, x="Job Role", y="Ctc Lpa",
        color="Job Role", color_discrete_sequence=px.colors.qualitative.Pastel,
        title="CTC Distribution by Job Role",
        labels={"Ctc Lpa": "CTC (LPA)", "Job Role": ""},
        category_orders={"Job Role": role_order},
    )
    fig_box.update_layout(**CHART_BASE, showlegend=False)
    fig_box.update_xaxes(gridcolor=C["b"], tickangle=-30)
    fig_box.update_yaxes(gridcolor=C["b"])

    # ── 6. Top 12 Recruiting Companies ──
    top_co = (placed["Company Name"].value_counts().head(12)
              .reset_index().rename(columns={"count": "Hires"}))
    top_co = top_co.sort_values("Hires", ascending=True)
    fig_co = px.bar(
        top_co, x="Hires", y="Company Name", orientation="h",
        title="Top 12 Recruiters",
        color="Hires", color_continuous_scale=["#3b82f6", "#a78bfa"],
        labels={"Hires": "Students Hired", "Company Name": ""},
        text="Hires",
    )
    fig_co.update_layout(**CHART_BASE, coloraxis_showscale=False)
    fig_co.update_traces(textposition="outside", textfont_color=C["sub"])
    fig_co.update_xaxes(gridcolor=C["b"])
    fig_co.update_yaxes(gridcolor="rgba(0,0,0,0)")

    # ── 7. Top Job Roles ──
    top_roles = (placed["Job Role"].value_counts().head(11)
                 .reset_index().rename(columns={"count": "Count"}))
    top_roles = top_roles.sort_values("Count", ascending=True)
    fig_roles = px.bar(
        top_roles, x="Count", y="Job Role", orientation="h",
        title="Top Job Roles",
        color="Count", color_continuous_scale=["#10b981", "#f59e0b"],
        labels={"Count": "Placements", "Job Role": ""},
        text="Count",
    )
    fig_roles.update_layout(**CHART_BASE, coloraxis_showscale=False)
    fig_roles.update_traces(textposition="outside", textfont_color=C["sub"])
    fig_roles.update_xaxes(gridcolor=C["b"])
    fig_roles.update_yaxes(gridcolor="rgba(0,0,0,0)")

    # ── 8. Monthly Placement Trend ──
    trend = (placed.dropna(subset=["Placement Date"])
             .groupby("Month").size().reset_index(name="Placements")
             .sort_values("Month"))
    fig_trend = px.area(
        trend, x="Month", y="Placements",
        title="Monthly Placement Trend (2022 – 2024)",
        color_discrete_sequence=[C["a1"]],
        labels={"Month": "Month", "Placements": "Placements"},
    )
    fig_trend.update_traces(fill="tozeroy", line_color=C["a1"],
                             fillcolor="rgba(59,130,246,0.18)")
    fig_trend.update_layout(**CHART_BASE)
    fig_trend.update_xaxes(gridcolor=C["b"], tickangle=-45, nticks=18)
    fig_trend.update_yaxes(gridcolor=C["b"])

    # ── 9. Avg CTC by Top 10 Companies ──
    ctc_co = (placed.groupby("Company Name")["Ctc Lpa"]
              .mean().round(2).reset_index()
              .nlargest(10, "Ctc Lpa")
              .sort_values("Ctc Lpa", ascending=True))
    ctc_co.columns = ["Company", "Avg CTC"]
    fig_ctc_co = px.bar(
        ctc_co, x="Avg CTC", y="Company", orientation="h",
        title="Top 10 Companies by Avg CTC (LPA)",
        color="Avg CTC", color_continuous_scale=["#f43f5e", "#f59e0b", "#10b981"],
        labels={"Avg CTC": "Avg CTC (LPA)", "Company": ""},
        text=ctc_co["Avg CTC"].apply(lambda v: f"₹{v}"),
    )
    fig_ctc_co.update_layout(**CHART_BASE, coloraxis_showscale=False)
    fig_ctc_co.update_traces(textposition="outside", textfont_color=C["sub"])
    fig_ctc_co.update_xaxes(gridcolor=C["b"])
    fig_ctc_co.update_yaxes(gridcolor="rgba(0,0,0,0)")

    return (kpis, fig_donut, fig_branch, fig_city,
            fig_ctc, fig_box, fig_co, fig_roles, fig_trend, fig_ctc_co)


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n✅ Placement Dashboard → http://127.0.0.1:8050\n")
    app.run(debug=True)
