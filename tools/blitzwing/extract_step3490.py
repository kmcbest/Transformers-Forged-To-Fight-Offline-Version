import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

full_log = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\2b682fd7-944e-4212-8d1f-cd18b91688cb\.system_generated\logs\transcript_full.jsonl")
with open(full_log, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        if obj.get("step_index") == 3490:
            calls = obj.get("tool_calls", [])
            for c in calls:
                args = c.get("args", {})
                content = args.get("Content", "")
                with open("e:/Agent/TFTF-blender/tools/blitzwing/gen_bundle_step3490.py", "w", encoding="utf-8") as out:
                    out.write(content)
                print("Wrote gen_bundle_step3490.py, size:", len(content))
