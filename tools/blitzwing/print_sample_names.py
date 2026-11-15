import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r"e:\Agent\TFTF-blender\Server\bot_names_zh.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for k, v in list(d.items())[:10]:
    print(f"{k}: {v}")
