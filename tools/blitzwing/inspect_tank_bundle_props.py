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

# Check PropsController
for pid in (3410776510343360670, 7860161868350027668):
    obj = obj_map.get(pid)
    if obj:
        tt = obj.read_typetree()
        print(f"\nPropsController PID {pid}:")
        props = tt.get("_props", {})
        keys = props.get("_serializedKeys", [])
        vals = props.get("_serializedValues", [])
        for k, v in zip(keys, vals):
            print(f"  Key '{k}': Name={v.get('Name')}, InitFlags={v.get('InitFlags')}, PosOffset={v.get('PositionOffset')}, RotOffset={v.get('RotationOffset')}, Renderers={v.get('_renderers')}")

# Check Tank SMRs
for pid in (2138194849323017337, 4626197738286450028):
    obj = obj_map.get(pid)
    if obj:
        tt = obj.read_typetree()
        print(f"\nTank SMR PID {pid}:")
        print(f"  Mesh: {tt.get('m_Mesh')}")
        print(f"  RootBone: {tt.get('m_RootBone')}")
        print(f"  Bones count: {len(tt.get('m_Bones', []))}")
        print(f"  Enabled: {tt.get('m_Enabled')}")
        print(f"  AABB: {tt.get('m_AABB')}")
