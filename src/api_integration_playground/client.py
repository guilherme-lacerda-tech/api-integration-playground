from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field

from .mock_api import ExpiredTokenError, MockPagedApi, RateLimitError, RequestTimeoutError, TransientApiError


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClientConfig:
    retries: int = 3
    timeout_seconds: float = 1.0
    base_backoff_seconds: float = 0.01
    rate_limit_seconds: float = 0.0
    cache_enabled: bool = True


@dataclass
class IntegrationMetrics:
    pages: int = 0
    retries: int = 0
    rate_limited: int = 0
    timeouts: int = 0
    token_refreshes: int = 0
    cache_hits: int = 0
    records_written: int = 0
    failures: list[str] = field(default_factory=list)


@dataclass
class IntegrationResult:
    records: list[dict]
    normalized_records: list[dict]
    metrics: IntegrationMetrics


class MockTargetStore:
    def __init__(self) -> None:
        self.records: dict[str, dict] = {}

    def upsert_many(self, records: list[dict]) -> int:
        for record in records:
            self.records[record["external_id"]] = record
        return len(records)


class ApiClient:
    def __init__(self, api: MockPagedApi, retries: int = 2, rate_limit_seconds: float = 0.0) -> None:
        self.api = api
        self.config = ClientConfig(retries=retries, rate_limit_seconds=rate_limit_seconds)
        self.cache: dict[str, list[dict]] = {}

    def fetch_all(self, client_id: str, client_secret: str, page_size: int = 3) -> list[dict]:
        return self.run(client_id, client_secret, page_size).records

    def run(self, client_id: str, client_secret: str, page_size: int = 3) -> IntegrationResult:
        cache_key = f"{client_id}:{page_size}"
        metrics = IntegrationMetrics()
        if self.config.cache_enabled and cache_key in self.cache:
            metrics.cache_hits = 1
            cached = self.cache[cache_key]
            return IntegrationResult(cached, normalize_records(cached), metrics)

        token = self._authenticate(client_id, client_secret, metrics)
        page = 1
        records: list[dict] = []
        while page is not None:
            current_page = page
            response, token = self._with_retry(
                lambda current_token, page_number=current_page: self.api.list_records(
                    current_token,
                    page_number,
                    page_size,
                    timeout_seconds=self.config.timeout_seconds,
                ),
                token,
                client_id,
                client_secret,
                metrics,
            )
            metrics.pages += 1
            records.extend(response["items"])
            page = response["next_page"]
            if self.config.rate_limit_seconds:
                time.sleep(self.config.rate_limit_seconds)

        normalized = normalize_records(records)
        self.cache[cache_key] = records
        return IntegrationResult(records, normalized, metrics)

    def _authenticate(self, client_id: str, client_secret: str, metrics: IntegrationMetrics) -> str:
        metrics.token_refreshes += 1
        return self.api.authenticate(client_id, client_secret)

    def _with_retry(self, operation, token: str, client_id: str, client_secret: str, metrics: IntegrationMetrics):
        for attempt in range(self.config.retries + 1):
            try:
                return operation(token), token
            except ExpiredTokenError:
                token = self._authenticate(client_id, client_secret, metrics)
            except RateLimitError as exc:
                metrics.rate_limited += 1
                if attempt >= self.config.retries:
                    metrics.failures.append("http_429")
                    raise
                self._sleep(exc.retry_after_seconds, attempt, metrics, "HTTP 429")
            except RequestTimeoutError:
                metrics.timeouts += 1
                if attempt >= self.config.retries:
                    metrics.failures.append("timeout")
                    raise
                self._sleep(self.config.base_backoff_seconds, attempt, metrics, "timeout")
            except TransientApiError:
                if attempt >= self.config.retries:
                    metrics.failures.append("http_500")
                    raise
                self._sleep(self.config.base_backoff_seconds, attempt, metrics, "HTTP 500")
        raise RuntimeError("retry loop exhausted")

    @staticmethod
    def _sleep(base_seconds: float, attempt: int, metrics: IntegrationMetrics, reason: str) -> None:
        metrics.retries += 1
        delay = min(base_seconds * (2**attempt), 0.05)
        logger.info("Retrying after %s in %.3fs", reason, delay)
        time.sleep(delay)


def normalize_records(records: list[dict]) -> list[dict]:
    return [
        {
            "external_id": record["id"],
            "status": record["state"],
            "source_system": record["source"],
            "updated_at": record["updatedAt"],
        }
        for record in records
    ]


def run_integration(api: MockPagedApi | None = None, target: MockTargetStore | None = None) -> IntegrationResult:
    api = api or MockPagedApi()
    target = target or MockTargetStore()
    result = ApiClient(api, retries=4).run("demo-client", "demo-secret", page_size=3)
    result.metrics.records_written = target.upsert_many(result.normalized_records)
    return result
