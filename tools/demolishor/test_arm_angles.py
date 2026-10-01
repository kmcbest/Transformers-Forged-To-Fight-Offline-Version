# -*- coding: utf-8 -*-
import bpy
import mathutils
import math

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx") or bpy.data.objects.get("cha_demolishor_gs_01")
l_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Arm02", "L_Arm03", "L_Arm04", "L_Elbow", "L_Finger"])]

l_shoulder_pivot = mathutils.Vector((-2.50, -0.35, 7.15))

# Test angles: 15, 18, 20, 22, 24
for angle in [15.0, 18.0, 20.0, 22.0, 24.0]:
    rot = mathutils.Matrix.Rotation(math.radians(-angle), 4, 'Y')
    hand_pts = []
    for v in mesh.data.vertices:
        if v.co.z <= 7.80 and any(g.group in l_arm_vgs and g.weight > 0.4 for g in v.groups):
            new_co = l_shoulder_pivot + (rot @ (v.co - l_shoulder_pivot))
            if new_co.z < 5.5:
                hand_pts.append(new_co)
    if hand_pts:
        ch = sum(hand_pts, mathutils.Vector()) / len(hand_pts)
        min_x = min(p.x for p in hand_pts)
        max_x = max(p.x for p in hand_pts)
        min_z = min(p.z for p in hand_pts)
        max_z = max(p.z for p in hand_pts)
        print(f"Angle {angle:4.1f}° -> Hand Center: X={ch.x:6.2f}, Z={ch.z:6.2f} | Span X=[{min_x:6.2f}, {max_x:6.2f}] Span Z=[{min_z:6.2f}, {max_z:6.2f}]")
