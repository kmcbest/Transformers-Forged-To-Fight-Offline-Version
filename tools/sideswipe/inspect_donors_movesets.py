import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
DONORS_DIR = ROOT / "extracted_apk" / "assets" / "assetpack"

def inspect_moveset(bid):
    p = DONORS_DIR / f"{bid}_odr" / f"{bid}.assetbundle"
    env = UnityPy.load(str(p))
    print(f"\n=== MoveSets in {bid} ===")
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_moves" in tt:
                moves = tt.get("_moves", [])
                if len(moves) > 5:
                    print(f"MoveSet PID={o.path_id} (count={len(moves)}):")
                    for i, m in enumerate(moves):
                        mname = m.get("_name", "")
                        if any(k in mname.lower() for k in ["medium", "special", "heavy"]):
                            print(f"  [{i:02d}] {mname}: {m.get('_asset')}")

inspect_moveset("cheetor_bw_transmetal")
inspect_moveset("drift_cin_aoe")
inspect_moveset("sideswipe_gs")
inspect_moveset("optimusprime_cin_tf")
