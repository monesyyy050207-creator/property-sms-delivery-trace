"""HTTP surface for a property manager's message request."""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .infrai_client import InfraiClient, InfraiError
from .maintenance_messaging import InspectionReminder, MaintenanceRequest, PropertyMessageService, TenantDocument

app = FastAPI()


class MessageRequest(BaseModel):
    kind: str
    reference: str
    tenant_phone: str
    detail: str


@app.post("/messages")
def send_message(request: MessageRequest) -> dict[str, str]:
    if request.kind == "maintenance":
        item = MaintenanceRequest(request.reference, request.tenant_phone, request.detail)
    elif request.kind == "document":
        item = TenantDocument(request.reference, request.tenant_phone, request.detail)
    elif request.kind == "inspection":
        item = InspectionReminder(request.reference, request.tenant_phone, request.detail)
    else:
        raise HTTPException(status_code=400, detail="kind must be maintenance, document, or inspection")
    try:
        result = PropertyMessageService(InfraiClient()).send_and_trace(item)
    except InfraiError as error:
        status = error.status_code if 400 <= error.status_code < 500 else 502
        raise HTTPException(status_code=status, detail=error.code) from error
    return {"message_id": result.message_id, "state": result.state, "action": result.action}
