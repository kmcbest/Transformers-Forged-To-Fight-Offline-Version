import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

# Check Barricade or Optimus Prime
bot_paths = [
    Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\optimusprime_cin_tf_odr\optimusprime_cin_tf.assetbundle"),
]

for bp in bot_paths:
    if not bp.exists():
        continue
    print(f"\n==========================================")
    print(f"Inspecting: {bp.name}")
    env = UnityPy.load(str(bp))
    for obj in env.objects:
        if obj.type.name == "Material":
            try:
                data = obj.read()
                name = getattr(data, 'm_Name', getattr(data, 'name', 'unnamed'))
                props = data.m_SavedProperties
                em_col = None
                overbright = None
                for k, v in props.m_Colors:
                    if "emiss" in k.lower():
                        em_col = (v.r, v.g, v.b, v.a)
                for k, v in props.m_Floats:
                    if "overbright" in k.lower():
                        overbright = v
                print(f"  Material '{name}': em_col={em_col}, overbright={overbright}")
                for k, v in props.m_TexEnvs:
                    tname = getattr(v.m_Texture.read(), 'm_Name', 'unknown') if v.m_Texture else "None"
                    if "emiss" in k.lower() or "comp" in k.lower():
                        print(f"    {k} = {tname}")
            except Exception as e:
                pass
