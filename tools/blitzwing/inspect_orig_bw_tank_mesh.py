import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

mesh_bundle = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle"
env = UnityPy.load(mesh_bundle)

for obj in env.objects:
    if obj.type.name == "Mesh":
        d = obj.read()
        name = getattr(d, "m_Name", "")
        if "tank" in name.lower():
            tt = obj.read_typetree()
            print(f"Mesh: {name}")
            print("  m_BoneNameHashes count:", len(tt.get("m_BoneNameHashes", [])))
            print("  m_BindPose count:", len(tt.get("m_BindPose", [])))
            print("  m_SubMeshes:", tt.get("m_SubMeshes"))
            print("  m_LocalAABB:", tt.get("m_LocalAABB"))
