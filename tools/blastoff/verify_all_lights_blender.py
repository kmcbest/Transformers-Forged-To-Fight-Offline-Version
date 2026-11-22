import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
ROBOT_FBX = ROOT / "3rd-party-models" / "BlastOff" / "03_fbx_exports" / "blastoff_robot_prepared.fbx"
TEX_DIR = ROOT / "3rd-party-models" / "BlastOff" / "02_textures"
OUT_PNG = ROOT / "renders" / "blastoff" / "verify_all_lights_blender.png"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROBOT_FBX))

robot = next(o for o in bpy.data.objects if o.type == "MESH")
mat = bpy.data.materials.new("MAT_Verify_Lights")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Roughness"].default_value = 0.50
bsdf.inputs["Metallic"].default_value = 0.28
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

td = nt.nodes.new("ShaderNodeTexImage")
td.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_main_Diffuse.png"))
nt.links.new(td.outputs["Color"], bsdf.inputs["Base Color"])

tn = nt.nodes.new("ShaderNodeTexImage")
tn.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_main_Normal_unity.png"))
tn.image.colorspace_settings.name = "Non-Color"
nm = nt.nodes.new("ShaderNodeNormalMap")
nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

te = nt.nodes.new("ShaderNodeTexImage")
te.image = bpy.data.images.load(str(TEX_DIR / "cha_blastoff_main_Emission.png"))
nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
bsdf.inputs["Emission Strength"].default_value = 4.5

robot.data.materials.clear()
robot.data.materials.append(mat)

# Camera 3/4 front full body view
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_data.lens = 35.0
cam_obj.location = (3.5, -18.5, 7.2)
from mathutils import Vector
direction = Vector((0.0, 0.0, 6.4)) - cam_obj.location
cam_obj.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.camera = cam_obj

sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_obj = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun_obj)
sun_data.energy = 3.0
sun_obj.rotation_euler = (0.7, 0.2, 0.4)

world = bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.04, 0.05, 0.08, 1.0)

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.samples = 48
scene.render.resolution_x = 1024
scene.render.resolution_y = 1024
scene.render.filepath = str(OUT_PNG)
bpy.ops.render.render(write_still=True)
print(f"Rendered {OUT_PNG}")
