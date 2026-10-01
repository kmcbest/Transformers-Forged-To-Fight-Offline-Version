# -*- coding: utf-8 -*-
import bpy
import mathutils

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx") or bpy.data.objects.get("cha_demolishor_gs_01")
print(f"Mesh found: {mesh.name}")

vg_names = {vg.index: vg.name for vg in mesh.vertex_groups}

l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee", "L_Toe", "L_Ankle"])]
r_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee", "R_Toe", "R_Ankle"])]
l_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Arm02", "L_Arm03", "L_Arm04", "L_Elbow", "L_Finger"])]
r_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Arm02", "R_Arm03", "R_Arm04", "R_Elbow", "R_Finger"])]

# Knee verts (Z ~ 3.5 - 4.5)
l_knees = [v.co for v in mesh.data.vertices if 3.5 <= v.co.z <= 4.5 and any(g.group in l_leg_vgs for g in v.groups)]
r_knees = [v.co for v in mesh.data.vertices if 3.5 <= v.co.z <= 4.5 and any(g.group in r_leg_vgs for g in v.groups)]

if l_knees:
    ck_l = sum(l_knees, mathutils.Vector()) / len(l_knees)
    min_x_l = min(v.x for v in l_knees)
    max_x_l = max(v.x for v in l_knees)
    print(f"Phase1 Left Knee: center X={ck_l.x:.2f}, span X=[{min_x_l:.2f}, {max_x_l:.2f}], Z={ck_l.z:.2f}")

if r_knees:
    ck_r = sum(r_knees, mathutils.Vector()) / len(r_knees)
    min_x_r = min(v.x for v in r_knees)
    max_x_r = max(v.x for v in r_knees)
    print(f"Phase1 Right Knee: center X={ck_r.x:.2f}, span X=[{min_x_r:.2f}, {max_x_r:.2f}], Z={ck_r.z:.2f}")

# Hand verts (Z < 5.4)
l_hands = [v.co for v in mesh.data.vertices if v.co.z < 5.4 and any(g.group in l_arm_vgs for g in v.groups)]
r_hands = [v.co for v in mesh.data.vertices if v.co.z < 5.4 and any(g.group in r_arm_vgs for g in v.groups)]
if l_hands:
    ch_l = sum(l_hands, mathutils.Vector()) / len(l_hands)
    min_x = min(v.x for v in l_hands)
    max_x = max(v.x for v in l_hands)
    print(f"Phase1 Left Hand: center X={ch_l.x:.2f}, span X=[{min_x:.2f}, {max_x:.2f}], Z={ch_l.z:.2f}")
if r_hands:
    ch_r = sum(r_hands, mathutils.Vector()) / len(r_hands)
    min_x = min(v.x for v in r_hands)
    max_x = max(v.x for v in r_hands)
    print(f"Phase1 Right Hand: center X={ch_r.x:.2f}, span X=[{min_x:.2f}, {max_x:.2f}], Z={ch_r.z:.2f}")
