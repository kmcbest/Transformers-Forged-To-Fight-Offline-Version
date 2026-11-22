import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

DONOR_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(DONOR_BUNDLE))

for o in env.objects:
    if o.type.name in ["MeshRenderer", "SkinnedMeshRenderer"]:
        tt = o.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID", 0)
        go_name = "<?>"
        if go_pid in env.objects:
            try:
                go_name = env.objects[go_pid].read_typetree().get("m_Name", "")
            except Exception:
                pass
        enabled = tt.get("m_Enabled", True)
        print(f"[{o.type.name}] PID={o.path_id} Enabled={enabled} GO='{go_name}'")
