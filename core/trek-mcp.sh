#!/bin/bash
# Load TREK config from .env
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
  export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep -E 'TREK_(URL|MCP_TOKEN)' | xargs)
fi

if [ -z "$TREK_MCP_TOKEN" ]; then
  echo "Error: TREK_MCP_TOKEN not set in .env" >&2
  exit 1
fi

if [ -z "$TREK_URL" ]; then
  echo "Error: TREK_URL not set in .env" >&2
  exit 1
fi

exec npx -y mcp-remote "${TREK_URL}/mcp" --header "Authorization: Bearer $TREK_MCP_TOKEN"
