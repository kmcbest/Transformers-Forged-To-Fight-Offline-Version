import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

DONOR = Path("extracted_apk/assets/assetpack/megatronus_gs_kabam_odr/megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(DONOR))

print("=== Checking Megatronus donor components ===")
# Check PropsController
for o in env.objects:
    if o.type.name == "MonoBehaviour":
        try:
            tt = o.read_typetree()
            if "_props" in tt:
                print(f"PropsController found at PID={o.path_id}:", tt["_props"])
        except Exception:
            pass

# Check all Meshes in donor
for o in env.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        print(f"Mesh PID={o.path_id}: name={tt.get('m_Name')}, verts={tt.get('m_VertexData', {}).get('m_VertexCount')}")

# Check all SMRs
for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        print(f"SMR PID={o.path_id}: mesh_pid={mesh_pid}")
