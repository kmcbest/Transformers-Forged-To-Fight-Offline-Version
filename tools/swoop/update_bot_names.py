import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
from pathlib import Path

names_path = Path(r"E:\Agent\TFTF-blender\Server\bot_names_zh.json")
with open(names_path, "r", encoding="utf-8") as f:
    data = json.load(f)

data["swoop_gs_deluxe2008"] = {
    "en": "Swoop",
    "zh": "飞标",
    "faction": "汽车人",
    "note": "机器恐龙 科技系",
    "desc": "汽车人机器恐龙中的空中侦察与对地轰炸专家。飞标在人形下可从胸口翼龙嘴喷吐烈火，在载具形态下化身机械翼龙撕裂苍穹。"
}

data["swoop"] = {
    "en": "Swoop",
    "zh": "飞标",
    "faction": "汽车人",
    "note": "机器恐龙 科技系"
}

with open(names_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=4)

print("Updated Server/bot_names_zh.json successfully!")
