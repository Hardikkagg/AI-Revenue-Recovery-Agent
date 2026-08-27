"""Generate synthetic historical recovery events for later ML training."""

from __future__ import annotations

import argparse
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "historical_events.csv"
DEFAULT_ROWS = 2500
DEFAULT_SEED = 42

EVENT_TYPES = (
    "payment_failure",
    "checkout_abandonment",
    "subscription_failure",
)

PAYMENT_METHODS = (
    "card",
    "paypal",
    "apple_pay",
    "google_pay",
    "ach",
    "bank_transfer",
)

PAYMENT_FAILURE_REASONS = (
    "insufficient_funds",
    "card_expired",
    "card_declined",
    "fraud_hold",
    "network_error",
    "processor_timeout",
)

CHECKOUT_FAILURE_REASONS = (
    "cart_hesitation",
    "shipping_cost",
    "payment_form_dropoff",
    "comparison_shopping",
    "session_timeout",
)

SUBSCRIPTION_FAILURE_REASONS = (
    "card_expired",
    "insufficient_funds",
    "account_closed",
    "dunning_unresponsive",
    "plan_cancelled_intent",
)

RECOVERY_ACTIONS = (
    "email_reminder",
    "sms_nudge",
    "retry_payment",
    "dunning_sequence",
    "offer_discount",
    "update_payment_method",
    "cart_recovery_email",
    "wait_retry",
)

REQUIRED_FIELDS = (
    "customer_id",
    "event_id",
    "event_type",
    "amount",
    "payment_method",
    "failure_reason",
    "customer_age",
    "account_age",
    "previous_successes",
    "previous_failures",
    "retry_count",
    "checkout_visits",
    "cart_value",
    "subscription_age",
    "timestamp",
    "recovery_action",
    "recovery_time",
    "recovered",
    "recovered_amount",
)


def _clamp(value: float, low: float = 0.04, high: float = 0.92) -> float:
    return max(low, min(high, value))


def _recovery_probability(row: dict, rng: random.Random) -> float:
    """Score recovery chance from features so labels are not pure noise."""
    p = 0.38

    p += min(row["account_age"], 1800) / 1800 * 0.14
    p += min(row["previous_successes"], 12) / 12 * 0.16
    p -= min(row["previous_failures"], 10) / 10 * 0.18
    p -= min(row["retry_count"], 6) / 6 * 0.10

    if row["amount"] > 250:
        p -= 0.08
    elif row["amount"] < 40:
        p += 0.05

    reason = row["failure_reason"]
    if reason in ("insufficient_funds", "network_error", "processor_timeout", "session_timeout"):
        p += 0.10
    elif reason in ("card_expired", "payment_form_dropoff"):
        p += 0.06
    elif reason in ("fraud_hold", "account_closed", "plan_cancelled_intent"):
        p -= 0.16
    elif reason in ("shipping_cost", "comparison_shopping"):
        p -= 0.07

    action = row["recovery_action"]
    event_type = row["event_type"]
    if event_type == "checkout_abandonment" and action in ("cart_recovery_email", "offer_discount"):
        p += 0.12
    if event_type == "payment_failure" and action in ("retry_payment", "update_payment_method"):
        p += 0.10
    if event_type == "subscription_failure" and action in ("dunning_sequence", "update_payment_method"):
        p += 0.10
    if action == "wait_retry":
        p -= 0.08

    # Faster follow-up helps checkout; slow dunning still works for subscriptions.
    if event_type == "checkout_abandonment" and row["recovery_time"] <= 6:
        p += 0.08
    elif event_type == "checkout_abandonment" and row["recovery_time"] > 48:
        p -= 0.10
    if event_type == "payment_failure" and row["recovery_time"] <= 24:
        p += 0.05

    if row["checkout_visits"] >= 4 and event_type == "checkout_abandonment":
        p += 0.04

    p += rng.uniform(-0.04, 0.04)
    return _clamp(p)


def _choose_action(event_type: str, failure_reason: str, rng: random.Random) -> str:
    if event_type == "checkout_abandonment":
        weights = {
            "cart_recovery_email": 0.32,
            "offer_discount": 0.22,
            "email_reminder": 0.18,
            "sms_nudge": 0.12,
            "wait_retry": 0.10,
            "retry_payment": 0.06,
        }
    elif event_type == "subscription_failure":
        weights = {
            "dunning_sequence": 0.28,
            "update_payment_method": 0.24,
            "retry_payment": 0.18,
            "email_reminder": 0.14,
            "sms_nudge": 0.10,
            "wait_retry": 0.06,
        }
        if failure_reason == "card_expired":
            weights["update_payment_method"] = 0.40
    else:
        weights = {
            "retry_payment": 0.28,
            "update_payment_method": 0.22,
            "email_reminder": 0.16,
            "sms_nudge": 0.12,
            "dunning_sequence": 0.10,
            "wait_retry": 0.08,
            "offer_discount": 0.04,
        }
        if failure_reason == "insufficient_funds":
            weights["retry_payment"] = 0.38
            weights["wait_retry"] = 0.16
        if failure_reason == "card_expired":
            weights["update_payment_method"] = 0.40

    actions = list(weights)
    probs = [weights[a] for a in actions]
    total = sum(probs)
    probs = [x / total for x in probs]
    return rng.choices(actions, weights=probs, k=1)[0]


