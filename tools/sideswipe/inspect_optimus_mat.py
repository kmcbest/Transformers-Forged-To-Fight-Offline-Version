import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bp = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\optimusprime_cin_tf_odr\optimusprime_cin_tf.assetbundle")
env = UnityPy.load(str(bp))

for obj in env.objects:
    if obj.type.name == "Material":
        data = obj.read()
        name = getattr(data, 'm_Name', 'unnamed')
        if name == "FA689EB17B16BC211655370B551DB08207C3F2EA":
            print(f"--- Material {name} ---")
            props = data.m_SavedProperties
            print("Floats:")
            for k, v in props.m_Floats:
                print(f"  {k} = {v}")
            print("\nColors:")
            for k, v in props.m_Colors:
                print(f"  {k} = ({v.r}, {v.g}, {v.b}, {v.a})")
            print("\nTextures:")
            for k, v in props.m_TexEnvs:
                try:
                    tn = getattr(v.m_Texture.read(), 'm_Name', 'unknown') if v.m_Texture else "None"
                except Exception:
                    tn = "Ref"
                print(f"  {k} = {tn}")
