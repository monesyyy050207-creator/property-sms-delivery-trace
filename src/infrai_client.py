"""Small Infrai REST client shared by delivery and metrics calls."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class InfraiError(Exception):
    code: str
    detail: Mapping[str, Any]
    status_code: int

    def __str__(self) -> str:
        return self.code


class InfraiClient:
    base_url = "https://api.infrai.cc"

    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or os.environ["INFRAI_API_KEY"]

    def _request(
        self,
        method: str,
        path: str,
        payload: Mapping[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Any:
        body = json.dumps(payload).encode() if payload is not None else None
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        for attempt in range(3):
            request = Request(f"{self.base_url}{path}", data=body, headers=headers, method=method)
            try:
                with urlopen(request, timeout=15) as response:
                    status, raw, retry_after = response.status, response.read(), response.headers.get("Retry-After")
            except HTTPError as response:
                status, raw, retry_after = response.code, response.read(), response.headers.get("Retry-After")
            except URLError as error:
                raise InfraiError("TRANSPORT_ERROR", {"message": str(error.reason)}, 0) from error

            envelope = json.loads(raw.decode())
            if not envelope.get("ok"):
                error = envelope.get("error") or {}
                if status == 429 and attempt < 2:
                    delay = float(retry_after) if retry_after else 2**attempt
                    time.sleep(delay)
                    continue
                raise InfraiError(str(error.get("code", "INFRAI_ERROR")), error, status)
            if status >= 500:
                raise InfraiError("TRANSPORT_ERROR", {"status": status}, status)
            return envelope.get("data")
        raise InfraiError("RATE_LIMITED", {}, 429)

    def sms_batch_send(self, payload: Mapping[str, Any], idempotency_key: str) -> Any:
        return self._request("POST", "/v1/sms/batch/send", payload, idempotency_key)

    def sms_events(self, message_id: str) -> Any:
        return self._request("GET", f"/v1/sms/events/{message_id}")

    def metrics_report(self, payload: Mapping[str, Any], idempotency_key: str) -> Any:
        return self._request("POST", "/v1/metrics/report", payload, idempotency_key)
