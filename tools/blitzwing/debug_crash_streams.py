import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
import UnityPy

MEGA = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
BW   = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")
MV   = Path(r"E:\Agent\TFTF-blender\assets_redeco\moves.assetbundle")

for label, p in [("MEGA", MEGA), ("BLITZWING", BW), ("MOVES", MV)]:
    env = UnityPy.load(str(p))
    sf = next(f for f in env.file.files.values() if hasattr(f, "externals"))
    print(f"\n=== {label}: {p.name} ===")
    print("  Externals (1-indexed FileID!):")
    for idx, ext in enumerate(sf.externals, 1):
        print(f"    FileID={idx}: path='{ext.path}' guid={ext.guid} type={ext.type}")
    print("  Files in CAB:", {k: len(getattr(v, 'bytes', b'')) if hasattr(v, 'bytes') else 'SF' for k, v in env.file.files.items()})

# Check every AudioClip m_Resource, Texture2D m_StreamData, Mesh m_StreamData, and AssetBundle m_PreloadTable in BLITZWING!
bw_env = UnityPy.load(str(BW))
bw_sf = next(f for f in bw_env.file.files.values() if hasattr(f, "externals"))
res_bytes_len = len(bw_env.file.files["CAB-7b4900007b4900007b4900007b490001.resource"].bytes)
ress_bytes_len = len(bw_env.file.files["CAB-7b4900007b4900007b4900007b490001.resS"].bytes)
print(f"\n=== Checking BLITZWING streams (.resource={res_bytes_len}, .resS={ress_bytes_len}) ===")
for o in bw_env.objects:
    if o.type.name == "AudioClip":
        t = o.read_typetree()
        r = t["m_Resource"]
        if r["m_Offset"] + r["m_Size"] > res_bytes_len or not r["m_Source"].endswith(".resource"):
            print(f"  [BAD AUDIO] {o.path_id} '{t['m_Name']}': {r}")
    elif o.type.name == "Texture2D":
        t = o.read_typetree()
        sd = t["m_StreamData"]
        if sd["size"] > 0:
            if sd["offset"] + sd["size"] > ress_bytes_len or not sd["path"].endswith(".resS"):
                print(f"  [BAD TEX STREAM] {o.path_id} '{t['m_Name']}': {sd}")
    elif o.type.name == "Mesh":
        t = o.read_typetree()
        sd = t.get("m_StreamData", {})
        if sd.get("size", 0) > 0:
            if sd["offset"] + sd["size"] > ress_bytes_len or not sd["path"].endswith(".resS"):
                print(f"  [BAD MESH STREAM] {o.path_id} '{t['m_Name']}': {sd}")
    elif o.type.name == "MonoBehaviour":
        t = o.read_typetree()
        sc = t["m_Script"]
        if sc["m_FileID"] == 0 and sc["m_PathID"] not in bw_sf.objects:
            print(f"  [BAD SCRIPT] {o.path_id} '{t.get('m_Name')}': {sc}")

# Check type_id / serialized_type of cloned objects in BLITZWING
for pid in (-8888888888888888911, -8888888888888888912):
    o = bw_sf.objects[pid]
    tt = o.read_typetree()
    print(f"  [CLONED OBJ] {pid}: type={o.type.name} type_id={o.type_id} serialized_type={o.serialized_type.class_id} name={tt.get('m_Name')}")

# Check moves.assetbundle cloned objects
mv_env = UnityPy.load(str(MV))
mv_sf = next(f for f in mv_env.file.files.values() if hasattr(f, "objects"))
for pid in (-8888888888888888901, -8888888888888888902, -8888888888888888903, -8888888888888888904):
    o = mv_sf.objects[pid]
    tt = o.read_typetree()
    print(f"  [MOVES CLONE] {pid}: type={o.type.name} type_id={o.type_id} name={tt.get('m_Name')} script_len={len(tt.get('m_Script',''))}")
