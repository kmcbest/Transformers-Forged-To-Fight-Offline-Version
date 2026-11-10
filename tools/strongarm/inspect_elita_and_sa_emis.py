import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image
from pathlib import Path

# 1. Inspect Elita One bundle PBR setup
p_elita = Path(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")
if p_elita.exists():
    print("=== ELITA ONE BUNDLE ===")
    env = UnityPy.load(str(p_elita))
    for obj in env.objects:
        if obj.type.name == "Material":
            m = obj.read_typetree()
            if not m.get("m_Name", "").startswith("fx_"):
                props = m.get("m_SavedProperties", {})
                floats = {k: round(v, 4) for k, v in props.get("m_Floats", []) if k in (
                    "_Mode", "_metallic_range", "_roughness_range", "_clearcoat_reflectance_range",
                    "_reflectance", "_emissive_range", "_emissive_overbright_range", "_emissive_none"
                )}
                colors = {k: (round(v['r'],3), round(v['g'],3), round(v['b'],3), round(v['a'],3))
                          for k, v in props.get("m_Colors", []) if k in ("_Color", "_base_col", "_emissive_intensity_col")}
                print(f"Mat '{m.get('m_Name')}' (PID {obj.path_id}): floats={floats}, colors={colors}")
        elif obj.type.name == "Texture2D":
            t = obj.read_typetree()
            nm = t.get("m_Name", "")
            if any(x in nm.lower() for x in ("nm", "raoe")):
                arr = np.array(obj.read().image)
                print(f"Tex '{nm}' ({arr.shape}):")
                for c in range(arr.shape[2] if arr.ndim == 3 else 1):
                    ch = arr[:, :, c] if arr.ndim == 3 else arr
                    print(f"  ch{c}: min={ch.min()}, max={ch.max()}, mean={ch.mean():.2f}, p99={np.percentile(ch, 99):.1f}")

# 2. Inspect Strongarm's current Emission PNGs per UV slot!
print("\n=== STRONGARM CURRENT EMISSION COVERAGE ===")
sa_dir = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm")
for fn in ["cha_strongarm_main_tform_misc_RAOE.png", "cha_strongarm_vh_tform_misc_RAOE.png"]:
    im = Image.open(sa_dir / fn)
    arr = np.array(im)
    print(f"{fn} ({im.mode}, {im.size}):")
    for c in range(arr.shape[2]):
        ch = arr[:, :, c]
        nz = (ch > 10).mean() * 100
        print(f"  ch{c}: min={ch.min()}, max={ch.max()}, mean={ch.mean():.2f}, >10 pct={nz:.2f}%")
    if arr.shape[2] == 4:
        # Check alpha channel (our intended emissive) per slot on main
        a = arr[:, :, 3]
        if "main" in fn:
            slots = {
                "chest_MD": (0, 0, 1024, 1024),
                "face_maskOn_MD": (0, 1024, 1024, 2048),
                "leg_MD": (1024, 0, 1536, 512),
                "hand_MD": (1024, 512, 1536, 1024),
                "body_MD": (1024, 1024, 1536, 1536),
                "head_MD": (1024, 1536, 1536, 2048),
                "doorWing_MD": (1536, 0, 2048, 512),
                "blaster_MD": (1536, 512, 2048, 1024),
            }
            for sname, (x0, y0, x1, y1) in slots.items():
                sub = a[y0:y1, x0:x1]
                print(f"    Slot {sname:15s}: >10 pct={(sub>10).mean()*100:.2f}%")
