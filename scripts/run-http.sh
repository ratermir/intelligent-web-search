#!/usr/bin/env bash
set -euo pipefail
echo "HTTP transport is intentionally not enabled in this build. Use stdio transport via an MCP host or proxy." >&2
exit 1
