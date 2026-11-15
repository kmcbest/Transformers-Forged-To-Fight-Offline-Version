import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

donor_bundle = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_bundle))

for o in env.objects:
    if o.path_id in (-8490429130128858862, -3021806434293993593):
        tt = o.read_typetree()
        print(f"\nDonor PropsController PID {o.path_id}:")
        keys = tt["_props"]["_serializedKeys"]
        vals = tt["_props"]["_serializedValues"]
        for k, v in zip(keys, vals):
            if k in ("transformed", "cannon"):
                print(f"  Key '{k}': Name={v.get('Name')}, RootPath='{v.get('RootPath')}'")
                print(f"    InitFlags={v.get('InitFlags')}, PosOffset={v.get('PositionOffset')}, RotOffset={v.get('RotationOffset')}")
                print(f"    renderers={v.get('_renderers')}")
