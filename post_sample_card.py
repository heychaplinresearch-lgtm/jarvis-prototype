#!/usr/bin/env python3
"""Post a sample Jarvis confirmation card to Slack to verify the UI."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from slack_client import post_message, build_confirmation_card, build_clarifying_question_card
from mock_heygen_api import get_user_state

# Read channel from .env
channel = "D0BDUSZBB7V"
env_path = os.path.expanduser("~/.hermes/.env")
for line in open(env_path):
    if line.startswith("SLACK_HOME_CHANNEL="):
        val = line.split("=", 1)[1].strip()
        if val and val != "ignore":
            channel = val
        break

print(f"Posting to channel: {channel}")

# 1. Sample confirmation card for quota grant
before_state = get_user_state("teodora@heygen.com")
intent = {
    "action": "quota_grant",
    "target_email": "teodora@heygen.com",
    "tier": "creator",
    "credits": 9999,
    "duration_days": 365,
    "confidence": 0.95,
    "raw_utterance": "comp teodora@heygen.com a creator sub for a year with 9999 credits",
}

resp = post_message(
    channel,
    "🤖 *Jarvis Prototype* — here's what a confirmation card looks like:",
)
thread_ts = resp["ts"]

card_resp = post_message(
    channel,
    "Action preview — react checkmark to confirm",
    thread_ts=thread_ts,
    blocks=build_confirmation_card(intent, before_state, "jrv_p_DEMO001"),
)
print(f"Confirmation card posted: ts={card_resp['ts']}")

# 2. Sample clarifying question
clari_resp = post_message(
    channel,
    "And here's what a clarifying question looks like:",
    thread_ts=thread_ts,
    blocks=build_clarifying_question_card(
        "I need a few details:\n"
        "1. What email address should receive the credits?\n"
        "2. How many credits?\n"
        "3. What tier (creator/pro/business)?"
    ),
)
print(f"Clarifying question posted: ts={clari_resp['ts']}")

print(f"\nThread: https://slack.com/archives/{channel}/p{thread_ts.replace('.','')}")
