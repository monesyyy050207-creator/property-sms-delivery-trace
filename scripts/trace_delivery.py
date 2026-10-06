"""Run one inspection reminder through the service workflow."""

from src.infrai_client import InfraiClient
from src.maintenance_messaging import InspectionReminder, PropertyMessageService


def main() -> None:
    reminder = InspectionReminder("INSP-204", "+1555010204", "2026-10-03 09:00")
    result = PropertyMessageService(InfraiClient()).send_and_trace(reminder)
    print(f"{result.message_id}: {result.state} -> {result.action}")


if __name__ == "__main__":
    main()
