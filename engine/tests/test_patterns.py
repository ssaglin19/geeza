"""Test all five OpenMuse-inspired patterns."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from boosh_flow.durable_tasks import TaskStore, TaskLease
from boosh_flow.action_review import ActionReviewer
from boosh_flow.pdf_forms import PDFFormProcessor
from boosh_flow.goals import GoalTracker, create_bill_watch_goal
from boosh_flow.conversation import ConversationStore, Message


def test_durable_tasks():
    store = TaskStore(":memory:")
    lease = store.create("task1", "flow1", {"key": "value"})
    assert lease.status == "pending"
    assert store.get("task1") is not None
    print("  durable_tasks: OK")


def test_action_review():
    reviewer = ActionReviewer()
    review = reviewer.create_review("a1", "payment", "test", "success")
    assert review.status == "pending"
    assert len(reviewer.get_pending()) == 1
    print("  action_review: OK")


def test_pdf_forms():
    processor = PDFFormProcessor()
    form = processor.extract_fields("test.pdf", "form1")
    assert form.status == "extracted"
    assert len(form.fields) == 3
    processor.fill_field("form1", "patient_name", "John Doe")
    summary = processor.get_review_summary("form1")
    assert summary["filled_fields"] == 1
    print("  pdf_forms: OK")


def test_goals():
    import tempfile
    import os
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        db_path = f.name
    try:
        tracker = GoalTracker(db_path)
        goal = create_bill_watch_goal("Electric", 150.00)
        tracker.add_goal(goal)
        assert goal.active
        assert len(tracker.get_due_goals()) == 1
        print("  goals: OK")
    finally:
        os.unlink(db_path)


def test_conversation():
    conv = ConversationStore(":memory:")
    thread = conv.create_thread("t1", "Test Thread")
    assert thread.name == "Test Thread"
    msg = Message("m1", "t1", "user", "Hello", 1234567890.0, {})
    conv.add_message(msg)
    messages = conv.get_messages("t1")
    assert len(messages) == 1
    assert messages[0].content == "Hello"
    print("  conversation: OK")


if __name__ == "__main__":
    test_durable_tasks()
    test_action_review()
    test_pdf_forms()
    test_goals()
    test_conversation()
    print("All five patterns working.")
