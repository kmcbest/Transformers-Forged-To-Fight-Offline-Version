import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

p = Path(r"E:\Agent\TFTF-blender\toolchain\megatron_anims_registered.assetbundle")
env = UnityPy.load(str(p))

for o in env.objects:
    if o.type.name == "AnimationClip":
        clip = o.read_typetree()
        cname = clip.get("m_Name", "")
        if "brawler_normal_idle" in cname.lower():
            print(f"AnimationClip: {cname}")
            mclip = clip.get("m_MuscleClip", {})
            clip_binding = mclip.get("m_ClipBindingConstant", {})
            generic_bindings = clip_binding.get("genericBindings", [])
            print(f"  GenericBindings: {len(generic_bindings)}")
            for b in generic_bindings:
                # print path hash and attribute
                print(f"    binding: path={b.get('path')} attribute={b.get('attribute')} classID={b.get('classID')}")
            break
