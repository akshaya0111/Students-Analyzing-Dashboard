"""
Besant Technologies – Student Analytics Dashboard
Run: python besant_dashboard.py
Then open: http://127.0.0.1:8050
"""

import pandas as pd
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px
import plotly.graph_objects as go
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

# ─────────────────────────────────────────────
# 1. LOAD DATA
# ─────────────────────────────────────────────
BASE = Path(__file__).resolve().parent

def load_excel(filename, **kwargs):
    path = BASE / filename
    if not path.exists():
        raise FileNotFoundError(
            f"Required data file not found: {path}\n"
            f"Please place the file next to besant_dashboard.py."
        )
    return pd.read_excel(path, **kwargs)


def find_existing_file(*filenames):
    for filename in filenames:
        path = BASE / filename
        if path.exists():
            return path
    raise FileNotFoundError(
        f"None of the expected files were found in {BASE}: {', '.join(filenames)}"
    )

students_df  = pd.read_excel(find_existing_file("student_dataset_5000_updated.xlsx"),  sheet_name="Students")
fees_df      = pd.read_excel(find_existing_file("student_fees_only.xlsx"),              sheet_name="Fees Dataset")
placement_df = pd.read_excel(find_existing_file(
    "student_placement_only (version 2).xlsb.xlsx",
    "student_placement_only__version_2__xlsb.xlsx"
), sheet_name="Placement Dataset")
courses_df   = pd.read_excel(find_existing_file("besant_courses_1000_updated.xlsx"),    sheet_name="Course_Data")
master_df    = pd.read_excel(find_existing_file("besant_analysis_1000.xlsx"),           sheet_name="Master_Combined")

# Normalise column names
students_df.columns  = students_df.columns.str.strip()
fees_df.columns      = fees_df.columns.str.strip()
placement_df.columns = placement_df.columns.str.strip()
courses_df.columns   = courses_df.columns.str.strip()
master_df.columns    = master_df.columns.str.strip()

placement_df["Placement Date"] = pd.to_datetime(placement_df["Placement Date"], errors="coerce")
placement_df["Placement Year"] = placement_df["Placement Date"].dt.year

# ─────────────────────────────────────────────
# 2. KPI HELPERS
# ─────────────────────────────────────────────
total_students  = len(students_df)
placed          = placement_df[placement_df["Placement Status"] == "Placed"]
placement_rate  = round(len(placed) / len(placement_df) * 100, 1)
avg_ctc         = round(placed["Ctc Lpa"].mean(), 2)
total_revenue   = fees_df["Total Paid"].sum()

# ─────────────────────────────────────────────
# 3. COLOUR PALETTE
# ─────────────────────────────────────────────
PRIMARY   = "#4F46E5"
ACCENT    = "#06B6D4"
SUCCESS   = "#10B981"
WARNING   = "#F59E0B"
DANGER    = "#EF4444"
DARK      = "#1E1B4B"
CARD_BG   = "#FFFFFF"
PAGE_BG   = "#F1F5F9"

CHART_COLORS = [PRIMARY, ACCENT, SUCCESS, WARNING, DANGER,
                "#8B5CF6", "#EC4899", "#14B8A6"]

def kpi_card(title, value, icon, color):
    return dbc.Card(
        dbc.CardBody([
            html.Div([
                html.Span(icon, style={"fontSize": "2rem"}),
                html.Div([
                    html.P(title, className="mb-0",
                           style={"fontSize": "0.78rem", "color": "#64748B", "fontWeight": "600",
                                  "textTransform": "uppercase", "letterSpacing": "0.05em"}),
                    html.H3(value, className="mb-0 fw-bold",
                            style={"color": color, "fontSize": "1.6rem"}),
                ], className="ms-3")
            ], className="d-flex align-items-center")
        ]),
        style={"borderLeft": f"4px solid {color}", "borderRadius": "12px",
               "boxShadow": "0 2px 12px rgba(0,0,0,0.07)", "background": CARD_BG},
        className="mb-3"
    )

# ─────────────────────────────────────────────
# 4. APP LAYOUT
# ─────────────────────────────────────────────
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP],
                meta_tags=[{"name": "viewport", "content": "width=device-width, initial-scale=1"}])
app.title = "Besant Student Analytics"

TABS = ["Overview", "Students", "Fees", "Placement", "Courses"]

