from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from api_integration_playground.client import MockTargetStore, run_integration
from api_integration_playground.mock_api import MockPagedApi


target = MockTargetStore()
result = run_integration(MockPagedApi(), target)
print(f"Fetched records: {len(result.records)}")
print(f"Normalized records: {len(result.normalized_records)}")
print(f"Records written to target: {result.metrics.records_written}")
print(f"Retries handled: {result.metrics.retries}")
print(f"Rate limits handled: {result.metrics.rate_limited}")
print(f"Timeouts handled: {result.metrics.timeouts}")
print(f"Token refreshes: {result.metrics.token_refreshes}")
