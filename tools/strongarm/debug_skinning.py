import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if "00" in name:
            print(f"Prowl Mesh: {name}, bindposes count: {len(tt.get('m_BindPose', []))}")
            print(f"Skin count: {len(tt.get('m_Skin', []))}")
            if len(tt.get('m_Skin', [])) > 0:
                print("First 3 skin weights in Prowl:")
                for s in tt['m_Skin'][:3]:
                    print(s)
            break
