"""Simulation Engine: Orchestrates sandbox execution of recovery strategies."""

from __future__ import annotations

import json
import time
import uuid
from typing import Any

from sqlalchemy.orm import Session

from app.agent.schemas import AnalysisResult, DetectedEvent
from app.models import Action, Customer, Event, RecoveryCase
from app.simulation.communication import SimulatedCommunicationService
from app.simulation.gateway import SimulatedPaymentGateway
from app.simulation.schemas import (
    SimulatedCommunicationResult,
    SimulatedGatewayResult,
    SimulationResult,
)


class RecoverySimulationEngine:
    """Safely executes recovery decisions in a simulated local environment."""

    def __init__(
        self,
        gateway: SimulatedPaymentGateway | None = None,
        communication: SimulatedCommunicationService | None = None,
    ) -> None:
        self.gateway = gateway or SimulatedPaymentGateway()
        self.communication = communication or SimulatedCommunicationService()

    def execute(
        self,
        analysis: AnalysisResult,
        db: Session | None = None,
    ) -> SimulationResult:
        """Simulate the execution of the recommended strategy and record results."""
        start_time = time.perf_counter()
        event = analysis.event
        strategy = analysis.recommended_strategy
        prob = analysis.recovery_probability
        amount = event.amount
        simulation_id = f"sim_{uuid.uuid4().hex[:12]}"

        gateway_res: SimulatedGatewayResult | None = None
        comm_res: SimulatedCommunicationResult | None = None
        action_details: dict[str, Any] = {}

        # 1. RETRY NOW
        if strategy == "retry_now":
            gateway_res = self.gateway.execute_retry(
                customer_id=event.customer_id,
                amount=amount,
                failure_reason=event.failure_reason,
                diagnosis_code=analysis.diagnosis.diagnosis_code,
                recovery_probability=prob,
                retry_count=event.retry_count,
                is_delayed=False,
                event_id=event.event_id,
            )
            recovered = gateway_res.success
            recovered_amount = min(amount, gateway_res.amount_settled) if recovered else 0.0
            outcome = "payment_recovered" if recovered else "payment_failed"
            status = "completed" if recovered else "failed"
            action_details = {
                "action": "immediate_gateway_retry",
                "reference": gateway_res.gateway_reference,
                "response_code": gateway_res.response_code,
            }
            if recovered:
                explanation = (
                    f"AI selected '{strategy}' (ML score {prob:.2f}). "
                    f"Simulated payment gateway approved the transaction, successfully recovering ${recovered_amount:.2f}."
                )
            else:
                explanation = (
                    f"AI selected '{strategy}' (ML score {prob:.2f}). "
                    f"Simulated payment gateway declined the transaction ({gateway_res.response_code})."
                )

        # 2. RETRY LATER
        elif strategy == "retry_later":
            gateway_res = self.gateway.execute_retry(
                customer_id=event.customer_id,
                amount=amount,
                failure_reason=event.failure_reason,
                diagnosis_code=analysis.diagnosis.diagnosis_code,
                recovery_probability=prob,
                retry_count=event.retry_count,
                is_delayed=True,
                event_id=event.event_id,
            )
            recovered = gateway_res.success
            recovered_amount = min(amount, gateway_res.amount_settled) if recovered else 0.0
            outcome = "payment_recovered" if recovered else "payment_failed"
            status = "completed" if recovered else "failed"
            action_details = {
                "action": "scheduled_delayed_retry",
                "delay_interval": "4_hours",
                "reference": gateway_res.gateway_reference,
                "response_code": gateway_res.response_code,
            }
            if recovered:
                explanation = (
                    f"AI selected '{strategy}' based on diagnosis '{analysis.diagnosis.diagnosis_code}'. "
                    f"Simulated delayed retry succeeded after transient failure, recovering ${recovered_amount:.2f}."
                )
            else:
                explanation = (
                    f"AI selected '{strategy}' (ML score {prob:.2f}). "
                    f"Simulated delayed retry attempt failed with {gateway_res.response_code}."
                )

        # 3. REQUEST ALTERNATE PAYMENT
        elif strategy == "request_alternate_payment":
            comm_res = self.communication.request_alternate_payment(
                customer_id=event.customer_id,
                amount=amount,
                failure_reason=event.failure_reason,
                recovery_probability=prob,
                previous_successes=event.previous_successes,
                event_id=event.event_id,
            )
            recovered = comm_res.customer_responded
            recovered_amount = amount if recovered else 0.0
            outcome = "customer_updated_payment" if recovered else "customer_unresponsive"
            status = "completed" if recovered else "failed"
            action_details = {
                "action": "alternate_payment_request_sent",
                "channel": comm_res.channel,
                "template": comm_res.template_name,
                "customer_responded": comm_res.customer_responded,
            }
            if recovered:
                explanation = (
                    f"AI requested alternate payment method. Customer responded and provided a valid replacement card, "
                    f"recovering ${recovered_amount:.2f}."
                )
            else:
                explanation = (
                    f"AI requested alternate payment method. Customer did not respond within the simulated window; "
                    f"no revenue recovered."
                )

        # 4. SEND CHECKOUT REMINDER
        elif strategy == "send_checkout_reminder":
            comm_res = self.communication.send_checkout_reminder(
                customer_id=event.customer_id,
                cart_value=event.cart_value or amount,
                checkout_visits=event.checkout_visits,
                recovery_probability=prob,
                event_id=event.event_id,
            )
            recovered = comm_res.customer_responded
            recovered_amount = amount if recovered else 0.0
            outcome = "checkout_completed" if recovered else "checkout_abandoned"
            status = "completed" if recovered else "failed"
            action_details = {
                "action": "checkout_reminder_sent",
                "channel": comm_res.channel,
                "template": comm_res.template_name,
                "customer_responded": comm_res.customer_responded,
            }
            if recovered:
                explanation = (
                    f"AI sent checkout abandonment reminder. Customer re-engaged and completed the order, "
                    f"recovering ${recovered_amount:.2f}."
                )
            else:
                explanation = (
                    f"AI sent checkout abandonment reminder. Customer did not complete checkout; $0.00 recovered."
                )

        # 5. SEND SUBSCRIPTION UPDATE REQUEST
        elif strategy == "send_subscription_update_request":
            comm_res = self.communication.send_subscription_update_request(
                customer_id=event.customer_id,
                amount=amount,
                failure_reason=event.failure_reason,
                recovery_probability=prob,
                subscription_age=event.subscription_age,
                event_id=event.event_id,
            )
            recovered = comm_res.customer_responded
            recovered_amount = amount if recovered else 0.0
            outcome = "customer_updated_payment" if recovered else "customer_unresponsive"
            status = "completed" if recovered else "failed"
            action_details = {
                "action": "subscription_update_sent",
                "channel": comm_res.channel,
                "template": comm_res.template_name,
                "customer_responded": comm_res.customer_responded,
            }
            if recovered:
                explanation = (
                    f"AI notified subscriber to update expired/declined payment details. Subscriber updated card successfully, "
                    f"recovering ${recovered_amount:.2f}."
                )
            else:
                explanation = (
                    f"AI notified subscriber to update payment details. Subscriber was unresponsive; $0.00 recovered."
                )

        # 6. ESCALATE TO MANUAL REVIEW
        elif strategy == "escalate_to_manual_review":
            recovered = False
            recovered_amount = 0.0
            outcome = "manual_review_required"
            status = "escalated"
            action_details = {
                "action": "ticket_created_for_ops",
                "priority": "high" if prob < 0.20 or event.failure_reason == "fraud_hold" else "medium",
                "reason": analysis.strategy_reason,
            }
            explanation = (
                f"Automated action halted for safety ({analysis.strategy_reason}). "
                f"Case escalated to human operations team for manual review."
            )

        # 7. DO NOTHING
        else:
            recovered = False
            recovered_amount = 0.0
            outcome = "no_action_taken"
            status = "skipped"
            action_details = {
                "action": "none",
                "reason": analysis.strategy_reason,
            }
            explanation = (
                f"No action taken because recovery probability ({prob:.2f}) was insufficient to justify intervention."
            )

        # Invariant safety check: never exceed amount at risk
        recovered_amount = min(amount, max(0.0, recovered_amount))

        execution_duration = round(time.perf_counter() - start_time, 4)

        result = SimulationResult(
            simulation_id=simulation_id,
            strategy=strategy,
            status=status,
            outcome=outcome,
            recovered=recovered,
            recovered_amount=recovered_amount,
            amount_at_risk=amount,
            execution_time_seconds=execution_duration,
            explanation=explanation,
            action_details=action_details,
            gateway_result=gateway_res,
            communication_result=comm_res,
        )

        # Optional DB persistence
        if db is not None:
            self._persist_simulation(db, analysis, result)

        return result

    def _persist_simulation(
        self,
        db: Session,
        analysis: AnalysisResult,
        sim: SimulationResult,
    ) -> None:
        """Persist customer, case, event, and action records for auditability."""
        event = analysis.event
        # 1. Ensure customer exists or fetch
        customer = db.query(Customer).filter_by(id=event.customer_id).first()
        if not customer:
            customer = Customer(
                id=event.customer_id,
                name=f"Customer #{event.customer_id}",
                email=f"customer{event.customer_id}@example.com",
            )
            db.add(customer)
            db.flush()

        # 2. Create RecoveryCase
        case_status = "resolved" if sim.recovered else ("escalated" if sim.status == "escalated" else "closed")
        case = RecoveryCase(
            customer_id=customer.id,
            amount=event.amount,
            currency="USD",
            status=case_status,
            failure_reason=event.failure_reason,
        )
        db.add(case)
        db.flush()

        # 3. Create Event record
        ev = Event(
            recovery_case_id=case.id,
            event_type=event.event_type,
            details=json.dumps({
                "payment_method": event.payment_method,
                "failure_reason": event.failure_reason,
                "retry_count": event.retry_count,
                "cart_value": event.cart_value,
                "subscription_age": event.subscription_age,
                "diagnosis": analysis.diagnosis.model_dump(),
                "recovery_probability": analysis.recovery_probability,
            }),
        )
        db.add(ev)

        # 4. Create Action record
        act = Action(
            recovery_case_id=case.id,
            action_type=sim.strategy,
            status=sim.status,
            details=json.dumps({
                "simulation_id": sim.simulation_id,
                "outcome": sim.outcome,
                "recovered": sim.recovered,
                "recovered_amount": sim.recovered_amount,
                "explanation": sim.explanation,
                "action_details": sim.action_details,
            }),
        )
        db.add(act)
        db.commit()


simulation_engine = RecoverySimulationEngine()
