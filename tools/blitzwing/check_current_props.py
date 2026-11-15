import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

p_bundle = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
env = UnityPy.load(str(p_bundle))

PROPS_SHOWCASE_PID = -8490429130128858862
PROPS_COMBAT_PID = -3021806434293993593

for o in env.objects:
    if o.path_id in (PROPS_SHOWCASE_PID, PROPS_COMBAT_PID):
        tt = o.read_typetree()
        print(f"\nPropsController PID {o.path_id}:")
        keys = tt["_props"]["_serializedKeys"]
        vals = tt["_props"]["_serializedValues"]
        for k, v in zip(keys, vals):
            print(f"  Key '{k}': Name={v.get('Name')}, InitFlags={v.get('InitFlags')}, RootPath={v.get('RootPath')}, renderers={v.get('_renderers')}")
            print(f"    PosOffset={v.get('PositionOffset')}, RotOffset={v.get('RotationOffset')}")
