"""Detect group threads and prevent the bot from responding in them.

Privacy guard: the bot must only respond in 1:1 conversations. Group threads
risk exposing personal information to unintended recipients.
"""

import re
from dataclasses import dataclass


@dataclass
class ThreadInfo:
    is_group: bool
    participant_count: int
    thread_id: str
    reason: str


def detect_group_thread(
    sender: str,
    recipients: list[str] | None = None,
    thread_name: str | None = None,
    message_guid: str | None = None,
) -> ThreadInfo:
    """
    Detect if a message is from a group thread.

    Args:
        sender: The sender's phone number or email
        recipients: List of all recipients (if available from the gateway)
        thread_name: Group thread name (if available)
        message_guid: iMessage GUID for thread identification

    Returns:
        ThreadInfo with is_group flag and reason
    """
    # If we have a recipients list, check count
    if recipients is not None:
        count = len(recipients)
        if count > 1:
            return ThreadInfo(
                is_group=True,
                participant_count=count,
                thread_id=thread_name or "unknown",
                reason=f"multiple recipients ({count})",
            )

    # If thread_name exists and looks like a group name
    if thread_name and not _is_phone_number(thread_name):
        return ThreadInfo(
            is_group=True,
            participant_count=-1,  # unknown
            thread_id=thread_name,
            reason=f"named group thread: {thread_name}",
        )

    # Check sender format — group threads often have weird sender IDs
    if _is_group_sender_id(sender):
        return ThreadInfo(
            is_group=True,
            participant_count=-1,
            thread_id=sender,
            reason="sender ID indicates group thread",
        )

    # Default: assume 1:1
    return ThreadInfo(
        is_group=False,
        participant_count=2,
        thread_id=sender,
        reason="1:1 conversation",
    )


def _is_phone_number(text: str) -> bool:
    """Check if text looks like a phone number."""
    return bool(re.match(r"^\+?[\d\s\-\(\)]{7,}$", text))


def _is_group_sender_id(sender: str) -> bool:
    """Check if sender ID indicates a group thread."""
    # iMessage group threads sometimes have alphanumeric IDs
    # or "chat" prefixes
    if sender.startswith("chat"):
        return True
    if not _is_phone_number(sender) and "@" not in sender:
        return True
    return False


def should_respond(thread_info: ThreadInfo) -> tuple[bool, str]:
    """
    Determine if the bot should respond in this thread.

    Returns:
        (should_respond, reason)
    """
    if thread_info.is_group:
        return False, f"group thread detected ({thread_info.reason}) — not responding for privacy"
    return True, "1:1 conversation — safe to respond"
