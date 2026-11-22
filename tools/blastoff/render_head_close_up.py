import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import math
import bpy
from mathutils import Vector

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "BlastOff" / "03_fbx_exports" / "blastoff_robot_prepared.fbx"
TEX_DIR = ROOT / "3rd-party-models" / "BlastOff" / "02_textures"
OUT_IMG = ROOT / "renders" / "blastoff" / "verify_eyes_lit_crown_unlit.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

robot = next(o for o in bpy.data.objects if o.type == "MESH")

# PBR Material with updated Emission
mat = bpy.data.materials.new("MAT_Head_Verify")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

# Diffuse
tex_d = nt.nodes.new("ShaderNodeTexImage")
tex_d.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_main_Diffuse.png"))
nt.links.new(tex_d.outputs["Color"], bsdf.inputs["Base Color"])

# Normal
tex_n = nt.nodes.new("ShaderNodeTexImage")
tex_n.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_main_Normal_unity.png"))
tex_n.image.colorspace_settings.name = "Non-Color"
nmap = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(tex_n.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

# Emission
tex_e = nt.nodes.new("ShaderNodeTexImage")
tex_e.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_main_Emission.png"))
nt.links.new(tex_e.outputs["Color"], bsdf.inputs["Emission"])
bsdf.inputs["Emission Strength"].default_value = 3.5
bsdf.inputs["Roughness"].default_value = 0.50
bsdf.inputs["Metallic"].default_value = 0.30

robot.data.materials.clear()
robot.data.materials.append(mat)

# Head close-up camera: Head is at Z ~ 11.2m
cam_data = bpy.data.cameras.new("CloseUpCam")
cam_obj = bpy.data.objects.new("CloseUpCam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_data.lens = 85.0
# Look slightly from front-left at eye level
cam_obj.location = Vector((-0.6, -4.5, 11.2))
cam_obj.rotation_euler = (math.radians(88), 0, math.radians(-8))
bpy.context.scene.camera = cam_obj

# Studio 3-point lighting
key = bpy.data.lights.new("KeySun", type='SUN')
key.energy = 3.5
key_obj = bpy.data.objects.new("KeySun", key)
bpy.context.collection.objects.link(key_obj)
key_obj.rotation_euler = (math.radians(50), math.radians(30), 0)

fill = bpy.data.lights.new("FillSun", type='SUN')
fill.energy = 2.0
fill_obj = bpy.data.objects.new("FillSun", fill)
bpy.context.collection.objects.link(fill_obj)
fill_obj.rotation_euler = (math.radians(45), math.radians(-40), 0)

rim = bpy.data.lights.new("RimSun", type='SUN')
rim.energy = 2.5
rim_obj = bpy.data.objects.new("RimSun", rim)
bpy.context.collection.objects.link(rim_obj)
rim_obj.rotation_euler = (math.radians(-45), math.radians(160), 0)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = str(OUT_IMG)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered {OUT_IMG}")
