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
        name = getattr(data, 'm_Name', '')
        if "vehicle" in name:
            print(f"AnimationClip: {name}")
            tt = obj.read_typetree()
            # Check bindings
            clip_binding = tt.get('m_ClipBindingConstant', {})
            gen_bindings = clip_binding.get('genericBindings', [])
            print(f"  Bindings count: {len(gen_bindings)}")
            paths = set()
            for b in gen_bindings:
                paths.add(b.get('path'))
            print(f"  Unique paths (hashes): {len(paths)}")
