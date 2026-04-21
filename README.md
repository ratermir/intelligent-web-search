# Intelligent Web Search

Self-hosted Python MCP server that combines:

- search via `ddgs`
- fast/simple URL fetch
- browser-based complex fetch with Playwright/Chromium
- deterministic heuristics for routing and quality evaluation
- a stable outward-facing tool contract for an LLM host

## Goals

This project is designed for exactly this pattern:

1. search the web cheaply
2. try a fast fetch first
3. inspect the result
4. fall back to browser rendering only when needed
5. keep the option open for a future small classifier model for borderline cases

## Exposed MCP tools

- `search_web(query, limit=5, region="wt-wt", safesearch="moderate")`
- `fetch_content(url, prefer_complex=False, debug=False)`
- `smart_retrieve(query, search_limit=5, fetch_limit=3, debug=False)`

## Public result contract

The fetch tools return a structured object with:

- `status`: `ok` | `partial` | `not_retrievable`
- `reason`: machine-readable reason
- `fetch_mode`: `simple` | `complex` | `none`
- `used_fallback`: whether complex fetch was used after simple fetch failed quality checks
- `title`, `content`, `markdown`, `url`, `final_url`
- `http_status`
- `diagnostics` when `debug=true`

## Internal workflow

Internally the decision layer uses three action states:

- `accept_simple`
- `retry_with_complex`
- `terminal_fail`

These are not exposed directly to the caller.

## Directory layout

```text
src/intelligent_web_search/
  models.py          Pydantic schemas
  search.py          ddgs-based search wrapper
  fetch_simple.py    cheap HTTP fetch + extraction
  fetch_complex.py   Playwright browser fetch
  heuristics.py      routing and quality checks
  orchestrator.py    end-to-end fetch orchestration
  server.py          MCP server entrypoint
scripts/
  install-playwright.sh
  run-http.sh
  run-stdio.sh
examples/
  openwebui-mcp-config.json
Dockerfile
```

## Run locally

### 1. Install dependencies

```bash
python -m venv .venv
. .venv/bin/activate
pip install -U pip
pip install -e .
python -m playwright install chromium
```

### 2. Run in stdio mode

```bash
intelligent-web-search --transport stdio
```

### 3. Current transport

This build is intentionally pinned to `stdio` for maximum MCP compatibility in first deployments.
HTTP transport can be added later, but is not enabled in the current server entrypoint.

## Docker build

```bash
docker build -t intelligent-web-search:latest .
```

## Docker run

```bash
docker run --rm -i \
  -e IWS_USER_AGENT="IntelligentWebSearch/0.1 (+local)" \
  intelligent-web-search:latest \
  intelligent-web-search --transport stdio
```

## Important runtime notes

### Browser path concurrency

The complex fetch path is intentionally expensive. By default, the code uses a semaphore so that browser fetches remain bounded. Tune with:

- `IWS_COMPLEX_FETCH_CONCURRENCY`
- `IWS_COMPLEX_FETCH_TIMEOUT`
- `IWS_SIMPLE_FETCH_TIMEOUT`

### Security posture

The service opens arbitrary URLs. Treat it as an untrusted-content processor.

Recommended hardening:

- run as non-root
- apply CPU/RAM limits
- restrict egress if your environment allows it
- keep Chromium sandboxing enabled where possible
- isolate from sensitive internal networks

### Future small-model hook

The code intentionally leaves a hook for a future classifier to arbitrate only borderline cases after deterministic heuristics run.

## Suggested Open-WebUI / MCP usage

Expose this service as a single MCP server. Let the main model call:

- `search_web` when it needs discovery
- `fetch_content` when it already has a URL
- `smart_retrieve` when it wants a query-to-content pipeline



## Functional test plan

See `TESTING.md` for the recommended scenario matrix and runtime checks.
