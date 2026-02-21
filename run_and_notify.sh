#!/bin/bash
cd ~/projects/gem-screener
export PYTHONPATH=src
REPORT=$(uv run python -m gem_screener 2>&1 | tail -40)
# Send to telegram via openclaw system event
openclaw system event --text "📊 Gem Screener Report:\n\n$REPORT" --mode now 2>/dev/null || true
# Also save to file
echo "$(date): Report generated" >> ~/projects/gem-screener/runs.log
echo "$REPORT" >> ~/projects/gem-screener/runs.log
echo "---" >> ~/projects/gem-screener/runs.log
