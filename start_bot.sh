#!/bin/bash
KEY=$(cat /proc/1/environ | tr '\0' '\n' | grep "^ANTHROPIC_API_KEY=" | head -1 | cut -d= -f2-)
export ANTHROPIC_API_KEY=$KEY
echo "API key: ${KEY:0:12}..."
export SLACK_HOME_CHANNEL=D0BDUSZBB7V
cd /home/hermes/jarvis-prototype
exec python3 bot.py
