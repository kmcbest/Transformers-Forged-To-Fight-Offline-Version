import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"e:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
objs = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        smr = o.read_typetree()
        go_pid = smr["m_GameObject"]["m_PathID"]
        mesh_pid = smr["m_Mesh"]["m_PathID"] if "m_Mesh" in smr else None
        mats = [m["m_PathID"] for m in smr.get("m_Materials", [])]
        
        go_name = objs[go_pid].read_typetree().get("m_Name", "") if go_pid in objs else "UNKNOWN"
        mesh_name = objs[mesh_pid].read_typetree().get("m_Name", "") if mesh_pid in objs else "UNKNOWN"
        print(f"SMR {o.path_id}: GO='{go_name}' (PID {go_pid}) Mesh='{mesh_name}' (PID {mesh_pid}) Mats={mats} Enabled={smr.get('m_Enabled')}")
