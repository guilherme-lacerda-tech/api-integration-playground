from __future__ import annotations

import pytest

from api_integration_playground.client import ApiClient, MockTargetStore, run_integration
from api_integration_playground.mock_api import MockPagedApi, RateLimitError, RequestTimeoutError, TransientApiError


def test_integration_handles_synthetic_failures() -> None:
    api = MockPagedApi(failure_plan=["http_500", "http_429", "timeout"], max_token_uses=2)
    result = run_integration(api, MockTargetStore())

    assert len(result.records) == 9
    assert len(result.normalized_records) == 9
    assert result.metrics.retries == 3
    assert result.metrics.rate_limited == 1
    assert result.metrics.timeouts == 1
    assert result.metrics.records_written == 9
    assert result.metrics.token_refreshes >= 2
    assert result.metrics.pages == 3


def test_fetch_all_uses_cache() -> None:
    client = ApiClient(MockPagedApi(failure_plan=[]), retries=1)

    first = client.fetch_all("demo-client", "demo-secret", page_size=4)
    second = client.run("demo-client", "demo-secret", page_size=4)

    assert len(first) == 9
    assert second.metrics.cache_hits == 1


def test_invalid_credentials_are_rejected() -> None:
    client = ApiClient(MockPagedApi(failure_plan=[]), retries=1)

    with pytest.raises(PermissionError):
        client.fetch_all("bad-client", "bad-secret")


@pytest.mark.parametrize(
    ("failure", "expected_error"),
    [
        ("http_500", TransientApiError),
        ("http_429", RateLimitError),
        ("timeout", RequestTimeoutError),
    ],
)
def test_retry_exhaustion_records_failure(failure: str, expected_error: type[Exception]) -> None:
    client = ApiClient(MockPagedApi(failure_plan=[failure, failure], max_token_uses=10), retries=1)

    with pytest.raises(expected_error):
        client.run("demo-client", "demo-secret")


def test_normalized_records_are_written_to_target_store() -> None:
    target = MockTargetStore()
    result = run_integration(MockPagedApi(failure_plan=[], max_token_uses=10), target)

    assert result.metrics.records_written == 9
    assert target.records["REC-003"]["status"] == "pending"
    assert target.records["REC-003"]["source_system"] == "mock-api-a"
