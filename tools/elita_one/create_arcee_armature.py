import json
import bpy
import mathutils
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BONES_PATH = ROOT / "tools" / "elita_one" / "arcee_extracted" / "arcee_63_bones.json"
BINDPOSES_PATH = ROOT / "tools" / "elita_one" / "arcee_extracted" / "arcee_bindposes.json"
BLEND_FILE = ROOT / "tools" / "elita_one" / "elita_one_arcee_setup.blend"

with open(BONES_PATH, "r") as f:
    bone_names = json.load(f)

with open(BINDPOSES_PATH, "r") as f:
    bindposes = json.load(f)

print(f"Loaded {len(bone_names)} bone names and {len(bindposes)} bindposes.")

bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

# Create Arcee Armature
arm_data = bpy.data.armatures.new("Arcee_Armature")
arm_obj = bpy.data.objects.new("Arcee_Armature", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

# Calculate bone rest matrices: Matrix = Inverse(BindPose)
# Note: Bindpose is in Unity coordinates (Y-up, Z-forward, X-right)
# In Blender, to match Arcee_Ghost_Reference (which was rotated 90 deg around X):
# rot_x_90 = Matrix.Rotation(math.radians(90.0), 4, 'X')
import math
rot_x = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'X')

edit_bones = {}
for i, name in enumerate(bone_names):
    bp = bindposes[i]
    m = mathutils.Matrix([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    try:
        inv_m = m.inverted()
    except Exception:
        inv_m = mathutils.Matrix.Identity(4)
        
    # Transform to Blender coordinates:
    # Unity: (X, Y, Z) -> Blender: rot_x @ (X, Y, Z)
    blender_m = rot_x @ inv_m
    
    eb = arm_data.edit_bones.new(name)
    pos = blender_m.to_translation()
    eb.head = pos
    # Tail 10cm along bone forward/up
    eb.tail = pos + blender_m.to_3x3() @ mathutils.Vector((0.0, 0.1, 0.0))
    edit_bones[name] = eb

bpy.ops.object.mode_set(mode='OBJECT')

# Position Arcee_Armature at Arcee reference location (X = 2.5m)
arm_obj.location = (2.5, 0.0, 0.0)
print(f"[✓] Created Arcee_Armature with {len(arm_data.bones)} official bones at X = 2.5m")

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_FILE))
print(f"[✓] Saved updated blend to {BLEND_FILE}")
