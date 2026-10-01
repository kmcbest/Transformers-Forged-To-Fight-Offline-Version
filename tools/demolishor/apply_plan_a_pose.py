# -*- coding: utf-8 -*-
"""
Plan A: Precise Rigid Pose Alignment for Demolishor.
1. Rotates Left & Right Arms inward/downward around shoulder pivots
   to match Ironhide's vertical arm silhouette.
2. Slightly narrows the wide leg stance around hip pivots
   to align feet with Ironhide's footing.
3. Levels the soles to the ground (Z=0).
4. Corrects Ironhide_Ghost_Reference rotation so it stands upright cleanly.
5. Saves to tools/demolishor/demolishor_phase1.blend.
"""
import sys
import bpy
import mathutils
import math
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_PATH = ROOT / "tools" / "demolishor" / "demolishor_phase1.blend"

print("=== Executing Plan A: Rigid Pose Alignment ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
if not mesh:
    print("[!] Demolishor robot mesh not found!")
    sys.exit(1)

# Ensure transforms applied
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.select_all(action='DESELECT')
mesh.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# 1. ARM DOWN ROTATION
# Ironhide arms: LeftArm X=-2.28, Hand X=-2.28.
# Demolishor: Shoulder X=-2.57, Hand X=-4.23 (needs ~22 deg inward rotation around Y)
l_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Arm02", "L_Arm03", "L_Arm04", "L_Elbow", "L_Finger"])]
r_arm_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Arm02", "R_Arm03", "R_Arm04", "R_Elbow", "R_Finger"])]

l_shoulder_pivot = mathutils.Vector((-2.45, -0.35, 7.20))
r_shoulder_pivot = mathutils.Vector((2.45, -0.35, 7.20))

arm_angle = 20.0 # degrees inward
rot_l_arm = mathutils.Matrix.Rotation(math.radians(arm_angle), 4, 'Y')
rot_r_arm = mathutils.Matrix.Rotation(math.radians(-arm_angle), 4, 'Y')

print(f"[*] Rotating arms downward by {arm_angle} degrees...")
for v in mesh.data.vertices:
    # Check if in left arm
    if any(g.group in l_arm_vgs and g.weight > 0.25 for g in v.groups):
        v.co = l_shoulder_pivot + (rot_l_arm @ (v.co - l_shoulder_pivot))
    # Check if in right arm
    elif any(g.group in r_arm_vgs and g.weight > 0.25 for g in v.groups):
        v.co = r_shoulder_pivot + (rot_r_arm @ (v.co - r_shoulder_pivot))

# 2. LEG NARROWING
# Demolishor feet span is 3.02m vs Ironhide 1.54m. Narrow legs by 6.5 degrees.
leg_angle = 6.5
l_hip_pivot = mathutils.Vector((-0.85, -0.1, 4.8))
r_hip_pivot = mathutils.Vector((0.85, -0.1, 4.8))

rot_l_leg = mathutils.Matrix.Rotation(math.radians(-leg_angle), 4, 'Y')
rot_r_leg = mathutils.Matrix.Rotation(math.radians(leg_angle), 4, 'Y')

l_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg", "L_Thigh", "L_Knee"])]
r_leg_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg", "R_Thigh", "R_Knee"])]
l_foot_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg03", "L_Leg04"])]
r_foot_vgs = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg03", "R_Leg04"])]

print(f"[*] Narrowing legs inward by {leg_angle} degrees...")
for v in mesh.data.vertices:
    if any(g.group in l_leg_vgs and g.weight > 0.25 for g in v.groups):
        v.co = l_hip_pivot + (rot_l_leg @ (v.co - l_hip_pivot))
    elif any(g.group in r_leg_vgs and g.weight > 0.25 for g in v.groups):
        v.co = r_hip_pivot + (rot_r_leg @ (v.co - r_hip_pivot))

# Re-level foot soles to ground
min_z = min(v.co.z for v in mesh.data.vertices)
print(f"[*] Re-grounding soles (offset {min_z:.3f}m)...")
for v in mesh.data.vertices:
    v.co.z -= min_z

mesh.data.update()

# 3. FIX IRONHIDE GHOST REFERENCE
ghost = bpy.data.objects.get("Ironhide_Ghost_Reference") or bpy.data.objects.get("ironhide")
if ghost:
    ghost.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.objects.active = ghost
    bpy.ops.object.select_all(action='DESELECT')
    ghost.select_set(True)
    bpy.ops.object.transform_apply(rotation=True)
    print("[✓] Ironhide ghost reference rotation set to 0 (standing upright)")

# 4. MEASURE NEW COORDINATES
hand_l = [v.co for v in mesh.data.vertices if any(g.group in l_arm_vgs and g.weight > 0.4 for g in v.groups)]
hand_r = [v.co for v in mesh.data.vertices if any(g.group in r_arm_vgs and g.weight > 0.4 for g in v.groups)]
foot_l = [v.co for v in mesh.data.vertices if any(g.group in l_foot_vgs and g.weight > 0.4 for g in v.groups)]
foot_r = [v.co for v in mesh.data.vertices if any(g.group in r_foot_vgs and g.weight > 0.4 for g in v.groups)]

print("\n--- Aligned Posture Metrics ---")
if hand_l and hand_r:
    print(f"  Left Arm X span : [{min(p.x for p in hand_l):.2f}, {max(p.x for p in hand_l):.2f}] (Target: ~ -2.3)")
    print(f"  Right Arm X span: [{min(p.x for p in hand_r):.2f}, {max(p.x for p in hand_r):.2f}] (Target: ~ +2.3)")
if foot_l and foot_r:
    print(f"  Left Foot X span : [{min(p.x for p in foot_l):.2f}, {max(p.x for p in foot_l):.2f}] (Target: ~ -0.8)")
    print(f"  Right Foot X span: [{min(p.x for p in foot_r):.2f}, {max(p.x for p in foot_r):.2f}] (Target: ~ +0.8)")

# Save scene
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_PATH))
print(f"\n[✓] Successfully saved aligned scene to: {BLEND_PATH}")
