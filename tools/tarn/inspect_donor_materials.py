import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image
import UnityPy

DONOR_TEX = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn\04_donor_reference\megatron_gs_leader2015\donor_textures")
for fn in sorted(DONOR_TEX.glob("*.png")):
    im = Image.open(fn)
    arr = np.array(im)
    print(f"Donor Tex {fn.name:38s} | mode={im.mode:4s} | size={im.size} | shape={arr.shape}")
    if arr.ndim == 3:
        for ch in range(arr.shape[2]):
            v = arr[:, :, ch]
            print(f"   ch{ch}: min={v.min():3d}, p50={np.median(v):5.1f}, p95={np.percentile(v,95):5.1f}, max={v.max():3d}")

# Also check Ironhide vs Arcee vs Megatron material floats in existing bundles
for label, bp in [
    ("megatron_gs", Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")),
    ("ironhide", Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ironhide_cin_rotf_odr\ironhide_cin_rotf.assetbundle")),
    ("onslaught", Path(r"E:\Agent\TFTF-blender\assets_redeco\onslaught_gs.assetbundle")),
]:
    if not bp.is_file():
        continue
    env = UnityPy.load(str(bp))
    print(f"\n=== Materials in {label} ===")
    for o in env.objects:
        if o.type.name == "Material":
            m = o.read_typetree()
            sp = m["m_SavedProperties"]
            fl = {k: v for k, v in sp.get("m_Floats", []) if any(t in k for t in ("Mode", "emissive", "metallic", "roughness", "clearcoat", "reflectance"))}
            co = {k: (round(v["r"],3), round(v["g"],3), round(v["b"],3), round(v["a"],3)) for k, v in sp.get("m_Colors", []) if any(t in k for t in ("Color", "base", "emissive"))}
            if "_Mode" in fl:
                print(f"  Mat {m['m_Name'][:16]} (PID={o.path_id}): floats={fl}")
                print(f"     colors={co}")
