import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import math
from mathutils import Vector, Matrix, Euler

ROBOT_FBX = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"
TEX_DIR = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=ROBOT_FBX)

arm = bpy.data.objects.get("Armature")
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']

# Clear modifiers and parent
for o in mesh_objs:
    o.modifiers.clear()
    o.parent = None

if arm:
    bpy.data.objects.remove(arm, do_unlink=True)

# Select all meshes and apply R_x(180)
bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]

bpy.ops.transform.rotate(value=math.pi, orient_axis='X')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Ground at Z=0 and scale to 10.85m
all_z = []
for o in mesh_objs:
    for v in o.data.vertices:
        all_z.append(v.co.z)

z_min = min(all_z)
z_max = max(all_z)
scale = 10.85 / (z_max - z_min)

for o in mesh_objs:
    for v in o.data.vertices:
        v.co.z -= z_min
        v.co.x *= scale
        v.co.y *= scale
        v.co.z *= scale
    o.data.update()

# Join all meshes into a single robot mesh
bpy.ops.object.select_all(action='DESELECT')
for o in mesh_objs:
    o.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]
bpy.ops.object.join()
robot = bpy.context.active_object
robot.name = "cha_sideswipe_main"

# Rotate left and right arm vertices down around shoulder joints
# Left shoulder pivot: X ~ 2.05, Y ~ -0.2, Z ~ 8.69
# Right shoulder pivot: X ~ -2.05, Y ~ -0.2, Z ~ 8.69
vg_map = {vg.name: vg.index for vg in robot.vertex_groups}

# Identify arm vertices
l_arm_vgs = [vg_map[n] for n in ["Bip_UpperArm_L", "Bip_LowerArm_L", "Bip_Hand_L", "Bn_Sword_L", 
                                 "Bip_Thumb_0_L", "Bip_Thumb_1_L", "Bip_Index_0_L", "Bip_Index_1_L", 
                                 "Bip_Middle_0_L", "Bip_Middle_1_L"] if n in vg_map]

r_arm_vgs = [vg_map[n] for n in ["Bip_UpperArm_R", "Bip_LowerArm_R", "Bip_Hand_R", "Bn_Sword_R", 
                                 "Bip_Thumb_0_R", "Bip_Thumb_1_R", "Bip_Index_0_R", "Bip_Index_1_R", 
                                 "Bip_Middle_0_R", "Bip_Middle_1_R"] if n in vg_map]

# Angle to rotate down: ~36 degrees around Y
# Left arm: rotate clockwise around -Y (or counter-clockwise around +Y)
# In Blender (+X left, +Z up): rotating from +X towards -Z is rotating around -Y by -36 deg!
R_L = Euler((0, math.radians(35), 0), 'XYZ').to_matrix()
pivot_L = Vector((2.05, -0.20, 8.69))

R_R = Euler((0, math.radians(-35), 0), 'XYZ').to_matrix()
pivot_R = Vector((-2.05, -0.20, 8.69))

for v in robot.data.vertices:
    is_l_arm = any(g.group in l_arm_vgs and g.weight > 0.3 for g in v.groups)
    is_r_arm = any(g.group in r_arm_vgs and g.weight > 0.3 for g in v.groups)
    if is_l_arm:
        v.co = pivot_L + R_L @ (v.co - pivot_L)
    elif is_r_arm:
        v.co = pivot_R + R_R @ (v.co - pivot_R)

robot.data.update()

# Set preview material
mat = bpy.data.materials.new("PreviewMat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load(os.path.join(TEX_DIR, "cha_sideswipe_main_Diffuse.png"))
mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
robot.data.materials.clear()
robot.data.materials.append(mat)

# Setup scene & camera
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
world = bpy.data.worlds.new("World")
scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.15, 0.15, 0.18, 1.0)

# Light
ld = bpy.data.lights.new("Sun", type='SUN')
ld.energy = 4.0
lo = bpy.data.objects.new("Sun", ld)
lo.location = (5, -15, 12)
scene.collection.objects.link(lo)

cam_d = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d)
cam.location = (0, -22, 5.5)
direction = Vector((0, 0, 5.0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
scene.collection.objects.link(cam)
scene.camera = cam

out_png = r"C:\Users\Xiangli496\.gemini\antigravity\brain\1ddfb8b4-479e-45f9-9da6-2409640018a4\sideswipe_test_arm_rotation.png"
scene.render.filepath = out_png
scene.render.resolution_x = 1280
scene.render.resolution_y = 960
bpy.ops.render.render(write_still=True)
print("Rendered test arm rotation to:", out_png)
