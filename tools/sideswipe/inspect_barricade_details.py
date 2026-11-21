import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle")
env = UnityPy.load(str(p))

print(f"=== Detailed Inspection of {p.name} ===")

print("\n--- Materials ---")
for o in env.objects:
    if o.type.name == "Material":
        tt = o.read_typetree()
        print(f"  Material: {tt.get('m_Name')} (pid={o.path_id})")

print("\n--- SkinnedMeshRenderers ---")
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        mat_pids = [m.get("m_PathID") for m in tt.get("m_Materials", [])]
        print(f"  SMR (pid={o.path_id}): mesh_pid={mesh_pid}, mats={mat_pids}, enabled={tt.get('m_Enabled')}")

print("\n--- MoveSet & AOCs ---")
for o in env.objects:
    if "moveset" in o.type.name.lower() or "charactercard" in o.type.name.lower() or o.type.name == "MonoBehaviour":
        try:
            tt = o.read_typetree()
            if "_moves" in tt:
                print(f"  MoveSet MonoBehaviour: pid={o.path_id}, moves count={len(tt.get('_moves', []))}")
        except Exception:
            pass
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print(f"  AOC: {tt.get('m_Name')} (pid={o.path_id})")
