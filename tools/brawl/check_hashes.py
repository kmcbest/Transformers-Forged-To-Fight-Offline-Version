import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

MESH_BUNDLE = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\brawl_mesh.assetbundle")
env = UnityPy.load(str(MESH_BUNDLE))
for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        print(f"=== {tt['m_Name']} ===")
        print("m_BoneNameHashes:", tt.get("m_BoneNameHashes"))
        print("m_RootBoneNameHash:", tt.get("m_RootBoneNameHash"))
