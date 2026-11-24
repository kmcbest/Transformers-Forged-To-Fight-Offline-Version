import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import zipfile
import UnityPy
from pathlib import Path

zip_path = Path(r"O:\agent\eternal-war-blitzwing.zip")
print("=== Zip contents ===")
with zipfile.ZipFile(zip_path, "r") as zf:
    for info in zf.infolist():
        print(f"  {info.filename} ({info.file_size} bytes)")

donor_path = Path(r"E:\Agent\TFTF-blender\extracted_apk\assets\assetpack\megatron_gs_leader2015_odr\megatron_gs_leader2015.assetbundle")
print("\n=== Megatron Donor Props & Weapons ===")
env = UnityPy.load(str(donor_path))
obj_map = {o.path_id: o for o in env.objects}

for o in env.objects:
    if o.type.name == "MonoBehaviour":
        tt = o.read_typetree()
        if "_props" in tt:
            print(f"\nPropsController PID={o.path_id}:")
            keys = tt["_props"]["_serializedKeys"]
            vals = tt["_props"]["_serializedValues"]
            for k, v in zip(keys, vals):
                print(f"  key='{k}' Name='{v.get('Name')}' InitFlags={v.get('InitFlags')} _startActive={v.get('_startActive')} RootPath='{v.get('RootPath')}' Pos={v.get('PositionOffset')} Rot={v.get('RotationOffset')} Renderers={v.get('_renderers')} AOC={v.get('OverrideController')}")
        if "m_Prefabs" in tt:
            print(f"\nPrefabList PID={o.path_id}:")
            for p in tt["m_Prefabs"]:
                pref_pid = p.get("Prefab", {}).get("m_PathID", 0)
                pref_name = ""
                if pref_pid in obj_map:
                    pref_name = obj_map[pref_pid].read_typetree().get("m_Name", "")
                print(f"  Prefab='{pref_name}' PID={pref_pid} Amount={p.get('Amount')}")
        if "_events" in tt and isinstance(tt["_events"], dict) and "_serializedKeys" in tt["_events"]:
            print(f"\nCharacterAudio PID={o.path_id}:")
            for k, v in zip(tt["_events"]["_serializedKeys"], tt["_events"]["_serializedValues"]):
                if "projectile" in str(k).lower() or "weapon" in str(k).lower() or "gun" in str(k).lower() or "sword" in str(k).lower():
                    print(f"  audio '{k}' -> {v}")

print("\n=== Weapon SMRs in Megatron Donor ===")
for pid in (4561093141354196631, 8495398593779105175, 7267330081541926865, -6758328762533593613):
    if pid in obj_map:
        smr = obj_map[pid].read_typetree()
        go_pid = smr["m_GameObject"]["m_PathID"]
        go = obj_map[go_pid].read_typetree()
        mesh_pid = smr["m_Mesh"]["m_PathID"]
        mesh_name = obj_map[mesh_pid].read_typetree().get("m_Name") if mesh_pid in obj_map else "?"
        mats = [m["m_PathID"] for m in smr.get("m_Materials", [])]
        bones = [b["m_PathID"] for b in smr.get("m_Bones", [])]
        print(f"  SMR {pid} (GO='{go['m_Name']}' {go_pid}): mesh='{mesh_name}'({mesh_pid}) mats={mats} bones_cnt={len(bones)} root_bone={smr.get('m_RootBone')}")

print("\n=== Projectile Objects in Megatron Donor ===")
for o in env.objects:
    if o.type.name == "GameObject":
        go = o.read_typetree()
        if "projectile" in go.get("m_Name", "").lower() or "bullet" in go.get("m_Name", "").lower():
            print(f"  GO '{go['m_Name']}' PID={o.path_id} comps={go.get('m_Component')}")
