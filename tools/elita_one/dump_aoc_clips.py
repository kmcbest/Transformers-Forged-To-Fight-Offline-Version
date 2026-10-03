import UnityPy

bundle_path = r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\arcee_gs_deluxe2014_odr\arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(bundle_path)

for obj in env.objects:
    if obj.type.name == "AnimatorOverrideController":
        aoc = obj.read()
        print(f"\n=== AOC: {aoc.m_Name} ===")
        for pair in aoc.m_Clips:
            try:
                over = pair.m_OverrideClip.read().m_Name if pair.m_OverrideClip.path_id != 0 else "None"
            except Exception:
                over = f"External(path_id={pair.m_OverrideClip.path_id})"
            print(f"  Override: {over}")
