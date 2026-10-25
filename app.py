from __future__ import annotations

import html
import hashlib
from datetime import date
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import plotly.io as pio
import streamlit as st

# Pin chart rendering to a light palette regardless of browser/Streamlit theme.
pio.templates.default = "plotly_white"
px.defaults.template = "plotly_white"

from db import (
    CSV_PATH, ROOT, ai_configuration, all_sales, answer_question, data_quality,
    ensure_db, initialize, load_dataframe, metadata, test_gemini_connection,
)

st.set_page_config(
    page_title="NOVA | Sales Intelligence",
    page_icon="◈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Local, responsive design system. Avoid external font dependencies and fixed-width content.
st.markdown(
    """
    <style>
    :root {
      color-scheme: light;
      --nova-ink:#172033; --nova-muted:#526581; --nova-line:#dbe3ef;
      --nova-panel:#ffffff; --nova-bg:#f4f7fc; --nova-primary:#4f46e5;
      --nova-primary-dark:#27215e; --nova-teal:#0f766e;
    }
    html, body, [class*="css"], [data-testid="stAppViewContainer"] {
      font-family: Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      color:var(--nova-ink);
    }
    .stApp { background:var(--nova-bg); }
    [data-testid="stHeader"] { background:transparent; }
    .block-container { max-width:1580px; padding-top:1.3rem; padding-bottom:3rem; }
    [data-testid="stSidebar"] { background:#fbfcff; border-right:1px solid var(--nova-line); }
    [data-testid="stSidebarContent"] { padding-top:1rem; }
    h1,h2,h3 { letter-spacing:-.025em; }
    h1 { font-size:clamp(1.8rem, 3.1vw, 2.65rem)!important; line-height:1.12!important; }
    h2 { font-size:1.45rem!important; }
    h3 { font-size:1.07rem!important; }
    .nova-hero {
      box-sizing:border-box; width:100%; padding:clamp(1.25rem, 3vw, 2rem);
      background:linear-gradient(115deg,rgba(79,70,229,.075),rgba(14,165,233,.045) 58%,rgba(255,255,255,.65));
      color:var(--nova-ink); border:1px solid rgba(203,213,225,.72); border-radius:22px; margin:0 0 1.2rem 0;
      box-shadow:0 10px 28px rgba(31,41,87,.055); overflow:hidden; overflow-wrap:anywhere;
    }
    .nova-brandline { display:flex; align-items:center; gap:.65rem; color:#4f46e5; font-size:.72rem; font-weight:800; letter-spacing:.11em; text-transform:uppercase; }
    .nova-mark { display:none; }
    .nova-hero-title { margin:.25rem 0 .55rem; font-size:clamp(1.75rem,3.2vw,2.7rem); font-weight:800; line-height:1.12; letter-spacing:-.04em; color:#172033; }
    .nova-hero-copy { color:#40516b; font-size:.98rem; line-height:1.6; max-width:1000px; margin:0; }
    .nova-kicker { color:var(--nova-muted); font-size:.71rem; font-weight:750; letter-spacing:.12em; text-transform:uppercase; margin-bottom:.4rem; }
    .nova-muted { color:var(--nova-muted); font-size:.88rem; line-height:1.55; }
    .nova-answer { box-sizing:border-box; width:100%; padding:1rem 1.1rem; border-radius:14px; border:1px solid #c7d2fe; background:#eef2ff; color:#20234c; line-height:1.65; overflow-wrap:anywhere; white-space:normal; }
    .nova-status { display:inline-flex; max-width:100%; padding:.35rem .65rem; border-radius:999px; background:#eef2ff; color:#3730a3; font-size:.75rem; font-weight:700; line-height:1.35; white-space:normal; overflow-wrap:anywhere; text-align:center; box-sizing:border-box; }
    .nova-status-ok { background:#dcfce7; color:#166534; }
    .nova-status-warn { background:#fef3c7; color:#92400e; }
    .nova-separator { border:0; border-top:1px solid var(--nova-line); margin:1.15rem 0; }
    div[data-testid="stVerticalBlockBorderWrapper"] { border-radius:16px; border-color:var(--nova-line); background:rgba(255,255,255,.76); }
    div[data-testid="stMetric"] { min-width:0; box-sizing:border-box; background:#fff; border:1px solid var(--nova-line); padding:1rem 1.05rem; border-radius:15px; box-shadow:0 2px 10px rgba(15,23,42,.025); height:100%; }
    div[data-testid="stMetricLabel"] { white-space:normal!important; overflow-wrap:anywhere; color:var(--nova-muted)!important; font-size:.78rem!important; line-height:1.4!important; }
    div[data-testid="stMetricValue"] { white-space:normal!important; overflow-wrap:anywhere; word-break:break-word; font-size:clamp(1.25rem,2vw,1.9rem)!important; line-height:1.2!important; font-weight:760!important; color:var(--nova-ink)!important; }
    div[data-testid="stMetricDelta"] { white-space:normal!important; overflow-wrap:anywhere; font-size:.75rem!important; }
    div[data-testid="stTabs"] button { font-weight:650; }
    .stButton>button, .stDownloadButton>button, [data-testid="stFormSubmitButton"] button { border-radius:10px; font-weight:650; min-height:2.7rem; white-space:normal; overflow-wrap:anywhere; }
    .stButton>button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] { box-shadow:0 5px 14px rgba(79,70,229,.16); }
    input, textarea, [data-baseweb="select"] { border-radius:10px!important; }
    [data-testid="stDataFrame"] { width:100%; }
    [data-testid="stAlert"] { overflow-wrap:anywhere; color:#263449; }
    [data-testid="stWidgetLabel"] p, [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] p, label, .stRadio label, .stCheckbox label {
      color:#33445d;
    }
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2,
    [data-testid="stMarkdownContainer"] h3, [data-testid="stMarkdownContainer"] h4,
    [data-testid="stTabs"] button { color:#172033; }
    [data-testid="stPlotlyChart"] { background:#fff; border:1px solid #e1e7f0; border-radius:14px; padding:.35rem; box-sizing:border-box; color:#172033; }
    [data-testid="stPlotlyChart"] .modebar { top:3px!important; right:4px!important; }
    .small-label { color:#526581; font-size:.75rem; }
    @media (max-width: 760px) {
      .block-container { padding-left:.8rem; padding-right:.8rem; }
      .nova-hero { border-radius:16px; }
      div[data-testid="stMetric"] { padding:.8rem; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def section_intro(title: str, description: str = ""):
    st.subheader(title)
    if description:
        st.markdown(f'<div class="nova-muted">{html.escape(description)}</div>', unsafe_allow_html=True)


def format_inr(value) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


def render_result_chart(result: dict, frame: pd.DataFrame):
    if frame.empty or len(frame) < 2:
        return
    chart = result.get("chart") or {}
    chart_type = chart.get("chart_type", "table")
    x_col, y_col = chart.get("x_column"), chart.get("y_column")
    if x_col not in frame.columns:
        x_col = frame.columns[0]
    numeric_cols = [c for c in frame.columns if pd.api.types.is_numeric_dtype(frame[c])]
    if y_col not in frame.columns or y_col not in numeric_cols:
        y_col = numeric_cols[0] if numeric_cols else None
    if chart_type == "table":
        return
    if not x_col or not y_col or x_col == y_col:
        # Generic fallback for results from the deterministic query engine.
        likely_x = next((c for c in frame.columns if str(c).lower() in {
            "month", "month label", "product", "region", "category", "sales_channel", "channel", "status", "sales channel"
        }), None)
        if likely_x and numeric_cols:
            x_col, y_col, chart_type = likely_x, numeric_cols[0], "bar"
        else:
            return
    if chart_type == "scatter" and (x_col not in numeric_cols or y_col not in numeric_cols):
        usable = [c for c in numeric_cols if c != y_col]
        if not usable or not y_col or y_col not in numeric_cols:
            st.info("Scatter plots need two numeric columns. Choose Bar, Line, or Table for this result set.")
            return
        x_col = usable[0]
    data = frame.copy()
    data[y_col] = pd.to_numeric(data[y_col], errors="coerce")
    data = data.dropna(subset=[x_col, y_col]).head(100)
    if data.empty:
        return
    labels = {x_col: str(x_col).replace("_", " ").title(), y_col: str(y_col).replace("_", " ").title()}
    title = str(chart.get("title") or f"{labels[y_col]} by {labels[x_col]}")[:100]
    if chart_type == "pie":
        fig = px.pie(data, names=x_col, values=y_col, hole=.48, title=title)
        fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}<br>%{value:,.2f}<extra></extra>")
    elif chart_type == "line":
        fig = px.line(data, x=x_col, y=y_col, markers=True, title=title, labels=labels)
        fig.update_traces(line_width=3, hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>")
    elif chart_type == "scatter":
        if len(numeric_cols) >= 2:
            second_y = y_col
            x_num = chart.get("x_column") if chart.get("x_column") in numeric_cols else numeric_cols[0]
            fig = px.scatter(data, x=x_num, y=second_y, title=title, labels=labels)
        else:
            fig = px.bar(data, x=x_col, y=y_col, title=title, labels=labels)
    else:
        fig = px.bar(data, x=x_col, y=y_col, title=title, labels=labels, text_auto=".3s")
        fig.update_traces(hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>")
    fig.update_layout(
        height=370, margin=dict(l=12, r=18, t=66, b=20),
        title=dict(font=dict(size=17, color="#172033"), x=0.02, xanchor="left"),
        font=dict(family="Inter, Arial, sans-serif", color="#334155"),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        legend_title_text="", hoverlabel=dict(bgcolor="white", font_color="#172033"),
    )
    if chart_type != "pie":
        fig.update_xaxes(title=labels.get(x_col, x_col), showgrid=False, automargin=True, tickangle=-15 if data[x_col].astype(str).str.len().max() > 12 else 0)
        fig.update_yaxes(title=labels.get(y_col, y_col), gridcolor="#e8edf5", automargin=True)
        if "revenue" in str(y_col).lower() or "amount" in str(y_col).lower() or "price" in str(y_col).lower():
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f")
    st.plotly_chart(fig, use_container_width=True, config={"displaylogo": False, "responsive": True})


# Database setup: respect the currently active uploaded dataset.
try:
    ensure_db()
except Exception as exc:
    st.error(f"NOVA could not open its local SQLite database ({type(exc).__name__}). Check the project folder and permissions.")
    st.stop()

# Streamlit secrets are supported for deployment; local .env remains the preferred Mac setup.
secret_api_key = ""
try:
    secret_api_key = str(st.secrets.get("GEMINI_API_KEY", "") or "").strip()
except Exception:
    secret_api_key = ""
# Ignore a placeholder in Streamlit secrets so a valid local .env key can still be used.
if secret_api_key and not ai_configuration(secret_api_key).get("configured"):
    secret_api_key = ""
env_ai_status = ai_configuration(secret_api_key or None)
runtime_api_key = ""
ai_status = env_ai_status

with st.sidebar:
    st.markdown("<div class='nova-brandline'><span class='nova-mark'>N</span><span>NOVA WORKSPACE</span></div>", unsafe_allow_html=True)
    st.caption("Sales intelligence · RSG challenge")
    st.markdown("---")
    st.markdown("#### Dataset workspace")
    st.caption("Import a CSV or Excel workbook. The first worksheet is used for Excel files.")
    with st.form("upload_form", clear_on_submit=False):
        upload = st.file_uploader("Upload sales data", type=["csv", "xlsx", "xls"], help="Required sales columns are listed in Data quality.")
        upload_clicked = st.form_submit_button("Validate & load into SQLite", type="primary", use_container_width=True)
    if upload_clicked:
        if upload is None:
            st.warning("Choose a file before loading.")
        else:
            try:
                incoming = pd.read_csv(upload) if upload.name.lower().endswith(".csv") else pd.read_excel(upload, sheet_name=0)
                with st.spinner("Validating schema and importing records…"):
                    report = load_dataframe(incoming, upload.name)
                st.session_state["upload_report"] = {"source": upload.name, **report}
                st.rerun()
            except Exception as exc:
                st.error(f"Import failed: {str(exc)[:350]}")
    active_meta = metadata()
    source = active_meta.get("source_name", "Challenge sample")
    st.markdown("---")
    st.markdown("#### Active data source")
    st.markdown(f"**{html.escape(source)}**")
    st.caption(f"{len(all_sales()):,} rows in SQLite")
    if st.button("Restore RSG sample dataset", use_container_width=True):
        initialize(CSV_PATH)
        st.toast("RSG sample data restored")
        st.rerun()
    st.markdown("---")
    st.markdown("#### AI query engine")
    runtime_api_key = st.text_input(
        "Override Gemini API key · session only",
        type="password",
        key="nova_runtime_gemini_key",
        placeholder="Optional: paste a valid API key here",
        help="Used only by this running app session. NOVA never writes this key to disk or shows it in logs. A valid key is required for open-ended AI-generated SQL.",
    ).strip()
    active_api_key = runtime_api_key or secret_api_key or None
    ai_status = ai_configuration(active_api_key)
    status_class = "nova-status-ok" if ai_status["configured"] else "nova-status-warn"
    status_text = "AI-to-SQL key detected" if ai_status["configured"] else "AI key missing / placeholder"
    st.markdown(f"<span class='nova-status {status_class}'>{status_text}</span>", unsafe_allow_html=True)
    st.caption(f"Model: {ai_status['model']} · key validity is confirmed only by a connection test" if ai_status["configured"] else "Open-ended questions require a valid GEMINI_API_KEY in this project's .env, Streamlit secrets, or the session-only field above.")
    if st.button("Test Gemini connection", use_container_width=True, key="nova_test_gemini"):
        with st.spinner("Checking Gemini credentials…"):
            connection_result = test_gemini_connection(active_api_key)
        st.session_state["nova_gemini_connection_result"] = connection_result
    if st.session_state.get("nova_gemini_connection_result"):
        connection_result = st.session_state["nova_gemini_connection_result"]
        (st.success if connection_result.get("ok") else st.error)(connection_result.get("message", "Connection test finished."))
    with st.expander("Metric definitions", expanded=False):
        st.markdown("**Recognized revenue** = Quantity × Unit price − Discount.")
        st.write("Only completed rows with a valid unit price contribute to recognized revenue. Returned rows and missing-price rows are excluded.")
        st.write("AI-generated SQL runs in a read-only SQLite sandbox with a single-table allowlist, a row cap, and an execution timeout.")

if "upload_report" in st.session_state:
    report = st.session_state.pop("upload_report")
    st.toast(f"Imported {report['loaded_rows']:,} rows · rejected {report['rejected_rows']:,}")

raw_df = all_sales()
if raw_df.empty:
    st.markdown("<div class='nova-hero'><div class='nova-brandline'>✦ NOVA WORKSPACE</div><div class='nova-hero-title'>NOVA : AI assisted business intelligence</div><p class='nova-hero-copy'>Upload a CSV or Excel sales table to explore business performance, ask questions in plain English, and inspect interactive reports.</p></div>", unsafe_allow_html=True)
    st.stop()

raw_df["Order_date"] = pd.to_datetime(raw_df["Order_date"], errors="coerce")
for col in ["Quantity", "Unit_price", "Discount_amount"]:
    raw_df[col] = pd.to_numeric(raw_df[col], errors="coerce")
raw_df["Revenue_INR"] = raw_df["Quantity"] * raw_df["Unit_price"] - raw_df["Discount_amount"]
raw_df["Eligible"] = raw_df["Status"].astype(str).str.lower().isin(["completed", "complete"]) & raw_df["Unit_price"].notna()
raw_df["Month"] = raw_df["Order_date"].dt.to_period("M").astype(str)

st.markdown(
    """
    <div class="nova-hero">
      <div class="nova-brandline">✦ NOVA WORKSPACE &nbsp; · &nbsp; BUSINESS ANALYTICS</div>
      <div class="nova-hero-title">NOVA : AI assisted business intelligence</div>
      <p class="nova-hero-copy">Ask business questions in plain English, inspect the SQL behind the numbers, and explore performance through interactive visual reports.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

# Results are based on the full active dataset. Dashboard filters are applied only to dashboards.
# The analyst panel stays on the landing page; dashboards are visible immediately below it.
left, right = st.columns([1.5, 1], gap="large")
with left:
    section_intro("✦ Ask NOVA", "Ask in plain English. With a valid Gemini key, NOVA generates a SQL query, runs it safely against SQLite, then explains the actual results.")
with right:
    status_class = "nova-status-ok" if ai_status["configured"] else "nova-status-warn"
    status_text = f"AI-to-SQL active · {ai_status['model']}" if ai_status["configured"] else "Local analytics · Gemini key not detected"
    st.markdown(f"<div style='text-align:right;padding-top:.45rem'><span class='nova-status {status_class}'>{html.escape(status_text)}</span></div>", unsafe_allow_html=True)
if not ai_status["configured"]:
    st.warning("AI-generated SQL is currently OFF because NOVA did not detect a usable Gemini key. The local fallback only understands common sales questions; open-ended questions need a valid key. Add it to this folder's .env or paste it in the sidebar, then click ‘Test Gemini connection’. No dashboards are disabled by this setting.")
suggestions = [
    "What is the total recognized revenue?",
    "Which product generated the most revenue and why?",
    "Show monthly revenue and month-over-month change",
    "Compare sales by region and sales channel",
    "Which products have high quantity but low revenue?",
    "Show transaction status counts and data-quality issues",
    "What percentage of revenue comes from each category?",
    "List the top 10 transactions by recognized revenue",
]
with st.container(border=True):
    with st.form("nova_question_form", clear_on_submit=True):
        question = st.text_area(
            "Business question",
            height=110,
            placeholder="Ask a question about the active sales data… e.g. Compare revenue by category and region",
            help="Ask in plain English about trends, products, regions, categories, channels, order counts, discounts, or data quality.",
        )
        choose_col, button_col = st.columns([3, 1])
        with choose_col:
            example = st.selectbox("Or start from a suggested analysis", ["Choose a suggestion…"] + suggestions)
        with button_col:
            st.markdown("<div style='height:1.65rem'></div>", unsafe_allow_html=True)
            submit = st.form_submit_button("Analyze question", type="primary", use_container_width=True)
    if submit:
        q = (question or "").strip() or (example if example != "Choose a suggestion…" else "")
        if not q:
            st.session_state["nova_last_result"] = {"question": "", "result": {"ok": False, "answer": "Enter a question or choose a suggestion.", "data": [], "sql": "", "intent": "unknown"}}
        else:
            try:
                with st.spinner("Planning query · validating SQL · reading SQLite · interpreting results…"):
                    result = answer_question(q, api_key=runtime_api_key or secret_api_key or None)
                st.session_state["nova_last_result"] = {"question": q, "result": result}
            except Exception as exc:
                st.session_state["nova_last_result"] = {
                    "question": q,
                    "result": {"ok": False, "answer": "NOVA could not finish the analysis. Review the diagnostic details and retry.", "data": [], "sql": "", "intent": "error", "diagnostic": type(exc).__name__},
                }
last = st.session_state.get("nova_last_result")
if last:
    st.markdown("<hr class='nova-separator'>", unsafe_allow_html=True)
    if last.get("question"):
        st.markdown(f"<div class='nova-kicker'>YOUR QUESTION</div><div style='font-size:1.05rem;font-weight:650;line-height:1.5;overflow-wrap:anywhere'>{html.escape(last['question'])}</div>", unsafe_allow_html=True)
    result = last["result"]
    if result.get("ok"):
        st.markdown(f"<div class='nova-answer'>{html.escape(str(result.get('answer','Analysis completed.')))}</div>", unsafe_allow_html=True)
        mode = result.get("mode", "deterministic")
        if mode == "gemini_sql":
            latency = result.get("execution_ms")
            st.caption("AI-generated SQL · read-only SQLite · answer grounded in returned rows" + (f" · {latency} ms query workflow" if latency is not None else ""))
        elif result.get("ai_notice"):
            st.warning(result["ai_notice"])
        elif mode == "deterministic_flexible":
            st.caption("Local SQL fallback · interpreted using safe templates; figures are calculated by SQLite")
        else:
            st.caption("Local SQL analytics · values computed from the active database")
        rows = result.get("data") or []
        result_df = pd.DataFrame(rows)
        if not result_df.empty:
            st.markdown("#### Result snapshot")
            info_cols = st.columns(3, gap="medium")
            info_cols[0].metric("Rows returned", f"{len(result_df):,}")
            info_cols[1].metric("Query engine", "Gemini SQL" if mode == "gemini_sql" else "Local SQL")
            info_cols[2].metric("Workflow latency", f"{result.get('execution_ms'):,} ms" if result.get("execution_ms") is not None else "Local")
            st.markdown("#### Interactive visualization")
            viz_key = hashlib.sha1(str(last.get("question", "")).encode("utf-8")).hexdigest()[:10]
            chart = dict(result.get("chart") or {})
            col_names = list(result_df.columns)
            numeric_names = [c for c in col_names if pd.api.types.is_numeric_dtype(result_df[c])]
            if not chart:
                preferred_x = next((c for c in col_names if str(c).lower() in {"month", "month label", "product", "region", "category", "channel", "sales_channel", "status"}), None)
                if preferred_x is None:
                    preferred_x = next((c for c in col_names if c not in numeric_names), col_names[0] if col_names else None)
                preferred_y = next((c for c in numeric_names if any(term in str(c).lower() for term in ("revenue", "sales", "amount", "units", "count", "quantity", "value"))), numeric_names[0] if numeric_names else None)
                chart = {"title": "Query results", "chart_type": "line" if preferred_x and "month" in str(preferred_x).lower() else ("bar" if len(result_df) >= 2 and preferred_x and preferred_y and preferred_x != preferred_y else "table"), "x_column": preferred_x, "y_column": preferred_y}
            if len(result_df) >= 2 and col_names:
                type_cols = st.columns([1.1, 1.4, 1.4], gap="medium")
                chart_options = ["Auto", "Bar", "Line", "Pie", "Scatter", "Table"]
                default_type = {"bar":"Bar", "line":"Line", "pie":"Pie", "scatter":"Scatter", "table":"Table"}.get(chart.get("chart_type", "table"), "Auto")
                with type_cols[0]:
                    chart_choice = st.selectbox("Chart type", chart_options, index=chart_options.index(default_type), key=f"nova_vis_type_{viz_key}")
                with type_cols[1]:
                    x_options = numeric_names if chart_choice == "Scatter" and numeric_names else col_names
                    default_x = chart.get("x_column") if chart.get("x_column") in x_options else x_options[0]
                    x_col = st.selectbox("Category / X axis", x_options, index=x_options.index(default_x), key=f"nova_vis_x_{viz_key}_{chart_choice.lower()}")
                with type_cols[2]:
                    if numeric_names:
                        default_y = chart.get("y_column") if chart.get("y_column") in numeric_names else numeric_names[0]
                        y_col = st.selectbox("Metric / Y axis", numeric_names, index=numeric_names.index(default_y), key=f"nova_vis_y_{viz_key}")
                    else:
                        y_col = None
                chosen_type = chart.get("chart_type", "bar") if chart_choice == "Auto" else chart_choice.lower()
                chart_override = {"title": chart.get("title") or "Query result", "chart_type": chosen_type, "x_column": x_col, "y_column": y_col}
                render_result_chart({**result, "chart": chart_override}, result_df)
            else:
                st.caption("This query returned a single result row, so NOVA displays a KPI/table instead of a misleading chart.")
            st.markdown("#### Supporting data")
            st.dataframe(result_df, use_container_width=True, hide_index=True, height=min(380, 42 + 36 * min(len(result_df), 9)))
            csv_bytes = result_df.to_csv(index=False).encode("utf-8-sig")
            st.download_button("Download query results (CSV)", csv_bytes, file_name="nova_query_results.csv", mime="text/csv")
        with st.expander("Query inspector · SQL executed", expanded=False):
            st.code(result.get("sql", "No SQL was needed."), language="sql")
            st.caption("AI proposes a single query; NOVA validates it, applies a SQLite read-only authorizer, limits execution time and output rows, and permits reads from the sales table only.")
        if result.get("diagnostic"):
            st.caption(f"Diagnostic category: {result['diagnostic']}")
    else:
        st.error(result.get("answer", "The question could not be analyzed."))
        if result.get("ai_notice"):
            st.info(result["ai_notice"])
        if result.get("diagnostic"):
            with st.expander("Technical details"):
                st.code(str(result["diagnostic"]))
else:
    st.markdown("#### Try one of these")
    qcols = st.columns(2)
    for idx, suggestion in enumerate(suggestions[:6]):
        with qcols[idx % 2]:
            if st.button(suggestion, key=f"suggest_{idx}", use_container_width=True):
                st.session_state["nova_last_result"] = {"question": suggestion, "result": answer_question(suggestion, api_key=runtime_api_key or secret_api_key or None)}
                st.rerun()
st.caption("Questions use the full active dataset, independently of dashboard filters. SQLite is the source of numeric truth; the model only helps translate the question into a safe query.")

# Dashboard workspace: overview is the default selected view, with performance, data explorer, and quality always available.
tabs = st.tabs(["Executive overview", "Performance analysis", "Data explorer", "Data quality"])

# Filters apply to the executive and performance views.
with tabs[0]:
    section_intro("▦ Executive overview", "A compact view of the business. Adjust the filters to refresh every metric and chart on the overview and performance tabs.")
    with st.container(border=True):
        f1, f2, f3, f4, f5 = st.columns([1.5, 1, 1, 1, 1.2])
        valid_dates = raw_df["Order_date"].dropna()
        min_date = valid_dates.min().date() if not valid_dates.empty else date.today()
        max_date = valid_dates.max().date() if not valid_dates.empty else date.today()
        default_date_range = (min_date, max_date) if min_date <= max_date else (date.today(), date.today())
        selected_dates = f1.date_input("Order date range", value=default_date_range, min_value=min_date, max_value=max_date, key="overview_dates")
        region_options = sorted(raw_df["Region"].dropna().astype(str).unique())
        category_options = sorted(raw_df["Category"].dropna().astype(str).unique())
        channel_options = sorted(raw_df["Sales_channel"].dropna().astype(str).unique())
        product_options = sorted(raw_df["Product"].dropna().astype(str).unique())
        selected_regions = f2.multiselect("Region", region_options, default=region_options, key="overview_regions")
        selected_categories = f3.multiselect("Category", category_options, default=category_options, key="overview_categories")
        selected_channels = f4.multiselect("Channel", channel_options, default=channel_options, key="overview_channels")
        selected_products = f5.multiselect("Product", product_options, default=product_options, key="overview_products", placeholder="All products")

    dashboard = raw_df.copy()
    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
        dashboard = dashboard[dashboard["Order_date"].dt.date.between(start_date, end_date)]
    for column, chosen in [("Region", selected_regions), ("Category", selected_categories), ("Sales_channel", selected_channels), ("Product", selected_products)]:
        dashboard = dashboard[dashboard[column].astype(str).isin(chosen)] if chosen else dashboard.iloc[0:0]
    eligible = dashboard[dashboard["Eligible"]].copy()
    revenue = float(eligible["Revenue_INR"].sum()) if not eligible.empty else 0.0
    orders = int(eligible["Transaction_Id"].nunique()) if not eligible.empty else 0
    units = float(eligible["Quantity"].sum()) if not eligible.empty else 0.0
    discounts = float(eligible["Discount_amount"].sum()) if not eligible.empty else 0.0
    average_order = revenue / orders if orders else 0.0
    valid_share = len(eligible) / len(dashboard) * 100 if len(dashboard) else 0.0
    st.markdown("#### ◈ Key performance indicators")
    kpis = [
        ("Recognized revenue", format_inr(revenue), "Completed sales after discounts"),
        ("Eligible transactions", f"{orders:,}", "Distinct transaction IDs"),
        ("Units sold", f"{units:,.0f}", "Completed rows with valid prices"),
        ("Average order value", format_inr(average_order), "Revenue divided by eligible transactions"),
        ("Discounts recorded", format_inr(discounts), "Discounts on eligible records"),
        ("Revenue-eligible rows", f"{valid_share:.1f}%", "Share of currently filtered rows"),
    ]
    for start in (0, 3):
        cols = st.columns(3, gap="medium")
        for col, (label, value, help_text) in zip(cols, kpis[start:start + 3]):
            with col:
                with st.container(border=True):
                    st.metric(label, value, help=help_text)
    if eligible.empty:
        st.info("No eligible completed sales match the current filters. Widen your date or dimension selections.")
    else:
        eligible["Month label"] = eligible["Order_date"].dt.to_period("M").astype(str)
        monthly = eligible.groupby("Month label", as_index=False).agg(Revenue=("Revenue_INR", "sum"), Units=("Quantity", "sum"), Transactions=("Transaction_Id", "nunique"))
        monthly["Month"] = pd.to_datetime(monthly["Month label"]).dt.strftime("%b %Y")
        monthly["Change (%)"] = monthly["Revenue"].pct_change() * 100
        product_perf = eligible.groupby("Product", as_index=False).agg(Revenue=("Revenue_INR", "sum"), Units=("Quantity", "sum")).sort_values("Revenue", ascending=False)
        category_perf = eligible.groupby("Category", as_index=False).agg(Revenue=("Revenue_INR", "sum")).sort_values("Revenue", ascending=False)
        region_perf = eligible.groupby("Region", as_index=False).agg(Revenue=("Revenue_INR", "sum")).sort_values("Revenue", ascending=False)
        channel_perf = eligible.groupby("Sales_channel", as_index=False).agg(Revenue=("Revenue_INR", "sum")).sort_values("Revenue", ascending=False)
        a, b = st.columns(2, gap="large")
        with a:
            fig = px.area(monthly, x="Month", y="Revenue", markers=True, title="Revenue trend over time", labels={"Month": "Order month", "Revenue": "Recognized revenue (₹)"})
            fig.update_traces(line_color="#4f46e5", fillcolor="rgba(79,70,229,.12)")
            fig.update_layout(height=360, margin=dict(l=12, r=12, t=60, b=10), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f", gridcolor="#e8edf5")
            fig.update_xaxes(title="Order month", showgrid=False)
            st.plotly_chart(fig, use_container_width=True)
        with b:
            fig = px.bar(product_perf.head(8).sort_values("Revenue"), x="Revenue", y="Product", orientation="h", title="Top products by revenue", text="Revenue", labels={"Revenue": "Recognized revenue (₹)", "Product": "Product"}, color="Revenue", color_continuous_scale=["#c7d2fe", "#4338ca"])
            fig.update_traces(texttemplate="₹%{x:,.0f}", textposition="outside", cliponaxis=False)
            fig.update_layout(height=360, margin=dict(l=12, r=60, t=60, b=10), coloraxis_showscale=False, paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            fig.update_xaxes(tickprefix="₹", tickformat=",.0f", gridcolor="#e8edf5")
            fig.update_yaxes(title="")
            st.plotly_chart(fig, use_container_width=True)
        st.markdown("#### Revenue mix")
        c, d, e = st.columns(3, gap="large")
        with c:
            fig = px.pie(category_perf, names="Category", values="Revenue", hole=.5, title="Revenue by category")
            fig.update_layout(height=330, margin=dict(l=8, r=8, t=58, b=8), paper_bgcolor="#ffffff", legend_title_text="Category")
            fig.update_traces(textinfo="percent+label", hovertemplate="%{label}<br>₹%{value:,.0f}<extra></extra>")
            st.plotly_chart(fig, use_container_width=True)
        with d:
            fig = px.bar(region_perf, x="Region", y="Revenue", title="Revenue by region", labels={"Region": "Region", "Revenue": "Recognized revenue (₹)"}, text_auto=".2s")
            fig.update_traces(marker_color="#0f766e", hovertemplate="%{x}<br>₹%{y:,.0f}<extra></extra>")
            fig.update_layout(height=330, margin=dict(l=10, r=10, t=58, b=8), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f", gridcolor="#e8edf5")
            st.plotly_chart(fig, use_container_width=True)
        with e:
            fig = px.bar(channel_perf, x="Sales_channel", y="Revenue", title="Revenue by sales channel", labels={"Sales_channel": "Sales channel", "Revenue": "Recognized revenue (₹)"}, text_auto=".2s")
            fig.update_traces(marker_color="#6474d9", hovertemplate="%{x}<br>₹%{y:,.0f}<extra></extra>")
            fig.update_layout(height=330, margin=dict(l=10, r=10, t=58, b=8), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff", showlegend=False)
            fig.update_yaxes(tickprefix="₹", tickformat=",.0f", gridcolor="#e8edf5")
            st.plotly_chart(fig, use_container_width=True)
        if not region_perf.empty:
            top_region = region_perf.iloc[0]
            top_product = product_perf.iloc[0]
            top_category = category_perf.iloc[0]
            call_cols = st.columns(3)
            for col, title, body in [
                (call_cols[0], "Leading region", f"{top_region['Region']} · {format_inr(top_region['Revenue'])}"),
                (call_cols[1], "Leading product", f"{top_product['Product']} · {format_inr(top_product['Revenue'])}"),
                (call_cols[2], "Leading category", f"{top_category['Category']} · {format_inr(top_category['Revenue'])}"),
            ]:
                with col, st.container(border=True):
                    st.markdown(f"<div class='nova-kicker'>{html.escape(title)}</div><div style='font-size:1.05rem;font-weight:700;overflow-wrap:anywhere'>{html.escape(body)}</div>", unsafe_allow_html=True)

with tabs[1]:
    section_intro("Performance analysis", "Compare the mix, pace, and shape of sales performance using the same filters selected in Executive overview.")
    st.info("Adjust the filters on the Executive overview tab; these performance charts update from the same selected data.")
    # Reconstruct same filters from session state; defaults are all selected.
    eligible_perf = raw_df.copy()
    dates_state = st.session_state.get("overview_dates")
    if isinstance(dates_state, (tuple, list)) and len(dates_state) == 2:
        eligible_perf = eligible_perf[eligible_perf["Order_date"].dt.date.between(dates_state[0], dates_state[1])]
    for col_name, state_name in [("Region", "overview_regions"), ("Category", "overview_categories"), ("Sales_channel", "overview_channels"), ("Product", "overview_products")]:
        state_values = st.session_state.get(state_name)
        if state_values is not None:
            eligible_perf = eligible_perf[eligible_perf[col_name].astype(str).isin(state_values)] if state_values else eligible_perf.iloc[0:0]
    eligible_perf = eligible_perf[eligible_perf["Eligible"]].copy()
    if eligible_perf.empty:
        st.info("No eligible sales match the active dashboard filters.")
    else:
        eligible_perf["Month"] = eligible_perf["Order_date"].dt.to_period("M").astype(str)
        monthly_perf = eligible_perf.groupby("Month", as_index=False).agg(Revenue=("Revenue_INR", "sum"), Units=("Quantity", "sum"), Transactions=("Transaction_Id", "nunique"))
        monthly_perf["Month label"] = pd.to_datetime(monthly_perf["Month"]).dt.strftime("%b %Y")
        monthly_perf["Revenue change (%)"] = monthly_perf["Revenue"].pct_change() * 100
        f1, f2 = st.columns(2, gap="large")
        with f1:
            fig = px.line(monthly_perf, x="Month label", y="Units", markers=True, title="Units sold by month", labels={"Month label": "Order month", "Units": "Units sold"})
            fig.update_traces(line_color="#0f766e", line_width=3)
            fig.update_layout(height=350, margin=dict(l=8,r=8,t=58,b=10), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            fig.update_yaxes(gridcolor="#e8edf5")
            st.plotly_chart(fig, use_container_width=True)
        with f2:
            fig = px.bar(monthly_perf.dropna(subset=["Revenue change (%)"]), x="Month label", y="Revenue change (%)", title="Month-over-month revenue change", labels={"Month label":"Order month", "Revenue change (%)":"Change vs previous month (%)"}, text_auto=".1f")
            fig.add_hline(y=0, line_color="#64748b", line_width=1)
            fig.update_traces(marker_color="#4f46e5", hovertemplate="%{x}<br>%{y:+.2f}%<extra></extra>")
            fig.update_layout(height=350, margin=dict(l=8,r=8,t=58,b=10), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            fig.update_yaxes(ticksuffix="%", gridcolor="#e8edf5")
            st.plotly_chart(fig, use_container_width=True)
        g1, g2 = st.columns(2, gap="large")
        with g1:
            heat = eligible_perf.pivot_table(index="Region", columns="Category", values="Revenue_INR", aggfunc="sum", fill_value=0)
            fig = px.imshow(heat, aspect="auto", color_continuous_scale="Blues", text_auto=".2s", title="Revenue matrix · region × category", labels={"x":"Category", "y":"Region", "color":"Revenue (₹)"})
            fig.update_layout(height=350, margin=dict(l=8,r=8,t=60,b=10), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            st.plotly_chart(fig, use_container_width=True)
        with g2:
            units_perf = eligible_perf.groupby("Product", as_index=False).agg(Units=("Quantity", "sum")).sort_values("Units", ascending=True)
            fig = px.bar(units_perf.tail(10), x="Units", y="Product", orientation="h", title="Products ranked by units sold", labels={"Units":"Units sold", "Product":"Product"}, text_auto=".0f")
            fig.update_traces(marker_color="#0f766e", textposition="outside", cliponaxis=False)
            fig.update_layout(height=350, margin=dict(l=8,r=40,t=60,b=10), paper_bgcolor="#ffffff", plot_bgcolor="#ffffff")
            fig.update_xaxes(gridcolor="#e8edf5")
            st.plotly_chart(fig, use_container_width=True)

with tabs[2]:
    section_intro("Data explorer", "Inspect detailed transactions or download summarized data for further work in Excel, Python, or Power BI.")
    explore = raw_df.copy()
    left, right = st.columns([1, 2], gap="large")
    with left:
        search = st.text_input("Search transactions", placeholder="Transaction ID, product, region…")
        status_options = sorted(explore["Status"].dropna().astype(str).unique())
        status_filter = st.multiselect("Transaction status", status_options, default=status_options)
    if search.strip():
        mask = pd.Series(False, index=explore.index)
        for col in ["Transaction_Id", "Product", "Region", "Category", "Sales_channel"]:
            mask = mask | explore[col].astype(str).str.contains(search.strip(), case=False, na=False)
        explore = explore[mask]
    explore = explore[explore["Status"].astype(str).isin(status_filter)] if status_filter else explore.iloc[0:0]
    display = explore[["Transaction_Id", "Order_date", "Product", "Category", "Region", "Sales_channel", "Quantity", "Unit_price", "Discount_amount", "Status", "Revenue_INR", "Eligible"]].copy()
    display["Order_date"] = display["Order_date"].dt.strftime("%Y-%m-%d")
    display = display.rename(columns={
        "Transaction_Id":"Transaction ID", "Order_date":"Order date", "Category":"Category", "Sales_channel":"Sales channel",
        "Quantity":"Quantity", "Unit_price":"Unit price (₹)", "Discount_amount":"Discount (₹)",
        "Revenue_INR":"Calculated row revenue (₹)", "Eligible":"Included in recognized revenue",
    })
    with right:
        st.metric("Rows matching search", f"{len(display):,}")
        st.download_button("Download filtered transactions CSV", display.to_csv(index=False).encode("utf-8-sig"), "nova_transactions.csv", "text/csv")
    st.dataframe(display, use_container_width=True, hide_index=True, height=470)
    st.markdown("#### Aggregated downloads")
    ok_data = raw_df[raw_df["Eligible"]].copy()
    dc1, dc2, dc3 = st.columns(3)
    if not ok_data.empty:
        product_export = ok_data.groupby("Product", as_index=False).agg(Revenue_INR=("Revenue_INR", "sum"), Units=("Quantity", "sum"), Transactions=("Transaction_Id", "nunique"))
        month_export = ok_data.groupby("Month", as_index=False).agg(Revenue_INR=("Revenue_INR", "sum"), Units=("Quantity", "sum"), Transactions=("Transaction_Id", "nunique"))
        region_export = ok_data.groupby("Region", as_index=False).agg(Revenue_INR=("Revenue_INR", "sum"), Units=("Quantity", "sum"), Transactions=("Transaction_Id", "nunique"))
        dc1.download_button("Product summary CSV", product_export.to_csv(index=False).encode("utf-8-sig"), "nova_product_summary.csv", "text/csv", use_container_width=True)
        dc2.download_button("Monthly summary CSV", month_export.to_csv(index=False).encode("utf-8-sig"), "nova_monthly_summary.csv", "text/csv", use_container_width=True)
        dc3.download_button("Regional summary CSV", region_export.to_csv(index=False).encode("utf-8-sig"), "nova_region_summary.csv", "text/csv", use_container_width=True)

with tabs[3]:
    section_intro("✓ Data quality & definitions", "Understand which records contribute to recognized revenue, and how NOVA treats invalid or incomplete inputs.")
    quality = data_quality()
    quality_metrics = [
        ("Source rows", quality["source_rows"]), ("Rows loaded", quality["loaded_rows"]),
        ("Rejected core rows", quality["rejected_rows"]), ("Completed rows", quality["completed_rows"]),
        ("Returned rows", quality["returned_rows"]),
        ("Missing / invalid prices", quality["missing_unit_price"] + quality.get("invalid_price_rows", 0)),
    ]
    for start in (0, 3):
        cols = st.columns(3, gap="medium")
        for col, (label, value) in zip(cols, quality_metrics[start:start + 3]):
            with col, st.container(border=True):
                st.metric(label, f"{value:,}")
    st.markdown("#### Calculation policy")
    with st.container(border=True):
        st.markdown("**Recognized revenue = Quantity × Unit price − Discount amount**")
        st.markdown("- Only `Completed` / `Complete` rows with a valid unit price are included in recognized revenue.")
        st.markdown("- Returned transactions, other statuses, and missing or invalid prices remain visible for quality review but do not contribute to revenue KPIs.")
        st.markdown("- Zero-quantity completed rows contribute zero revenue. These figures are revenue, not profit.")
        st.markdown("- Invalid dates, missing key dimensions, negative quantities, and negative discounts are rejected during upload.")
        st.markdown("- Dashboard filters update the overview and performance views. The AI Analyst runs against the full active SQLite dataset.")
        st.markdown("- AI-generated SQL is accepted only as a single read-only query against the `sales` table. SQLite authorizer rules deny writes and access to other tables.")
    with st.expander("Required upload columns", expanded=False):
        st.write("Transaction ID, order date, product, category, region, sales channel, quantity, unit price, discount amount, and status. Common aliases such as `date`, `transaction id`, `product_name`, `qty`, `price`, and `channel` are normalized automatically.")
    with st.expander("AI setup status", expanded=False):
        st.write(ai_status["message"])
        st.code("GEMINI_API_KEY=your_gemini_api_key_here\nGEMINI_MODEL=gemini-3.8-flash", language="dotenv")
        st.caption("Keep the real .env file local and out of public GitHub repositories. The distributed ZIP uses a placeholder rather than embedding credentials.")

st.markdown("<hr class='nova-separator'>", unsafe_allow_html=True)
st.markdown("<div class='small-label'>NOVA · RSG Graduate Engineer Trainee challenge prototype · Read-only AI analytics · Verify business metric policies before production deployment.</div>", unsafe_allow_html=True)
