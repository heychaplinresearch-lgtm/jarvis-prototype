#!/usr/bin/env python3
"""Launch the Jarvis bot, extracting the API key from process 1 environment."""
import os, sys, subprocess

# Get key from /proc/1/environ
key = ""
with open('/proc/1/environ', 'rb') as f:
    for item in f.read().split(b'\x00'):
        decoded = item.decode('utf-8', errors='ignore')
        if decoded.startswith('ANTHROPIC_API_KEY='):
            key = decoded.split('=', 1)[1]
            break

if not key:
    print("ERROR: ANTHROPIC_API_KEY not found in /proc/1/environ")
    sys.exit(1)

print(f"Launching bot with key: {key[:12]}...")

env = os.environ.copy()
env['ANTHROPIC_API_KEY'] = key
env['SLACK_HOME_CHANNEL'] = 'D0BDUSZBB7V'

os.chdir('/home/hermes/jarvis-prototype')
os.execve(sys.executable, [sys.executable, '/home/hermes/jarvis-prototype/bot.py'], env)
