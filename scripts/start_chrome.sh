#!/usr/bin/env bash
# Launch Chrome with CDP remote debugging enabled.
# Usage: ./scripts/start_chrome.sh [port]
#
# After Chrome opens:
#   1. Log in to JD / Taobao in the browser
#   2. Start the app: uvicorn src.app:app --reload --port 8000
#   3. The app will auto-connect via CDP and reuse your login session

set -euo pipefail

PORT="${1:-9222}"
USER_DATA_DIR="${SA_CHROME_USER_DATA:-$HOME/.shopping-assist-chrome}"

if [[ "$OSTYPE" == "darwin"* ]]; then
    CHROME="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    if [[ ! -f "$CHROME" ]]; then
        CHROME="/Applications/Chromium.app/Contents/MacOS/Chromium"
    fi
elif [[ -f /usr/bin/google-chrome ]]; then
    CHROME="/usr/bin/google-chrome"
elif [[ -f /usr/bin/google-chrome-stable ]]; then
    CHROME="/usr/bin/google-chrome-stable"
elif [[ -f /usr/bin/chromium-browser ]]; then
    CHROME="/usr/bin/chromium-browser"
elif [[ -f /usr/bin/chromium ]]; then
    CHROME="/usr/bin/chromium"
else
    echo "Error: Chrome/Chromium not found" >&2
    exit 1
fi

mkdir -p "$USER_DATA_DIR"

echo "======================================"
echo "  Shopping Assist - Chrome CDP"
echo "======================================"
echo ""
echo "  Chrome: $CHROME"
echo "  CDP Port: $PORT"
echo "  Profile: $USER_DATA_DIR"
echo ""
echo "  1. Login to JD / Taobao in browser"
echo "  2. Run: uvicorn src.app:app --reload --port 8000"
echo ""

exec "$CHROME" \
    --remote-debugging-port="$PORT" \
    --user-data-dir="$USER_DATA_DIR" \
    --no-first-run \
    --no-default-browser-check
