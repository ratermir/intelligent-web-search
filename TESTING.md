# Testing checklist

This document focuses only on functional validation of retrieval quality and runtime behavior.
Security, observability and small-model arbitration are intentionally out of scope for this phase.

## Goal

Validate that the service:

- returns stable search results
- accepts normal pages via `simple` fetch when possible
- falls back to `complex` fetch when appropriate
- returns clear failure modes when content cannot be retrieved
- does not hang or accumulate stuck browser processes during repeated use

## Recommended test sequence

1. Start with `debug=true` for all fetch tests.
2. Run each test URL at least 3 times.
3. Record:
   - `status`
   - `reason`
   - `fetch_mode`
   - `used_fallback`
   - response time
   - whether returned content is actually useful
4. For browser-heavy scenarios, run 5 to 10 URLs concurrently.
5. Repeat the most problematic cases twice in a row to detect browser cleanup issues.

## Core scenarios

### 1. Small static page

Examples:
- short blog post
- simple product page with plain HTML
- tiny docs page

Expectations:
- `status=ok` or `partial`
- `fetch_mode=simple`
- `used_fallback=false`
- content should not be empty just because the page is short

Checks:
- short but valid pages are not escalated unnecessarily
- title extraction is correct
- redirects are handled

### 2. Large static page

Examples:
- long documentation page
- standards/reference page
- large article

Expectations:
- `status=ok`
- `fetch_mode=simple`
- `used_fallback=false`
- extracted content is reasonably complete and not cut too aggressively

Checks:
- truncation behavior via `IWS_MAX_CONTENT_CHARS`
- extraction quality on long pages
- performance remains acceptable

### 3. SPA shell with almost no server-rendered text

Examples:
- React/Vue app shell
- page that returns mostly `<div id="app">` or `<div id="root">`

Expectations:
- simple fetch is rejected
- `complex` fetch is attempted automatically
- final response should usually be `fetch_mode=complex`

Checks:
- `reason` from simple path indicates SPA/insufficient text
- fallback actually improves content quality

### 4. Dynamic page with delayed content load

Examples:
- page that fills content after XHR/fetch calls
- news page with delayed article body rendering

Expectations:
- simple fetch may fail quality checks
- complex fetch should succeed if extra wait is sufficient

Checks:
- tune `IWS_BROWSER_EXTRA_WAIT_MS`
- check whether `domcontentloaded` is enough or if this site family needs a different approach later

### 5. Anti-bot / challenge page

Examples:
- Cloudflare challenge
- robot check / CAPTCHA page

Expectations:
- simple fetch should detect challenge markers or blocked status
- complex fetch may or may not help
- if still blocked, response should be `not_retrievable`, not fake success

Checks:
- no false `ok` with challenge HTML as content
- returned `reason` is diagnostic enough

### 6. Login wall / SSO protected page

Examples:
- pages that redirect to sign-in
- docs behind SSO

Expectations:
- simple fetch often rejects result
- complex fetch may still fail
- final response should usually be `partial` or `not_retrievable`

Checks:
- sign-in pages are not mistaken for real content
- login redirect final URL is visible in diagnostics

### 7. Non-HTML content

Examples:
- PDF URL
- image URL
- ZIP/download link

Expectations:
- should not be reported as successful article text
- should return `not_retrievable` or clear unsupported-content reason

Checks:
- `content_type`
- `reason=unsupported_content_type`

### 8. Redirect-heavy page

Examples:
- tracking links
- shorteners
- redirect chains

Expectations:
- normal redirects should succeed
- redirect loops should fail cleanly

Checks:
- final URL is set
- too many redirects returns a clear failure

### 9. 404 / 410 page

Expectations:
- final result should be `not_retrievable`
- reason should be `not_found`

Checks:
- no fallback loop for obvious permanent misses

### 10. 5xx upstream error page

Expectations:
- should fail clearly
- should not be returned as real content

Checks:
- verify distinction between temporary upstream error vs. normal content

## Runtime behavior checks

### A. Parallel browser load

Run 5 to 10 simultaneous URLs that are known to trigger `complex` fetch.

Expectations:
- concurrency is bounded
- no burst of uncontrolled Chromium instances
- requests queue rather than crash

What to watch:
- memory usage
- process count
- eventual completion of all requests

### B. Repeated timeout scenario

Use a site that hangs or responds very slowly.

Expectations:
- request ends within configured timeout budget
- next requests still work afterwards
- no permanently stuck browser page/context remains

### C. Repeated failure scenario

Use several URLs that always fail:
- DNS failure
- refused connection
- broken TLS
- blocked site

Expectations:
- failures remain fast and deterministic
- no degradation of later successful requests

### D. Mixed workload

Run together:
- small static pages
- large pages
- SPA pages
- blocked pages

Expectations:
- simple pages should not slow down dramatically just because some complex pages are running
- complex concurrency limit should protect the process

## Suggested acceptance criteria for first functional milestone

A reasonable first milestone is:

- normal static pages succeed mostly through `simple` fetch
- SPA/dynamic pages frequently improve via `complex` fallback
- blocked/login/challenge pages fail honestly rather than returning junk as success
- no visible zombie Chromium buildup after repeated runs
- no hung requests beyond configured timeout budgets

## Things to tune after first test round

Most likely knobs:

- `IWS_MIN_OK_TEXT_CHARS`
- `IWS_MIN_PARTIAL_TEXT_CHARS`
- `IWS_BROWSER_EXTRA_WAIT_MS`
- `IWS_COMPLEX_FETCH_CONCURRENCY`
- `IWS_SIMPLE_FETCH_*_TIMEOUT`
- `IWS_COMPLEX_FETCH_NAV_TIMEOUT`
- `IWS_COMPLEX_FETCH_EXTRACT_TIMEOUT`
- marker lists in `heuristics.py`
