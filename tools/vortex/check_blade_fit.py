import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
import mathutils

bpy.ops.wm.open_mainfile(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\vortex\vortex_master.blend")
arm = bpy.data.objects["Vortex_ARM"]
blade_l = bpy.data.objects["WEP_IonBlade_SKEL.mo_L.dmx"]

scale_factor = 2.05
arm.scale = (scale_factor, scale_factor, scale_factor)
arm.rotation_euler = (0, 0, math.radians(90.0))
bpy.context.view_layer.update()

w_wrist = arm.matrix_world @ arm.data.bones["bip_hand_L"].head_local
w_elbow = arm.matrix_world @ arm.data.bones["bip_lowerArm_L"].head_local

b_verts = [arm.matrix_world @ v.co for v in blade_l.data.vertices]
min_bx = min(v.x for v in b_verts)
max_bx = max(v.x for v in b_verts)
min_by = min(v.y for v in b_verts)
max_by = max(v.y for v in b_verts)
min_bz = min(v.z for v in b_verts)
max_bz = max(v.z for v in b_verts)

print(f"Left Hand (wrist): ({w_wrist.x:.3f}, {w_wrist.y:.3f}, {w_wrist.z:.3f})")
print(f"Left Elbow:        ({w_elbow.x:.3f}, {w_elbow.y:.3f}, {w_elbow.z:.3f})")
print(f"Blade_L bounds: X=[{min_bx:.3f}, {max_bx:.3f}], Y=[{min_by:.3f}, {max_by:.3f}], Z=[{min_bz:.3f}, {max_bz:.3f}]")
