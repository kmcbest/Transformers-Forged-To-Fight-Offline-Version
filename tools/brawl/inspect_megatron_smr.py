import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tt = obj.read_typetree()
        go_pid = tt.get("m_GameObject", {}).get("m_PathID")
        mesh_pid = tt.get("m_Mesh", {}).get("m_PathID")
        bones = tt.get("m_Bones", [])
        print(f"SMR PID={obj.path_id}, GO_PID={go_pid}, Mesh_PID={mesh_pid}, Bones_Count={len(bones)}")
        # Print first 5 bone PIDs
        print(f"  First 5 bone PPtrs: {bones[:5]}")
