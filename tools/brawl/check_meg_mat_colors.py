import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

MEG_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_cin_rotf_odr\megatron_cin_rotf.assetbundle")
env = UnityPy.load(str(MEG_BUNDLE))

for o in env.objects:
    if o.type.name == "Material":
        tt = o.read_typetree()
        if o.path_id in (2758279787216392959, -8143696719442631496):
            cols = {k: v for k, v in tt["m_SavedProperties"]["m_Colors"]}
            print(f"Mat {o.path_id} colors: {cols}")
    elif o.type.name == "AnimationClip":
        tt = o.read_typetree()
        n = tt.get("m_Name", "")
        if "megatron" in n.lower() or "vehicle" in n.lower() or "brawler" in n.lower() or "teamselect" in n.lower():
            print(f"Clip: {n}")
