import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import math
from mathutils import Vector

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

# Remove old armature
for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    bpy.data.objects.remove(a, do_unlink=True)

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objs:
    o.modifiers.clear()
    o.select_set(True)

bpy.context.view_layer.objects.active = mesh_objs[0]

# Rotate 180 around X instead of Y!
bpy.ops.transform.rotate(value=math.pi, orient_axis='X')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Find bounds
min_co = Vector((float('inf'), float('inf'), float('inf')))
max_co = Vector((float('-inf'), float('-inf'), float('-inf')))

for obj in mesh_objs:
    for corner in obj.bound_box:
        world_co = obj.matrix_world @ Vector(corner)
        for i in range(3):
            min_co[i] = min(min_co[i], world_co[i])
            max_co[i] = max(max_co[i], world_co[i])

print(f"Bounds after R_x(180):")
print(f"  X: [{min_co.x:.4f}, {max_co.x:.4f}]")
print(f"  Y: [{min_co.y:.4f}, {max_co.y:.4f}]")
print(f"  Z: [{min_co.z:.4f}, {max_co.z:.4f}]")

# Check which side is Left Arm / Right Arm
for obj in mesh_objs:
    vg_map = {vg.name: vg.index for vg in obj.vertex_groups}
    for bname in ["Bip_UpperArm_L", "Bip_UpperArm_R", "Bip_Hand_L", "Bip_Hand_R", "Bn_Wheel_L", "Bn_Wheel_R"]:
        if bname in vg_map:
            idx = vg_map[bname]
            pts = [(obj.matrix_world @ v.co) for v in obj.data.vertices if any(g.group == idx for g in v.groups)]
            if pts:
                xs = [p.x for p in pts]
                ys = [p.y for p in pts]
                zs = [p.z for p in pts]
                print(f"  {bname:15s}: mean=({sum(xs)/len(xs):.4f}, {sum(ys)/len(ys):.4f}, {sum(zs)/len(zs):.4f})")
