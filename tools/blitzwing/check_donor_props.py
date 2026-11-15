import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)

for o in env.objects:
    if o.path_id in (-8490429130128858862, -3021806434293993593):
        t = o.read_typetree()
        print(f"Donor PropsController PID={o.path_id}:")
        keys = t["_props"]["_serializedKeys"]
        vals = t["_props"]["_serializedValues"]
        for k, v in zip(keys, vals):
            print(f"  Prop '{k}': Name='{v.get('Name')}' InitFlags={v.get('InitFlags')} Pos={v.get('PositionOffset')} Rot={v.get('RotationOffset')} Renderers={v.get('_renderers')}")
