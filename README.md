    # API Integration Playground

    Independent public portfolio project for **Python**, **automation**,
    **systems integration** and **solutions engineering**.

    This repository was created from scratch with a fictional domain and
    synthetic data. It does not contain corporate code, real data, private
    endpoints, credentials, logs or proprietary rules.

    ## Problem

    API integrations need authentication, pagination, retry, error handling and clear logs.

    ## Objective

    Demonstrate robust API client patterns against a simulated API.

    ## Current Features

    - Simulated authentication.
- Paged records.
- Transient failure retry.
- In-memory cache.

    ## Architecture

    ```mermaid
    flowchart LR
        A["Synthetic input"] --> B["Python processing"]
        B --> C["Rules / validation"]
        C --> D["Generated local output"]
        D --> E["Future API / dashboard"]
    ```

    See [docs/architecture.md](docs/architecture.md) for details.

    ## Stack

    Current:

    `Python` `Mock API` `Retry` `Pagination` `Cache`

    Planned evolution:

    - PyTest
- httpx
- FastAPI mock server
- Docker
- GitHub Actions

    ## Run Locally

    ```powershell
    python examples/run_demo.py
    ```

    The demo uses only files under `data/sample/` and writes generated output
    to ignored local folders.

    ## Repository Workflow

    This project is intended to evolve through:

    - Issues for planned work.
    - Milestones for learning phases.
    - Small branches and pull requests.
    - Releases when a useful increment is ready.

    Draft issues are documented in [docs/github-issues.md](docs/github-issues.md).

    ## Roadmap

    See [ROADMAP.md](ROADMAP.md).

    ## Security and Independence

    See [SECURITY.md](SECURITY.md) and [DISCLAIMER.md](DISCLAIMER.md).
