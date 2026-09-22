"""Stored action review with provider outcome verification."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ActionReview:
    action_id: str
    action_type: str  # payment, form_submit, email_send
    provider: str  # consumers_energy, kroger, gmail
    status: str  # pending, verified, failed
    expected_outcome: str
    actual_outcome: Optional[str]
    verification_method: str  # page_state, receipt, confirmation_code
    verified_at: Optional[float]


class ActionReviewer:
    """Verifies that external writes actually happened."""

    def __init__(self):
        self.reviews = []

    def create_review(
        self,
        action_id: str,
        action_type: str,
        provider: str,
        expected_outcome: str,
        verification_method: str = "page_state",
    ) -> ActionReview:
        review = ActionReview(
            action_id=action_id,
            action_type=action_type,
            provider=provider,
            status="pending",
            expected_outcome=expected_outcome,
            actual_outcome=None,
            verification_method=verification_method,
            verified_at=None,
        )
        self.reviews.append(review)
        return review

    def verify_page_state(
        self,
        review: ActionReview,
        driver,
        expected_selector: str,
        expected_text: str,
    ) -> bool:
        """Verify by checking page state after the action."""
        try:
            snapshot = driver.snapshot()
            for element in snapshot.get("elements", []):
                if element.get("selector") == expected_selector:
                    if expected_text.lower() in (element.get("text") or "").lower():
                        review.actual_outcome = element.get("text")
                        review.status = "verified"
                        return True
            review.status = "failed"
            review.actual_outcome = "expected element not found"
            return False
        except Exception as e:
            review.status = "failed"
            review.actual_outcome = str(e)
            return False

    def verify_receipt(
        self,
        review: ActionReview,
        receipt_text: str,
        confirmation_pattern: str,
    ) -> bool:
        """Verify by checking a receipt or confirmation message."""
        import re
        if re.search(confirmation_pattern, receipt_text, re.IGNORECASE):
            review.actual_outcome = receipt_text
            review.status = "verified"
            return True
        review.status = "failed"
        review.actual_outcome = "confirmation pattern not found"
        return False

    def get_pending(self) -> list:
        return [r for r in self.reviews if r.status == "pending"]

    def get_failed(self) -> list:
        return [r for r in self.reviews if r.status == "failed"]
