import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\characters_procedural_odr\character_anim_procedural.assetbundle")
if not p.exists():
    print("Not found")
    sys.exit()

env = UnityPy.load(str(p))
for o in env.objects:
    if o.type.name == "AnimationClip":
        clip = o.read_typetree()
        cname = clip.get("m_Name", "")
        if cname == "brawler_normal_idle":
            print(f"Clip: {cname}")
            mclip = clip.get("m_MuscleClip", {})
            for k in mclip:
                if k != "m_Clip":
                    print(f"  {k}: {type(mclip[k])}")
            bindings = mclip.get("m_ClipBindingConstant", {}).get("genericBindings", [])
            print(f"  genericBindings: {len(bindings)}")
            for b in bindings[:10]:
                print("   ", b)
            break
