import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

# 1. Check Elita One Root GameObjects and Animator references
env_e = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\elita_one_gs.assetbundle")
e_gos = {o.path_id: o.read_typetree() for o in env_e.objects if o.type.name == "GameObject"}
e_trs = {o.path_id: o.read_typetree() for o in env_e.objects if o.type.name == "Transform"}
for pid, tr in e_trs.items():
    if tr.get("m_Father", {}).get("m_PathID") == 0:
        gpid = tr.get("m_GameObject", {}).get("m_PathID")
        print(f"ELITA Root GO: '{e_gos[gpid].get('m_Name')}' (PID {gpid})")

# 2. Check Prowl Official vs Strongarm Current Root GameObjects, Animators, and any object differences!
env_p = UnityPy.load(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
env_s = UnityPy.load(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")

p_gos = {o.path_id: o.read_typetree() for o in env_p.objects if o.type.name == "GameObject"}
p_trs = {o.path_id: o.read_typetree() for o in env_p.objects if o.type.name == "Transform"}
for pid, tr in p_trs.items():
    if tr.get("m_Father", {}).get("m_PathID") == 0:
        gpid = tr.get("m_GameObject", {}).get("m_PathID")
        print(f"PROWL OFFICIAL Root GO: '{p_gos[gpid].get('m_Name')}' (PID {gpid})")

s_gos = {o.path_id: o.read_typetree() for o in env_s.objects if o.type.name == "GameObject"}
s_trs = {o.path_id: o.read_typetree() for o in env_s.objects if o.type.name == "Transform"}
for pid, tr in s_trs.items():
    if tr.get("m_Father", {}).get("m_PathID") == 0:
        gpid = tr.get("m_GameObject", {}).get("m_PathID")
        print(f"STRONGARM CURRENT Root GO: '{s_gos[gpid].get('m_Name')}' (PID {gpid})")

# Compare Animators in PROWL OFFICIAL vs STRONGARM CURRENT
print("\n=== ANIMATORS DIFF (PROWL OFFICIAL vs STRONGARM) ===")
p_objs = {o.path_id: o for o in env_p.objects}
s_objs = {o.path_id: o for o in env_s.objects}

for pid, o in p_objs.items():
    if o.type.name == "Animator":
        pt = o.read_typetree()
        st = s_objs[pid].read_typetree() if pid in s_objs else None
        gname = p_gos.get(pt.get("m_GameObject", {}).get("m_PathID"), {}).get("m_Name")
        if pt != st:
            print(f"ANIMATOR DIFF PID={pid} GO='{gname}':")
            for k in pt:
                if st is None or pt[k] != st.get(k):
                    print(f"  {k}: OFFICIAL={pt[k]} vs STRONGARM={st.get(k) if st else None}")
        else:
            print(f"ANIMATOR IDENTICAL PID={pid} GO='{gname}' ctrl={pt.get('m_Controller')}")

# Compare ALL objects present in p_objs that changed unexpectedly (excluding Mesh, SMR, Material, Texture2D, AssetBundle, GameObject.m_Name)
print("\n=== OTHER STRUCTURAL DIFFS ===")
for pid, o in p_objs.items():
    if o.type.name in ("GameObject", "MonoBehaviour", "AnimatorOverrideController", "AnimatorController", "Animation"):
        pt = o.read_typetree()
        st = s_objs[pid].read_typetree()
        if o.type.name == "GameObject":
            # ignore only expected root renames
            pt_copy = dict(pt)
            st_copy = dict(st)
            if pt_copy.get("m_Name") != st_copy.get("m_Name"):
                print(f"GO rename: {pt_copy['m_Name']} -> {st_copy['m_Name']}")
            pt_copy.pop("m_Name", None)
            st_copy.pop("m_Name", None)
            if pt_copy != st_copy:
                print(f"GO DIFF PID={pid}: {pt_copy} vs {st_copy}")
        elif pt != st:
            print(f"{o.type.name} DIFF PID={pid} name='{pt.get('m_Name')}':")
            if o.type.name == "AnimatorOverrideController":
                for c1, c2 in zip(pt.get("m_Clips", []), st.get("m_Clips", [])):
                    if c1 != c2:
                        print(f"  clip diff: {c1} -> {c2}")
            else:
                for k in pt:
                    if pt[k] != st.get(k):
                        print(f"  {k}: {str(pt[k])[:120]} -> {str(st.get(k))[:120]}")
