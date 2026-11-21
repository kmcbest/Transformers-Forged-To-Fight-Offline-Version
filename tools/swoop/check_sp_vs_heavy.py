import sys
import json
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle")
objs = {o.path_id: o for o in env.objects}

# Print all Jet AOC clips
jet_aoc = objs[-6340484879223379266].read_typetree()
aenv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle")
aobjs = {o.path_id: o for o in aenv.objects}

print("=== All 18 Jet AOC slots ===")
for i, p in enumerate(jet_aoc["m_Clips"]):
    of, op = p["m_OriginalClip"]["m_FileID"], p["m_OriginalClip"]["m_PathID"]
    vf, vp = p["m_OverrideClip"]["m_FileID"], p["m_OverrideClip"]["m_PathID"]
    onm = aobjs[op].read().m_Name if (of == 5 and op in aobjs) else str((of, op))
    vnm = objs[vp].read().m_Name if (vf == 0 and vp in objs) else (aobjs[vp].read().m_Name if (vf == 5 and vp in aobjs) else str((vf, vp)))
    print(f"  [{i:2d}] orig=({of},{op}) {onm:32s} -> over=({vf},{vp}) {vnm}")

# Check Avatar of transformed (-5001927141424851882) vs Robot Avatar
av = objs[-5001927141424851882].read_typetree()
print(f"\n=== transformed Avatar (-5001927141424851882): '{av.get('m_Name')}' ===")
print("  skeleton len:", len(av.get("m_Avatar", {}).get("m_AvatarSkeleton", {}).get("data", {}).get("m_Node", [])))

# Check animator_prop_gameplay (341294063036995988) states!
ctrl = objs[341294063036995988].read_typetree()
print(f"\n=== Controller '{ctrl.get('m_Name')}' (341294063036995988) ===")
tos = ctrl.get("m_TOS", [])
tos_map = dict(tos) if isinstance(tos, list) else tos
# Find states in m_Controller
states = ctrl.get("m_Controller", {}).get("m_StateMachineArray", [])
for sm in states:
    for st in sm.get("m_StateConstantArray", []):
        st_name = tos_map.get(st.get("m_NameID"), st.get("m_NameID"))
        print(f"  State '{st_name}' speed={st.get('m_Speed')} loop={st.get('m_Loop')} leafBlendTreeCount={len(st.get('m_BlendTreeConstantArray', []))}")

# Check in assets_redeco/moves.assetbundle what Character MoveSets point to move_heavy_starscream_shoot!
menv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")
for o in menv.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        if "move_heavy_starscream" in d.m_Script or "move_heavy_jet" in d.m_Name:
            if d.m_Name.startswith("move_heavy"):
                print(f"  Move in moves.assetbundle: {d.m_Name}")
