import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import math
from pathlib import Path
import bpy
from mathutils import Euler, Matrix, Quaternion, Vector

ROOT = Path("e:/Agent/TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"
OUT_IMG = ROOT / "renders/swoop/debug_blender_fists2.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")
sym = bpy.data.objects.get("Symbol_AB")

arm.animation_data_clear()
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')
bpy.ops.pose.select_all(action='SELECT')
bpy.ops.pose.transforms_clear()

# First test native attack01 ONLY on R finger bones vs custom world-axis curl!
# Let's see how Right Finger1/2 bones orient in Bip001 armature local space!
# Wait: look at mesh_local = armature-to-mesh transform!
mat_arm_to_mesh = mesh.matrix_world.inverted() @ arm.matrix_world

def curl_bone_in_mesh_axis(bname, mesh_axis, angle_deg):
    """Apply a rotation of `angle_deg` around `mesh_axis` (in mesh space) to pose bone `bname`."""
    pb = arm.pose.bones.get(bname)
    if not pb: return
    # bone rest rotation in mesh space = (mat_arm_to_mesh.to_3x3() @ pb.bone.matrix_local.to_3x3())
    # Wait: pose bone matrix_basis rotates around bone's LOCAL axes!
    # To convert mesh_axis -> bone local axis:
    bone_in_mesh = (mat_arm_to_mesh.to_3x3() @ pb.bone.matrix_local.to_3x3()).normalized()
    local_axis = (bone_in_mesh.inverted() @ mesh_axis).normalized()
    pb.rotation_mode = 'QUATERNION'
    pb.rotation_quaternion = Quaternion(local_axis, math.radians(angle_deg))

# Print Right vs Left Finger axis directions in mesh space first
for bn in ["Bone_L_Finger0", "Bone_L_Finger1", "Bone_L_Finger2", "Bone_R_Finger0", "Bone_R_Finger1", "Bone_R_Finger2"]:
    b = arm.data.bones[bn]
    bm = (mat_arm_to_mesh.to_3x3() @ b.matrix_local.to_3x3()).normalized()
    print(f"{bn:15s} in mesh space: X={tuple(round(x,2) for x in bm.col[0])}, Y={tuple(round(x,2) for x in bm.col[1])}, Z={tuple(round(x,2) for x in bm.col[2])}")

# Wait: Left hand palm faces INWARD (-X in mesh space! Left hand is at +X=+0.54, palm points toward body -X).
# Check: Left fingers hang down (-Z). Curling inward from -Z toward -X (palm center):
# (-Z) cross (-X) = +Y? Wait: (0,0,-1) x (-1,0,0) = (0, 1, 0)!
# Wait: Earlier Bone_L_Finger1 local Z was ~ (0, -1, 0) in arm, let's check mesh space!
# Regardless, using mesh_axis:
# Left hand (+X=+0.54): curling fingertips from -Z -> -X rotates around mesh +Y (+1) by +angle (or -angle? Let's verify right-hand rule: thumb along +Y -> fingers curl from +Z to +X, or from -Z to -X!! YES! Cross(+Y, -Z) = -X!)
# Right hand (-X=-0.54): curling fingertips from -Z -> +X (inward toward body!) -> Cross(-Y, -Z) = +X! So mesh -Y!

# Curl Left fingers around mesh +Y:
for bname, deg in [
    ("Bone_L_Finger1", 65), ("Bone_L_Finger11", 75), ("Bone_L_Finger12", 65),
    ("Bone_L_Finger2", 65), ("Bone_L_Finger21", 80), ("Bone_L_Finger22", 75),
]:
    curl_bone_in_mesh_axis(bname, Vector((0, 1, 0)), deg)

# Curl Left thumb: tuck slightly forward/inward/down across curled index
curl_bone_in_mesh_axis("Bone_L_Finger0", Vector((-0.3, 0.2, 1.0)).normalized(), 28)
curl_bone_in_mesh_axis("Bone_L_Finger01", Vector((0, 1, 0.5)).normalized(), 35)
curl_bone_in_mesh_axis("Bone_L_Finger02", Vector((0, 1, 0.5)).normalized(), 45)

# Curl Right fingers around mesh -Y (completely symmetrical!):
for bname, deg in [
    ("Bone_R_Finger1", 65), ("Bone_R_Finger11", 75), ("Bone_R_Finger12", 65),
    ("Bone_R_Finger2", 65), ("Bone_R_Finger21", 80), ("Bone_R_Finger22", 75),
]:
    curl_bone_in_mesh_axis(bname, Vector((0, -1, 0)), deg)

# Curl Right thumb symmetrically across Right index
curl_bone_in_mesh_axis("Bone_R_Finger0", Vector((-0.3, -0.2, -1.0)).normalized(), 28)
curl_bone_in_mesh_axis("Bone_R_Finger01", Vector((0, -1, -0.5)).normalized(), 35)
curl_bone_in_mesh_axis("Bone_R_Finger02", Vector((0, -1, -0.5)).normalized(), 45)

# Also slide Bone_L_Hand & Bone_R_Hand slightly downward (-0.055 mesh Z) so clenched fists emerge cleanly out of cuffs!
for hname in ["Bone_L_Hand", "Bone_R_Hand"]:
    pb = arm.pose.bones[hname]
    bone_in_mesh = (mat_arm_to_mesh.to_3x3() @ pb.bone.matrix_local.to_3x3()).normalized()
    local_down = (bone_in_mesh.inverted() @ Vector((0, 0, -0.055)))
    pb.location = local_down

bpy.ops.object.mode_set(mode='OBJECT')

deps = bpy.context.evaluated_depsgraph_get()
ev_obj = mesh.evaluated_get(deps)
ev_mesh = bpy.data.meshes.new_from_object(ev_obj)

baked_obj = bpy.data.objects.new("BakedPreview", ev_mesh)
bpy.context.scene.collection.objects.link(baked_obj)
baked_obj.matrix_world = Matrix.Identity(4)
mesh.hide_render = True
if sym:
    sym.hide_render = True

cam_d = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = Vector((0.35, -1.65, -0.25))
direction = Vector((0.0, 0.0, -0.28)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()

ld = bpy.data.lights.new("Sun", 'SUN')
l = bpy.data.objects.new("Sun", ld)
bpy.context.scene.collection.objects.link(l)
l.rotation_euler = Euler((math.radians(55), 0, math.radians(-25)), 'XYZ')
ld.energy = 3.5

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720
bpy.context.scene.render.filepath = str(OUT_IMG)
bpy.ops.render.render(write_still=True)
print(f"Saved preview2 to {OUT_IMG}")
