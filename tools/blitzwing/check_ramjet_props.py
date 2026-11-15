import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

rj_bundle = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(rj_bundle))

for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_props" in tt:
            print(f"\nRamjet PropsController PID {o.path_id}:")
            keys = tt["_props"]["_serializedKeys"]
            vals = tt["_props"]["_serializedValues"]
            for k, v in zip(keys, vals):
                print(f"  Prop '{k}': Name='{v.get('Name')}' RootPath='{v.get('RootPath')}' InitFlags={v.get('InitFlags')}")
                print(f"    AOC={v.get('OverrideController')} renderers={v.get('_renderers')}")
                print(f"    pos={v.get('PositionOffset')} rot={v.get('RotationOffset')}")
