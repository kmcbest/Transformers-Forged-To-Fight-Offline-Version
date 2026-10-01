# -*- coding: utf-8 -*-
import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx") or bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee", "L_Toe", "L_Ankle"])]
r_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee", "R_Toe", "R_Ankle"])]

leg_shift = 0.38 # meters

l_foot_pts = [mathutils.Vector((v.co.x + leg_shift, v.co.y, v.co.z)) for v in mesh.data.vertices if v.co.z < 1.5 and any(g.group in l_leg_vgs and g.weight > 0.3 for g in v.groups)]
r_foot_pts = [mathutils.Vector((v.co.x - leg_shift, v.co.y, v.co.z)) for v in mesh.data.vertices if v.co.z < 1.5 and any(g.group in r_leg_vgs and g.weight > 0.3 for g in v.groups)]

if l_foot_pts:
    cf = sum(l_foot_pts, mathutils.Vector()) / len(l_foot_pts)
    min_x = min(p.x for p in l_foot_pts)
    max_x = max(p.x for p in l_foot_pts)
    print(f"Shifted Left Foot Center: X={cf.x:.2f}, Span X=[{min_x:.2f}, {max_x:.2f}] | Target Ironhide Foot Bone: X=-0.77")

if r_foot_pts:
    cf = sum(r_foot_pts, mathutils.Vector()) / len(r_foot_pts)
    min_x = min(p.x for p in r_foot_pts)
    max_x = max(p.x for p in r_foot_pts)
    print(f"Shifted Right Foot Center: X={cf.x:.2f}, Span X=[{min_x:.2f}, {max_x:.2f}] | Target Ironhide Foot Bone: X=0.77")
