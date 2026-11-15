import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy, json

donor_bundle = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
env = UnityPy.load(str(donor_bundle))

for o in env.objects:
    if o.path_id in (-8490429130128858862, -3021806434293993593):
        tt = o.read_typetree()
        print(f"\nPropsController PID {o.path_id}:")
        vals = tt["_props"]["_serializedValues"]
        for v in vals:
            if v["Name"] in ("transformed", "cannon"):
                print(f"Prop '{v['Name']}':")
                for k in v:
                    print(f"  {k}: {v[k]}")
