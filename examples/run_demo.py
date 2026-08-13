from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api_integration_playground.client import ApiClient
from api_integration_playground.mock_api import MockPagedApi


client = ApiClient(MockPagedApi(), retries=2)
records = client.fetch_all("demo-client", "demo-secret")
cached = client.fetch_all("demo-client", "demo-secret")
print(f"Fetched records: {len(records)}")
print(f"Cache reused: {records == cached}")
