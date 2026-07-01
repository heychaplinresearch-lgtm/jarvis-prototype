#!/usr/bin/env python3
"""Check last messages in the DM channel."""
import json, urllib.request, os, sys
sys.path.insert(0, os.path.dirname(__file__))
from slack_client import _bot_token

token = _bot_token()
url = 'https://slack.com/api/conversations.history?channel=D0BDUSZBB7V&limit=5'
req = urllib.request.Request(url, headers={'Authorization': f'Bearer {token}'})
resp = json.loads(urllib.request.urlopen(req).read())
msgs = resp.get('messages', [])
print(f'Got {len(msgs)} messages, ok={resp.get("ok")}')
for m in msgs[:5]:
    user = m.get("user", "bot")
    txt = m.get("text", "")[:80]
    print(f'  ts={m["ts"]} user={user}: {txt}')
