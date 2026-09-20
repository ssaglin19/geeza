#!/usr/bin/env python3
"""Quick Needle eval: 7 examples, one per class."""
import needle

@needle.tool
def handle_bills(query: str):
    """Pay bills, handle utility payments, manage accounts."""
    return {"skill": "handle_bills", "query": query}

@needle.tool
def check_schedule(query: str):
    """Check calendar, appointments, medication reminders."""
    return {"skill": "check_schedule", "query": query}

@needle.tool
def contact_family(query: str):
    """Call family, read messages from family."""
    return {"skill": "contact_family", "query": query}

@needle.tool
def get_groceries(query: str):
    """Order groceries, buy food, shopping."""
    return {"skill": "get_groceries", "query": query}

@needle.tool
def check_safety(query: str):
    """Verify if an email, call, or message is a scam or fraud attempt."""
    return {"skill": "check_safety", "query": query}

@needle.tool
def general_help(query: str):
    """Answer factual questions, tell time, do calculations, explain concepts."""
    return {"skill": "general_help", "query": query}

@needle.tool
def emergency(query: str):
    """Call 911, get immediate medical help, report fire or break-in."""
    return {"skill": "emergency", "query": query}

agent = needle.Needle(tools=[handle_bills, check_schedule, contact_family, get_groceries, check_safety, general_help, emergency])

tests = [
    ("I need to pay the electric bill", "handle_bills"),
    ("What is on my calendar today", "check_schedule"),
    ("Call my son Sean", "contact_family"),
    ("Order some milk and bread", "get_groceries"),
    ("Is this email a scam", "check_safety"),
    ("What time is it", "general_help"),
    ("I fell and cannot get up", "emergency"),
]

correct = 0
for text, expected in tests:
    result = agent.run(text)
    # Needle returns tool results; extract skill from the first result
    predicted = "none"
    if result.get("results"):
        first = result["results"][0]
        if isinstance(first, dict) and "skill" in first:
            predicted = first["skill"]
        elif isinstance(first, dict) and "query" in first:
            # Fallback: infer from which tool was called
            predicted = "unknown"
    ok = predicted == expected
    correct += ok
    status = "OK" if ok else "MISS"
    print(f"{status}: {text[:40]}... -> {predicted} (expected {expected})")

print(f"\nAccuracy: {correct}/{len(tests)} = {correct/len(tests):.2f}")
