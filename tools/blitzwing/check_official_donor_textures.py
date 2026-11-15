import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy
import numpy as np

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_path))

for o in env.objects:
    if o.type.name == "Texture2D":
        tt = o.read_typetree()
        if tt["m_Name"] in ("main_tform_misc_RAOE", "main_NM"):
            t = o.read()
            img = t.image
            arr = np.array(img)
            print(f"Official Texture '{t.m_Name}' {img.size} {img.mode}:")
            for c in range(arr.shape[2]):
                ch_data = arr[:, :, c]
                print(f"  Channel {c} ({'R' if c==0 else 'G' if c==1 else 'B' if c==2 else 'A'}): min={ch_data.min()}, max={ch_data.max()}, mean={ch_data.mean():.2f}")
