# Architecture

## Design Goal

Demonstrate integration behavior that is common in real REST environments while keeping every API, token and record synthetic.

## Flow

```mermaid
flowchart TB
    Source["Mock API A"] --> Client["Resilient API client"]
    Client --> Retry["Retry, backoff, timeout handling"]
    Retry --> Normalize["Normalization"]
    Normalize --> Target["Mock API B / target store"]
    Client --> Metrics["Integration metrics and logs"]
```

## Failure Scenarios

- `HTTP 429` rate limiting with retry-after behavior.
- `HTTP 500` transient server failure.
- Request timeout.
- Expired synthetic token with re-authentication.

## Boundaries

- No external API credentials are used.
- All tokens are generated in memory.
- The target store is synthetic and can be replaced by a database or API later.
