import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))

for o in env.objects:
    if o.type.name == "SkinnedMeshRenderer":
        tt = o.read_typetree()
        mesh_pid = tt["m_Mesh"]["m_PathID"]
        for o2 in env.objects:
            if o2.path_id == mesh_pid:
                m_name = o2.read_typetree()["m_Name"]
                if "cannon" in m_name:
                    print(f"SMR {o.path_id}: Mesh='{m_name}', bones={len(tt.get('m_Bones', []))}")
                    print(f"  Materials: {tt.get('m_Materials')}")
