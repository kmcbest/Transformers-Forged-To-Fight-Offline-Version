import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import math
from mathutils import Vector, Euler

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
for o in mesh_objs:
    o.modifiers.clear()
    o.parent = None
for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    bpy.data.objects.remove(a, do_unlink=True)

bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]

bpy.ops.transform.rotate(value=math.pi, orient_axis='X')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

all_z = [v.co.z for o in mesh_objs for v in o.data.vertices]
z_min = min(all_z)
scale = 10.85 / (max(all_z) - z_min)

for o in mesh_objs:
    for v in o.data.vertices:
        v.co.z -= z_min
        v.co.x *= scale
        v.co.y *= scale
        v.co.z *= scale
    o.data.update()

bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]
bpy.ops.object.join()
robot = bpy.context.active_object

vg_map = {vg.name: vg.index for vg in robot.vertex_groups}
l_arm_vgs = [vg_map[n] for n in ["Bip_UpperArm_L", "Bip_LowerArm_L", "Bip_Hand_L", "Bn_Sword_L", 
                                 "Bip_Thumb_0_L", "Bip_Thumb_1_L", "Bip_Index_0_L", "Bip_Index_1_L", 
                                 "Bip_Middle_0_L", "Bip_Middle_1_L"] if n in vg_map]

for deg in [35, 38, 42]:
    R_L = Euler((0, math.radians(deg), 0), 'XYZ').to_matrix()
    pivot_L = Vector((2.05, -0.20, 8.69))
    hand_pts = []
    for v in robot.data.vertices:
        if any(g.group == vg_map["Bip_Hand_L"] and g.weight > 0.4 for g in v.groups):
            p = pivot_L + R_L @ (v.co - pivot_L)
            hand_pts.append(p)
    hx = sum(p.x for p in hand_pts) / len(hand_pts)
    hz = sum(p.z for p in hand_pts) / len(hand_pts)
    print(f"Deg={deg}: Hand mean X={hx:.3f}, Z={hz:.3f} (Target Barricade LeftHand: X=2.057, Z=4.597)")
