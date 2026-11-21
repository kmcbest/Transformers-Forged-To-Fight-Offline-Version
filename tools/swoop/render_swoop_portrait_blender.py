import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"
DIFF_TEX = ROOT / "3rd-party-models/swoop/02_textures/cha_swoop_main_Diffuse.png"
NORM_TEX = ROOT / "3rd-party-models/swoop/02_textures/cha_swoop_main_Normal_unity.png"
OUT_RAW_PNG = ROOT / "scratch/swoop_portrait_raw.png"
OUT_RAW_PNG.parent.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.render.resolution_x = 512
scene.render.resolution_y = 512
scene.render.film_transparent = True
scene.view_settings.view_transform = 'Standard'

# Setup material with textures
swoop_mesh = bpy.data.objects.get("cha_swoop_robot")
assert swoop_mesh is not None, "Missing cha_swoop_robot mesh!"

mat = bpy.data.materials.new(name="M_Swoop_Portrait")
mat.use_nodes = True
nodes = mat.node_tree.nodes
nodes.clear()

node_output = nodes.new(type='ShaderNodeOutputMaterial')
node_bsdf = nodes.new(type='ShaderNodeBsdfPrincipled')
node_bsdf.inputs['Roughness'].default_value = 0.4
node_bsdf.inputs['Metallic'].default_value = 0.1

# Diffuse
node_tex = nodes.new(type='ShaderNodeTexImage')
node_tex.image = bpy.data.images.load(str(DIFF_TEX))
mat.node_tree.links.new(node_tex.outputs['Color'], node_bsdf.inputs['Base Color'])

# Normal
if NORM_TEX.is_file():
    node_norm_tex = nodes.new(type='ShaderNodeTexImage')
    node_norm_tex.image = bpy.data.images.load(str(NORM_TEX))
    node_norm_tex.image.colorspace_settings.name = 'Non-Color'
    node_norm_map = nodes.new(type='ShaderNodeNormalMap')
    node_norm_map.inputs['Strength'].default_value = 1.0
    mat.node_tree.links.new(node_norm_tex.outputs['Color'], node_norm_map.inputs['Color'])
    mat.node_tree.links.new(node_norm_map.outputs['Normal'], node_bsdf.inputs['Normal'])

mat.node_tree.links.new(node_bsdf.outputs['BSDF'], node_output.inputs['Surface'])

if swoop_mesh.data.materials:
    swoop_mesh.data.materials[0] = mat
else:
    swoop_mesh.data.materials.append(mat)

# Camera setup: bust shot focusing on head, crest, chest
target_pos = Vector((0.0, -0.2, 9.8))
angle_deg = 15.0
angle_rad = math.radians(angle_deg)
cam_dist = 6.2
cam_x = target_pos.x + cam_dist * math.sin(angle_rad)
cam_y = target_pos.y - cam_dist * math.cos(angle_rad)
cam_z = target_pos.z + 0.1

cam_data = bpy.data.cameras.new("PortraitCam")
cam_data.lens = 50.0
cam_data.clip_start = 0.1
cam_obj = bpy.data.objects.new("PortraitCam", cam_data)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

cam_obj.location = (cam_x, cam_y, cam_z)

# Point camera at target
direction = target_pos - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# Lighting: 3-point lights
key_light = bpy.data.lights.new(name="KeyLight", type='SUN')
key_light.energy = 4.0
key_light.color = (1.0, 0.96, 0.92)
key_obj = bpy.data.objects.new("KeyLight", key_light)
key_obj.rotation_euler = (math.radians(45), math.radians(15), math.radians(35))
scene.collection.objects.link(key_obj)

fill_light = bpy.data.lights.new(name="FillLight", type='SUN')
fill_light.energy = 2.0
fill_light.color = (0.7, 0.85, 1.0)
fill_obj = bpy.data.objects.new("FillLight", fill_light)
fill_obj.rotation_euler = (math.radians(50), math.radians(-30), math.radians(-60))
scene.collection.objects.link(fill_obj)

rim_light = bpy.data.lights.new(name="RimLight", type='SUN')
rim_light.energy = 3.5
rim_light.color = (1.0, 1.0, 1.0)
rim_obj = bpy.data.objects.new("RimLight", rim_light)
rim_obj.rotation_euler = (math.radians(-35), math.radians(10), math.radians(150))
scene.collection.objects.link(rim_obj)

scene.render.filepath = str(OUT_RAW_PNG)
bpy.ops.render.render(write_still=True)
print(f"Rendered raw portrait to: {OUT_RAW_PNG}")
