import bpy
import mathutils
import numpy as np
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
ARCEE_OBJ = ROOT / "tools" / "elita_one" / "arcee_extracted" / "arcee_robot_reference.obj"
OUT_BLEND = ROOT / "tools" / "elita_one" / "elita_one_arcee_setup.blend"

print("=== Setting up Elita One & Arcee in Blender ===")
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Arcee reference OBJ
bpy.ops.wm.obj_import(filepath=str(ARCEE_OBJ))
arcee_objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']
arcee_mesh = arcee_objs[0] if arcee_objs else None
if arcee_mesh:
    arcee_mesh.name = "Arcee_Ghost_Reference"
    print(f"[✓] Imported Arcee reference: {len(arcee_mesh.data.vertices)} verts")
    a_bb = arcee_mesh.bound_box
    print(f"    Arcee X: [{min(v[0] for v in a_bb):.2f}, {max(v[0] for v in a_bb):.2f}]")
    print(f"    Arcee Y: [{min(v[1] for v in a_bb):.2f}, {max(v[1] for v in a_bb):.2f}]")
    print(f"    Arcee Z: [{min(v[2] for v in a_bb):.2f}, {max(v[2] for v in a_bb):.2f}]")

# 2. Import Elita One FBX
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

# Find Elita robot objects
elita_mesh = bpy.data.objects.get("SK_CH_11.001")
elita_arm = bpy.data.objects.get("SK_CH_11")

# Delete vehicle objects and icospheres for clean workspace
for name in ["Icosphere", "Icosphere.001", "SK_TR_11", "SK_TR_11.001"]:
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)

if elita_mesh and elita_arm:
    elita_mesh.name = "Elita_One_Mesh"
    elita_arm.name = "Elita_One_Armature"
    print(f"[✓] Imported Elita One Robot: {len(elita_mesh.data.vertices)} verts, {len(elita_arm.data.bones)} bones")
    e_bb = elita_mesh.bound_box
    print(f"    Elita X: [{min(v[0] for v in e_bb):.2f}, {max(v[0] for v in e_bb):.2f}]")
    print(f"    Elita Y: [{min(v[1] for v in e_bb):.2f}, {max(v[1] for v in e_bb):.2f}]")
    print(f"    Elita Z: [{min(v[2] for v in e_bb):.2f}, {max(v[2] for v in e_bb):.2f}]")

# Save initial blend
bpy.ops.wm.save_as_mainfile(filepath=str(OUT_BLEND))
print(f"[✓] Saved initial setup to: {OUT_BLEND}")