def generate_rows(n: int = DEFAULT_ROWS, seed: int = DEFAULT_SEED) -> list[dict]:
    rng = random.Random(seed)
    now = datetime(2026, 8, 1, 12, 0, 0)

    customer_count = max(350, n // 6)
    customers = []
    for i in range(1, customer_count + 1):
        customers.append(
            {
                "customer_id": i,
                "customer_age": rng.randint(18, 72),
                "account_created_days_ago": rng.randint(14, 2200),
                "previous_successes": rng.randint(0, 8),
                "previous_failures": rng.randint(0, 5),
            }
        )

    rows: list[dict] = []
    for seq in range(1, n + 1):
        customer = rng.choice(customers)
        event_type = rng.choices(EVENT_TYPES, weights=(0.40, 0.32, 0.28), k=1)[0]
        days_ago = rng.randint(1, min(customer["account_created_days_ago"] - 1, 540))
        timestamp = now - timedelta(
            days=days_ago,
            hours=rng.randint(0, 23),
            minutes=rng.randint(0, 59),
        )
        account_age = max(1, customer["account_created_days_ago"] - days_ago)

        if event_type == "checkout_abandonment":
            amount = round(rng.lognormvariate(3.6, 0.7), 2)
            amount = float(min(max(amount, 8.99), 650.00))
            cart_value = round(amount * rng.uniform(0.97, 1.03), 2)
            checkout_visits = rng.randint(1, 9)
            subscription_age = 0
            payment_method = rng.choice(PAYMENT_METHODS)
            failure_reason = rng.choice(CHECKOUT_FAILURE_REASONS)
            retry_count = rng.randint(0, 2)
            recovery_time = round(rng.uniform(0.5, 72.0), 2)
        elif event_type == "subscription_failure":
            amount = round(rng.choice([9.99, 12.99, 19.99, 29.99, 49.99, 79.99, 119.99]) * rng.choice([1, 1, 1, 12]), 2)
            if amount > 200:
                amount = round(amount / 12, 2)
            cart_value = 0.0
            checkout_visits = rng.randint(0, 1)
            subscription_age = rng.randint(1, max(2, min(account_age, 1500)))
            payment_method = rng.choices(
                PAYMENT_METHODS, weights=(0.55, 0.18, 0.08, 0.07, 0.08, 0.04), k=1
            )[0]
            failure_reason = rng.choice(SUBSCRIPTION_FAILURE_REASONS)
            retry_count = rng.randint(0, 5)
            recovery_time = round(rng.uniform(6.0, 240.0), 2)
        else:
            amount = round(rng.lognormvariate(3.8, 0.65), 2)
            amount = float(min(max(amount, 5.00), 900.00))
            cart_value = 0.0
            checkout_visits = rng.randint(0, 2)
            subscription_age = 0
            payment_method = rng.choices(
                PAYMENT_METHODS, weights=(0.50, 0.16, 0.12, 0.10, 0.08, 0.04), k=1
            )[0]
            failure_reason = rng.choice(PAYMENT_FAILURE_REASONS)
            retry_count = rng.randint(0, 4)
            recovery_time = round(rng.uniform(1.0, 96.0), 2)

        recovery_action = _choose_action(event_type, failure_reason, rng)

        row = {
            "customer_id": customer["customer_id"],
            "event_id": seq,
            "event_type": event_type,
            "amount": amount,
            "payment_method": payment_method,
            "failure_reason": failure_reason,
            "customer_age": customer["customer_age"],
            "account_age": account_age,
            "previous_successes": customer["previous_successes"],
            "previous_failures": customer["previous_failures"],
            "retry_count": retry_count,
            "checkout_visits": checkout_visits,
            "cart_value": cart_value,
            "subscription_age": subscription_age,
            "timestamp": timestamp.strftime("%Y-%m-%dT%H:%M:%S"),
            "recovery_action": recovery_action,
            "recovery_time": recovery_time,
            "recovered": False,
            "recovered_amount": 0.0,
        }

        recovered = rng.random() < _recovery_probability(row, rng)
        row["recovered"] = recovered
        if recovered:
            # Most recoveries collect the original amount; a few are partial.
            if rng.random() < 0.12:
                row["recovered_amount"] = round(amount * rng.uniform(0.55, 0.95), 2)
            else:
                row["recovered_amount"] = amount
            customer["previous_successes"] += 1
        else:
            row["recovered_amount"] = 0.0
            customer["previous_failures"] += 1

        rows.append(row)

    return rows


def write_csv(rows: list[dict], output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(REQUIRED_FIELDS))
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return output_path


def load_csv(path: Path) -> list[dict]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def parse_bool(value: str | bool) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"true", "1", "yes"}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic historical recovery events.")
    parser.add_argument("--rows", type=int, default=DEFAULT_ROWS)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    rows = generate_rows(n=args.rows, seed=args.seed)
    path = write_csv(rows, args.output)
    recovered = sum(1 for row in rows if row["recovered"])
    types = {row["event_type"] for row in rows}
    print(f"Wrote {len(rows)} rows to {path}")
    print(f"Event types: {sorted(types)}")
    print(f"Recovered: {recovered} ({recovered / len(rows):.1%})")
    print(f"Not recovered: {len(rows) - recovered}")


if __name__ == "__main__":
    main()
