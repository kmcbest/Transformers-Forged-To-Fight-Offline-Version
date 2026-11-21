import sys
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

p = r"E:\Agent\TFTF\extracted_apk\assets\assetpack\skywarp_gs_leader2015_odr\skywarp_gs_leader2015.assetbundle"
e = UnityPy.load(p)
objs = {o.path_id: o for o in e.objects}
for fn, fobj in e.file.files.items():
    if hasattr(fobj, "externals"):
        for fi, ext in enumerate(fobj.externals, start=1):
            print(f"ext[{fi}] = {getattr(ext, 'path', ext)}")

for o in e.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_defaultTransformedScaleFactor" in tt:
            print(f"ControllerProps ({o.path_id}): _defaultTransformedScaleFactor={tt.get('_defaultTransformedScaleFactor')} _specialTransformedScaleFactor={tt.get('_specialTransformedScaleFactor')}")
        if "_overrideControllerList" in tt:
            for x in tt["_overrideControllerList"]:
                if "heavy" in x.get("StateUniqueName", "").lower():
                    print(f"OCList: {x}")
        if "_props" in tt:
            for k, v in zip(tt["_props"]["_serializedKeys"], tt["_props"]["_serializedValues"]):
                if k == "transformed":
                    print(f"Prop 'transformed': InitFlags={v['InitFlags']} RootPath={v['RootPath']} Pos={v['PositionOffset']} Rot={v['RotationOffset']} Scale={v['Scale']}")
        if "_moves" in tt:
            for m in tt["_moves"]:
                if "heavy" in m.get("_animStateName", "").lower():
                    print(f"MoveSet: {m}")
    elif o.type.name == "AnimatorOverrideController":
        aoc = o.read_typetree()
        print(f"AOC {o.path_id} ({aoc.get('m_Name')}):")
        for idx, pair in enumerate(aoc.get("m_Clips", [])):
            if idx in (12, 58) or pair["m_OverrideClip"]["m_PathID"] == 7645321843667068633:
                print(f"  [{idx}] orig={pair['m_OriginalClip']} over={pair['m_OverrideClip']}")
