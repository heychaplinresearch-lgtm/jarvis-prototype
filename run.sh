#!/bin/bash
# Bootstrap the ANTHROPIC_API_KEY from process 1 env and run a python script
KEY=$(cat /proc/1/environ | tr '\0' '\n' | grep '^ANTHROPIC_API_KEY=' | head -1 | cut -d= -f2-)
export ANTHROPIC_API_KEY="$KEY"
echo "API key: ${KEY:0:12}..."
cd /home/hermes/jarvis-prototype
python3 "$@"
