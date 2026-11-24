import sys
import os
from pathlib import Path
import bpy
import math
import mathutils
from mathutils import Vector, Euler

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_DIR = ROOT / "3rd-party-models" / "Blitzwing_EW" / "01_source"
OUT_DIR = ROOT / "renders" / "blitzwing"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def setup_pbr_material(mat, t_path, n_path, arm_path, is_alpha=False):
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    output = nodes.new("ShaderNodeOutputMaterial")
    output.location = (600, 0)

    bsdf = nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.location = (200, 0)
    links.new(bsdf.outputs["BSDF"], output.inputs["Surface"])

    if t_path and os.path.exists(t_path):
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.location = (-400, 200)
        tex_node.image = bpy.data.images.load(str(t_path))
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
        if is_alpha:
            links.new(tex_node.outputs["Alpha"], bsdf.inputs["Alpha"])
            mat.blend_method = 'BLEND'

    if n_path and os.path.exists(n_path):
        norm_img_node = nodes.new("ShaderNodeTexImage")
        norm_img_node.location = (-400, -100)
        norm_img_node.image = bpy.data.images.load(str(n_path))
        norm_img_node.image.colorspace_settings.name = 'Non-Color'
        norm_map = nodes.new("ShaderNodeNormalMap")
        norm_map.location = (-150, -100)
        links.new(norm_img_node.outputs["Color"], norm_map.inputs["Color"])
        links.new(norm_map.outputs["Normal"], bsdf.inputs["Normal"])

    if arm_path and os.path.exists(arm_path):
        arm_node = nodes.new("ShaderNodeTexImage")
        arm_node.location = (-400, -400)
        arm_node.image = bpy.data.images.load(str(arm_path))
        arm_node.image.colorspace_settings.name = 'Non-Color'
        sep = nodes.new("ShaderNodeSeparateColor")
        sep.location = (-150, -400)
        links.new(arm_node.outputs["Color"], sep.inputs["Color"])
        links.new(sep.outputs["Green"], bsdf.inputs["Roughness"])
        links.new(sep.outputs["Blue"], bsdf.inputs["Metallic"])

def setup_studio_lighting():
    key_data = bpy.data.lights.new(name="KeyLight", type='SUN')
    key_data.energy = 4.0
    key_data.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new(name="KeyLight", object_data=key_data)
    bpy.context.scene.collection.objects.link(key_obj)
    key_obj.rotation_euler = Euler((math.radians(50), math.radians(25), math.radians(40)), 'XYZ')

    fill_data = bpy.data.lights.new(name="FillLight", type='SUN')
    fill_data.energy = 2.2
    fill_data.color = (0.85, 0.92, 1.0)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = Euler((math.radians(45), math.radians(-35), math.radians(-130)), 'XYZ')

    rim_data = bpy.data.lights.new(name="RimLight", type='SUN')
    rim_data.energy = 3.2
    rim_data.color = (1.0, 0.95, 0.9)
    rim_obj = bpy.data.objects.new(name="RimLight", object_data=rim_data)
    bpy.context.scene.collection.objects.link(rim_obj)
    rim_obj.rotation_euler = Euler((math.radians(-35), math.radians(50), math.radians(160)), 'XYZ')

# =========================================================================
# 1. Dedicated Perfect Jet Render
# =========================================================================
print("=== 1. Dedicated Jet Render ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V2.fbx"))

jet_arm = bpy.data.objects.get("H_shandian_G1_V2")
if jet_arm:
    jet_arm.animation_data_clear()
    jet_arm.data.pose_position = 'REST'

for mat in bpy.data.materials:
    is_alp = "_alp" in mat.name
    t = SRC_DIR / "H_shandian_G1_V2_T.png"
    n = SRC_DIR / "H_shandian_G1_V2_N.png"
    arm = SRC_DIR / "H_shandian_G1_V2_ARM.png"
    setup_pbr_material(mat, t, n, arm, is_alpha=is_alp)

setup_studio_lighting()

