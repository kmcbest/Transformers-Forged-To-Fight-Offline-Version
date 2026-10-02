import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
arcee_bundle_path = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"

env = UnityPy.load(str(arcee_bundle_path))

go_dict = {}
tr_dict = {}
tr_to_go = {}
go_to_tr = {}

for obj in env.objects:
    if obj.type.name == "GameObject":
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == "Transform":
        tr = obj.read_typetree()
        tr_dict[obj.path_id] = tr
        go_id = tr.get("m_GameObject", {}).get("m_PathID")
        tr_to_go[obj.path_id] = go_id
        go_to_tr[go_id] = obj.path_id

def get_prefab_transforms(root_go_id):
    result = {}
    def recurse(go_id):
        go = go_dict.get(go_id)
        if not go: return
        name = go.get('m_Name')
        tr_id = go_to_tr.get(go_id)
        if name not in result:
            result[name] = tr_id
        tr = tr_dict.get(tr_id)
        if tr:
            for child in tr.get('m_Children', []):
                c_tr_id = child.get('m_PathID')
                c_go_id = tr_to_go.get(c_tr_id)
                recurse(c_go_id)
    recurse(root_go_id)
    return result

p1_transforms = get_prefab_transforms(-5193028223035516378)
p2_transforms = get_prefab_transforms(-4037407093067927022)

print(f"Prefab 1 (Showcase) unique named transforms: {len(p1_transforms)}")
print(f"Prefab 2 (Combat LW) unique named transforms: {len(p2_transforms)}")

# Check SMR bones
for smr_pid in [3949589716393965935, 8283545308434878436]:
    for obj in env.objects:
        if obj.path_id == smr_pid:
            smr = obj.read_typetree()
            bones = smr.get("m_Bones", [])
            in_p1 = sum(1 for b in bones if b.get("m_PathID") in p1_transforms.values())
            in_p2 = sum(1 for b in bones if b.get("m_PathID") in p2_transforms.values())
            print(f"SMR {smr_pid}: {len(bones)} bones | In P1: {in_p1} | In P2: {in_p2}")
