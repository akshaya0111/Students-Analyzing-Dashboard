"""
Student Analytics Dashboard
============================
Run: python student_dashboard.py
Then open: http://127.0.0.1:8050 in your browser

Requirements:
    pip install dash plotly pandas openpyxl
"""

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, dcc, html, Input, Output
import warnings
warnings.filterwarnings("ignore")

# ── Load Data ──────────────────────────────────────────────────────────────────
BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "student_dataset_5000_updated.xlsx"
if not DATA_FILE.exists():
    raise FileNotFoundError(
        f"Dataset not found: {DATA_FILE}.\n"
        "Place 'student_dataset_5000_updated.xlsx' in the same folder as this script."
    )

df_raw = pd.read_excel(DATA_FILE, sheet_name="Students", header=None)
df_raw.columns = df_raw.iloc[0]
df = df_raw[1:].reset_index(drop=True)
df["cgpa"] = pd.to_numeric(df["cgpa"], errors="coerce")
df["passed_out_year"] = pd.to_numeric(df["passed_out_year"], errors="coerce").astype("Int64")

# ── Color Palette ──────────────────────────────────────────────────────────────
COLORS = {
    "bg": "#0f172a",
    "card": "#1e293b",
    "border": "#334155",
    "accent1": "#6366f1",  # indigo
    "accent2": "#22d3ee",  # cyanvv
    "accent3": "#f472b6",  # pink
    "accent4": "#34d399",  # emerald
    "text": "#f1f5f9",
    "subtext": "#94a3b8",
}

GENDER_COLORS   = ["#6366f1", "#f472b6"]
DEGREE_COLORS   = ["#22d3ee", "#34d399", "#f59e0b"]
SCHEME_COLORS   = ["#818cf8", "#34d399"]
LOCATION_COLORS = ["#f472b6", "#22d3ee"]

# ── KPI Helper ─────────────────────────────────────────────────────────────────
def kpi_card(title, value, color, icon=""):
    return html.Div([
        html.P(f"{icon}  {title}", style={"margin": "0 0 6px", "color": COLORS["subtext"], "fontSize": "13px", "fontWeight": "500"}),
        html.H2(str(value), style={"margin": 0, "color": color, "fontSize": "32px", "fontWeight": "700"}),
    ], style={
        "background": COLORS["card"],
        "border": f"1px solid {COLORS['border']}",
        "borderTop": f"3px solid {color}",
        "borderRadius": "12px",
        "padding": "20px 24px",
        "flex": "1",
        "minWidth": "160px",
    })

# ── App ────────────────────────────────────────────────────────────────────────
app = Dash(__name__)
app.title = "Student Analytics Dashboard"

YEARS = sorted(df["passed_out_year"].dropna().unique().tolist())

