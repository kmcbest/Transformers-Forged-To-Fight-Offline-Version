import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path("e:/Agent/TFTF-blender/assets_redeco/blitzwing_gs.assetbundle")
env = UnityPy.load(str(bundle_path))
obj_map = {o.path_id: o for o in env.objects}

for pc_pid in (-8490429130128858862, -3021806434293993593):
    pc = obj_map[pc_pid].read_typetree()
    props = pc["_props"]
    for k, v in zip(props["_serializedKeys"], props["_serializedValues"]):
        if k in ("transformed", "transformed_2"):
            print(f"PC {pc_pid} Prop '{k}':")
            for field, val in v.items():
                print(f"    {field}: {val}")
