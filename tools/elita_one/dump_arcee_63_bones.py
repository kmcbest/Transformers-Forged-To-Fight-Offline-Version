import sys
import json
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

for obj in env.objects:
    if obj.path_id == 8283545308434878436: # SMR on Prefab 1
        tree = obj.read_typetree()
        bones = tree.get("m_Bones", [])
        bone_names = [go_dict.get(tr_to_go.get(b.get("m_PathID")), {}).get("m_Name") for b in bones]
        print(f"63 Deform Bones of Arcee SMR:")
        for i, b in enumerate(bone_names):
            print(f"  {i:2d}: {b}")
        with open(ROOT / "tools" / "elita_one" / "arcee_63_bones.json", "w", encoding="utf-8") as f:
            json.dump(bone_names, f, indent=2)
