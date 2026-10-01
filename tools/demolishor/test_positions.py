# -*- coding: utf-8 -*-
import bpy
import mathutils

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")
mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx") or bpy.data.objects.get("cha_demolishor_gs_01")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

print("\n=== Ironhide Hand & Finger Bones ===")
fingers = [b for b in arm.pose.bones if any(k in b.name.lower() for k in ["hand", "finger", "thumb", "index", "middle", "ring", "pinky"])]
for b in fingers:
    head = arm.matrix_world @ b.head
    tail = arm.matrix_world @ b.tail
    print(f"  {b.name:22s}: head=(X={head.x:6.2f}, Y={head.y:6.2f}, Z={head.z:6.2f}) tail=(X={tail.x:6.2f}, Y={tail.y:6.2f}, Z={tail.z:6.2f})")

l_f_heads = [arm.matrix_world @ b.head for b in fingers if b.name.startswith("Left")]
r_f_heads = [arm.matrix_world @ b.head for b in fingers if b.name.startswith("Right")]
if l_f_heads:
    cl = sum(l_f_heads, mathutils.Vector()) / len(l_f_heads)
    min_x = min(p.x for p in l_f_heads)
    max_x = max(p.x for p in l_f_heads)
    print(f"\nIronhide Left Finger Cluster: center X={cl.x:.2f}, span X=[{min_x:.2f}, {max_x:.2f}], Z={cl.z:.2f}")
if r_f_heads:
    cr = sum(r_f_heads, mathutils.Vector()) / len(r_f_heads)
    min_x = min(p.x for p in r_f_heads)
    max_x = max(p.x for p in r_f_heads)
    print(f"Ironhide Right Finger Cluster: center X={cr.x:.2f}, span X=[{min_x:.2f}, {max_x:.2f}], Z={cr.z:.2f}")
