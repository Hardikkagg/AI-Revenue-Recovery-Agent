"""Tests for the synthetic historical events dataset."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
CSV_PATH = PROJECT_ROOT / "data" / "historical_events.csv"

sys.path.insert(0, str(SCRIPTS_DIR))

from generate_data import (  # noqa: E402
    EVENT_TYPES,
    REQUIRED_FIELDS,
    generate_rows,
    parse_bool,
)

MIN_ROWS = 2000


def _load_csv() -> list[dict]:
    assert CSV_PATH.exists(), f"Missing dataset: {CSV_PATH}"
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_generator_creates_at_least_2000_rows() -> None:
    rows = generate_rows(n=2000, seed=1)
    assert len(rows) >= MIN_ROWS


def test_generated_csv_has_at_least_2000_rows() -> None:
    rows = _load_csv()
    assert len(rows) >= MIN_ROWS


def test_all_three_event_types_exist() -> None:
    rows = _load_csv()
    types = {row["event_type"] for row in rows}
    assert set(EVENT_TYPES).issubset(types)


def test_required_fields_exist() -> None:
    rows = _load_csv()
    assert rows
    assert tuple(rows[0].keys()) == REQUIRED_FIELDS
    for row in rows:
        for field in REQUIRED_FIELDS:
            assert field in row
            assert row[field] != ""


def test_unrecovered_rows_have_zero_recovered_amount() -> None:
    rows = _load_csv()
    unrecovered = [row for row in rows if not parse_bool(row["recovered"])]
    assert unrecovered
    for row in unrecovered:
        assert float(row["recovered_amount"]) == 0.0


def test_both_recovered_and_non_recovered_examples_exist() -> None:
    rows = _load_csv()
    recovered = [row for row in rows if parse_bool(row["recovered"])]
    unrecovered = [row for row in rows if not parse_bool(row["recovered"])]
    assert recovered
    assert unrecovered


def test_recovered_amount_matches_amount_when_recovered() -> None:
    rows = _load_csv()
    recovered = [row for row in rows if parse_bool(row["recovered"])]
    exact = sum(1 for row in recovered if float(row["recovered_amount"]) == float(row["amount"]))
    assert exact / len(recovered) >= 0.75
    for row in recovered:
        assert float(row["recovered_amount"]) > 0
        assert float(row["recovered_amount"]) <= float(row["amount"]) + 0.001


def test_event_type_fields_are_internally_consistent() -> None:
    rows = _load_csv()
    for row in rows:
        if row["event_type"] == "checkout_abandonment":
            assert float(row["cart_value"]) > 0
            assert int(row["checkout_visits"]) >= 1
            assert int(row["subscription_age"]) == 0
        elif row["event_type"] == "subscription_failure":
            assert int(row["subscription_age"]) >= 1
            assert float(row["cart_value"]) == 0.0
        elif row["event_type"] == "payment_failure":
            assert int(row["subscription_age"]) == 0
            assert row["failure_reason"]