app.layout = html.Div([

    # ── Header ──
    html.Div([
        html.H1("🎓 Student Analytics Dashboard", style={
            "color": COLORS["text"], "margin": "0", "fontSize": "26px", "fontWeight": "700"
        }),
        html.P("5,000 Student Records · Interactive Analysis", style={
            "color": COLORS["subtext"], "margin": "4px 0 0", "fontSize": "14px"
        }),
    ], style={"padding": "28px 32px 20px", "borderBottom": f"1px solid {COLORS['border']}"}),

    # ── Filters ──
    html.Div([
        html.Div([
            html.Label("Year Range", style={"color": COLORS["subtext"], "fontSize": "13px", "marginBottom": "6px", "display": "block"}),
            dcc.RangeSlider(
                id="year-slider",
                min=YEARS[0], max=YEARS[-1],
                value=[YEARS[0], YEARS[-1]],
                marks={y: {"label": str(y), "style": {"color": COLORS["subtext"], "fontSize": "11px"}} for y in YEARS},
                step=1,
                tooltip={"placement": "bottom", "always_visible": False},
            ),
        ], style={"flex": "2", "minWidth": "260px"}),

        html.Div([
            html.Label("Gender", style={"color": COLORS["subtext"], "fontSize": "13px", "marginBottom": "6px", "display": "block"}),
            dcc.Dropdown(
                id="gender-filter",
                options=[{"label": "All", "value": "All"}] + [{"label": g, "value": g} for g in df["gender"].unique()],
                value="All", clearable=False,
                style={"background": COLORS["card"], "color": "#000"},
            ),
        ], style={"flex": "1", "minWidth": "140px"}),

        html.Div([
            html.Label("Degree", style={"color": COLORS["subtext"], "fontSize": "13px", "marginBottom": "6px", "display": "block"}),
            dcc.Dropdown(
                id="degree-filter",
                options=[{"label": "All", "value": "All"}] + [{"label": d, "value": d} for d in sorted(df["degree"].unique())],
                value="All", clearable=False,
                style={"background": COLORS["card"], "color": "#000"},
            ),
        ], style={"flex": "1", "minWidth": "140px"}),

        html.Div([
            html.Label("Scheme", style={"color": COLORS["subtext"], "fontSize": "13px", "marginBottom": "6px", "display": "block"}),
            dcc.Dropdown(
                id="scheme-filter",
                options=[{"label": "All", "value": "All"}] + [{"label": s, "value": s} for s in df["scheme"].unique()],
                value="All", clearable=False,
                style={"background": COLORS["card"], "color": "#000"},
            ),
        ], style={"flex": "1", "minWidth": "140px"}),
    ], style={
        "display": "flex", "gap": "20px", "alignItems": "flex-end",
        "padding": "20px 32px",
        "background": COLORS["card"],
        "borderBottom": f"1px solid {COLORS['border']}",
        "flexWrap": "wrap",
    }),

    # ── KPIs ──
    html.Div(id="kpi-row", style={
        "display": "flex", "gap": "16px", "padding": "24px 32px 8px", "flexWrap": "wrap"
    }),

    # ── Row 1: Charts ──
    html.Div([
        dcc.Graph(id="cgpa-dist",    style={"flex": "2", "minWidth": "300px"}),
        dcc.Graph(id="gender-pie",   style={"flex": "1", "minWidth": "240px"}),
        dcc.Graph(id="degree-pie",   style={"flex": "1", "minWidth": "240px"}),
    ], style={"display": "flex", "gap": "16px", "padding": "8px 32px", "flexWrap": "wrap"}),

    # ── Row 2: Charts ──
    html.Div([
        dcc.Graph(id="year-trend",   style={"flex": "2", "minWidth": "300px"}),
        dcc.Graph(id="scheme-bar",   style={"flex": "1", "minWidth": "240px"}),
        dcc.Graph(id="location-bar", style={"flex": "1", "minWidth": "240px"}),
    ], style={"display": "flex", "gap": "16px", "padding": "8px 32px", "flexWrap": "wrap"}),

    # ── Row 3: Charts ──
    html.Div([
        dcc.Graph(id="cgpa-degree-box",  style={"flex": "1", "minWidth": "300px"}),
        dcc.Graph(id="cgpa-heatmap",     style={"flex": "1", "minWidth": "300px"}),
    ], style={"display": "flex", "gap": "16px", "padding": "8px 32px 32px", "flexWrap": "wrap"}),

], style={
    "background": COLORS["bg"],
    "minHeight": "100vh",
    "fontFamily": "'Inter', 'Segoe UI', sans-serif",
})


# ── Callbacks ──────────────────────────────────────────────────────────────────
def apply_filters(year_range, gender, degree, scheme):
    filtered = df[
        (df["passed_out_year"] >= year_range[0]) &
        (df["passed_out_year"] <= year_range[1])
    ]
    if gender != "All":
        filtered = filtered[filtered["gender"] == gender]
    if degree != "All":
        filtered = filtered[filtered["degree"] == degree]
    if scheme != "All":
        filtered = filtered[filtered["scheme"] == scheme]
    return filtered


CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color=COLORS["text"],
    font_family="'Inter','Segoe UI',sans-serif",
    margin=dict(t=44, b=30, l=30, r=20),
    legend=dict(bgcolor="rgba(0,0,0,0)", font_color=COLORS["subtext"]),
)


