from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from typing import Deque


class IntegrationApiError(RuntimeError):
    status_code = 500


class TransientApiError(IntegrationApiError):
    status_code = 500


class RateLimitError(IntegrationApiError):
    status_code = 429

    def __init__(self, retry_after_seconds: float = 0.01) -> None:
        super().__init__("synthetic rate limit")
        self.retry_after_seconds = retry_after_seconds


class RequestTimeoutError(IntegrationApiError):
    status_code = 408


class ExpiredTokenError(PermissionError):
    pass


@dataclass(frozen=True)
class MockRecord:
    external_id: str
    status: str
    source_system: str
    updated_at: str

    def to_api_payload(self) -> dict:
        return {
            "id": self.external_id,
            "state": self.status,
            "source": self.source_system,
            "updatedAt": self.updated_at,
        }


class MockPagedApi:
    def __init__(self, failure_plan: list[str] | None = None, max_token_uses: int = 2) -> None:
        self.calls = 0
        self.auth_calls = 0
        self.failure_plan: Deque[str] = deque(["http_500", "http_429", "timeout"] if failure_plan is None else failure_plan)
        self.max_token_uses = max_token_uses
        self.token_uses: dict[str, int] = {}
        self.records = [
            MockRecord(f"REC-{i:03d}", "ok" if i % 3 else "pending", "mock-api-a", f"2026-08-13T10:{i:02d}:00Z")
            for i in range(1, 10)
        ]

    def authenticate(self, client_id: str, client_secret: str) -> str:
        if client_id != "demo-client" or client_secret != "demo-secret":
            raise PermissionError("invalid synthetic credentials")
        self.auth_calls += 1
        token = f"synthetic-token-{self.auth_calls}"
        self.token_uses[token] = 0
        return token

    def list_records(self, token: str, page: int, page_size: int, timeout_seconds: float = 1.0) -> dict:
        if token not in self.token_uses:
            raise ExpiredTokenError("invalid or expired token")
        if self.token_uses[token] >= self.max_token_uses:
            raise ExpiredTokenError("synthetic token expired")

        self.calls += 1
        self.token_uses[token] += 1
        self._maybe_fail(timeout_seconds)

        start = (page - 1) * page_size
        end = start + page_size
        items = [record.to_api_payload() for record in self.records[start:end]]
        return {"items": items, "next_page": page + 1 if end < len(self.records) else None}

    def _maybe_fail(self, timeout_seconds: float) -> None:
        if not self.failure_plan:
            return
        failure = self.failure_plan.popleft()
        if failure == "http_500":
            raise TransientApiError("synthetic HTTP 500")
        if failure == "http_429":
            raise RateLimitError()
        if failure == "timeout" or timeout_seconds <= 0:
            raise RequestTimeoutError("synthetic timeout")