app.layout = dbc.Container(fluid=True, style={"background": PAGE_BG, "minHeight": "100vh",
                                               "fontFamily": "'Segoe UI', sans-serif"}, children=[

    # ── HEADER ──────────────────────────────
    dbc.Row(dbc.Col(
        html.Div([
            html.H2("🎓 Besant Technologies – Student Analytics",
                    className="mb-0 fw-bold text-white"),
            html.P("Real-time insights across students, fees, placements & courses",
                   className="mb-0 text-white-50 small")
        ], className="py-3 px-4"),
        style={"background": f"linear-gradient(135deg, {DARK} 0%, {PRIMARY} 100%)",
               "borderRadius": "0 0 16px 16px", "marginBottom": "1.5rem"}
    )),

    # ── KPI CARDS ───────────────────────────
    dbc.Row([
        dbc.Col(kpi_card("Total Students",   f"{total_students:,}", "👨‍🎓", PRIMARY),  md=3),
        dbc.Col(kpi_card("Placement Rate",   f"{placement_rate}%",  "🏆", SUCCESS),  md=3),
        dbc.Col(kpi_card("Avg CTC (LPA)",    f"₹{avg_ctc}",         "💰", WARNING),  md=3),
        dbc.Col(kpi_card("Total Revenue",    f"₹{total_revenue/1e6:.1f}M", "📈", ACCENT), md=3),
    ], className="mb-2 px-3"),

    # ── TABS ────────────────────────────────
    dbc.Row(dbc.Col(
        dbc.Tabs(id="main-tabs", active_tab="tab-Overview",
                 children=[dbc.Tab(label=t, tab_id=f"tab-{t}") for t in TABS],
                 className="mb-3"),
        className="px-3"
    )),

    # ── TAB CONTENT ─────────────────────────
    dbc.Row(dbc.Col(html.Div(id="tab-content"), className="px-3")),

    # ── FOOTER ──────────────────────────────
    dbc.Row(dbc.Col(
        html.P("© 2025 Besant Technologies Dashboard · Built with Dash & Plotly",
               className="text-center text-muted small py-3 mt-3")
    ))
])

