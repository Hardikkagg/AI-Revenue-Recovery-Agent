"""Simulated Customer Communication for safe, sandbox recovery notifications."""

from __future__ import annotations

import random
from app.simulation.schemas import SimulatedCommunicationResult


class SimulatedCommunicationService:
    """Sandbox Communication Dispatcher. Does not send real emails or SMS messages."""

    def __init__(self, seed: int | None = None) -> None:
        self._seed = seed

    def _get_rng(self, customer_id: int, event_id: int | None = None) -> random.Random:
        if self._seed is not None:
            return random.Random(self._seed)
        seed_val = hash((customer_id, event_id or 0, "communication"))
        return random.Random(seed_val)

    def send_checkout_reminder(
        self,
        customer_id: int,
        cart_value: float,
        checkout_visits: int,
        recovery_probability: float,
        event_id: int | None = None,
    ) -> SimulatedCommunicationResult:
        """Simulate sending an abandoned checkout recovery reminder email."""
        template = "checkout_abandonment_reminder_v1"
        message = (
            f"[SIMULATED EMAIL] Hi Customer #{customer_id}, we noticed you left items in your cart "
            f"valued at ${cart_value:.2f}. Click here to complete your checkout with 1-click."
        )

        # High intent (multiple visits, high ML probability) raises response likelihood
        intent_bonus = min(0.20, checkout_visits * 0.05)
        effective_prob = max(0.10, min(0.90, recovery_probability + intent_bonus))

        rng = self._get_rng(customer_id, event_id)
        roll = rng.random()
        customer_responded = roll < effective_prob

        return SimulatedCommunicationResult(
            channel="email",
            status="simulated_sent",
            template_name=template,
            message=message,
            customer_responded=customer_responded,
            response_delay_seconds=120 if customer_responded else 0,
        )

    def send_subscription_update_request(
        self,
        customer_id: int,
        amount: float,
        failure_reason: str,
        recovery_probability: float,
        subscription_age: int = 0,
        event_id: int | None = None,
    ) -> SimulatedCommunicationResult:
        """Simulate sending a subscription payment method update notification."""
        template = "subscription_update_request_v1"
        message = (
            f"[SIMULATED EMAIL] Hi Customer #{customer_id}, your recurring subscription payment of "
            f"${amount:.2f} could not be processed ({failure_reason}). Please update your billing details."
        )

        # Loyal subscribers (longer subscription age) respond at higher rates
        loyalty_bonus = min(0.15, (subscription_age / 365) * 0.10)
        effective_prob = max(0.10, min(0.90, recovery_probability + loyalty_bonus))

        rng = self._get_rng(customer_id, event_id)
        roll = rng.random()
        customer_responded = roll < effective_prob

        return SimulatedCommunicationResult(
            channel="email",
            status="simulated_sent",
            template_name=template,
            message=message,
            customer_responded=customer_responded,
            response_delay_seconds=300 if customer_responded else 0,
        )

    def request_alternate_payment(
        self,
        customer_id: int,
        amount: float,
        failure_reason: str,
        recovery_probability: float,
        previous_successes: int = 0,
        event_id: int | None = None,
    ) -> SimulatedCommunicationResult:
        """Simulate sending an alternate payment method request."""
        template = "alternate_payment_request_v1"
        message = (
            f"[SIMULATED EMAIL] Hi Customer #{customer_id}, your payment of ${amount:.2f} failed "
            f"({failure_reason}). Please provide an alternate card or payment method."
        )

        history_bonus = min(0.15, previous_successes * 0.03)
        effective_prob = max(0.10, min(0.85, recovery_probability + history_bonus))

        rng = self._get_rng(customer_id, event_id)
        roll = rng.random()
        customer_responded = roll < effective_prob

        return SimulatedCommunicationResult(
            channel="email",
            status="simulated_sent",
            template_name=template,
            message=message,
            customer_responded=customer_responded,
            response_delay_seconds=180 if customer_responded else 0,
        )
