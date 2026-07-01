#!/usr/bin/env python3
"""Test the intent parser against real Claude."""
import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))

import anthropic
from intent_parser import SYSTEM_PROMPT, INTENT_TOOL, _validate_intent

client = anthropic.Anthropic()

tests = [
    "comp teodora@heygen.com a creator sub for a year with 9999 credits",
    "who is mtoth109@gmail.com and what did they do last 7 days",
    "give someone some credits",
    "grant 100 api credits to partner@acme.com for 30 days",
    "14-day enterprise trial for admin@example.com, 5 seats",
    "create a test account for partner@acme.com, creator tier, 90 day expiry",
]

print("Intent Parser Test\n" + "="*60)
for utt in tests:
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": utt}],
        tools=[INTENT_TOOL],
        tool_choice={"type": "tool", "name": "parse_intent"},
    )
    for block in response.content:
        if block.type == "tool_use":
            r = _validate_intent(block.input, utt)
            conf = r.get("confidence", 0)
            needs_clarify = r.get("needs_clarification", False)
            flag = "OK " if conf >= 0.7 and not needs_clarify else "?? "
            print(f"{flag} \"{utt}\"")
            print(f"     action={r.get('action')} target={r.get('target_email')} tier={r.get('tier')} credits={r.get('credits')} days={r.get('duration_days')} conf={conf:.0%}")
            if needs_clarify:
                print(f"     CLARIFY: {r.get('clarifying_question')}")
            print()
