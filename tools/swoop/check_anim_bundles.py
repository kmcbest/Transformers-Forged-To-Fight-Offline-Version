import sys
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

p = r"E:\Agent\TFTF-blender\assets_netflix\character_anim_procedural.assetbundle"
e = UnityPy.load(p)
print("Files:", list(e.file.files.keys()))

check_pids = {
    7645321843667068633,
    -643812257501667161,
    -8287216037977883126,
    -7632205551962568777,
    2235498278053343569,
    -7989888022101248653,
}

for o in e.objects:
    if o.type.name == "AnimationClip":
        d = o.read()
        if o.path_id in check_pids or ("starscream" in d.m_Name.lower() and "heavy" in d.m_Name.lower()) or ("ramjet" in d.m_Name.lower() and "heavy" in d.m_Name.lower()):
            tt = o.read_typetree()
            m_cl = tt.get("m_ClipBindingConstant", {})
            gc = m_cl.get("genericBindings", [])
            stop = tt.get("m_MuscleClip", {}).get("m_StopTime")
            print(f"Clip pid={o.path_id:21d} name={d.m_Name:45s} stop={stop:.3f} bindings={len(gc)} in_check={o.path_id in check_pids}")
            # print Transform bindings if transformed clip
            if "transformed" in d.m_Name.lower() or o.path_id in (-8287216037977883126, 7645321843667068633):
                for b in gc[:12]:
                    print(f"    binding: path={b.get('path')} attr={b.get('attribute')} typeID={b.get('typeID')}")
