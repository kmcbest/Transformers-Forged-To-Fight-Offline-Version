import json
from pathlib import Path

fpath = Path(r"E:\Agent\TFTF-blender\Server\bot_names_zh.json")
data = json.loads(fpath.read_text(encoding="utf-8"))

data["onslaught_gs"] = {
    "en": "Onslaught",
    "zh": "袭击",
    "faction": "霸天虎",
    "note": "塞伯坦陨落·爆破系",
    "desc": "战车队冷酷沉着的战术指挥官，重装炮火专家。他擅长制定周密残忍的突袭计划，身披重甲，背负双联防空火箭炮与小臂转轮重机炮，在战场上以压倒性的火力粉碎一切阻碍。"
}

fpath.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")
print("[OK] Updated Server/bot_names_zh.json successfully!")
