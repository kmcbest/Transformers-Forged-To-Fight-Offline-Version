import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

full_log = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\2b682fd7-944e-4212-8d1f-cd18b91688cb\.system_generated\logs\transcript_full.jsonl")
target_steps = {3878, 4230}
with open(full_log, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("step_index") in target_steps:
            print(f"=== STEP {obj.get('step_index')} ===")
            calls = obj.get("tool_calls", [])
            for c in calls:
                args = c.get("args", {})
                print("TARGET:\n", args.get("Target"))
                print("REPLACEMENT:\n", args.get("Replacement"))
