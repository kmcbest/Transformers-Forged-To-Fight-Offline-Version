import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from pathlib import Path
from PIL import Image
import numpy as np
import UnityPy

SRC = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
print("=== Source Textures Check ===")
for f in sorted(SRC.iterdir()):
    name = f.name.lower()
    if any(k in name for k in ["blastoff", "chest", "armup", "armlo", "legs", "head", "vh"]):
        if not ("brawl" in name or "vortex" in name or "swindle" in name or "onslaught" in name or "bruticus" in name):
            im = Image.open(f)
            arr = np.array(im.convert("RGB"))
            print(f"  {f.name:42s} size={im.size} mean={arr.mean():.1f} max={arr.max()}")

# Also check Megatronus material properties in donor bundle
DONOR = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatronus_gs_kabam_odr\megatronus_gs_kabam.assetbundle")
env = UnityPy.load(str(DONOR))
obj_map = {o.path_id: o for o in env.objects}
print("\n=== Donor Megatronus Material Properties ===")
for pid in (-7624887367596881865, -1880645829306736032):
    tt = obj_map[pid].read_typetree()
    print(f"Mat PID={pid} name={tt.get('m_Name')}")
    sp = tt.get("m_SavedProperties", {})
    print("  Floats:", sp.get("m_Floats"))
    print("  Colors:", sp.get("m_Colors"))
    for k, v in sp.get("m_TexEnvs", []):
        tpid = v.get("m_Texture", {}).get("m_PathID")
        print(f"  Tex {k}: pid={tpid}, scale={v.get('m_Scale')}, off={v.get('m_Offset')}")
