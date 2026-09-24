# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import UnityPy
from PIL import Image
import numpy as np

sys.stdout.reconfigure(encoding='utf-8')

bundle_path = "extracted_apk/assets/assetpack/ironhide_cin_rotf_odr/ironhide_cin_rotf.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "Texture2D":
        t = obj.read()
        if "raoe" in t.m_Name.lower():
            img = t.image
            arr = np.array(img)
            print(f"Texture: {t.m_Name}, Size: {t.m_Width}x{t.m_Height}, Format: {t.m_TextureFormat}")
            print(f"  Shape: {arr.shape}")
            for c, c_name in enumerate(["R (Roughness)", "G (AO)", "O (Opacity/Other)", "E (Emissive)"][:arr.shape[2]]):
                ch = arr[:, :, c]
                print(f"    {c_name}: min={ch.min()}, max={ch.max()}, mean={ch.mean():.1f}")
