import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json

with open(r"e:\Agent\TFTF-blender\Server\bot_names_zh.json", "r", encoding="utf-8") as f:
    d = json.load(f)

for k, v in d.items():
    if any(w in v for w in ("喷气", "冲锋", "天火", "红蜘蛛", "滑翔机", "风刃")):
        print(f"{k}: {v}")