@app.callback(
    Output("kpi-row", "children"),
    Output("cgpa-dist", "figure"),
    Output("gender-pie", "figure"),
    Output("degree-pie", "figure"),
    Output("year-trend", "figure"),
    Output("scheme-bar", "figure"),
    Output("location-bar", "figure"),
    Output("cgpa-degree-box", "figure"),
    Output("cgpa-heatmap", "figure"),
    Input("year-slider", "value"),
    Input("gender-filter", "value"),
    Input("degree-filter", "value"),
    Input("scheme-filter", "value"),
)
def update_dashboard(year_range, gender, degree, scheme):
    d = apply_filters(year_range, gender, degree, scheme)
    total = len(d)
    avg_cgpa = round(d["cgpa"].mean(), 2) if total else 0
    placement_pct = f"{round(100 * len(d[d['scheme']=='Placement']) / total, 1)}%" if total else "0%"
    top_performers = len(d[d["cgpa"] >= 9.0])

    kpis = [
        kpi_card("Total Students",   f"{total:,}",       COLORS["accent1"], "👥"),
        kpi_card("Average CGPA",     avg_cgpa,            COLORS["accent2"], "📊"),
        kpi_card("Placement %",      placement_pct,       COLORS["accent4"], "🏢"),
        kpi_card("Top Performers",   f"{top_performers:,}", COLORS["accent3"], "⭐"),
    ]

    # CGPA Distribution
    fig_cgpa = px.histogram(
        d, x="cgpa", nbins=30, color_discrete_sequence=[COLORS["accent1"]],
        title="CGPA Distribution",
        labels={"cgpa": "CGPA", "count": "Students"},
    )
    fig_cgpa.update_layout(**CHART_LAYOUT)
    fig_cgpa.update_traces(marker_line_color=COLORS["bg"], marker_line_width=0.5)

    # Gender Pie
    gc = d["gender"].value_counts().reset_index()
    fig_gender = px.pie(gc, names="gender", values="count", title="Gender Split",
                        color_discrete_sequence=GENDER_COLORS, hole=0.45)
    fig_gender.update_layout(**CHART_LAYOUT)
    fig_gender.update_traces(textfont_color=COLORS["text"])

    # Degree Pie
    dc = d["degree"].value_counts().reset_index()
    fig_degree = px.pie(dc, names="degree", values="count", title="Degree Split",
                        color_discrete_sequence=DEGREE_COLORS, hole=0.45)
    fig_degree.update_layout(**CHART_LAYOUT)
    fig_degree.update_traces(textfont_color=COLORS["text"])

    # Year Trend
    yr = d.groupby("passed_out_year").size().reset_index(name="count")
    fig_year = px.line(yr, x="passed_out_year", y="count", markers=True,
                       title="Students by Pass-Out Year",
                       labels={"passed_out_year": "Year", "count": "Students"},
                       color_discrete_sequence=[COLORS["accent2"]])
    fig_year.update_layout(**CHART_LAYOUT)
    fig_year.update_traces(line_width=2.5, marker_size=7)
    fig_year.update_xaxes(gridcolor=COLORS["border"], tickformat="d")
    fig_year.update_yaxes(gridcolor=COLORS["border"])

    # Scheme Bar
    sc = d["scheme"].value_counts().reset_index()
    fig_scheme = px.bar(sc, x="scheme", y="count", title="Scheme Breakdown",
                        color="scheme", color_discrete_sequence=SCHEME_COLORS,
                        labels={"scheme": "Scheme", "count": "Students"})
    fig_scheme.update_layout(**CHART_LAYOUT, showlegend=False)
    fig_scheme.update_xaxes(gridcolor=COLORS["border"])
    fig_scheme.update_yaxes(gridcolor=COLORS["border"])

    # Location Bar
    lc = d["current_location"].value_counts().reset_index()
    fig_loc = px.bar(lc, x="current_location", y="count", title="Current Location",
                     color="current_location", color_discrete_sequence=LOCATION_COLORS,
                     labels={"current_location": "Location", "count": "Students"})
    fig_loc.update_layout(**CHART_LAYOUT, showlegend=False)
    fig_loc.update_xaxes(gridcolor=COLORS["border"])
    fig_loc.update_yaxes(gridcolor=COLORS["border"])

    # CGPA by Degree Box
    fig_box = px.box(d, x="degree", y="cgpa", color="degree",
                     color_discrete_sequence=DEGREE_COLORS,
                     title="CGPA by Degree",
                     labels={"degree": "Degree", "cgpa": "CGPA"})
    fig_box.update_layout(**CHART_LAYOUT, showlegend=False)
    fig_box.update_xaxes(gridcolor=COLORS["border"])
    fig_box.update_yaxes(gridcolor=COLORS["border"])

    # CGPA Heatmap: Degree × Year (avg CGPA)
    pivot = d.groupby(["degree", "passed_out_year"])["cgpa"].mean().reset_index()
    pivot_table = pivot.pivot(index="degree", columns="passed_out_year", values="cgpa").round(2)
    fig_heat = go.Figure(go.Heatmap(
        z=pivot_table.values,
        x=[str(c) for c in pivot_table.columns],
        y=pivot_table.index.tolist(),
        colorscale="Viridis",
        colorbar=dict(title="Avg CGPA", tickfont=dict(color=COLORS["subtext"])),
        text=pivot_table.values.round(1),
        texttemplate="%{text}",
        textfont={"size": 11, "color": "white"},
    ))
    fig_heat.update_layout(title="Avg CGPA: Degree × Year", **CHART_LAYOUT)
    fig_heat.update_xaxes(title="Year", gridcolor=COLORS["border"])
    fig_heat.update_yaxes(title="Degree", gridcolor=COLORS["border"])

    return kpis, fig_cgpa, fig_gender, fig_degree, fig_year, fig_scheme, fig_loc, fig_box, fig_heat


# ── Run ────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("\n✅ Dashboard running → http://127.0.0.1:8050\n")
    # Bind explicitly and disable the reloader to avoid parent/child exit behavior
    app.run(host="127.0.0.1", port=8050, debug=False)
