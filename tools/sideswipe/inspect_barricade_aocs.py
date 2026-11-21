import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle")
env = UnityPy.load(str(p))
obj_map = {o.path_id: o for o in env.objects}

print(f"=== AOCs in {p.name} ===")
for o in env.objects:
    if o.type.name == "AnimatorOverrideController":
        tt = o.read_typetree()
        print(f"\nAOC: {tt.get('m_Name')} (pid={o.path_id})")
        for cl in tt.get("m_Clips", []):
            orig = cl.get("m_OriginalClip", {})
            over = cl.get("m_OverrideClip", {})
            over_pid = over.get("m_PathID")
            over_obj = obj_map.get(over_pid)
            over_name = over_obj.read_typetree().get("m_Name") if over_obj and over_obj.type.name == "AnimationClip" else ""
            if orig.get("m_PathID") == 8310889249667241404 or "run" in over_name.lower() or "loco" in over_name.lower():
                print(f"  [RUN/LOCO] orig={orig.get('m_PathID')} -> over={over_pid} ({over_name})")
