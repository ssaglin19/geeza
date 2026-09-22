"""Goals & tracking: recurring checks with local notifications."""
import json
import time
from dataclasses import dataclass
from typing import Callable, Optional


@dataclass
class Goal:
    goal_id: str
    name: str
    check_type: str  # price_threshold, text_availability, page_change
    target: str  # URL or flow_id
    condition: dict  # {"operator": "<", "value": 100.00}
    schedule: str  # daily, weekly, hourly
    last_check: Optional[float]
    last_result: Optional[dict]
    active: bool


class GoalTracker:
    """Tracks goals and schedules recurring checks."""

    def __init__(self, db_path: str = "goals.json"):
        self.db_path = db_path
        self.goals = self._load()

    def _load(self) -> dict:
        try:
            with open(self.db_path, "r") as f:
                content = f.read().strip()
                if not content:
                    return {}
                data = json.loads(content)
                return {g["goal_id"]: Goal(**g) for g in data.get("goals", [])}
        except FileNotFoundError:
            return {}

    def _save(self):
        with open(self.db_path, "w") as f:
            json.dump({"goals": [vars(g) for g in self.goals.values()]}, f, indent=2)

    def add_goal(self, goal: Goal):
        self.goals[goal.goal_id] = goal
        self._save()

    def remove_goal(self, goal_id: str):
        if goal_id in self.goals:
            del self.goals[goal_id]
            self._save()

    def get_due_goals(self) -> list:
        """Get goals that are due for checking."""
        now = time.time()
        due = []
        for goal in self.goals.values():
            if not goal.active:
                continue
            if goal.last_check is None:
                due.append(goal)
                continue
            interval = self._schedule_to_seconds(goal.schedule)
            if now - goal.last_check >= interval:
                due.append(goal)
        return due

    def _schedule_to_seconds(self, schedule: str) -> float:
        return {
            "hourly": 3600,
            "daily": 86400,
            "weekly": 604800,
        }.get(schedule, 86400)

    def check_goal(self, goal: Goal, checker: Callable) -> dict:
        """Run a check for a goal. Returns result dict."""
        result = checker(goal)
        goal.last_check = time.time()
        goal.last_result = result
        self._save()
        return result

    def evaluate_condition(self, goal: Goal, current_value: float) -> bool:
        """Evaluate if the goal condition is met."""
        op = goal.condition.get("operator", "<")
        target = goal.condition.get("value", 0)
        if op == "<":
            return current_value < target
        elif op == ">":
            return current_value > target
        elif op == "==":
            return current_value == target
        elif op == "<=":
            return current_value <= target
        elif op == ">=":
            return current_value >= target
        return False


def create_bill_watch_goal(bill_name: str, threshold: float, schedule: str = "daily") -> Goal:
    """Create a goal to watch for bill amount spikes."""
    return Goal(
        goal_id=f"bill_watch_{bill_name.lower().replace(' ', '_')}",
        name=f"Watch {bill_name} for spikes",
        check_type="price_threshold",
        target=bill_name,
        condition={"operator": ">", "value": threshold},
        schedule=schedule,
        last_check=None,
        last_result=None,
        active=True,
    )


def create_availability_goal(item_name: str, url: str, schedule: str = "daily") -> Goal:
    """Create a goal to check if an item is available."""
    return Goal(
        goal_id=f"availability_{item_name.lower().replace(' ', '_')}",
        name=f"Check if {item_name} is available",
        check_type="text_availability",
        target=url,
        condition={"operator": "==", "value": "available"},
        schedule=schedule,
        last_check=None,
        last_result=None,
        active=True,
    )
