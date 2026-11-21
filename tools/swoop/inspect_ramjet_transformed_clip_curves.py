import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy

PROC_BUNDLE = r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle"
env = UnityPy.load(PROC_BUNDLE)

for o in env.objects:
    if o.type.name == "AnimationClip":
        tt = o.read_typetree()
        if tt["m_Name"] in ["frontend_Ramjet_levelup_vehicle_idle_transformed", "frontend_Jet_levelup_vehicle_idle", "Ramjet_Normal_attackHeavy_transformed"]:
            print(f"=== {tt['m_Name']} ===")
            mc = tt.get("m_MuscleClip", {})
            print(f"  m_StartTime={mc.get('m_StartTime')}, m_StopTime={mc.get('m_StopTime')}")
            bindings = tt.get("m_ClipBindingConstant", {}).get("genericBindings", [])
            print(f"  genericBindings count: {len(bindings)}")
            for b in bindings[:15]:
                print(f"    path={b.get('path')} attr={b.get('attribute')} typeID={b.get('typeID')}")
