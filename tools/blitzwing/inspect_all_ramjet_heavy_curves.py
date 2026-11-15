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
        bind = tt.get("m_ClipBindingConstant", {})
        print("Clip name:", tt.get("m_Name"))
        for b in bind.get("genericBindings", []):
            path_hash = b.get("path")
            attr = b.get("attribute")
            # 1=pos, 2=rot, 3=scale
            attr_name = {1: "Position", 2: "Rotation", 3: "Scale"}.get(attr, f"attr_{attr}")
            print(f"  path={path_hash} ({attr_name}) classID={b.get('classID')}")
