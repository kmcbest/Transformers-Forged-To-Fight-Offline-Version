import UnityPy
from pathlib import Path

bundle_path = Path("toolchain/unity_build_project/AssetBundles/demolishor_mesh.assetbundle")
if not bundle_path.exists():
    print("Bundle not found!")
else:
    env = UnityPy.load(str(bundle_path))
    for obj in env.objects:
        if obj.type.name == "GameObject":
            data = obj.read()
            print(f"GameObject: {data.m_Name}")
        elif obj.type.name == "Transform":
            data = obj.read()
            print(f"Transform: rot={data.m_LocalRotation}, scale={data.m_LocalScale}")
