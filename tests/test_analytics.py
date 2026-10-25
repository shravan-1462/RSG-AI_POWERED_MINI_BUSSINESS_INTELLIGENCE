import pandas as pd
import pytest
from db import initialize, answer_question, metrics, load_dataframe, all_sales

@pytest.fixture(autouse=True)
def setup_db():
    initialize()


def test_total_revenue():
    r = answer_question("What is the total revenue?")
    assert r["ok"] and "1,439,200" in r["answer"]


def test_top_product():
    r = answer_question("Which product generated the highest revenue?")
    assert r["ok"] and "Monitor" in r["answer"]


def test_monthly_trend():
    r = answer_question("What is the monthly revenue trend?")
    assert r["ok"] and len(r["data"]) == 6


def test_top_region():
    r = answer_question("Which region generated the highest sales?")
    assert r["ok"] and "South" in r["answer"]


def test_month_comparison_full_names():
    r = answer_question("How did revenue change between January and February?")
    assert r["ok"] and "February" in r["answer"]


def test_month_comparison_abbreviations():
    r = answer_question("Compare Jan vs Mar")
    assert r["ok"] and "March" in r["answer"]


def test_question_variations():
    cases = [
        "show sales by category", "Which sales channel performed best?",
        "How many units were sold?", "What is the average order value?",
        "Show discounts by total", "Show transaction status breakdown",
        "Which product sold the most units?", "Show sales by region"
    ]
    assert all(answer_question(q)["ok"] for q in cases)


def test_single_month_revenue():
    r = answer_question("What was revenue in March?")
    assert r["ok"] and "March" in r["answer"]


def test_unsupported_question():
    r = answer_question("Tell me tomorrow's weather")
    assert not r["ok"]


def test_empty_question():
    assert not answer_question(" ")["ok"]


def test_destructive_sql_rejected():
    assert not answer_question("DROP TABLE sales")["ok"]


def test_metrics():
    m = metrics()
    assert m["transactions"] == 49
    assert m["revenue"] == pytest.approx(1439200.0)


def test_upload_with_alias_columns_and_duplicate_date_column():
    df = pd.DataFrame({
        "Transaction_Id": ["X1"], "Order_date": ["03-01-2026"], "date": ["2026-01-03"],
        "Product": ["Widget"], "Category": ["General"], "Region": ["North"],
        "Sales_channel": ["Online"], "Quantity": [2], "Unit_price": [100],
        "Discount_amount": [5], "Status": ["Completed"]
    })
    report = load_dataframe(df, "test-upload.csv")
    assert report["source_rows"] == 1
    assert report["loaded_rows"] == 1
    assert len(all_sales()) == 1
    assert metrics()["revenue"] == pytest.approx(195.0)


def test_upload_alias_only_schema():
    df = pd.DataFrame({
        "transaction id": ["X2"], "date": ["2026-02-05"], "product_name": ["Widget"],
        "category": ["General"], "region": ["East"], "channel": ["Retail"],
        "qty": [3], "price": [50], "discount": [0], "status": ["Completed"]
    })
    report = load_dataframe(df, "alias-upload.csv")
    assert report["loaded_rows"] == 1
    assert metrics()["revenue"] == pytest.approx(150.0)


def test_highest_revenue_month():
    r = answer_question("Which month had the highest sales?")
    assert r["ok"] and "May 2026" in r["answer"] and "318,500" in r["answer"]


def test_lowest_revenue_month():
    r = answer_question("Which month had the lowest revenue?")
    assert r["ok"] and "January 2026" in r["answer"] and "210,250" in r["answer"]


def test_ai_sql_executor_allows_read_only_count_and_aggregate():
    from db import _execute_generated_sql
    count_df = _execute_generated_sql("SELECT COUNT(*) AS n FROM sales")
    assert int(count_df.iloc[0]["n"]) == 51
    revenue_df = _execute_generated_sql(
        "SELECT ROUND(SUM(Quantity * Unit_price - Discount_amount), 2) AS revenue "
        "FROM sales WHERE lower(Status) IN ('completed','complete') AND Unit_price IS NOT NULL"
    )
    assert float(revenue_df.iloc[0]["revenue"]) == pytest.approx(1439200.0)


def test_ai_sql_validator_rejects_mutations_and_multiple_statements():
    from db import _validate_generated_sql
    with pytest.raises(ValueError):
        _validate_generated_sql("DELETE FROM sales")
    with pytest.raises(ValueError):
        _validate_generated_sql("SELECT * FROM sales; SELECT * FROM sales")


def test_ai_sql_executor_blocks_other_tables():
    from db import _execute_generated_sql
    with pytest.raises(ValueError):
        _execute_generated_sql("SELECT name FROM sqlite_master")


def test_ai_first_question_flow_generates_executes_and_summarizes(monkeypatch):
    import db
    monkeypatch.setenv("GEMINI_API_KEY", "sk-test-key-" + "x" * 40)
    monkeypatch.setattr(db, "_openai_client", lambda: object())
    db._cached_query_plan.cache_clear()
    monkeypatch.setattr(db, "_llm_generate_sql", lambda client, question: {
        "sql": "SELECT Product AS product, ROUND(SUM(Quantity * Unit_price - Discount_amount), 2) AS revenue FROM sales WHERE lower(Status) IN ('completed','complete') AND Unit_price IS NOT NULL GROUP BY Product ORDER BY revenue DESC LIMIT 5",
        "title": "Top products by revenue", "chart_type": "bar", "x_column": "product", "y_column": "revenue"
    })
    result = db.answer_question("Show me the top products by realized sales and explain the mix")
    assert result["ok"] is True
    assert result["mode"] == "gemini_sql"
    assert result["intent"] == "ai_generated_sql"
    assert "Monitor" in result["answer"] and "473,000" in result["answer"]
    assert result["data"][0]["product"] == "Monitor"
    assert result["execution_ms"] >= 0
    assert result["chart"]["chart_type"] == "bar"


def test_multi_dimension_question_uses_safe_group_by_fallback():
    r = answer_question("Show total sales by region and product")
    assert r["ok"]
    assert r["mode"] == "deterministic_flexible"
    assert set(r["data"][0]) == {"region", "product", "revenue"}
    assert "GROUP BY Region, Product" in r["sql"]


def test_question_can_break_down_sales_by_channel_and_category():
    r = answer_question("Compare revenue by sales channel and category")
    assert r["ok"]
    assert len(r["data"]) > 1
    assert "channel" in r["data"][0]
    assert "category" in r["data"][0]


def test_all_write_statement_families_are_rejected():
    from db import _validate_generated_sql
    for sql in [
        "INSERT INTO sales VALUES (1)",
        "UPDATE sales SET Quantity=0",
        "DELETE FROM sales",
        "ALTER TABLE sales ADD COLUMN hack TEXT",
        "DROP TABLE sales",
        "CREATE TABLE x AS SELECT * FROM sales",
        "PRAGMA table_info(sales)",
    ]:
        with pytest.raises(ValueError):
            _validate_generated_sql(sql)


def test_safe_fallback_handles_more_natural_wording():
    cases = [
        "Could you break down sales across categories?",
        "Give me a monthly breakdown of turnover",
        "How much discount amount was given?",
        "Compare revenue across the sales channels",
    ]
    assert all(answer_question(q)["ok"] for q in cases)


def test_openai_connection_rejects_placeholder_without_network():
    from db import test_gemini_connection
    result = test_gemini_connection("your_gemini_api_key_here")
    assert not result["ok"]
    assert "No usable Gemini API key" in result["message"]
