import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from pathlib import Path

obj_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.obj")
tex_path = Path(r"E:\Agent\RID_game\strongarm_extracted\strongarm_vehicle.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.obj(filepath=str(obj_path))

m = bpy.data.objects['strongarm_vehicle']

# Create material with texture
mat = bpy.data.materials.new(name="Mat_Vehicle")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load(str(tex_path))
mat.node_tree.links.new(bsdf.inputs['Base Color'], tex_node.outputs['Color'])
m.data.materials.clear()
m.data.materials.append(mat)

# Add Camera & Light
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 4.0
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.rotation_euler = (math.radians(45), math.radians(20), math.radians(30))

bpy.context.scene.render.resolution_x = 640
bpy.context.scene.render.resolution_y = 480

# View 1: Looking from +Z towards -Z
cam_obj.location = (0, 1.5, 7.0)
cam_obj.rotation_euler = (math.radians(10), 0, 0)
bpy.context.scene.render.filepath = r"E:\Agent\TFTF-blender\tools\strongarm\view_from_pos_z.png"
bpy.ops.render.render(write_still=True)

# View 2: Looking from -Z towards +Z
cam_obj.location = (0, 1.5, -7.0)
cam_obj.rotation_euler = (math.radians(170), 0, math.radians(180))
bpy.context.scene.render.filepath = r"E:\Agent\TFTF-blender\tools\strongarm\view_from_neg_z.png"
bpy.ops.render.render(write_still=True)

print("Rendered view_from_pos_z.png and view_from_neg_z.png!")
