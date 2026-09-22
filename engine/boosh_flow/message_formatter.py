"""Format responses for the text-message interface.

Produces rich link formatting, step-by-step guidance, and voice-friendly
text for the SMS/iMessage gateway.
"""

from dataclasses import dataclass
from enum import Enum


class MessageType(Enum):
    TEXT = "text"
    RICH_LINK = "rich_link"
    STEP_BY_STEP = "step_by_step"
    CONFIRMATION = "confirmation"
    ERROR = "error"


@dataclass
class FormattedMessage:
    type: MessageType
    text: str
    url: str | None = None
    steps: list[str] | None = None
    requires_confirmation: bool = False


def format_bill_guidance(vendor: str, amount: str, url: str) -> FormattedMessage:
    """Format a bill-pay guidance message with Safari link."""
    return FormattedMessage(
        type=MessageType.STEP_BY_STEP,
        text=f"Your {vendor} bill is {amount}. I'll walk you through paying it.",
        steps=[
            f"1. Tap this link to open {vendor}: {url}",
            "2. Sign in with your usual email and password",
            "3. Find the 'Pay Bill' button",
            "4. Check the amount matches what I told you",
            "5. Tap Pay, then come back and tell me when it's done",
        ],
        url=url,
        requires_confirmation=True,
    )


def format_scam_warning(subject: str) -> FormattedMessage:
    """Format a scam alert — never includes the scam content."""
    return FormattedMessage(
        type=MessageType.ERROR,
        text=f"⚠️ The message about '{subject}' looks like a scam. Don't click any links or call any numbers in it. I'll tell Sean to check it.",
    )


def format_emergency() -> FormattedMessage:
    """Format emergency response — immediate, no fluff."""
    return FormattedMessage(
        type=MessageType.TEXT,
        text="Calling 911 now. Stay on the line.",
    )


def format_family_call(name: str, phone: str) -> FormattedMessage:
    """Format family contact message."""
    return FormattedMessage(
        type=MessageType.RICH_LINK,
        text=f"Tap to call {name}:",
        url=f"tel:{phone}",
    )


def format_confirmation(question: str) -> FormattedMessage:
    """Format a yes/no confirmation request."""
    return FormattedMessage(
        type=MessageType.CONFIRMATION,
        text=question,
        requires_confirmation=True,
    )


def format_fallback(heard: str, skills: list[str]) -> FormattedMessage:
    """Format the 'I don't understand' fallback."""
    skill_list = ", ".join(skills)
    return FormattedMessage(
        type=MessageType.TEXT,
        text=f'I heard: "{heard}". I\'m still learning — for now I can help with {skill_list}.',
    )


def format_weather(temp: str, condition: str, advice: str) -> FormattedMessage:
    """Format weather response."""
    return FormattedMessage(
        type=MessageType.TEXT,
        text=f"It's {temp} and {condition}. {advice}",
    )


def format_schedule(items: list[str]) -> FormattedMessage:
    """Format schedule/calendar response."""
    if not items:
        return FormattedMessage(
            type=MessageType.TEXT,
            text="Nothing on your schedule today. Enjoy your day!",
        )
    lines = ["Here's your day:"] + [f"• {item}" for item in items]
    return FormattedMessage(
        type=MessageType.TEXT,
        text="\n".join(lines),
    )
