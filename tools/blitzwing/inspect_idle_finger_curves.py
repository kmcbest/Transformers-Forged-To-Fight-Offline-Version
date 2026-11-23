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
        if "idle" in cname.lower() or "combat" in cname.lower():
            print(f"AnimationClip: {cname}")
            # check rotation curves or muscle curves
            curves = clip.get("m_RotationCurves", [])
            print(f"  RotationCurves: {len(curves)}")
            for c in curves:
                path = c.get("path", "")
                if "Index" in path or "Finger" in path or "Hand" in path:
                    print(f"    curve path: {path}")
            # muscle clip
            mclip = clip.get("m_MuscleClip", {})
            clip_binding = mclip.get("m_ClipBindingConstant", {})
            generic_bindings = clip_binding.get("genericBindings", [])
            for b in generic_bindings:
                if b.get("attribute") in [1, 2, 3, 4]:
                    # attribute 2 is rotation
                    pass
            print(f"  GenericBindings: {len(generic_bindings)}")
            break
