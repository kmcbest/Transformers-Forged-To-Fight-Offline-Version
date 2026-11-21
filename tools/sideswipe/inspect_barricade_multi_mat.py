import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bp = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\barricade_cin_dotm_odr\barricade_cin_dotm.assetbundle")
env = UnityPy.load(str(bp))

for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        data = obj.read()
        if hasattr(data, 'm_Materials') and len(data.m_Materials) > 1:
            print(f"SkinnedMeshRenderer: {data.m_GameObject.read().m_Name if data.m_GameObject else 'unnamed'}")
            for i, mp in enumerate(data.m_Materials):
                m = mp.read()
                print(f"  Material[{i}]: {m.m_Name}")
                props = m.m_SavedProperties
                for k, v in props.m_Colors:
                    if "emiss" in k.lower() or "col" in k.lower():
                        print(f"    {k} = ({v.r:.3f}, {v.g:.3f}, {v.b:.3f}, {v.a:.3f})")
                for k, v in props.m_TexEnvs:
                    try:
                        tn = getattr(v.m_Texture.read(), 'm_Name', 'unknown') if v.m_Texture else "None"
                    except Exception:
                        tn = "Ref"
                    if "tex" in k.lower():
                        print(f"    {k} = {tn}")
