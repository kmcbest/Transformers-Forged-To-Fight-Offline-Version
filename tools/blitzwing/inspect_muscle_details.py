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
        print("Clip:", tt.get("m_Name"))
        mc = tt.get("m_MuscleClip", {})
        print("StartX:", mc.get("m_StartX"))
        print("StopX:", mc.get("m_StopX"))
        print("AverageSpeed:", mc.get("m_AverageSpeed"))
        print("OrientationOffsetY:", mc.get("m_OrientationOffsetY"))
        print("Level:", mc.get("m_Level"))
        print("CycleOffset:", mc.get("m_CycleOffset"))
        print("HeightFromFeet:", mc.get("m_HeightFromFeet"))
