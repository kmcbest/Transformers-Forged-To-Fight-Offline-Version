import bpy
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"E:\Agent\TFTF-blender\3rd-party-models\transformers-galatic-trials-elita-one\source\Elita_One.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

obj = bpy.data.objects['SK_CH_11.001']
mesh = obj.data

cam_data = bpy.data.cameras.new("FrontCam")
cam_obj = bpy.data.objects.new("FrontCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (1.5, 0.0, 7.38)
cam_obj.rotation_euler = (np.radians(90), 0, np.radians(90))
cam_data.lens = 85

light_data = bpy.data.lights.new("FrontLight", type='POINT')
light_obj = bpy.data.objects.new("FrontLight", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (1.2, 0.0, 7.6)
light_data.energy = 20

# Create cyan glow material
glow_mat = bpy.data.materials.new("PerfectEyeGlow")
glow_mat.use_nodes = True
nodes = glow_mat.node_tree.nodes
nodes.clear()
node_emit = nodes.new(type='ShaderNodeEmission')
node_emit.inputs['Color'].default_value = (0.0, 0.8, 1.0, 1.0)
node_emit.inputs['Strength'].default_value = 15.0
node_out = nodes.new(type='ShaderNodeOutputMaterial')
glow_mat.node_tree.links.new(node_emit.outputs['Emission'], node_out.inputs['Surface'])

mesh.materials.append(glow_mat)
glow_idx = len(mesh.materials) - 1

# Polys that form the true eye:
# 1. Front slit:
front_slits = [2386, 2387, 2392, 2393, 2398, 2400, 2409, 2413, 2414, 2423, 2427, 2431]
# 2. Upper inner socket:
inner_socket = [3364, 3365, 3366, 3178, 3174, 3172]

perfect_eye_polys = front_slits + inner_socket
print(f"Total perfect eye polys: {len(perfect_eye_polys)}")

for idx in perfect_eye_polys:
    mesh.polygons[idx].material_index = glow_idx

bpy.context.scene.render.resolution_x = 512
bpy.context.scene.render.resolution_y = 512
bpy.context.scene.render.filepath = r"E:\Agent\TFTF-blender\tools\elita_one\perfect_eyes_glow_render.png"
bpy.ops.render.render(write_still=True)
print("Rendered perfect_eyes_glow_render.png")

bpy.ops.wm.quit_blender()
