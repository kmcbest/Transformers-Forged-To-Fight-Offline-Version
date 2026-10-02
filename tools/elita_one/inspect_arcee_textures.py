import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(str(arcee_bundle))

print("=== Texture2D in Arcee bundle ===")
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        name = tree.get("m_Name")
        w = tree.get("m_Width")
        h = tree.get("m_Height")
        fmt = tree.get("m_TextureFormat")
        print(f"PID: {obj.path_id:20d} | Name: {name:32s} | {w}x{h} | Format: {fmt}")
