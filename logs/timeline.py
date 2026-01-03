import datetime
import os
from typing import List

LOG_FILE = os.path.join(os.path.dirname(__file__), "events.log")


def log_event(event_type: str, details: str) -> None:
    """Log an event to the timeline."""
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"{timestamp} | {event_type} | {details}\n"

    try:
        with open(LOG_FILE, "a") as f:
            f.write(entry)
    except Exception as e:
        print(f"Failed to write log: {e}")


def read_recent(n: int = 10) -> List[str]:
    """Read the n most recent events."""
    if not os.path.exists(LOG_FILE):
        return []

    try:
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
        return [line.strip() for line in lines[-n:]]
    except Exception as e:
        print(f"Failed to read logs: {e}")
        return []


if __name__ == "__main__":
    # Simple CLI for testing
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "--export":
        # Export logic (dummy for now)
        print(f"Exporting logs to {sys.argv[2]}...")
    else:
        print("\n".join(read_recent()))
