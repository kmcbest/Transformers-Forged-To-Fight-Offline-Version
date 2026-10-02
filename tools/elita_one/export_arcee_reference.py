import sys
import json
import struct
from pathlib import Path
import UnityPy

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "arcee_gs_deluxe2014_odr" / "arcee_gs_deluxe2014.assetbundle"
OUT_DIR = ROOT / "tools" / "elita_one" / "arcee_extracted"
OUT_DIR.mkdir(parents=True, exist_ok=True)

print(f"=== Extracting Arcee Data from {BUNDLE.name} ===")
env = UnityPy.load(str(BUNDLE))

# 1. Map GameObjects and Transforms
tr_to_go = {}
go_to_tr = {}
go_dict = {}
tr_dict = {}

for obj in env.objects:
    if obj.type.name == 'GameObject':
        go_dict[obj.path_id] = obj.read_typetree()
    elif obj.type.name == 'Transform':
        tree = obj.read_typetree()
        tr_dict[obj.path_id] = tree
        go_id = tree.get('m_GameObject', {}).get('m_PathID')
        tr_to_go[obj.path_id] = go_id
        go_to_tr[go_id] = obj.path_id

# Find robot SMR (63 bones)
robot_smr = None
robot_bone_names = []
for obj in env.objects:
    if obj.type.name == "SkinnedMeshRenderer":
        tree = obj.read_typetree()
        bones = tree.get("m_Bones", [])
        if len(bones) == 63 and not robot_bone_names:
            robot_smr = tree
            for b in bones:
                tr_id = b.get("m_PathID")
                go_id = tr_to_go.get(tr_id)
                robot_bone_names.append(go_dict.get(go_id, {}).get("m_Name", "UNKNOWN"))

print(f"[✓] Extracted {len(robot_bone_names)} Arcee robot bones:")
for i, b in enumerate(robot_bone_names):
    print(f"  [{i:2d}] {b}")

(OUT_DIR / "arcee_63_bones.json").write_text(json.dumps(robot_bone_names, indent=2), encoding="utf-8")

# Extract Arcee Body Mesh and save as OBJ for Blender reference
for obj in env.objects:
    if obj.type.name == "Mesh":
        tree = obj.read_typetree()
        if tree.get("m_Name") == "cha_arcee_gs_deluxe2014_00":
            mesh_obj = obj.read()
            # UnityPy mesh export
            obj_text = mesh_obj.export()
            if isinstance(obj_text, str):
                (OUT_DIR / "arcee_robot_reference.obj").write_text(obj_text, encoding="utf-8")
                print(f"[✓] Exported Arcee robot reference OBJ ({len(obj_text)/1024:.1f} KB)")
            
            # Save bindposes
            bindposes = tree.get("m_BindPose", [])
            (OUT_DIR / "arcee_bindposes.json").write_text(json.dumps(bindposes, indent=2), encoding="utf-8")
            print(f"[✓] Saved {len(bindposes)} Arcee bindposes.")
            break

# Also extract textures
for obj in env.objects:
    if obj.type.name == "Texture2D":
        tree = obj.read_typetree()
        name = tree.get("m_Name")
        if name in ("cha_arcee_gs_deluxe2014_main_a", "main_NM", "main_tform_misc_RAOE"):
            tex = obj.read()
            out_png = OUT_DIR / f"{name}.png"
            tex.image.save(out_png)
            print(f"[✓] Saved texture: {out_png.name} ({tex.image.size})")
