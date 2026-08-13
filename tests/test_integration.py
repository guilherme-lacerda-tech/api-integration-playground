from __future__ import annotations

from api_integration_playground.client import ApiClient, MockTargetStore, run_integration
from api_integration_playground.mock_api import MockPagedApi


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


def test_fetch_all_uses_cache() -> None:
    client = ApiClient(MockPagedApi(failure_plan=[]), retries=1)

    first = client.fetch_all("demo-client", "demo-secret", page_size=4)
    second = client.run("demo-client", "demo-secret", page_size=4)

    assert len(first) == 9
    assert second.metrics.cache_hits == 1
