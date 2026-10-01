import bpy

bpy.ops.wm.open_mainfile(filepath="tools/demolishor/demolishor_phase1.blend")

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
arm = bpy.data.objects.get("Ironhide_Reference_Armature")

# Check Demolishor original toes / feet:
toes_vg = [vg.index for vg in mesh.vertex_groups if "toe" in vg.name.lower()]
toes_pts = [v.co for v in mesh.data.vertices if any(g.group in toes_vg for g in v.groups)]
if toes_pts:
    min_y = min(p.y for p in toes_pts)
    max_y = max(p.y for p in toes_pts)
    avg_y = sum(p.y for p in toes_pts) / len(toes_pts)
    print(f"Demolishor Toes Y: [{min_y:.2f}, {max_y:.2f}], avg: {avg_y:.2f}")

# Check Demolishor heels:
ankle_vg = [vg.index for vg in mesh.vertex_groups if "ankle" in vg.name.lower()]
ankle_pts = [v.co for v in mesh.data.vertices if any(g.group in ankle_vg for g in v.groups)]
if ankle_pts:
    avg_y_ankle = sum(p.y for p in ankle_pts) / len(ankle_pts)
    print(f"Demolishor Ankle Y avg: {avg_y_ankle:.2f}")

# Check Ironhide Toes vs Ankle:
ih_toe = arm.data.bones.get("RightToeBase")
ih_ankle = arm.data.bones.get("RightFoot")
print(f"Ironhide Foot (Ankle) Y: {ih_ankle.head_local.y:.2f}")
print(f"Ironhide ToeBase (Front of foot) Y: {ih_toe.head_local.y:.2f}")
