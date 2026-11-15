import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

log_path = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\2b682fd7-944e-4212-8d1f-cd18b91688cb\.system_generated\logs\transcript.jsonl")
with open(log_path, "r", encoding="utf-8") as f:
    for line in f:
        obj = json.loads(line)
        calls = obj.get("tool_calls", [])
        for c in calls:
            name = c.get("name", "") or c.get("tool_name", "")
            args = c.get("args", {})
            if "edit_file" in name or "write_file" in name:
                path = args.get("Path", "")
                if "generate_blitzwing_bundle" in path:
                    print(f"Step {obj.get('step_index')}: {name} {path}")
