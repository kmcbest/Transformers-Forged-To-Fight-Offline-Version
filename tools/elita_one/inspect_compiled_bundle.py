import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
BUNDLE_PATH = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "elita_one_mesh.assetbundle"

env = UnityPy.load(str(BUNDLE_PATH))
print(f"=== Objects in {BUNDLE_PATH.name} ===")
for obj in env.objects:
    if obj.type.name in ["Mesh", "Texture2D", "Transform", "GameObject"]:
        tree = obj.read_typetree()
        name = tree.get("m_Name", "")
        if obj.type.name == "Mesh":
            vc = tree.get("m_VertexData", {}).get("m_VertexCount")
            print(f"[{obj.type.name:15s}] {name:30s} | Verts: {vc}")
        elif obj.type.name == "Texture2D":
            w = tree.get("m_Width")
            h = tree.get("m_Height")
            fmt = tree.get("m_TextureFormat")
            print(f"[{obj.type.name:15s}] {name:30s} | {w}x{h} (Format {fmt})")
        elif obj.type.name == "GameObject":
            print(f"[{obj.type.name:15s}] {name}")
