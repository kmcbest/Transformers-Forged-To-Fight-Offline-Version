import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import UnityPy

ROOT = Path("e:/Agent/TFTF-blender")
JET_JSON = ROOT / "tools/swoop/ramjet_jet_29_authoritative_bindposes.json"
with open(JET_JSON, "r", encoding="utf-8") as f:
    jdata = json.load(f)["bones"]

print("=== 1. Ramjet 29 Jet Bones (Unity World Pos & Parent) ===")
for bname, info in jdata.items():
    ux, uy, uz = info["unity_world_pos"]
    print(f"  {bname:28s}: parent={info['parent']:28s} pos=({ux:+6.3f}, {uy:+6.3f}, {uz:+6.3f})")

RAMJET_AB = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(RAMJET_AB))
print("\n=== 2. AnimationClips in Ramjet Bundle ===")
for o in env.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        if "transform" in tt["m_Name"].lower() or "vehicle" in tt["m_Name"].lower() or "heavy" in tt["m_Name"].lower() or "idle" in tt["m_Name"].lower():
            print(f"  Clip: {tt['m_Name']}")
