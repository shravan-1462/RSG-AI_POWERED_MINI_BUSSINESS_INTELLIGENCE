# NOVA AI question troubleshooting and dashboard update

## What changed
- Added a sidebar OpenAI connection test that never prints or logs the API key.
- Added support for Streamlit secrets in addition to the local `.env` file and a session-only key override.
- Clearer UI status distinguishes a detected key from a verified connection.
- Kept the Executive Overview, Performance Analysis, Data Explorer, and Data Quality dashboards in the application.
- Updated documentation to describe the actual low-latency workflow: one OpenAI call for SQL planning, safe read-only SQLite execution, then a local factual summary from the returned rows.
- Added a regression test ensuring a placeholder key is rejected before any network request.

## Important credential finding
The `.env` file in the working project copy did not contain a usable-looking OpenAI API key; it contained a placeholder-length value. A valid key is therefore not included in the ZIP. For security, `.env` is excluded from the package. Copy `.env.example` to `.env`, add a valid key locally, and use **Test OpenAI connection** in the sidebar before asking open-ended questions.

## Validation
- Python compilation: passed for `app.py`, `db.py`, and `api.py`.
- Automated tests: 25 passed.
- SQL execution is read-only and constrained to the `sales` table, with blocked mutation statements, timeout, and row cap.
- Live OpenAI requests were not tested because the project copy did not contain a usable key.
