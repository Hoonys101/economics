import sys
import os
import io

# Force UTF-8 for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.getcwd())
from scripts.jules_bridge import JulesBridge
import json

b = JulesBridge()
sessions = b.list_sessions(page_size=15)
target_ids = ['1168830734155576498', '7846289173909215125', '9460236520355501841']

print("\n📊 Jules Status Monitor")
print("-" * 50)
for s in sessions:
    sid = s.get("id")
    if sid in target_ids:
        state = s.get("state")
        title = s.get("title")
        print(f"[{state:<12}] {sid} : {title}")
print("-" * 50)
