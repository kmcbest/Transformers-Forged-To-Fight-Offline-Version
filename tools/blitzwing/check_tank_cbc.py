import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')
import UnityPy

DONOR_BUNDLE = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle"
env = UnityPy.load(DONOR_BUNDLE)

for o in env.objects:
    if o.type.name == "AnimationClip":
        t = o.read_typetree()
        name = t.get("m_Name")
        if name in ("frontend_Megatron_GS_levelup_vehicle_idle_transformed", "megatron_GS_attackHeavy_transformed"):
            print(f"=== CLIP: {name} ===")
            cbc = t.get("m_ClipBindingConstant", {})
            generic_bindings = cbc.get("genericBindings", [])
            print(f"  genericBindings count: {len(generic_bindings)}")
            for b in generic_bindings[:10]:
                print(f"    path={b.get('path')} attribute={b.get('attribute')} typeID={b.get('typeID')}")
