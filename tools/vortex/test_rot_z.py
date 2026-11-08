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

for ang in [90.0, -90.0]:
    arm.rotation_euler = (0, 0, math.radians(ang))
    bpy.context.view_layer.update()
    
    pelvis = arm.matrix_world @ arm.data.bones["bip_pelvis"].head_local
    head = arm.matrix_world @ arm.data.bones["bip_head"].head_local
    hand_l = arm.matrix_world @ arm.data.bones["bip_hand_L"].head_local
    hand_r = arm.matrix_world @ arm.data.bones["bip_hand_R"].head_local
    
    print(f"\n--- With Rot Z = {ang}° ---")
    print(f"  Hand_L (should have X < 0): X={hand_l.x:.3f}, Y={hand_l.y:.3f}, Z={hand_l.z:.3f}")
    print(f"  Hand_R (should have X > 0): X={hand_r.x:.3f}, Y={hand_r.y:.3f}, Z={hand_r.z:.3f}")
