import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy
from PIL import Image
import io

BUNDLE = r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle"
env = UnityPy.load(BUNDLE)

print("=== CHECK CURRENT blitzwing_gs.assetbundle ===")
for o in env.objects:
    if o.type.name == "Material":
        t = o.read_typetree()
        if o.path_id in (8075787426780741283, 1722215546450231611, 8175378592256487408):
            print(f"Material {o.path_id}: '{t['m_Name']}'")
            print("  Floats:", t["m_SavedProperties"]["m_Floats"])
            print("  Colors:", t["m_SavedProperties"]["m_Colors"])
            print("  TexEnvs:", [(k, v["m_Texture"]["m_PathID"]) for k, v in t["m_SavedProperties"]["m_TexEnvs"] if v["m_Texture"]["m_PathID"] != 0])

for o in env.objects:
    if o.type.name == "Texture2D":
        t = o.read()
        print(f"Texture2D {o.path_id}: '{t.m_Name}' {t.m_Width}x{t.m_Height} fmt={t.m_TextureFormat}")
        try:
            img = t.image
            if img:
                bands = img.getbands()
                extrema = img.getextrema()
                print(f"    bands={bands} extrema={extrema}")
        except Exception as e:
            print(f"    image decode failed: {e}")
