# Design notes

## Why one container

This build deliberately keeps these parts together in one OCI image:

- MCP server
- search adapter (`ddgs`)
- simple fetcher
- complex fetcher (Playwright)
- deterministic decision logic

That gives a single deployable artifact while still keeping the code modular.

## Internal decision model

The orchestrator reasons with three internal action states:

- `accept_simple`
- `retry_with_complex`
- `terminal_fail`

These internal states are translated to the public API contract.

## Public fetch contract

- `ok`: useful content was retrieved
- `partial`: some content exists but quality may be incomplete
- `not_retrievable`: content could not be obtained reliably

## Failure taxonomy

Returned `reason` values are intended to be machine-readable.
Typical values:

- `not_found`
- `network_or_timeout`
- `challenge_or_bot_protection_detected`
- `javascript_required_marker_detected`
- `spa_shell_marker_with_insufficient_text`
- `complex_fetch_failed_after_simple_rejected`

## Future classifier hook

The deterministic heuristic path should stay first.
A future small model should be inserted only for borderline outcomes, not for obvious cases.

Suggested future flow:

```text
simple fetch
-> hard heuristics
-> if borderline: small classifier
-> accept simple OR retry complex OR terminal fail
```

## Resource guidance

Suggested starting point per container:

- CPU: 1-2 vCPU
- memory: 1.5-3 GiB

Increase memory when browser concurrency is raised.

## Things intentionally left out

This build does not yet include:

- HTTP MCP transport
- proxy rotation
- stealth browser plugins
- screenshot capture
- PDF-specific extraction
- robots.txt / policy enforcement layer
- URL allow/deny lists

Those are good next steps, but not required for the core architecture.
