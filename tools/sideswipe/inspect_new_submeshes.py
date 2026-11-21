import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

ab_path = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\sideswipe_robot.assetbundle"
env = UnityPy.load(ab_path)

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        name = tt.get("m_Name", "")
        if "00" in name:
            submeshes = tt.get("m_SubMeshes", [])
            print(f"Mesh: {name}, SubMeshes count: {len(submeshes)}")
            for i, sm in enumerate(submeshes):
                print(f"  SubMesh[{i}]: firstByte={sm.get('firstByte')}, indexCount={sm.get('indexCount')}")
