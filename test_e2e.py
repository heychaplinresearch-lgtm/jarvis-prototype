#!/usr/bin/env python3
"""
End-to-end test of the Jarvis bot flow — simulates the full loop:
1. Receive a mention (as if from yichi.huang)
2. Parse intent
3. Post dry-run confirmation card
4. Simulate a ✅ reaction  
5. Execute and write audit row
"""
import sys, os, json, time
sys.path.insert(0, os.path.dirname(__file__))

import anthropic
from intent_parser import INTENT_TOOL, SYSTEM_PROMPT, _validate_intent
from pending_store import write_pending, get_by_message_ts, mark_executed
from audit_log import write_audit, query_audit
from slack_client import (
    post_message, update_message,
    build_confirmation_card, build_audit_ack_card,
)
import mock_heygen_api as heygen

CHANNEL = "D0BDUSZBB7V"
BOT_USER_ID = "U0BDYHHJQTY"
OWNER_SLACK_ID = "U0BBD6002R2"  # yichi.huang
CONFIDENCE_THRESHOLD = 0.70

def run_e2e_test(utterance: str, label: str):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"Utterance: {utterance}")
    print('='*60)
    
    # Step 1: Parse intent
    client = anthropic.Anthropic()
    response = client.messages.create(
        model="claude-haiku-4-5",
        max_tokens=512,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": utterance}],
        tools=[INTENT_TOOL],
        tool_choice={"type": "tool", "name": "parse_intent"},
    )
    intent = None
    for block in response.content:
        if block.type == "tool_use":
            intent = _validate_intent(block.input, utterance)
    
    if not intent:
        print("FAIL: No intent parsed")
        return
    
    conf = intent.get("confidence", 0)
    print(f"[1] Parse: action={intent.get('action')} target={intent.get('target_email')} conf={conf:.0%}")
    
    if intent.get("needs_clarification") or conf < CONFIDENCE_THRESHOLD:
        q = intent.get("clarifying_question", "Need more info")
        print(f"[2] CLARIFY: {q}")
        resp = post_message(CHANNEL, f"🤔 Clarifying question posted to Slack:\n_{q}_")
        print(f"    Posted to Slack: ts={resp['ts']}")
        return
    
    if intent.get("action") == "lookup":
        # Read-only: no confirmation
        result = heygen.lookup_user(intent.get("target_email", ""))
        audit_id = write_audit(OWNER_SLACK_ID, "lookup", "success", intent,
                                before_state=result, channel_id=CHANNEL)
        print(f"[2] LOOKUP result: {json.dumps(result)}")
        print(f"[3] Audit written: {audit_id}")
        resp = post_message(CHANNEL, f"Lookup result for `{intent['target_email']}`: `{json.dumps(result)}`\nAudit: `{audit_id}`")
        print(f"    Posted to Slack: ts={resp['ts']}")
        return
    
    # Write action: dry-run → confirmation card
    target_email = intent.get("target_email", "")
    before_state = heygen.get_user_state(target_email)
    print(f"[2] Before state: {json.dumps(before_state)}")
    
    # Post confirmation card
    card_resp = post_message(
        CHANNEL,
        f"Jarvis dry-run for `{target_email}` — react ✅ to confirm",
        blocks=build_confirmation_card(intent, before_state, "PENDING"),
    )
    card_ts = card_resp["ts"]
    print(f"[3] Confirmation card posted: ts={card_ts}")
    
    # Store pending
    pending_id = write_pending(
        actor_slack_id=OWNER_SLACK_ID,
        intent=intent,
        before_state=before_state,
        channel_id=CHANNEL,
        thread_ts=card_ts,
        message_ts=card_ts,
    )
    print(f"[4] Pending stored: {pending_id}")
    
    # Simulate ✅ reaction (in real bot this comes from Slack reaction_added event)
    print(f"[5] Simulating ✅ reaction from {OWNER_SLACK_ID}...")
    pending = get_by_message_ts(card_ts)
    assert pending is not None, "Pending not found!"
    
    # TOCTOU check
    current_state = heygen.get_user_state(target_email)
    assert current_state == before_state, "State changed between dry-run and execute!"
    print(f"[6] TOCTOU check: state unchanged ✓")
    
    # Execute
    from bot import _execute_intent
    after_state = _execute_intent(intent)
    print(f"[7] Executed! After state: {json.dumps(after_state)}")
    
    # Write audit BEFORE acking
    audit_id = write_audit(
        actor_slack_id=OWNER_SLACK_ID,
        action=intent.get("action", "unknown"),
        result="success",
        intent=intent,
        before_state=before_state,
        after_state=after_state,
        channel_id=CHANNEL,
        message_ts=card_ts,
    )
    mark_executed(pending_id)
    print(f"[8] Audit row written: {audit_id}")
    
    # Post ack
    ack_resp = post_message(
        CHANNEL,
        f"✅ Done. Audit: `{audit_id}`",
        blocks=build_audit_ack_card(audit_id, intent.get("action", ""), target_email, after_state),
    )
    print(f"[9] Ack posted to Slack: ts={ack_resp['ts']}")
    print(f"\nSUCCESS: Full round-trip completed for {label}")


if __name__ == "__main__":
    # Test 1: Quota grant (the primary use case)
    run_e2e_test(
        "comp teodora@heygen.com a creator sub for a year with 9999 credits",
        "Quota Grant — full round trip"
    )
    
    # Test 2: Lookup (read-only, no confirmation)
    run_e2e_test(
        "who is mtoth109@gmail.com and what did they do last 7 days",
        "Lookup — read-only, no confirmation needed"
    )
    
    # Test 3: Ambiguous → clarifying question
    run_e2e_test(
        "give someone some credits",
        "Ambiguous — should trigger clarifying question"
    )
    
    # Test 4: Create account
    run_e2e_test(
        "create a test account for newpartner@acme.com, creator tier, 90 day expiry",
        "Create Account"
    )
    
    print("\n\nAudit log:")
    rows = query_audit(limit=10)
    for r in rows:
        print(f"  {r['audit_id']} | {r['action']} | {r['target_email']} | {r['result']} | {r['ts'][:19]}")
