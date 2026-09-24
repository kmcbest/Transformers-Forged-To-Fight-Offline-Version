# -*- coding: utf-8 -*-
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

appdata = Path(r"C:\Users\lenovo\AppData\Roaming\UnityHub")
for f in ["hubConfig.json", "user-settings.json", "firstTimeSettings.json"]:
    p = appdata / f
    if p.exists():
        print(f"=== {f} ===")
        print(p.read_text(encoding="utf-8", errors="replace"))
