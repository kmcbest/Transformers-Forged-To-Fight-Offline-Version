import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

BASE_DIR = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = BASE_DIR / r"extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env_d = UnityPy.load(str(DONOR_BUNDLE))

print("=== All Renderers in Donor ===")
for o in env_d.objects:
    if o.type.name in ("SkinnedMeshRenderer", "MeshRenderer"):
        tt = o.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        bones = len(tt.get("m_Bones", [])) if "m_Bones" in tt else None
        print(f"Renderer PID={o.path_id} Type={o.type.name} GO_PID={go_pid} MeshPID={mesh_pid} Bones={bones}")

# Print GameObject names for all renderers
renderer_go_pids = {tt.get("m_GameObject", {}).get("m_PathID") for o in env_d.objects if o.type.name in ("SkinnedMeshRenderer", "MeshRenderer") for tt in [o.read_typetree()]}
for o in env_d.objects:
    if o.path_id in renderer_go_pids:
        tt = o.read_typetree()
        print(f"GO PID={o.path_id} Name={tt.get('m_Name')}")