# ─────────────────────────────────────────────
# 5. TAB CALLBACK
# ─────────────────────────────────────────────
@app.callback(Output("tab-content", "children"), Input("main-tabs", "active_tab"))
def render_tab(tab):

    # ── OVERVIEW ────────────────────────────
    if tab == "tab-Overview":
        # Gender split
        gender = students_df["gender"].value_counts().reset_index()
        gender.columns = ["Gender", "Count"]
        fig_gender = px.pie(gender, names="Gender", values="Count", hole=0.5,
                            color_discrete_sequence=CHART_COLORS, title="Gender Distribution")
        fig_gender.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Degree split
        degree = students_df["degree"].value_counts().reset_index()
        degree.columns = ["Degree", "Count"]
        fig_degree = px.bar(degree, x="Degree", y="Count", color="Degree",
                            color_discrete_sequence=CHART_COLORS, title="Students by Degree")
        fig_degree.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                                 plot_bgcolor="rgba(0,0,0,0)", xaxis_title="", yaxis_title="Count")

        # Year-wise
        year = students_df["passed_out_year"].value_counts().sort_index().reset_index()
        year.columns = ["Year", "Count"]
        fig_year = px.line(year, x="Year", y="Count", markers=True,
                           color_discrete_sequence=[PRIMARY], title="Pass-out Year Trend")
        fig_year.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Scheme split
        scheme = students_df["scheme"].value_counts().reset_index()
        scheme.columns = ["Scheme", "Count"]
        fig_scheme = px.bar(scheme, x="Count", y="Scheme", orientation="h",
                            color="Scheme", color_discrete_sequence=CHART_COLORS,
                            title="Students by Scheme")
        fig_scheme.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                                 plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", xaxis_title="Count")

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_gender,  config={"displayModeBar": False}), md=3),
            dbc.Col(dcc.Graph(figure=fig_degree,  config={"displayModeBar": False}), md=3),
            dbc.Col(dcc.Graph(figure=fig_year,    config={"displayModeBar": False}), md=3),
            dbc.Col(dcc.Graph(figure=fig_scheme,  config={"displayModeBar": False}), md=3),
        ])

    # ── STUDENTS ────────────────────────────
    elif tab == "tab-Students":
        # CGPA histogram
        fig_cgpa = px.histogram(students_df, x="cgpa", nbins=20,
                                color_discrete_sequence=[PRIMARY], title="CGPA Distribution",
                                labels={"cgpa": "CGPA"})
        fig_cgpa.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Top native locations
        loc = students_df["native_location"].value_counts().head(10).reset_index()
        loc.columns = ["Location", "Count"]
        fig_loc = px.bar(loc, x="Count", y="Location", orientation="h",
                         color="Location", color_discrete_sequence=CHART_COLORS,
                         title="Top 10 Native Locations")
        fig_loc.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", xaxis_title="Count")

        # CGPA by degree box
        fig_box = px.box(students_df, x="degree", y="cgpa", color="degree",
                         color_discrete_sequence=CHART_COLORS,
                         title="CGPA by Degree", labels={"degree": "Degree", "cgpa": "CGPA"})
        fig_box.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)")

        # Gender by degree
        gd = students_df.groupby(["degree", "gender"]).size().reset_index(name="Count")
        fig_gd = px.bar(gd, x="degree", y="Count", color="gender",
                        barmode="group", color_discrete_sequence=CHART_COLORS,
                        title="Gender Breakdown by Degree")
        fig_gd.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                              xaxis_title="", legend_title="Gender")

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_cgpa, config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_loc,  config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_box,  config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_gd,   config={"displayModeBar": False}), md=6),
        ])

    # ── FEES ────────────────────────────────
    elif tab == "tab-Fees":
        # Fee status donut
        fs = fees_df["Fee Status"].value_counts().reset_index()
        fs.columns = ["Status", "Count"]
        fig_fs = px.pie(fs, names="Status", values="Count", hole=0.5,
                        color_discrete_sequence=CHART_COLORS, title="Fee Status Distribution")
        fig_fs.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Revenue breakdown
        rev = {
            "Enroll Fee":       fees_df["Enroll Fee"].sum(),
            "Partial Payment":  fees_df["Partial Payment"].sum(),
            "Full Payment":     fees_df["Full Payment"].sum(),
            "Balance Due":      fees_df["Balance Due"].sum(),
        }
        fig_rev = px.bar(x=list(rev.keys()), y=list(rev.values()),
                         color=list(rev.keys()), color_discrete_sequence=CHART_COLORS,
                         title="Revenue Breakdown", labels={"x": "Category", "y": "Amount (₹)"})
        fig_rev.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                               plot_bgcolor="rgba(0,0,0,0)")

        # Total fees distribution
        fig_tf = px.histogram(fees_df, x="Total Fees", nbins=30,
                              color_discrete_sequence=[ACCENT], title="Total Fees Histogram",
                              labels={"Total Fees": "Total Fees (₹)"})
        fig_tf.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Payment mode (master)
        pm = master_df["payment_mode"].value_counts().reset_index()
        pm.columns = ["Mode", "Count"]
        fig_pm = px.pie(pm, names="Mode", values="Count",
                        color_discrete_sequence=CHART_COLORS, title="Payment Mode Split")
        fig_pm.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_fs,  config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_rev, config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_tf,  config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_pm,  config={"displayModeBar": False}), md=6),
        ])

    # ── PLACEMENT ───────────────────────────
    elif tab == "tab-Placement":
        # Status donut
        ps = placement_df["Placement Status"].value_counts().reset_index()
        ps.columns = ["Status", "Count"]
        fig_ps = px.pie(ps, names="Status", values="Count", hole=0.5,
                        color_discrete_sequence=[SUCCESS, DANGER],
                        title="Placement Status")
        fig_ps.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Top 10 companies
        co = placed["Company Name"].value_counts().head(10).reset_index()
        co.columns = ["Company", "Count"]
        fig_co = px.bar(co, x="Count", y="Company", orientation="h",
                        color="Company", color_discrete_sequence=CHART_COLORS,
                        title="Top 10 Hiring Companies")
        fig_co.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", xaxis_title="Placed Students")

        # CTC histogram
        fig_ctc = px.histogram(placed.dropna(subset=["Ctc Lpa"]), x="Ctc Lpa", nbins=20,
                               color_discrete_sequence=[WARNING], title="CTC Distribution (LPA)",
                               labels={"Ctc Lpa": "CTC (LPA)"})
        fig_ctc.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Placement by branch (top 12)
        br = placed["Branch"].value_counts().head(12).reset_index()
        br.columns = ["Branch", "Count"]
        fig_br = px.bar(br, x="Branch", y="Count", color="Branch",
                        color_discrete_sequence=CHART_COLORS,
                        title="Placements by Branch (Top 12)")
        fig_br.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)",
                              xaxis={"tickangle": -35}, xaxis_title="", yaxis_title="Count")

        # Yearly trend
        yt = placement_df[placement_df["Placement Status"] == "Placed"].groupby(
            "Placement Year").size().reset_index(name="Placed")
        fig_yt = px.line(yt.dropna(), x="Placement Year", y="Placed", markers=True,
                         color_discrete_sequence=[PRIMARY], title="Yearly Placement Trend")
        fig_yt.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Top job roles
        jr = placed["Job Role"].value_counts().head(8).reset_index()
        jr.columns = ["Role", "Count"]
        fig_jr = px.bar(jr, x="Count", y="Role", orientation="h",
                        color="Role", color_discrete_sequence=CHART_COLORS,
                        title="Top Job Roles")
        fig_jr.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", xaxis_title="Count")

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_ps,  config={"displayModeBar": False}), md=4),
            dbc.Col(dcc.Graph(figure=fig_co,  config={"displayModeBar": False}), md=8),
            dbc.Col(dcc.Graph(figure=fig_ctc, config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_yt,  config={"displayModeBar": False}), md=6),
            dbc.Col(dcc.Graph(figure=fig_br,  config={"displayModeBar": False}), md=8),
            dbc.Col(dcc.Graph(figure=fig_jr,  config={"displayModeBar": False}), md=4),
        ])

    # ── COURSES ─────────────────────────────
    elif tab == "tab-Courses":
        # Category donut
        cat = courses_df["category"].value_counts().reset_index()
        cat.columns = ["Category", "Count"]
        fig_cat = px.pie(cat, names="Category", values="Count", hole=0.5,
                         color_discrete_sequence=CHART_COLORS, title="Courses by Category")
        fig_cat.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")

        # Mode split
        mode = courses_df["mode"].value_counts().reset_index()
        mode.columns = ["Mode", "Count"]
        fig_mode = px.bar(mode, x="Mode", y="Count", color="Mode",
                          color_discrete_sequence=CHART_COLORS, title="Course Delivery Mode")
        fig_mode.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)", xaxis_title="", yaxis_title="Count")

        # Fee by category
        fc = courses_df.groupby("category")["fee"].mean().reset_index()
        fc.columns = ["Category", "Avg Fee"]
        fig_fc = px.bar(fc.sort_values("Avg Fee", ascending=False), x="Avg Fee", y="Category",
                        orientation="h", color="Category", color_discrete_sequence=CHART_COLORS,
                        title="Avg Course Fee by Category (₹)")
        fig_fc.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                              plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", xaxis_title="Avg Fee (₹)")

        # Completion rate
        courses_df["completion_rate"] = (
            courses_df["full_completion"] /
            (courses_df["full_completion"] + courses_df["partial_completion"])
        ).fillna(0) * 100
        top_courses = courses_df.groupby("course_name")["completion_rate"].mean()\
                                .sort_values(ascending=False).head(10).reset_index()
        fig_comp = px.bar(top_courses, x="completion_rate", y="course_name", orientation="h",
                          color="course_name", color_discrete_sequence=CHART_COLORS,
                          title="Top 10 Courses by Completion Rate (%)")
        fig_comp.update_layout(showlegend=False, paper_bgcolor="rgba(0,0,0,0)",
                                plot_bgcolor="rgba(0,0,0,0)", yaxis_title="", xaxis_title="Completion %")

        return dbc.Row([
            dbc.Col(dcc.Graph(figure=fig_cat,  config={"displayModeBar": False}), md=4),
            dbc.Col(dcc.Graph(figure=fig_mode, config={"displayModeBar": False}), md=4),
            dbc.Col(dcc.Graph(figure=fig_fc,   config={"displayModeBar": False}), md=4),
            dbc.Col(dcc.Graph(figure=fig_comp, config={"displayModeBar": False}), md=12),
        ])

    return html.P("Select a tab above.", className="text-muted p-3")


# ─────────────────────────────────────────────
# 6. RUN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app.run(debug=False, host="127.0.0.1", port=8050)
