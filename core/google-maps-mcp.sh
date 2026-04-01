#!/bin/bash
# Load Google Maps API key from .env
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
if [ -f "$SCRIPT_DIR/.env" ]; then
  export $(grep -v '^#' "$SCRIPT_DIR/.env" | grep -E 'GOOGLE_MAPS_API_KEY' | xargs)
fi

if [ -z "$GOOGLE_MAPS_API_KEY" ]; then
  echo "Error: GOOGLE_MAPS_API_KEY not set in .env" >&2
  exit 1
fi

exec npx -y @modelcontextprotocol/server-google-maps
