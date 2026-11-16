import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
op_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "optimusprime_cin_tf_odr" / "optimusprime_cin_tf.assetbundle"
gr_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "grindor_cin_rotf_odr" / "grindor_cin_rotf.assetbundle"

print("--- OPTIMUS PRIME MOVESET ---")
env_op = UnityPy.load(str(op_bundle))
for obj in env_op.objects:
    if obj.type.name == "MonoBehaviour":
        tt = obj.read_typetree()
        if "_moves" in tt:
            for m in tt.get("_moves", []):
                state = m.get("_animStateName", "")
                if "attack" in state.lower() or "light" in state.lower() or "medium" in state.lower():
                    print(f"  {state:<22} -> {m.get('_name')} (FileID={m.get('_asset',{}).get('m_FileID')}, PID={m.get('_asset',{}).get('m_PathID')})")

print("\n--- GRINDOR MOVESET ---")
env_gr = UnityPy.load(str(gr_bundle))
for obj in env_gr.objects:
    if obj.type.name == "MonoBehaviour":
        tt = obj.read_typetree()
        if "_moves" in tt:
            for m in tt.get("_moves", []):
                state = m.get("_animStateName", "")
                if "special" in state.lower() or "specialattack01" in state.lower():
                    print(f"  {state:<22} -> {m.get('_name')} (FileID={m.get('_asset',{}).get('m_FileID')}, PID={m.get('_asset',{}).get('m_PathID')})")
