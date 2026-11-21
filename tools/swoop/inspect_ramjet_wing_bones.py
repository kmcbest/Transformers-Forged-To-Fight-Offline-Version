import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import json
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(DONOR_BUNDLE))

with open(r"e:\Agent\TFTF-blender\tools\swoop\ramjet_78_authoritative_bindposes.json", "r", encoding="utf-8") as f:
    r78 = json.load(f)

bone_names = r78["bone_names"]
print("Ramjet 78 bones sample:")
for b in bone_names:
    if any(k in b.lower() for k in ["wing", "prop", "pad", "spine"]):
        print(f"  {b}")
