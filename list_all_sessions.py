import sys
import os
import io

# Force UTF-8 for output
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

sys.path.append(os.getcwd())
from scripts.jules_bridge import JulesBridge
import json

b = JulesBridge()
sessions = b.list_sessions(page_size=20)

print("\n📊 All Jules Sessions")
print("-" * 80)
for s in sessions:
    sid = s.get("id")
    state = s.get("state")
    title = s.get("title")
    print(f"[{state:<12}] {sid} : {title}")
print("-" * 80)
