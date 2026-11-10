import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF-blender\toolchain\prowl_anims_registered.assetbundle")
env = UnityPy.load(str(bundle_path))

for obj in env.objects:
    if obj.type.name == "AnimationClip":
        data = obj.read()
        name = getattr(data, 'm_Name', getattr(data, 'name', ''))
        if name in ["tactical_normal_idle", "Prefight_Tactical_idle"]:
            print(f"\nAnimationClip: {name}")
            # Check curve bindings
            # In UnityPy, check m_ClipBindingConstant
            cbc = getattr(data, 'm_ClipBindingConstant', None)
            if cbc:
                pptr_curves = getattr(cbc, 'genericBindings', [])
                print(f"  Total curve bindings: {len(pptr_curves)}")
