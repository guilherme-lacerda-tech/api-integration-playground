from __future__ import annotations

import time

from .mock_api import MockPagedApi, TransientApiError


class ApiClient:
    def __init__(self, api: MockPagedApi, retries: int = 2, rate_limit_seconds: float = 0.0) -> None:
        self.api = api
        self.retries = retries
        self.rate_limit_seconds = rate_limit_seconds
        self.cache: dict[str, list[dict]] = {}

    def fetch_all(self, client_id: str, client_secret: str, page_size: int = 3) -> list[dict]:
        cache_key = f"{client_id}:{page_size}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        token = self.api.authenticate(client_id, client_secret)
        page = 1
        records: list[dict] = []
        while page is not None:
            response = self._with_retry(lambda: self.api.list_records(token, page, page_size))
            records.extend(response["items"])
            page = response["next_page"]
            if self.rate_limit_seconds:
                time.sleep(self.rate_limit_seconds)
        self.cache[cache_key] = records
        return records

    def _with_retry(self, operation):
        for attempt in range(self.retries + 1):
            try:
                return operation()
            except TransientApiError:
                if attempt >= self.retries:
                    raise
                time.sleep(0.01)
