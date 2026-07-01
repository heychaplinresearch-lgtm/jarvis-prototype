#!/usr/bin/env python3
"""Send a test @mention to trigger the bot."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from slack_client import post_message

channel = 'D0BDUSZBB7V'
BOT_USER_ID = 'U0BDYHHJQTY'

resp = post_message(
    channel,
    f"<@{BOT_USER_ID}> comp teodora@heygen.com a creator sub for a year with 9999 credits",
)
print(f"Test mention posted: ts={resp['ts']}")
