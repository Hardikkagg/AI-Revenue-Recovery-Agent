"""Optional helper: load historical_events.csv into SQLite using existing models.

This does not change the database schema. Extra CSV fields are stored as JSON
in Event.details / Action.details for later use.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BACKEND_DIR = PROJECT_ROOT / "backend"
DEFAULT_CSV = PROJECT_ROOT / "data" / "historical_events.csv"

sys.path.insert(0, str(BACKEND_DIR))

from app.database import SessionLocal, init_db  # noqa: E402
from app.models import Action, Customer, Event, RecoveryCase  # noqa: E402


def _bool(value: str) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def seed(csv_path: Path, limit: int | None = None) -> int:
    init_db()
    inserted = 0
    customers_by_id: dict[int, Customer] = {}

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))

    if limit is not None:
        rows = rows[:limit]

    db = SessionLocal()
    try:
        for row in rows:
            customer_id = int(row["customer_id"])
            customer = customers_by_id.get(customer_id)
            if customer is None:
                customer = Customer(
                    name=f"Customer {customer_id}",
                    email=f"customer{customer_id}@example.com",
                )
                db.add(customer)
                db.flush()
                customers_by_id[customer_id] = customer

            recovered = _bool(row["recovered"])
            case = RecoveryCase(
                customer_id=customer.id,
                amount=float(row["amount"]),
                currency="USD",
                status="recovered" if recovered else "open",
                failure_reason=row["failure_reason"],
            )
            db.add(case)
            db.flush()

            db.add(
                Event(
                    recovery_case_id=case.id,
                    event_type=row["event_type"],
                    details=json.dumps(row),
                )
            )
            db.add(
                Action(
                    recovery_case_id=case.id,
                    action_type=row["recovery_action"],
                    status="succeeded" if recovered else "failed",
                    details=json.dumps(
                        {
                            "recovery_time": row["recovery_time"],
                            "recovered_amount": row["recovered_amount"],
                        }
                    ),
                )
            )
            inserted += 1

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()

    return inserted


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed SQLite from historical_events.csv")
    parser.add_argument("--csv", type=Path, default=DEFAULT_CSV)
    parser.add_argument("--limit", type=int, default=None, help="Optional row cap for smoke tests")
    args = parser.parse_args()
    count = seed(args.csv, limit=args.limit)
    print(f"Seeded {count} historical events into SQLite")


if __name__ == "__main__":
    main()
