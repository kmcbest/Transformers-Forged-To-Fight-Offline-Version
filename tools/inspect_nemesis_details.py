import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\assets_ios\nemesisprime_gs_voyager2015_odr\nemesisprime_gs_voyager2015.assetbundle")
env = UnityPy.load(str(bundle_path))

print("=== MESHES ===")
for obj in env.objects:
    if obj.type.name == "Mesh":
        try:
            tree = obj.read_typetree()
            print(f"Mesh: {tree.get('m_Name')}")
        except Exception as e:
            print(f"Mesh error: {e}")

print("\n=== TEXTURES ===")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        try:
            tree = obj.read_typetree()
            print(f"Texture2D: {tree.get('m_Name')}")
        except Exception as e:
            print(f"Texture error: {e}")

print("\n=== MATERIALS ===")
for obj in env.objects:
    if obj.type.name == "Material":
        try:
            tree = obj.read_typetree()
            print(f"Material: {tree.get('m_Name')}")
        except Exception as e:
            print(f"Material error: {e}")
