# -*- coding: utf-8 -*-
import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx") or bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee", "L_Toe", "L_Ankle"])]

print("=== Demolishor Phase1 Left Leg Profile vs Ironhide Bones ===")
# Check at different Z slices
for z_low, z_high, label in [
    (5.0, 6.0, "Thigh Top (Hip)"),
    (4.3, 5.0, "Thigh Mid     "),
    (3.7, 4.3, "Knee Joint    "),
    (2.5, 3.5, "Shin / Calf   "),
    (1.0, 2.0, "Ankle         "),
    (0.0, 1.0, "Foot / Sole   ")
]:
    pts = [v.co for v in mesh.data.vertices if z_low <= v.co.z <= z_high and any(g.group in l_leg_vgs for g in v.groups)]
    if pts:
        cx = sum(p.x for p in pts) / len(pts)
        cy = sum(p.y for p in pts) / len(pts)
        min_x = min(p.x for p in pts)
        max_x = max(p.x for p in pts)
        print(f"  {label} (Z={z_low:.1f}~{z_high:.1f}): Center X={cx:6.2f}, Y={cy:6.2f} | Span X=[{min_x:6.2f}, {max_x:6.2f}]")

print("\n=== Ironhide Leg Bones ===")
for bname in ["LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase"]:
    b = arm.pose.bones.get(bname)
    if b:
        head = arm.matrix_world @ b.head
        tail = arm.matrix_world @ b.tail
        print(f"  {bname:12s}: head=(X={head.x:6.2f}, Y={head.y:6.2f}, Z={head.z:6.2f}) tail=(X={tail.x:6.2f}, Y={tail.y:6.2f}, Z={tail.z:6.2f})")
