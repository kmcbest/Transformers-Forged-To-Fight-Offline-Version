import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector, Matrix

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
BLASTOFF_MESH_NAMES = [
    "RB_Blastoff_CHARSKEL_Head.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoR.001.dmx",
    "RB_BlastoffWing_STAT.001.dmx",
    "RB_BlastoffWing_STAT.dmx",
]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

arm = bpy.data.objects.get("Blast-off_ARM")
robot_objs = [bpy.data.objects[n] for n in BLASTOFF_MESH_NAMES if n in bpy.data.objects]

# Check raw positions
print(f"Raw arm loc: {arm.location}")
for o in robot_objs:
    print(f"Raw obj {o.name} loc: {o.location}")

# If we shift all objects by (0, 10.0118, 0) to center them at (0, 0, 0):
RAW_OFFSET_Y = 10.0118

arm.location.y += RAW_OFFSET_Y
for o in robot_objs:
    o.location.y += RAW_OFFSET_Y

bpy.context.view_layer.update()
print(f"After shift, arm loc: {arm.location}")

# Now rotate R_z(-90)
R_z90 = Matrix.Rotation(math.radians(-90), 4, 'Z')
arm.matrix_world = R_z90 @ arm.matrix_world
for o in robot_objs:
    o.matrix_world = R_z90 @ o.matrix_world

bpy.context.view_layer.update()

# Now check bounding box of robot_objs
all_xs, all_ys, all_zs = [], [], []
for o in robot_objs:
    for v in o.data.vertices:
        wco = o.matrix_world @ v.co
        all_xs.append(wco.x)
        all_ys.append(wco.y)
        all_zs.append(wco.z)

print(f"\nAfter Centering + R_z(-90):")
print(f"X (Left/Right): [{min(all_xs):.3f}, {max(all_xs):.3f}] (center={0.5*(min(all_xs)+max(all_xs)):.3f})")
print(f"Y (Fwd/Back):   [{min(all_ys):.3f}, {max(all_ys):.3f}] (center={0.5*(min(all_ys)+max(all_ys)):.3f})")
print(f"Z (Height):     [{min(all_zs):.3f}, {max(all_zs):.3f}]")

# Check Left hand vs Right hand bone in Blast-off_ARM:
test_lh = arm.matrix_world @ arm.data.bones["bip_hand_L"].head_local
test_rh = arm.matrix_world @ arm.data.bones["bip_hand_R"].head_local
print(f"\nArmature Left Hand head:  {test_lh}")
print(f"Armature Right Hand head: {test_rh}")
print(f"Left Hand X: {test_lh.x:.3f} (+X expected, > 0: {test_lh.x > 0})")
print(f"Right Hand X: {test_rh.x:.3f} (-X expected, < 0: {test_rh.x < 0})")
