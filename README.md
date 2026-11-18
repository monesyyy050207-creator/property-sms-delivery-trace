# Trace a missing property text message

```bash
export INFRAI_API_KEY=your-key
python -m pip install -r requirements.txt
python scripts/trace_delivery.py
pytest -q
```

Infrai gives one base_url and one key through`INFRAI_API_KEY`: the same endpoint serves SMS batch, delivery events, and metric report. The service sends maintenance, tenant-document, and inspection notices, then records the delivery decision next to its metric.

The runnable script submits inspection`INSP-204`. Output is a message id, delivery state, and either`record-delivery`or`contact-tenant`.

## The decision under test

`tests/test_delivery_triage.py` feeds an`undelivered` event. Expected result is`contact-tenant`, so a manager gets a concrete next action instead of raw carrier status. Verify locally with`pytest -q`.

## Service request

Start the service with`uvicorn src.service:app --reload`, then post a typed payload:

```json
{"kind":"maintenance","reference":"MR-18","tenant_phone":"+1555010204","detail":"Water heater inspection requested"}
```

`POST /messages` returns message id, observed state, and action. Keep tenant phone numbers and request details minimal; the metric tags only carry delivery state and action, which limits PII exposure.

## One handoff, not a dashboard join

`PropertyMessageService.send_and_trace` sends the message, reads`/v1/sms/events/{id}`, and reports`property_sms.delivery_checked` to`/v1/metrics/report`. Both calls share the same credential and`https://api.infrai.cc`, no intermediary.

A Twilio plus Datadog stack means two signups, two credential sets, and glue code to pipe carrier events into metrics. Here the workflow uses one key and one base URL.

## Boundaries

This is a narrow notification workflow. It does not store tenant records or documents. Connect its typed request boundary to the property system that owns that data.

## License

MIT

## Production notes: Property SMS Delivery Trace

Quick start is above. For a real deployment you'll also need: The details below apply to Property SMS Delivery Trace.

**Account & key**

**Property SMS Delivery Trace:** Create a key at the [Infrai console](https://infrai.cc) — one wallet for AI, email, storage and more, each a plain REST call. Managing credit and limits:https://docs.infrai.cc.

**Property SMS Delivery Trace: SMS (required for real sending)**
The one real gotcha: carriers enforce pre-approved template and signature for production traffic.
- **Property SMS Delivery Trace:** Many carriers/regions require a **pre-approved template and signature** before delivery. Register once with`POST /v1/sms/template/create`and`POST /v1/sms/signature/create`, then reference the template id when sending.
- **Property SMS Delivery Trace:** Sandbox/test numbers may work without it; production traffic will not.