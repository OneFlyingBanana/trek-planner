#!/bin/bash
# Register MCP servers for Claude Code
# Run this after cloning the repo: bash setup-mcp.sh

set -e

echo "Registering MCP servers for Claude Code..."

claude mcp add trek -- bash core/trek-mcp.sh
claude mcp add google-maps -- bash core/google-maps-mcp.sh
claude mcp add airbnb -- npx -y @openbnb/mcp-server-airbnb

echo "Done! Make sure you have a .env file with:"
echo "  TREK_URL=<your trek url>"
echo "  TREK_MCP_TOKEN=<your token>"
echo "  GOOGLE_MAPS_API_KEY=<your api key>"
