import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"e:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))

for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        smr = o.read_typetree()
        go_pid = smr["m_GameObject"]["m_PathID"]
        mesh_pid = smr["m_Mesh"]["m_PathID"] if "m_Mesh" in smr else None
        mats = [m["m_PathID"] for m in smr.get("m_Materials", [])]
        print(f"SMR PID={o.path_id} GO_PID={go_pid} Mesh_PID={mesh_pid} Mats={mats}")
