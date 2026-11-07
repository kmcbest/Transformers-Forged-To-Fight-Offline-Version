import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import UnityPy

IH_BUNDLE = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\ironhide_cin_rotf_odr\ironhide_cin_rotf.assetbundle")
PROC_BUNDLE = Path(r"E:\Agent\TFTF\assets_netflix\character_anim_procedural.assetbundle")

env = UnityPy.load(str(IH_BUNDLE))
id_to_obj = {o.path_id: o for o in env.objects}

def get_name(o):
    try:
        return o.read_typetree().get("m_Name", "")
    except Exception:
        return ""

for o in env.objects:
    if o.type.name == "AssetBundle":
        ab = o.read_typetree()
        print("=== IRONHIDE CONTAINER ASSETS ===")
        for item in ab.get("m_Container", []):
            key = item[0]
            pid = item[1]["asset"]["m_PathID"]
            target = id_to_obj.get(pid)
            print(f"  '{key}' -> [{target.type.name if target else '?'}] '{get_name(target) if target else '?'}' (pid={pid})")
    elif o.type.name == "Material":
        mt = o.read_typetree()
        mname = mt.get("m_Name")
        texs = []
        for te in mt.get("m_SavedProperties", {}).get("m_TexEnvs", []):
            pname = te[0] if isinstance(te, (list, tuple)) else te.get("first", "")
            sec = te[1] if isinstance(te, (list, tuple)) else te.get("second", {})
            tpid = sec.get("m_Texture", {}).get("m_PathID", 0)
            if tpid and tpid in id_to_obj:
                texs.append(f"{pname}={get_name(id_to_obj[tpid])}")
        print(f"Material '{mname}': {texs}")

print("\n=== BRAWLER / IRONHIDE CLIPS IN PROCEDURAL BUNDLE ===")
env_p = UnityPy.load(str(PROC_BUNDLE))
clips = []
for o in env_p.objects:
    if o.type.name == "AnimationClip":
        nm = get_name(o)
        if any(k in nm.lower() for k in ["ironhide", "brawler", "heavy", "teamselect", "prefight"]):
            clips.append(nm)
for c in sorted(set(clips)):
    print(f"  Clip: '{c}'")
