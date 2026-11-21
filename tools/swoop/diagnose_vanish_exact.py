import sys
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

env = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle")
objs = {o.path_id: o for o in env.objects}

# 1. Check all MonoBehaviours on Main Root (1529847556182042256)
root_go = objs[1529847556182042256].read_typetree()
for c in root_go["m_Component"]:
    co = objs[c["component"]["m_PathID"]]
    if co.type.name == "MonoBehaviour":
        tt = co.read_typetree()
        relevant = {k: v for k, v in tt.items() if k in ("_defaultTransformedScaleFactor", "_transformedScaleFactor", "_fighterTransform", "_characterModel", "_transformedTransform", "_propsController")}
        if relevant or "_transform" in str(tt).lower():
            print(f"Root MB {co.path_id}: { {k: v for k, v in tt.items() if k not in ('m_GameObject','m_Enabled','m_Script','_moves','PrefabList','_props')} }")

# 2. Check Vehicle SMR (4450385079657545705) & Robot SMR (-3606013326717668247) & Mesh AABBs
for name, pid in (("Robot SMR", -3606013326717668247), ("Vehicle SMR", 4450385079657545705)):
    tt = objs[pid].read_typetree()
    m_tt = objs[tt["m_Mesh"]["m_PathID"]].read_typetree()
    rb_pid = tt["m_RootBone"]["m_PathID"]
    rb_go = objs[objs[rb_pid].read_typetree()["m_GameObject"]["m_PathID"]].read_typetree()["m_Name"] if rb_pid in objs else str(rb_pid)
    print(f"\n{name} ({pid}):")
    print(f"  m_Enabled={tt.get('m_Enabled')} m_UpdateWhenOffscreen={tt.get('m_UpdateWhenOffscreen')} m_RootBone={rb_go}({rb_pid})")
    print(f"  SMR m_AABB={tt.get('m_AABB')}")
    print(f"  Mesh m_LocalAABB={m_tt.get('m_LocalAABB')}")
    print(f"  m_Materials={tt.get('m_Materials')}")

# 3. Check transformed GO (7693429312995989932) & its Transform & Animator
tgo = objs[7693429312995989932].read_typetree()
print(f"\ntransformed GO ({tgo.get('m_Name')}): m_IsActive={tgo.get('m_IsActive')}")
for c in tgo["m_Component"]:
    co = objs[c["component"]["m_PathID"]]
    ct = co.read_typetree()
    print(f"  comp {co.type.name} ({co.path_id}):", {k: v for k, v in ct.items() if k in ("m_LocalPosition", "m_LocalRotation", "m_LocalScale", "m_Controller", "m_Avatar", "m_ApplyRootMotion", "m_UpdateMode", "m_CullingMode", "m_Enabled")})

# 4. Compare Ramjet_Normal_attackHeavy vs StarScream_Normal_attackHeavy in character_anim_procedural.assetbundle
aenv = UnityPy.load(r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle")
aobjs = {o.path_id: o for o in aenv.objects}
for cid in (7645321843667068633, -8287216037977883126, -7989888022101248653, 2235498278053343569):
    c = aobjs[cid].read_typetree()
    mc = c["m_MuscleClip"]
    bc = c["m_ClipBindingConstant"]
    print(f"\nClip {cid} '{c.get('m_Name')}':")
    print(f"  m_StopTime={mc['m_StopTime']} m_StartTime={mc['m_StartTime']} loop={mc['m_LoopTime']} keepOrigY={mc.get('m_KeepOriginalPositionY')}")
    print(f"  m_DeltaPose x={mc.get('m_DeltaPose',{}).get('m_X')} startX={mc.get('m_StartX')} stopX={mc.get('m_StopX')}")
