import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BRAWL_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\brawl_gs.assetbundle")
env = UnityPy.load(str(BRAWL_BUNDLE))
sf = list(env.assets)[0]

for pid, obj in sf.objects.items():
    if obj.type.name == "SkinnedMeshRenderer":
        tt = obj.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        go_name = sf.objects[go_pid].read_typetree().get("m_Name") if go_pid in sf.objects else "UNKNOWN"
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        mesh_name = sf.objects[mesh_pid].read_typetree().get("m_Name") if mesh_pid in sf.objects else "UNKNOWN"
        mats = [m.get("m_PathID") for m in tt.get("m_Materials", [])]
        print(f"SMR PID {pid}: GO='{go_name}' (PID={go_pid}), Mesh='{mesh_name}' (PID={mesh_pid}), Mats={mats}, Bones={len(tt.get('m_Bones', []))}")
