# -*- coding: utf-8 -*-
"""
Plan A Rigorous Pose Alignment:
- Rotates Left Arm inward around Left Shoulder by -22 deg (around Y)
- Rotates Right Arm inward around Right Shoulder by +22 deg (around Y)
- Rotates Left Leg inward around Left Hip by +6.5 deg (around Y)
- Rotates Right Leg inward around Right Hip by -6.5 deg (around Y)
- Removes stray vehicle objects and unused armatures
- Fixes Ironhide ghost reference to stand upright (Rotation X = 0)
- Re-grounds boots to Z = 0
"""
import sys
import bpy
import mathutils
import math
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_PATH = ROOT / "tools" / "demolishor" / "demolishor_phase1.blend"

print("=== Executing Plan A Rigorous Pose Alignment ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

# 1. Clean unused vehicle and extra objects
to_remove = ["Demolishor_ARM", "Demolishor_VH_ARM", "VH_Demolishor_SKEL.mo.dmx", "CP_DemolishorArm_SKEL.mo.dmx"]
for name in to_remove:
    obj = bpy.data.objects.get(name)
    if obj:
        bpy.data.objects.remove(obj, do_unlink=True)
print(f"[✓] Removed unused vehicle and accessory objects")

# 2. Fix Ironhide Ghost Reference rotation
ghost = bpy.data.objects.get("Ironhide_Ghost_Reference") or bpy.data.objects.get("ironhide")
if ghost:
    ghost.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.objects.active = ghost
    bpy.ops.object.select_all(action='DESELECT')
    ghost.select_set(True)
    bpy.ops.object.transform_apply(rotation=True)
    print("[✓] Ironhide ghost reference rotation fixed to 0 (stands upright)")

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
if not mesh:
    print("[!] Demolishor robot mesh not found!")
    sys.exit(1)

# Ensure transforms applied
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 3. ARM ROTATION
# Target Ironhide arm line: X = +/- 2.28
# Demolishor shoulder pivot: X = +/- 2.50, Y = -0.35, Z = 7.15
l_shoulder_pivot = mathutils.Vector((-2.50, -0.35, 7.15))
r_shoulder_pivot = mathutils.Vector(( 2.50, -0.35, 7.15))

arm_angle = 22.0 # degrees

# In Blender Y-axis rotation (Y points forward):
# For Left Arm (X < 0): rotating by -arm_angle brings the hand from X=-4.2 towards X=-2.5
rot_l_arm = mathutils.Matrix.Rotation(math.radians(-arm_angle), 4, 'Y')
rot_r_arm = mathutils.Matrix.Rotation(math.radians( arm_angle), 4, 'Y')

l_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Arm02", "L_Arm03", "L_Arm04", "L_Elbow", "L_Finger"])]
r_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Arm02", "R_Arm03", "R_Arm04", "R_Elbow", "R_Finger"])]

# Don't rotate upper shoulder exhaust stacks/collar (only points below Z=7.8)
for v in mesh.data.vertices:
    if v.co.z <= 7.80:
        if any(g.group in l_arm_vgs and g.weight > 0.25 for g in v.groups):
            v.co = l_shoulder_pivot + (rot_l_arm @ (v.co - l_shoulder_pivot))
        elif any(g.group in r_arm_vgs and g.weight > 0.25 for g in v.groups):
            v.co = r_shoulder_pivot + (rot_r_arm @ (v.co - r_shoulder_pivot))

print(f"[✓] Arms rotated downward/inward by {arm_angle} degrees")

# 4. LEG NARROWING
# Narrow feet from 3.0m span towards Ironhide's 1.54m span
leg_angle = 6.0
l_hip_pivot = mathutils.Vector((-0.85, -0.1, 4.8))
r_hip_pivot = mathutils.Vector(( 0.85, -0.1, 4.8))

# For Left Leg (X < 0): rotating by +leg_angle brings leg towards center
rot_l_leg = mathutils.Matrix.Rotation(math.radians( leg_angle), 4, 'Y')
rot_r_leg = mathutils.Matrix.Rotation(math.radians(-leg_angle), 4, 'Y')

l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee"])]
r_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee"])]

for v in mesh.data.vertices:
    if any(g.group in l_leg_vgs and g.weight > 0.25 for g in v.groups):
        v.co = l_hip_pivot + (rot_l_leg @ (v.co - l_hip_pivot))
    elif any(g.group in r_leg_vgs and g.weight > 0.25 for g in v.groups):
        v.co = r_hip_pivot + (rot_r_leg @ (v.co - r_hip_pivot))

print(f"[✓] Legs narrowed inward by {leg_angle} degrees")

# 5. RE-GROUND SOLES TO Z = 0
min_z = min(v.co.z for v in mesh.data.vertices)
for v in mesh.data.vertices:
    v.co.z -= min_z
mesh.data.update()
print(f"[✓] Soles re-grounded to Z = 0.00 (offset: {min_z:.3f}m)")

# 6. MEASURE RESULTS
hand_l_pts = [v.co for v in mesh.data.vertices if any(g.group in l_arm_vgs and g.weight > 0.4 for g in v.groups)]
hand_r_pts = [v.co for v in mesh.data.vertices if any(g.group in r_arm_vgs and g.weight > 0.4 for g in v.groups)]
foot_l_pts = [v.co for v in mesh.data.vertices if v.co.z < 1.5 and any(g.group in l_leg_vgs and g.weight > 0.4 for g in v.groups)]
foot_r_pts = [v.co for v in mesh.data.vertices if v.co.z < 1.5 and any(g.group in r_leg_vgs and g.weight > 0.4 for g in v.groups)]

print("\n--- Final Aligned Metrics vs Ironhide ---")
if hand_l_pts:
    c_l = sum(hand_l_pts, mathutils.Vector()) / len(hand_l_pts)
    print(f"  Left Arm Center : X={c_l.x:.2f}, Z={c_l.z:.2f} (Ironhide Arm: X=-2.28, Z=6.0~7.0)")
if hand_r_pts:
    c_r = sum(hand_r_pts, mathutils.Vector()) / len(hand_r_pts)
    print(f"  Right Arm Center: X={c_r.x:.2f}, Z={c_r.z:.2f} (Ironhide Arm: X=+2.28, Z=6.0~7.0)")
if foot_l_pts and foot_r_pts:
    c_fl = sum(foot_l_pts, mathutils.Vector()) / len(foot_l_pts)
    c_fr = sum(foot_r_pts, mathutils.Vector()) / len(foot_r_pts)
    print(f"  Left Foot Center : X={c_fl.x:.2f} (Ironhide Foot: X=-0.77)")
    print(f"  Right Foot Center: X={c_fr.x:.2f} (Ironhide Foot: X=+0.77)")

bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
print(f"\n[✓] Successfully updated: {BLEND_PATH}")
