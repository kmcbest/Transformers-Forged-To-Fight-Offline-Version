import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import math
from mathutils import Vector, Euler

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"
BARR_OBJ = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\00_donor_reference\cha_barricade_cin_dotm_00_robot.obj"

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Barricade OBJ
bpy.ops.import_scene.obj(filepath=BARR_OBJ)
barr = bpy.context.selected_objects[0]
barr.name = "Barricade_Reference"

# Convert Barricade OBJ from Unity coords (X, Y_up, Z_fwd) to Blender coords (Left=+X, Fwd=-Y, Up=+Z)
# Unity: -X=Right, +X=Left, +Y=Up, +Z=Fwd
# In Barricade OBJ: X is Unity X, Y is Unity Y, Z is Unity Z
for v in barr.data.vertices:
    ux, uy, uz = v.co.x, v.co.y, v.co.z
    v.co.x = -ux  # Left is +X
    v.co.y = -uz  # Forward is -Y
    v.co.z = uy   # Up is +Z
barr.data.update()

# Shift Barricade to +X = +4.5m
barr.location = Vector((4.5, 0, 0))

# 2. Import raw Sideswipe FBX
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)
arm = bpy.data.objects.get("Armature")
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o != barr]

# Clear parent and armatures
for o in mesh_objs:
    o.modifiers.clear()
    o.parent = None
if arm:
    bpy.data.objects.remove(arm, do_unlink=True)

print("Sideswipe raw mesh objects count:", len(mesh_objs))

# Let's test the current rotation in build_aligned_sideswipe_robot.py:
# bpy.ops.transform.rotate(value=math.pi, orient_axis='X')
# Let's inspect where chest headlights and back wings are!
bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]

# What was line 190 in build_aligned_sideswipe_robot.py?
bpy.ops.transform.rotate(value=math.pi, orient_axis='X')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Scale height to 10.85
all_z = [v.co.z for o in mesh_objs for v in o.data.vertices]
z_min, z_max = min(all_z), max(all_z)
scale_factor = 10.85 / (z_max - z_min)
for o in mesh_objs:
    for v in o.data.vertices:
        v.co.z -= z_min
        v.co.x *= scale_factor
        v.co.y *= scale_factor
        v.co.z *= scale_factor
    o.data.update()

# Shift to -X = -4.5m
for o in mesh_objs:
    o.location.x -= 4.5

# Check Mesh 20 (chest headlights) pos
m20 = bpy.data.objects.get("20")
if m20:
    pts = [m20.matrix_world @ v.co for v in m20.data.vertices]
    print(f"Mesh 20 pos in Blender space: ({sum(p.x for p in pts)/len(pts):.3f}, {sum(p.y for p in pts)/len(pts):.3f}, {sum(p.z for p in pts)/len(pts):.3f})")

# Check back door/wings (44.001 Bn_DoorR_2 or similar)
m_door = bpy.data.objects.get("44.001")
if m_door:
    pts = [m_door.matrix_world @ v.co for v in m_door.data.vertices]
    print(f"Back Door/Wing pos in Blender space: ({sum(p.x for p in pts)/len(pts):.3f}, {sum(p.y for p in pts)/len(pts):.3f}, {sum(p.z for p in pts)/len(pts):.3f})")

# Check Barricade chest pos:
barr_chest = [v.co for v in barr.data.vertices if 7.5 < v.co.z < 9.0]
print(f"Barricade chest Y in Blender space: [{min(v.y for v in barr_chest):.3f}, {max(v.y for v in barr_chest):.3f}] (mean={sum(v.y for v in barr_chest)/len(barr_chest):.3f})")
