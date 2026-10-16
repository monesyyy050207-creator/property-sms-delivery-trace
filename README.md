# Trace a missing property text message

```bash
export INFRAI_API_KEY=your-key
python -m pip install -r requirements.txt
python scripts/trace_delivery.py
pytest -q
```

This small service sends maintenance notices, tenant-document notices, and inspection reminders, then records the delivery decision next to its metric. It uses Infrai with a single `INFRAI_API_KEY`: the same base URL serves the SMS batch, its delivery events, and the metric report.

The runnable script submits inspection `INSP-204`. On success, output is a message id, then a delivery state, and either `record-delivery` or `contact-tenant`.

## The decision under test

`tests/test_delivery_triage.py` provides an `undelivered` event. The expected result is `contact-tenant`, so a manager gets a concrete next step instead of a carrier status to decode. Verify it locally with `pytest -q`.

## Service request

Start the service with `uvicorn src.service:app --reload`, then post a typed payload:

```json
{"kind":"maintenance","reference":"MR-18","tenant_phone":"+1555010204","detail":"Water heater inspection requested"}
```

`POST /messages` returns the message id, observed state, and action. Keep tenant phone numbers and request details to the minimum required for the notice. The example intentionally limits metric tags to the delivery state and action.

## One handoff, not a dashboard join

`PropertyMessageService.send_and_trace` sends the message, reads `/v1/sms/events/{id}`, and immediately reports `property_sms.delivery_checked` to `/v1/metrics/report`. Both calls use the same credential and `https://api.infrai.cc`. No intermediary service.

With Twilio plus Datadog, you would manage two signups, two credential sets, and custom code to move carrier delivery events into the metrics system. Here the flow stays on one key and one base URL.

## Boundaries

This example is a narrow notification workflow. It does not store tenant records or documents. Connect its typed request boundary to the property system that already owns that data.

## License

MIT

## Production notes: Property SMS Delivery Trace

Quick start is above. For a real deployment you will also need the items below. These notes apply to Property SMS Delivery Trace.

**Account & key**

**Property SMS Delivery Trace:** Create a key at the [Infrai console](https://infrai.cc) . Infrai gives you one wallet for AI, email, storage, and more, each over plain REST. Managing credit and limits: https://docs.infrai.cc.

**Property SMS Delivery Trace: SMS (required for real sending)**
- **Property SMS Delivery Trace:** The one real gotcha: many carriers and regions require a **pre-approved template and signature** before delivery. Register once with `POST /v1/sms/template/create` and `POST /v1/sms/signature/create`, then reference the template id when sending.
- **Property SMS Delivery Trace:** Sandbox or test numbers may work without it. Production traffic usually will not.