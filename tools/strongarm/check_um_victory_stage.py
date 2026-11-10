import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

# 1. Inspect ultramagnus_gs_leader VictoryStagePrefab & fight AOC
um_paths = list(Path(r"E:\Agent\TFTF\extracted_apk").glob("**/ultramagnus_gs_leader.assetbundle"))
if um_paths:
    env = UnityPy.load(str(um_paths[0]))
    sf = next(f for f in list(env.files.values())[0].files.values() if hasattr(f, "externals"))
    print("Ultra Magnus externals:", [(i+1, getattr(e, 'path', str(e))) for i, e in enumerate(sf.externals)])
    for o in env.objects:
        if o.type.name == "MonoBehaviour":
            t = o.read_typetree()
            if "VictoryStagePrefab" in t:
                print("UM PlayerReferences:", t.get("VictoryStagePrefab"))
        elif o.type.name == "AnimatorOverrideController":
            aoc = o.read_typetree()
            if "fight" in aoc.get("m_Name", "").lower():
                for c in aoc.get("m_Clips", []):
                    op = c.get("m_OriginalClip", {})
                    if op.get("m_PathID") in (3642901185112467297, -4048722777385356729):
                        print("UM Victory AOC entry:", c)
else:
    print("No ultramagnus_gs_leader.assetbundle found")

# 2. Compare Prowl vs Ultra Magnus VictoryStagePrefab external
p_env = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
sf_p = next(f for f in list(p_env.files.values())[0].files.values() if hasattr(f, "externals"))
print("Prowl externals:", [(i+1, getattr(e, 'path', str(e))) for i, e in enumerate(sf_p.externals)])
for o in p_env.objects:
    if o.type.name == "MonoBehaviour":
        t = o.read_typetree()
        if "VictoryStagePrefab" in t:
            print("Prowl PlayerReferences:", t.get("VictoryStagePrefab"))
