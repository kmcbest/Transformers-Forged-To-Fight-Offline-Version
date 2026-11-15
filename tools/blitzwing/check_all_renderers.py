import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

BUNDLE = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(BUNDLE)

print("=== CHECK ALL SMRs IN blitzwing_gs.assetbundle ===")
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        t = o.read_typetree()
        mesh_pid = t.get("m_Mesh", {}).get("m_PathID")
        mat_pids = [m.get("m_PathID") for m in t.get("m_Materials", [])]
        enabled = t.get("m_Enabled")
        go_pid = t.get("m_GameObject", {}).get("m_PathID")
        print(f"SMR PID={o.path_id} enabled={enabled}: mesh={mesh_pid} mats={mat_pids} go={go_pid}")

print("\n=== CHECK ALL MESH RENDERERS IN blitzwing_gs.assetbundle ===")
for o in env.objects:
    if o.type.name == "MeshRenderer":
        t = o.read_typetree()
        mat_pids = [m.get("m_PathID") for m in t.get("m_Materials", [])]
        enabled = t.get("m_Enabled")
        go_pid = t.get("m_GameObject", {}).get("m_PathID")
        print(f"MeshRenderer PID={o.path_id} enabled={enabled}: mats={mat_pids} go={go_pid}")
