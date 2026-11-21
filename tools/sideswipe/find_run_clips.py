import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MOVES = ROOT / "assets_netflix" / "moves.assetbundle"
PROC = ROOT / "assets_netflix" / "character_anim_procedural.assetbundle"

print("Searching for Bonecrusher run clips...")
for p in [MOVES, PROC]:
    if not p.exists():
        continue
    env = UnityPy.load(str(p))
    for o in env.objects:
        if o.type.name == "AnimationClip":
            try:
                tt = o.read_typetree()
                name = tt.get("m_Name", "")
                if "bonecrusher" in name.lower() and ("run" in name.lower() or "loco" in name.lower() or "skat" in name.lower()):
                    print(f"  Found in {p.name}: {name} (pid={o.path_id})")
            except Exception:
                pass

# Also search Barricade run clips in moves.assetbundle and donor bundle
barr_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "barricade_cin_dotm_odr" / "barricade_cin_dotm.assetbundle"
if barr_path.exists():
    env_b = UnityPy.load(str(barr_path))
    for o in env_b.objects:
        if o.type.name == "AnimationClip":
            try:
                tt = o.read_typetree()
                name = tt.get("m_Name", "")
                if "run" in name.lower() or "loco" in name.lower():
                    print(f"  Found in Barricade bundle: {name} (pid={o.path_id})")
            except Exception:
                pass