jet_mesh = bpy.data.objects.get("H_shandian_G1_V2.001")
bpy.context.view_layer.update()
bbox = [jet_mesh.matrix_world @ Vector(c) for c in jet_mesh.bound_box]
min_x, max_x = min(v.x for v in bbox), max(v.x for v in bbox)
min_y, max_y = min(v.y for v in bbox), max(v.y for v in bbox)
min_z, max_z = min(v.z for v in bbox), max(v.z for v in bbox)
cx, cy, cz = (min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2
jet_diag = (Vector((max_x, max_y, max_z)) - Vector((min_x, min_y, min_z))).length

cam_data = bpy.data.cameras.new("CamJetDedicated")
cam_obj = bpy.data.objects.new("CamJetDedicated", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Camera viewing Jet from 3-quarter top-front
dist = jet_diag * 1.5
cam_obj.location = Vector((cx + dist * 0.55, cy - dist * 0.75, cz + dist * 0.45))
rot_q = (Vector((cx, cy, cz)) - cam_obj.location).to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_q.to_euler()

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1200
bpy.context.scene.render.resolution_y = 1200
out_jet = OUT_DIR / "gate1_jet_preview.png"
bpy.context.scene.render.filepath = str(out_jet)
bpy.ops.render.render(write_still=True)
print(f"Rendered dedicated Jet to {out_jet}")

# =========================================================================
# 2. Perfect Triple-Changer Studio Showcase (Robot + Tank + Jet)
# =========================================================================
print("\n=== 2. Triple-Changer Studio Showcase ===")
bpy.ops.wm.read_factory_settings(use_empty=True)

# 2a. Import Robot
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))
robot_arm = bpy.data.objects.get("floor")
if robot_arm:
    robot_arm.animation_data_clear()
    robot_arm.data.pose_position = 'REST'
for w_name in ["H_shandian_G1_W1_Lod", "H_shandian_G1_W2_Lod"]:
    w = bpy.data.objects.get(w_name)
    if w:
        w.hide_render = True

# 2b. Import Tank
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V1.fbx"))
tank_mesh = bpy.data.objects.get("H_shandian_G1_V1.001")
tank_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != robot_arm][0]
if tank_arm:
    tank_arm.animation_data_clear()
    tank_arm.data.pose_position = 'REST'

# 2c. Import Jet
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V2.fbx"))
jet_mesh = bpy.data.objects.get("H_shandian_G1_V2.001")
jet_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != robot_arm and o != tank_arm][0]
if jet_arm:
    jet_arm.animation_data_clear()
    jet_arm.data.pose_position = 'REST'

# Position & Rotate vehicles flanking the robot:
# Robot: center (0, 0, 0)
# Tank: on the left, rotated 35 deg outward
if tank_arm:
    tank_arm.location = Vector((-0.075, 0.005, 0.0))
    tank_arm.rotation_euler = Euler((0, 0, math.radians(25)), 'XYZ')

# Jet: on the right, rotated -35 deg outward
if jet_arm:
    jet_arm.location = Vector((0.075, 0.005, 0.0))
    jet_arm.rotation_euler = Euler((0, 0, math.radians(-25)), 'XYZ')

for mat in bpy.data.materials:
    mname = mat.name.replace(".001", "").replace(".002", "")
    is_alp = "_alp" in mname
    if "V1" in mname:
        t = SRC_DIR / "H_shandian_G1_V1_T.png"
        n = SRC_DIR / "H_shandian_G1_V1_N.png"
        arm = SRC_DIR / "H_shandian_G1_V1_ARM.png"
    elif "V2" in mname:
        t = SRC_DIR / "H_shandian_G1_V2_T.png"
        n = SRC_DIR / "H_shandian_G1_V2_N.png"
        arm = SRC_DIR / "H_shandian_G1_V2_ARM.png"
    elif "W" in mname:
        t = SRC_DIR / "H_shandian_G1_W1_T.png"
        n = SRC_DIR / "H_shandian_G1_W1_N.png"
        arm = SRC_DIR / "H_shandian_G1_W1_ARM.png"
    else:
        t = SRC_DIR / f"{mname}_T.png"
        n = SRC_DIR / f"{mname}_N.png"
        arm = SRC_DIR / f"{mname}_ARM.png"
    setup_pbr_material(mat, t, n, arm, is_alpha=is_alp)

setup_studio_lighting()

# Add a dark studio floor plane
bpy.ops.mesh.primitive_plane_add(size=2.0, location=(0, 0, 0))
floor_plane = bpy.context.active_object
floor_mat = bpy.data.materials.new(name="StudioFloor")
floor_mat.use_nodes = True
bsdf = floor_mat.node_tree.nodes.get("Principled BSDF")
if bsdf:
    bsdf.inputs["Base Color"].default_value = (0.04, 0.04, 0.05, 1.0)
    bsdf.inputs["Roughness"].default_value = 0.35
    bsdf.inputs["Metallic"].default_value = 0.8
floor_plane.data.materials.append(floor_mat)

# Showcase Camera
cam_data = bpy.data.cameras.new("CamShowcase")
cam_obj = bpy.data.objects.new("CamShowcase", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Camera viewing all 3 modes
cam_obj.location = Vector((0.0, -0.21, 0.045))
rot_q = (Vector((0.0, 0.0, 0.035)) - cam_obj.location).to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_q.to_euler()

bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
out_showcase = OUT_DIR / "gate1_blitzwing_triple_changer_showcase.png"
bpy.context.scene.render.filepath = str(out_showcase)
bpy.ops.render.render(write_still=True)
print(f"Rendered perfect Triple Changer Showcase to {out_showcase}")
