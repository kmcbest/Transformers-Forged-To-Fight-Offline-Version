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
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        if "ramjet" in tt.get("m_Name", "").lower() and "heavy" in tt.get("m_Name", "").lower():
            print(f"Found clip PID {o.path_id}: '{tt.get('m_Name')}'")
            print(f"  MuscleClip Start={tt.get('m_MuscleClip', {}).get('m_StartTime')}, Stop={tt.get('m_MuscleClip', {}).get('m_StopTime')}")
            bind = tt.get("m_ClipBindingConstant", {})
            print(f"  Bindings count: {len(bind.get('genericBindings', []))}")
            for b in bind.get("genericBindings", [])[:15]:
                print(f"    binding: path={b.get('path')} attr={b.get('attribute')} classID={b.get('classID')}")
