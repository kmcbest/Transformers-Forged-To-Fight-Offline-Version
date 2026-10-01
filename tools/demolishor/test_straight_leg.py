# -*- coding: utf-8 -*-
import bpy
import mathutils
import math

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx") or bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee", "L_Toe", "L_Ankle"])]
r_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee", "R_Toe", "R_Ankle"])]

# Step 1: Shift whole leg so Knee is at X = +/- 0.77
# Raw knee center is -1.15. Target is -0.77. Shift = +0.38
shift_x = 0.38
for v in mesh.data.vertices:
    if v.co.z <= 5.0:
        if any(g.group in l_leg_vgs and g.weight > 0.25 for g in v.groups):
            v.co.x += shift_x
        elif any(g.group in r_leg_vgs and g.weight > 0.25 for g in v.groups):
            v.co.x -= shift_x

# Step 2: Rotate lower leg (Z <= 3.3) inward around knee pivot (-0.77, 0, 3.3)
# To straighten the calf from X = -1.58 to X = -0.77
pivot_l = mathutils.Vector((-0.77, 0.0, 3.30))
pivot_r = mathutils.Vector(( 0.77, 0.0, 3.30))
rot_angle = 15.0 # degrees

rot_l = mathutils.Matrix.Rotation(math.radians(-rot_angle), 4, 'Y')
rot_r = mathutils.Matrix.Rotation(math.radians( rot_angle), 4, 'Y')

for v in mesh.data.vertices:
    if v.co.z <= 3.30:
        if any(g.group in l_leg_vgs and g.weight > 0.25 for g in v.groups):
            v.co = pivot_l + (rot_l @ (v.co - pivot_l))
        elif any(g.group in r_leg_vgs and g.weight > 0.25 for g in v.groups):
            v.co = pivot_r + (rot_r @ (v.co - pivot_r))

# Re-ground soles to Z = 0
min_z = min(v.co.z for v in mesh.data.vertices)
for v in mesh.data.vertices:
    v.co.z -= min_z
mesh.data.update()

# Profile new leg
print("\n=== Straight Leg Alignment Profile ===")
for z_low, z_high, label in [
    (4.5, 5.5, "Thigh Top  "),
    (3.5, 4.3, "Knee Joint "),
    (2.0, 3.0, "Shin / Calf"),
    (0.0, 1.0, "Foot / Sole")
]:
    pts = [v.co for v in mesh.data.vertices if z_low <= v.co.z <= z_high and any(g.group in l_leg_vgs for g in v.groups)]
    if pts:
        cx = sum(p.x for p in pts) / len(pts)
        min_x = min(p.x for p in pts)
        max_x = max(p.x for p in pts)
        print(f"  {label}: Center X={cx:6.2f} | Span X=[{min_x:6.2f}, {max_x:6.2f}] | Target Bone X=-0.77")
