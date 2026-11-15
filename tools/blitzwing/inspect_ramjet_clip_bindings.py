import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle")
env = UnityPy.load(str(p_bundle))

for o in env.objects:
    if o.path_id == 2235498278053343569:
        tt = o.read_typetree()
        print(f"AnimationClip: {tt.get('m_Name')} (PID {o.path_id})")
        cbc = tt.get("m_ClipBindingConstant", {})
        bindings = cbc.get("genericBindings", [])
        print(f"GenericBindings count: {len(bindings)}")
        for b in bindings:
            path_hash = b.get("path")
            attr = b.get("attribute")
            cl_id = b.get("classID")
            print(f"  path_hash={path_hash}, attr={attr}, classID={cl_id}")
