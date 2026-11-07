import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path

for fn in ["brawler_idle_matrices.json", "brawler_light_01_matrices.json", "brawler_light_02_matrices.json"]:
    p = Path(r"E:\Agent\TFTF-blender\tools\demolishor") / fn
    if not p.exists():
        continue
    d = json.loads(p.read_text(encoding="utf-8"))
    print(f"=== {fn}: len={d['length']}s, frames={len(d['frames'])} ===")
    for f in d["frames"][::3]:
        bm = {b["name"]: b["m"] for b in f["bones"]}
        hips = bm["Hips"]
        lh = bm["LeftHand"]
        rh = bm["RightHand"]
        print(f"  f={f['frameIndex']:2d} t={f['time']:.2f}s | Hips=({hips[3]:.2f},{hips[7]:.2f},{hips[11]:.2f}) | LH=({lh[3]:.2f},{lh[7]:.2f},{lh[11]:.2f}) | RH=({rh[3]:.2f},{rh[7]:.2f},{rh[11]:.2f})")
