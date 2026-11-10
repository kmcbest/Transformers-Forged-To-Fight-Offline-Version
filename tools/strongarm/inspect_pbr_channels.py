import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from pathlib import Path

def inspect_bundle(path, label):
    print(f"\n================ {label}: {path.name} ================")
    env = UnityPy.load(str(path))
    for obj in env.objects:
        if obj.type.name == "Texture2D":
            t_tree = obj.read_typetree()
            t_name = t_tree.get("m_Name", "")
            if any(k in t_name.lower() for k in ("main_nm", "raoe", "tform_misc_nm", "contactshadow")):
                tex = obj.read()
                im = tex.image
                arr = np.array(im)
                print(f"Tex '{t_name}' (PID {obj.path_id}): mode={im.mode}, size={im.size}, fmt={t_tree.get('m_TextureFormat')}")
                for ch in range(arr.shape[2] if arr.ndim == 3 else 1):
                    c = arr[:, :, ch] if arr.ndim == 3 else arr
                    print(f"  ch{ch}: min={c.min()}, max={c.max()}, mean={c.mean():.2f}, p99={np.percentile(c, 99):.1f}")
        elif obj.type.name == "Material":
            m_tree = obj.read_typetree()
            m_name = m_tree.get("m_Name", "")
            if not m_name.startswith("fx_"):
                props = m_tree.get("m_SavedProperties", {})
                floats = {k: round(v, 4) for k, v in props.get("m_Floats", [])}
                colors = {k: (round(v['r'],3), round(v['g'],3), round(v['b'],3), round(v['a'],3)) for k, v in props.get("m_Colors", [])}
                print(f"Mat '{m_name}' (PID {obj.path_id}):")
                print(f"  floats: {floats}")
                print(f"  colors: {colors}")

inspect_bundle(Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle"), "PROWL OFFICIAL")
inspect_bundle(Path(r"E:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle"), "VORTEX WORKING")
inspect_bundle(Path(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle"), "STRONGARM CURRENT")
