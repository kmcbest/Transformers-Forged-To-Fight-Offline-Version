import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

BUNDLE_PATH = Path(r"E:\Agent\TFTF-blender\toolchain\megatron_anims_registered.assetbundle")
env = UnityPy.load(str(BUNDLE_PATH))

# Search all AnimationClips for any clip with curves
for obj in env.objects:
    if obj.type.name == "AnimationClip":
        tree = obj.read_typetree()
        cname = tree.get("m_Name", "")
        clip_data = tree.get("m_ClipBindingConstant", {})
        generic_bindings = clip_data.get("genericBindings", [])
        if generic_bindings:
            print(f"Clip '{cname}': {len(generic_bindings)} bindings")
            for b in generic_bindings[:10]:
                print(f"  path={b.get('path')}, attribute={b.get('attribute')}, typeID={b.get('typeID')}")
            break
