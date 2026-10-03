import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
elita_bundle = ROOT / "assets_redeco" / "elita_one_gs.assetbundle"
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

e_env = UnityPy.load(str(elita_bundle))
a_env = UnityPy.load(str(arcee_bundle))

e_objs = {obj.path_id: obj for obj in e_env.objects}
a_objs = {obj.path_id: obj for obj in a_env.objects}

print(f"Arcee objects: {len(a_objs)}")
print(f"Elita objects: {len(e_objs)}")

only_in_a = set(a_objs.keys()) - set(e_objs.keys())
only_in_e = set(e_objs.keys()) - set(a_objs.keys())
common = set(a_objs.keys()) & set(e_objs.keys())

print(f"Only in Arcee: {len(only_in_a)}")
for pid in only_in_a:
    print(f"  {pid}: {a_objs[pid].type.name}")

print(f"Only in Elita: {len(only_in_e)}")
for pid in only_in_e:
    print(f"  {pid}: {e_objs[pid].type.name}")

# Check modified objects
diff_types = {}
for pid in common:
    ao = a_objs[pid]
    eo = e_objs[pid]
    if ao.type.name != eo.type.name:
        print(f"Type mismatch for {pid}: {ao.type.name} vs {eo.type.name}")
        continue
    
    tname = ao.type.name
    # compare raw or typetree
    try:
        at = ao.read_typetree()
        et = eo.read_typetree()
        if at != et:
            diff_types.setdefault(tname, []).append(pid)
    except Exception as ex:
        # maybe raw bytes differ
        pass

print("\nModified object types:")
for tname, pids in diff_types.items():
    print(f"  {tname} ({len(pids)} modified):")
    for pid in pids[:10]:
        try:
            name = a_objs[pid].read_typetree().get("m_Name", "")
            print(f"    pid {pid}: name='{name}'")
        except:
            print(f"    pid {pid}")
