# NOVA — AI Business Intelligence Assistant

NOVA is a polished Streamlit application for exploring sales data and asking plain-English business questions. It stores the active dataset in SQLite, uses Gemini to draft a SQL query and explain the returned results when a valid key is configured, and renders the query results in interactive charts and tables. A deterministic fallback is included for common questions when Gemini is not configured or unavailable.

## What it includes

- **AI analyst:** question → AI-generated SQL → validation → read-only SQLite execution → AI explanation grounded in returned rows.
- **Safe SQL execution:** one `SELECT`/`WITH ... SELECT` statement only; SQLite read-only connection; database authorizer permits reads from `sales` only; write operations and system-table access are denied; output is capped at 200 rows; execution has a time limit.
- **Professional dashboard:** responsive layout, wrapped labels, six KPI tiles arranged for readability, monthly trends, revenue mix, product/region/channel rankings, month-over-month change, units sold, and region/category heatmap.
- **Interactive result output:** model-selected chart type (bar, line, pie, scatter, or table), supporting result table, downloadable result CSV, and SQL audit panel.
- **Data upload:** CSV, XLSX and XLS uploads, common column aliases, validation report, SQLite storage, and ability to restore the original RSG sample.
- **Filtering and exploration:** date range, region, category, channel, product, transaction search, status filter, table downloads, and data-quality summaries.
- **API:** FastAPI endpoints `/health`, `/metrics`, and `/ask`.
- **Testing:** regression tests for analytics, data imports, read-only SQL controls, and a mocked AI-generated-query workflow.

## Run locally (macOS, Linux, or Windows)

Python 3.10+ is recommended.

```bash
python -m venv .venv
# macOS / Linux
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Create a local `.env` file from the template, then edit it with your own valid Gemini API key from Google AI Studio:

```bash
cp .env.example .env
```

`.env` should contain:

```dotenv
GEMINI_API_KEY=your_actual_gemini_api_key_here
GEMINI_MODEL=gemini-3.8-flash
```

Do not commit `.env` or a real API key to GitHub. `.gitignore` excludes `.env`. Keep `.env` local and private; the ZIP package includes `.env.example` only.

Start NOVA:

```bash
streamlit run app.py
```

Streamlit normally opens at `http://localhost:8501`.

### How AI questioning works

With a valid `GEMINI_API_KEY`, NOVA sends the question and known sales schema/business metric rules to the configured Gemini model. The model returns JSON containing one SQL query and chart metadata. NOVA validates and executes the SQL in a read-only SQLite sandbox, then summarizes the actual returned rows locally to minimize latency and avoid a second model call. SQL, supporting rows, and an interactive chart/table are shown to the user.

The model is not allowed to write to the database or access other tables. Query validation includes a single-statement check; SQLite additionally enforces read-only access, a table/column allowlist, timeout and output row cap. Never treat this prototype as a substitute for authentication, rate limiting, monitoring, privacy review, or deployment hardening.

If the API key is missing, still a placeholder, invalid, or not reachable, NOVA uses a deterministic parser for common supported questions. When the question is outside that parser's coverage and AI is unavailable, it returns a clear unsupported/error response instead of inventing an answer. The sidebar includes **Test Gemini connection**. A key-shaped string is not enough: the connection test confirms whether Gemini accepts the key. If this test fails, open-ended questions cannot use the LLM until the key, network, model access, and API billing are corrected. The app still includes a deterministic fallback for common supported questions.

## Example questions

- `What is the total recognized revenue?`
- `Which product generated the most revenue and why?`
- `Show monthly revenue and month-over-month change`
- `Compare sales by region and sales channel`
- `Which products have high quantity but low revenue?`
- `What percentage of revenue comes from each category?`
- `List the top 10 transactions by recognized revenue`
- `Show transaction status counts and data-quality issues`

## Upload schema and validation

The uploaded table should contain these fields (common aliases and variations are normalized):

- `Transaction_Id`
- `Order_date`
- `Product`
- `Category`
- `Region`
- `Sales_channel`
- `Quantity`
- `Unit_price`
- `Discount_amount`
- `Status`

Examples of recognized aliases include `transaction id`, `date`, `product_name`, `channel`, `qty`, `price`, and `discount`. Excel files import the first worksheet. Upload replaces the active SQLite `sales` table; use **Restore RSG sample dataset** in the sidebar to restore the supplied data.

Invalid dates, missing essential identifiers/dimensions, negative quantities, and negative discounts are rejected. Rows with missing or negative unit prices are retained with a missing price for data-quality inspection but excluded from revenue calculations.

## API

Open a second terminal, activate the environment, then run:

```bash
uvicorn api:app --reload
```

- `GET http://127.0.0.1:8000/health`
- `GET http://127.0.0.1:8000/metrics`
- `POST http://127.0.0.1:8000/ask` with JSON body `{"question":"What is the total revenue?"}`
- API explorer: `http://127.0.0.1:8000/docs`

## Automated tests

```bash
python -m pytest -q
```

The tests do not require a Gemini API key. The AI workflow test mocks the model responses but executes the generated SQL against the actual SQLite database and validates the extracted results. To validate live Gemini operation, configure a valid key and submit questions in the app.

## Architecture

```text
CSV / XLSX / XLS
       │
       ▼
Pandas validation + schema normalization
       │
       ▼
SQLite table: sales
       │
       ├── Gemini text-to-SQL planner ──┐
       │                                ▼
       └── deterministic fallback   SQL validation
                                        │
                                SQLite read-only sandbox
                                        │
                                result rows + SQL audit
                                        │
                          Gemini result-grounded summary
                                        │
                       Streamlit interactive charts/tables
                                        │
                               FastAPI /ask endpoint
```

## Revenue definition and supplied-data baseline

**Recognized revenue = Quantity × Unit price − Discount amount.** Only `Completed`/`Complete` rows with a valid unit price are included. Returned records and rows with missing/invalid prices do not contribute. These are prototype assumptions and should be confirmed with a business owner before production use. Revenue is not profit.

Calculated from the supplied challenge CSV:

| Metric | Value |
|---|---:|
| Source rows | 51 |
| Completed rows | 50 |
| Returned rows | 1 |
| Missing unit-price rows | 1 |
| Rows contributing to revenue | 49 |
| Recognized revenue | ₹1,439,200 |
| Top product | Monitor — ₹473,000 |
| Top region | South — ₹411,200 |
| Top sales channel | Online — ₹746,750 |
| Jan 2026 revenue | ₹210,250 |
| Feb 2026 revenue | ₹234,600 |
| Mar 2026 revenue | ₹223,900 |
| Apr 2026 revenue | ₹240,700 |
| May 2026 revenue | ₹318,500 |
| Jun 2026 revenue | ₹211,250 |

Dashboard filters apply to overview and performance charts. The AI analyst queries the full active SQLite dataset and states that scope in the interface.

## Limitations

- This is a local prototype with no login, user roles, or multi-user permissions.
- The AI query is constrained, but generated SQL can still choose a semantically incorrect interpretation; review the SQL and results.
- Gemini use requires a valid API key, an available model, network access, and appropriate API/account access. No live API credentials are included in the package.
- Before production, add authentication, secrets management, privacy safeguards, rate limits, audit logging, backups, and stronger dataset-level governance.

## AI development reflection — personalize before submission

Edit these points to accurately describe your own experience before submitting the project:

1. Which AI tools you used.
2. How AI supported development.
3. Problems you personally encountered.
4. How you debugged and tested the application.
5. What you would improve with another day of work.
