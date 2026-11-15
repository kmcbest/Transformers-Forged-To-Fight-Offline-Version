import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

mesh_bundle = r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\blitzwing_mesh.assetbundle"
env1 = UnityPy.load(mesh_bundle)

for obj in env1.objects:
    if obj.type.name == "GameObject":
        print("GO:", obj.read().m_Name)
    if obj.type.name == "SkinnedMeshRenderer":
        tt = obj.read_typetree()
        print("SMR:", tt.get("m_Name"), "Bones:", len(tt.get("m_Bones", [])))
