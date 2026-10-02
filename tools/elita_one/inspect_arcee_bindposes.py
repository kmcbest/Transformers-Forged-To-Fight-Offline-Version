import sys
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
arcee_bundle = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
env = UnityPy.load(str(arcee_bundle))

go_dict = {}
tr_to_go = {}
for obj in env.objects:
    if obj.type.name == "GameObject":
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == "Transform":
        tr = obj.read_typetree()
        tr_to_go[obj.path_id] = tr.get("m_GameObject", {}).get("m_PathID")

# Get Arcee body mesh bindposes
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_arcee_gs_deluxe2014_00":
            bp = tree.get("m_BindPose", [])
            print(f"Arcee Mesh cha_arcee_gs_deluxe2014_00 has {len(bp)} bindposes")

# Get SMR bones order
for smr_pid in [3949589716393965935, 8283545308434878436]:
    for obj in env.objects:
        if obj.path_id == smr_pid:
            tree = obj.read_typetree()
            bones = tree.get("m_Bones", [])
            bone_names = [go_dict.get(tr_to_go.get(b.get("m_PathID")), {}).get("m_Name") for b in bones]
            print(f"SMR {smr_pid} bone count: {len(bone_names)}")
            print(f"First 10 bones: {bone_names[:10]}")
