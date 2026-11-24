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

    # Base Color Texture
    if t_path and os.path.exists(t_path):
        tex_node = nodes.new("ShaderNodeTexImage")
        tex_node.location = (-400, 200)
        tex_node.image = bpy.data.images.load(str(t_path))
        links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
        if is_alpha:
            links.new(tex_node.outputs["Alpha"], bsdf.inputs["Alpha"])
            mat.blend_method = 'BLEND'

    # Normal Map Texture
    if n_path and os.path.exists(n_path):
        norm_img_node = nodes.new("ShaderNodeTexImage")
        norm_img_node.location = (-400, -100)
        norm_img_node.image = bpy.data.images.load(str(n_path))
        norm_img_node.image.colorspace_settings.name = 'Non-Color'
        norm_map = nodes.new("ShaderNodeNormalMap")
        norm_map.location = (-150, -100)
        links.new(norm_img_node.outputs["Color"], norm_map.inputs["Color"])
        links.new(norm_map.outputs["Normal"], bsdf.inputs["Normal"])

    # ARM Texture (R=AO, G=Roughness, B=Metallic)
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

# Setup lighting studio
def setup_studio_lighting():
    # Key light
    key_data = bpy.data.lights.new(name="KeyLight", type='SUN')
    key_data.energy = 3.5
    key_data.color = (1.0, 0.98, 0.95)
    key_obj = bpy.data.objects.new(name="KeyLight", object_data=key_data)
    bpy.context.scene.collection.objects.link(key_obj)
    key_obj.rotation_euler = Euler((math.radians(50), math.radians(20), math.radians(35)), 'XYZ')

    # Fill light
    fill_data = bpy.data.lights.new(name="FillLight", type='SUN')
    fill_data.energy = 1.8
    fill_data.color = (0.85, 0.9, 1.0)
    fill_obj = bpy.data.objects.new(name="FillLight", object_data=fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.rotation_euler = Euler((math.radians(45), math.radians(-30), math.radians(-140)), 'XYZ')

    # Rim light
    rim_data = bpy.data.lights.new(name="RimLight", type='SUN')
    rim_data.energy = 2.5
    rim_data.color = (1.0, 0.95, 0.9)
    rim_obj = bpy.data.objects.new(name="RimLight", object_data=rim_data)
    bpy.context.scene.collection.objects.link(rim_obj)
    rim_obj.rotation_euler = Euler((math.radians(-30), math.radians(60), math.radians(170)), 'XYZ')

# =========================================================================
# 1. RENDER ROBOT MODE
# =========================================================================
print("=== 1. Rendering Robot Mode ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))

arm_obj = bpy.data.objects.get("floor")
if arm_obj:
    arm_obj.animation_data_clear()
    arm_obj.data.pose_position = 'REST'

# Connect robot materials
for mat in bpy.data.materials:
    mname = mat.name.replace(".001", "").replace(".002", "")
    t = SRC_DIR / f"{mname}_T.png"
    n = SRC_DIR / f"{mname}_N.png"
    arm = SRC_DIR / f"{mname}_ARM.png"
    if not t.exists() and "W" in mname:
        t = SRC_DIR / "H_shandian_G1_W1_T.png"
        n = SRC_DIR / "H_shandian_G1_W1_N.png"
        arm = SRC_DIR / "H_shandian_G1_W1_ARM.png"
    setup_pbr_material(mat, t, n, arm)

# Hide weapons from between feet for clean robot presentation
for w_name in ["H_shandian_G1_W1_Lod", "H_shandian_G1_W2_Lod"]:
    w = bpy.data.objects.get(w_name)
    if w:
        w.hide_render = True

setup_studio_lighting()

# Camera for Robot (Front 45 perspective)
robot_mesh = bpy.data.objects.get("H_shandian_G1_M_Lod")
bbox = [robot_mesh.matrix_world @ Vector(c) for c in robot_mesh.bound_box]
min_x, max_x = min(v.x for v in bbox), max(v.x for v in bbox)
min_y, max_y = min(v.y for v in bbox), max(v.y for v in bbox)
min_z, max_z = min(v.z for v in bbox), max(v.z for v in bbox)
cx, cy, cz = (min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2
height = max_z - min_z

cam_data = bpy.data.cameras.new("CamRobot")
cam_obj = bpy.data.objects.new("CamRobot", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

dist = height * 2.2
cam_obj.location = Vector((cx + dist * 0.35, cy - dist * 0.9, cz + height * 0.05))
rot_q = (Vector((cx, cy, cz)) - cam_obj.location).to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_q.to_euler()

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1200
bpy.context.scene.render.resolution_y = 1200
out_robot = OUT_DIR / "gate1_robot_preview.png"
bpy.context.scene.render.filepath = str(out_robot)
bpy.ops.render.render(write_still=True)
print(f"Rendered Robot to {out_robot}")

# =========================================================================
# 2. RENDER TANK MODE (V1)
# =========================================================================
print("\n=== 2. Rendering Tank Mode (V1) ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V1.fbx"))

arm_obj = bpy.data.objects.get("floor")
if arm_obj:
    arm_obj.animation_data_clear()
    arm_obj.data.pose_position = 'REST'

for mat in bpy.data.materials:
    is_alp = "_alp" in mat.name
    t = SRC_DIR / "H_shandian_G1_V1_T.png"
    n = SRC_DIR / "H_shandian_G1_V1_N.png"
    arm = SRC_DIR / "H_shandian_G1_V1_ARM.png"
    setup_pbr_material(mat, t, n, arm, is_alpha=is_alp)

setup_studio_lighting()

tank_mesh = bpy.data.objects.get("H_shandian_G1_V1.001")
bbox = [tank_mesh.matrix_world @ Vector(c) for c in tank_mesh.bound_box]
min_x, max_x = min(v.x for v in bbox), max(v.x for v in bbox)
min_y, max_y = min(v.y for v in bbox), max(v.y for v in bbox)
min_z, max_z = min(v.z for v in bbox), max(v.z for v in bbox)
cx, cy, cz = (min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2
tank_len = max(max_x - min_x, max_y - min_y, max_z - min_z)

cam_data = bpy.data.cameras.new("CamTank")
cam_obj = bpy.data.objects.new("CamTank", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

dist = tank_len * 2.2
cam_obj.location = Vector((cx + dist * 0.7, cy - dist * 0.7, cz + dist * 0.5))
rot_q = (Vector((cx, cy, cz)) - cam_obj.location).to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_q.to_euler()

out_tank = OUT_DIR / "gate1_tank_preview.png"
bpy.context.scene.render.filepath = str(out_tank)
bpy.ops.render.render(write_still=True)
print(f"Rendered Tank to {out_tank}")

# =========================================================================
# 3. RENDER JET MODE (V2)
# =========================================================================
print("\n=== 3. Rendering Jet Mode (V2) ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V2.fbx"))

arm_obj = bpy.data.objects.get("H_shandian_G1_V2")
if arm_obj:
    arm_obj.animation_data_clear()
    arm_obj.data.pose_position = 'REST'

for mat in bpy.data.materials:
    is_alp = "_alp" in mat.name
    t = SRC_DIR / "H_shandian_G1_V2_T.png"
    n = SRC_DIR / "H_shandian_G1_V2_N.png"
    arm = SRC_DIR / "H_shandian_G1_V2_ARM.png"
    setup_pbr_material(mat, t, n, arm, is_alpha=is_alp)

setup_studio_lighting()

jet_mesh = bpy.data.objects.get("H_shandian_G1_V2.001")
bbox = [jet_mesh.matrix_world @ Vector(c) for c in jet_mesh.bound_box]
min_x, max_x = min(v.x for v in bbox), max(v.x for v in bbox)
min_y, max_y = min(v.y for v in bbox), max(v.y for v in bbox)
min_z, max_z = min(v.z for v in bbox), max(v.z for v in bbox)
cx, cy, cz = (min_x + max_x)/2, (min_y + max_y)/2, (min_z + max_z)/2
jet_len = max(max_x - min_x, max_y - min_y, max_z - min_z)

cam_data = bpy.data.cameras.new("CamJet")
cam_obj = bpy.data.objects.new("CamJet", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

dist = jet_len * 2.2
cam_obj.location = Vector((cx + dist * 0.7, cy - dist * 0.7, cz + dist * 0.5))
rot_q = (Vector((cx, cy, cz)) - cam_obj.location).to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_q.to_euler()

out_jet = OUT_DIR / "gate1_jet_preview.png"
bpy.context.scene.render.filepath = str(out_jet)
bpy.ops.render.render(write_still=True)
print(f"Rendered Jet to {out_jet}")

# =========================================================================
# 4. RENDER TRIPLE CHANGER SHOWCASE (ALL 3 TOGETHER)
# =========================================================================
print("\n=== 4. Rendering Triple Changer Combined Showcase ===")
bpy.ops.wm.read_factory_settings(use_empty=True)

# 4a. Import Robot
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_M_LOD.fbx"))
robot_arm = bpy.data.objects.get("floor")
if robot_arm:
    robot_arm.animation_data_clear()
    robot_arm.data.pose_position = 'REST'
for w_name in ["H_shandian_G1_W1_Lod", "H_shandian_G1_W2_Lod"]:
    w = bpy.data.objects.get(w_name)
    if w:
        w.hide_render = True

# 4b. Import Tank
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V1.fbx"))
tank_mesh = bpy.data.objects.get("H_shandian_G1_V1.001")
tank_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != robot_arm][0]
if tank_arm:
    tank_arm.animation_data_clear()
    tank_arm.data.pose_position = 'REST'

# 4c. Import Jet
bpy.ops.import_scene.fbx(filepath=str(SRC_DIR / "H_shandian_G1_V2.fbx"))
jet_mesh = bpy.data.objects.get("H_shandian_G1_V2.001")
jet_arm = [o for o in bpy.data.objects if o.type == 'ARMATURE' and o != robot_arm and o != tank_arm][0]
if jet_arm:
    jet_arm.animation_data_clear()
    jet_arm.data.pose_position = 'REST'

# Configure all materials
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

# Arrange positions:
# Robot at center (0, 0, 0)
# Tank on the left (-0.065, 0, 0)
# Jet on the right (+0.065, 0, 0)
if tank_arm:
    tank_arm.location = Vector((-0.065, -0.010, 0))
if jet_arm:
    jet_arm.location = Vector((0.065, -0.010, 0))

setup_studio_lighting()

# Showcase Camera
cam_data = bpy.data.cameras.new("CamShowcase")
cam_obj = bpy.data.objects.new("CamShowcase", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = Vector((0.0, -0.22, 0.045))
rot_q = (Vector((0.0, -0.01, 0.035)) - cam_obj.location).to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_q.to_euler()

bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
out_showcase = OUT_DIR / "gate1_blitzwing_triple_changer_showcase.png"
bpy.context.scene.render.filepath = str(out_showcase)
bpy.ops.render.render(write_still=True)
print(f"Rendered Triple Changer Showcase to {out_showcase}")
