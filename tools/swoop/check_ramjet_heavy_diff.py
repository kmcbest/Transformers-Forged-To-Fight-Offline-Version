import sys
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

def dump_bot(path, label):
    print(f"================ {label} ================")
    e = UnityPy.load(path)
    objs = {o.path_id: o for o in e.objects}
    for o in e.objects:
        if o.type.name == "MonoBehaviour":
            tt = o.read_typetree()
            if "_defaultTransformedScaleFactor" in tt:
                print(f"ControllerProps ({o.path_id}): _defaultTransformedScaleFactor={tt.get('_defaultTransformedScaleFactor')} _specialTransformedScaleFactor={tt.get('_specialTransformedScaleFactor')}")
            if "_overrideControllerList" in tt:
                for x in tt["_overrideControllerList"]:
                    if "heavy" in x.get("StateUniqueName", "").lower() or "heavy" in x.get("OverrideClipName", "").lower():
                        print(f"OCList: {x}")
            if "_props" in tt:
                for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
                    if k == "transformed":
                        print(f"Prop 'transformed': InitFlags={v['InitFlags']} RootPath={v['RootPath']} Pos={v['PositionOffset']} Rot={v['RotationOffset']} Scale={v['Scale']} _animator={v['_animator']} _renderers={v['_renderers']}")
                        for r in v["_renderers"]:
                            rp = r["m_PathID"]
                            if rp in objs:
                                rt = objs[rp].read_typetree()
                                print(f"  Renderer {rp} ({objs[rp].type.name}): m_Enabled={rt.get('m_Enabled')} UpdateOffscreen={rt.get('m_UpdateWhenOffscreen')} AABB={rt.get('m_AABB')}")
            if "_moves" in tt and "AnimatorState" not in str(tt.keys()):
                for m in tt["_moves"]:
                    if "heavy" in m.get("_animStateName", "").lower() or "heavy" in m.get("_name", "").lower():
                        print(f"MoveSet entry: {m}")

dump_bot(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle", "Donor Ramjet")
dump_bot(r"E:\Agent\TFTF-blender\assets_redeco\starscream_ghost_gs.assetbundle", "Starscream Ghost")
dump_bot(r"E:\Agent\TFTF-blender\assets_redeco\swoop_gs_deluxe2008.assetbundle", "Current Swoop")
