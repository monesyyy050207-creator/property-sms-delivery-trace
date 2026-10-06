"""Property-management message workflow and delivery triage."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .infrai_client import InfraiClient


@dataclass(frozen=True)
class MaintenanceRequest:
    request_id: str
    tenant_phone: str
    summary: str


@dataclass(frozen=True)
class TenantDocument:
    document_id: str
    tenant_phone: str
    label: str


@dataclass(frozen=True)
class InspectionReminder:
    inspection_id: str
    tenant_phone: str
    scheduled_for: str


@dataclass(frozen=True)
class DeliveryDecision:
    message_id: str
    state: str
    action: str


def message_for(item: MaintenanceRequest | TenantDocument | InspectionReminder) -> str:
    if isinstance(item, MaintenanceRequest):
        return f"Maintenance request {item.request_id}: {item.summary}"
    if isinstance(item, TenantDocument):
        return f"Tenant document ready: {item.label} ({item.document_id})"
    return f"Inspection {item.inspection_id} is scheduled for {item.scheduled_for}"


def decide_delivery(message_id: str, event: Mapping[str, Any]) -> DeliveryDecision:
    state = str(event.get("status", "pending"))
    action = "contact-tenant" if state in {"failed", "undelivered"} else "record-delivery"
    return DeliveryDecision(message_id=message_id, state=state, action=action)


class PropertyMessageService:
    def __init__(self, infrai: InfraiClient) -> None:
        self.infrai = infrai

    def send_and_trace(self, item: MaintenanceRequest | TenantDocument | InspectionReminder) -> DeliveryDecision:
        if isinstance(item, MaintenanceRequest):
            reference = item.request_id
        elif isinstance(item, TenantDocument):
            reference = item.document_id
        else:
            reference = item.inspection_id
        sent = self.infrai.sms_batch_send(
            {"messages": [{"to": item.tenant_phone, "body": message_for(item)}]},
            idempotency_key=f"property-message-{reference}",
        )
        message_id = str(sent["message_id"])
        event = self.infrai.sms_events(message_id)
        decision = decide_delivery(message_id, event)
        self.infrai.metrics_report(
            {"type": "counter", "name": "property_sms.delivery_checked", "value": 1, "tags": {"state": decision.state, "action": decision.action}},
            idempotency_key=f"property-delivery-check-{message_id}",
        )
        return decision
