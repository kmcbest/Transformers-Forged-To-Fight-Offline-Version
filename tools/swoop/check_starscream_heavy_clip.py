import sys
import json
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

aenv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle")
aobjs = {o.path_id: o for o in aenv.objects}

ss_t = aobjs[-7989888022101248653].read_typetree()
print("StarScream_Normal_attackHeavy_transformed:")
print("  stopTime:", ss_t["m_MuscleClip"]["m_StopTime"])
print("  m_StartX:", ss_t["m_MuscleClip"].get("m_StartX"))
print("  m_StopX:", ss_t["m_MuscleClip"].get("m_StopX"))
print("  bindings count:", len(ss_t["m_ClipBindingConstant"]["genericBindings"]))

# Check Starscream's ProjectileMoveEvent vs Swoop's ProjectileMoveEvent in moves.assetbundle
menv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
for o in menv.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        if d.m_Name in ("move_heavy_swoop", "move_heavy_starscream_shoot"):
            data = json.loads(d.m_Script)
            for ev in data["moves"]["events"]:
                if ev.get("type") in ("ProjectileMoveEvent", "ParticleMoveEvent"):
                    print(f"\n{d.m_Name} {ev['type']} f={ev['f']}: pn={ev.get('pn')} po={ev.get('po')} ref={ev.get('ref')} atr={ev.get('atr')}")
