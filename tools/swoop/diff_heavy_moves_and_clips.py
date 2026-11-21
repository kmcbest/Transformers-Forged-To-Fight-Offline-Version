import sys
import os
import json
import glob
import UnityPy

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

m_path = r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle"
menv = UnityPy.load(m_path)
targets = ("move_heavy_swoop", "move_heavy_starscream_shoot", "move_heavy_ramjet_donut", "move_heavy_grimlock")
moves_by_name = {}
for o in menv.objects:
    if o.type.name == "TextAsset":
        d = o.read()
        if d.m_Name in targets:
            moves_by_name[d.m_Name] = json.loads(d.m_Script)

for name in targets:
    if name not in moves_by_name:
        print(f"MISSING {name}")
        continue
    evs = moves_by_name[name]["moves"]["events"]
    print(f"\n=== {name} (events={len(evs)}) ===")
    for ev in evs:
        t = ev.get("type", "")
        if any(k in t for k in ("Transform", "Prop", "Anim", "Prefab", "Projectile", "Scale", "State", "Camera")):
            compact = {k: v for k, v in ev.items() if k not in ("sc", "cc", "dn", "mn", "id", "c")}
            print(f"  f={ev.get('f'):2d} d={ev.get('d',0):2d} {t:28s} {compact}")

# Search CAB-a742a3fff84aa604ba32daca2b1ea500 across assetbundles
print("\n=== Searching for CAB-a742a3fff84aa604ba32daca2b1ea500 & 7645321843667068633 ===")
for root_dir in (r"E:\Agent\TFTF-blender\assets_redeco", r"E:\Agent\TFTF-blender\assets_netflix", r"E:\Agent\TFTF\assets_netflix", r"E:\Agent\TFTF\assets"):
    if not os.path.isdir(root_dir):
        continue
    for p in glob.glob(os.path.join(root_dir, "*.assetbundle")):
        bn = os.path.basename(p)
        if any(x in bn for x in ("shared", "ramjet", "starscream", "grimlock", "anim", "fighter")):
            try:
                e = UnityPy.load(p)
                fnames = list(e.file.files.keys())
                if any("a742a3fff84aa604ba32daca2b1ea500" in fn for fn in fnames):
                    print(f"  FOUND CAB in {p} -> {fnames}")
                    for o in e.objects:
                        if o.path_id in (7645321843667068633, -7632205551962568777, 5214496857524066160):
                            print(f"    OBJ {o.path_id} type={o.type.name} name={getattr(o.read(), 'm_Name', '?')}")
                # also inspect ramjet's original AOC
                if bn == "ramjet_gs_deluxe2008.assetbundle":
                    objs = {o.path_id: o for o in e.objects}
                    aoc_fight = objs[6432204470035570307].read_typetree()
                    aoc_jet = objs[-6340484879223379266].read_typetree()
                    print(f"  Original Ramjet Fight AOC [58]: {aoc_fight['m_Clips'][58]}")
                    print(f"  Original Ramjet Jet   AOC [12]: {aoc_jet['m_Clips'][12]}")
            except Exception:
                pass
