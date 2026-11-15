import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

proc_path = Path("e:/Agent/TFTF-blender/assets_netflix/character_anim_procedural.assetbundle")
if not proc_path.exists():
    proc_path = Path("E:/Agent/TFTF/extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle")

env = UnityPy.load(str(proc_path))
for o in env.objects:
    if o.path_id == 2235498278053343569:
        tt = o.read_typetree()
        clip = o.read()
        print("Clip name:", tt.get("m_Name"))
        # In typetree, let's see if sample animation or curves are present
        print("m_SampleRate:", tt.get("m_SampleRate"))
        mc = tt.get("m_MuscleClip", {})
        print("MuscleClip keys:", list(mc.keys()))
        data = mc.get("m_ClipData", {})
        print("ClipData keys:", list(data.keys()))
