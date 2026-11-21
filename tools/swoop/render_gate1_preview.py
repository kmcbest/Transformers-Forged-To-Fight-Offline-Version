import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import os

bpy.ops.wm.read_factory_settings(use_empty=True)

# Create plane with material displaying the diffuse atlas
bpy.ops.mesh.primitive_plane_add(size=2, location=(0, 0, 0))
plane = bpy.context.active_object

mat = bpy.data.materials.new("M_Atlas_Preview")
mat.use_nodes = True
plane.data.materials.append(mat)
bsdf = mat.node_tree.nodes.get("Principled BSDF")

tex_path = r"e:\Agent\TFTF-blender\3rd-party-models\swoop\02_textures\cha_swoop_main_Diffuse.png"
if os.path.exists(tex_path):
    img = bpy.data.images.load(tex_path)
    tex_node = mat.node_tree.nodes.new('ShaderNodeTexImage')
    tex_node.image = img
    mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_node.outputs['Color'])

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam
cam.location = (0, 0, 2.45)
cam.rotation_euler = (0, 0, 0)

world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs['Color'].default_value = (0.05, 0.05, 0.05, 1.0)
    bg.inputs['Strength'].default_value = 1.0

light_data = bpy.data.lights.new(name="Sun", type='SUN')
light_data.energy = 2.0
light = bpy.data.objects.new(name="Sun", object_data=light_data)
bpy.context.scene.collection.objects.link(light)
light.location = (0, 0, 5)

out_dir = r"e:\Agent\TFTF-blender\renders\swoop"
os.makedirs(out_dir, exist_ok=True)
out_file = os.path.join(out_dir, "gate1_blender_preview.png")

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = out_file
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered Gate 1 texture preview to {out_file}")
