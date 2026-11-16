import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(str(DONOR))
sf = [f for f in env.file.files.values() if hasattr(f, "objects")][0]

for i, ext in enumerate(sf.externals):
    print(f"External {i+1}: {ext.name}")

# Now check what moveset and fight AOC in donor pointed to!
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_moves" in tt:
            print("Found MoveSet in Donor:")
            for m in tt.get("_moves", [])[:3]:
                print(f"  {m.get('_name')}: asset={m.get('_asset')}")
    elif o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print("Found AOC in Donor:")
        for c in tt.get("m_Clips", [])[:3]:
            print(f"  Orig={c.get('m_OriginalClip')}, Override={c.get('m_OverrideClip')}")
