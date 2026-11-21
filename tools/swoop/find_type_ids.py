import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
from pathlib import Path

bundle_path = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
env = UnityPy.load(str(bundle_path))
sf = list(env.assets)[0]

print(f"Total sf.types: {len(sf.types)}")
print(f"Total sf.script_types: {len(sf.script_types)}")

# map script_types index to (fid, pid)
st_map = {i: (st.local_serialized_file_index, st.local_identifier_in_file) for i, st in enumerate(sf.script_types)}

script_pids = {
    "Projectile": -3660570848581127988,
    "MoveSet": 2297153707519481197,
    "PrefabLib": -3815473324432562333,
    "MoveSequencer": 4113389322536752908,
}

for name, spid in script_pids.items():
    # find in script_types
    matching_sti = [i for i, (fid, pid) in st_map.items() if fid == 0 and pid == spid]
    print(f"\n{name} (spid={spid}): matching script_types index = {matching_sti}")
    # find in sf.types
    matching_type_ids = []
    for type_id, t in enumerate(sf.types):
        if t.class_id == 114 and t.script_type_index in matching_sti:
            matching_type_ids.append((type_id, t.script_type_index))
    print(f"  matching type_ids in sf.types: {matching_type_ids}")
