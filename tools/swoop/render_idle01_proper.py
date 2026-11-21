import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
swoop = bpy.data.objects.get("Swoop.001")

# Apply idle01 action
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

# Assign material with texture
mat = bpy.data.materials.new("M_Preview")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png")
mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])
swoop.data.materials.clear()
swoop.data.materials.append(mat)

# Let's find evaluated bounding box of Swoop.001 in idle01 frame 1
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()
pts = [eval_obj.matrix_world @ v.co for v in eval_mesh.vertices]
min_c = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
max_c = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
center = (min_c + max_c) / 2.0
size = max_c - min_c
print(f"Evaluated bounding box: min={min_c}, max={max_c}")
print(f"Center: {center}, Size: {size}")

# Position camera to look directly at center
cam_data = bpy.data.cameras.new("Cam")
cam_data.clip_start = 0.001
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)

# In idle01: front is towards -Y or +Y?
# Head is at Y=0.001, feet at Y=-0.005. Let's place camera at -Y looking at +Y:
cam.location = Vector((center.x, center.y - size.z * 2.2, center.z))
cam.rotation_euler = (1.5708, 0, 0)
bpy.context.scene.camera = cam

# Lights
light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 4.0
light = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.785, 0.5, 0)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = "e:/Agent/TFTF-blender/renders/swoop/swoop_idle01_proper.png"
bpy.ops.render.render(write_still=True)
print("Rendered swoop_idle01_proper.png")
eval_obj.to_mesh_clear()
