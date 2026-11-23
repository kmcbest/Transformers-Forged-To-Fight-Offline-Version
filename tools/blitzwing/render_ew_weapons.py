import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import math
from pathlib import Path
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")

arm = bpy.data.objects["floor"]
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

# Apply H_shandian_G1_W1_T.png material
tex_img = bpy.data.images.load(r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_W1_T.png")
mat = bpy.data.materials.new("WpnMat")
mat.use_nodes = True
nodes = mat.node_tree.nodes
links = mat.node_tree.links
nodes.clear()
out = nodes.new("ShaderNodeOutputMaterial")
bsdf = nodes.new("ShaderNodeBsdfPrincipled")
tex = nodes.new("ShaderNodeTexImage")
tex.image = tex_img
links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

# Hide body
bpy.data.objects["H_shandian_G1_M_Lod"].hide_render = True
bpy.data.objects["H_shandian_G1_M_Lod"].hide_viewport = True

# Setup lighting & camera
scene = bpy.context.scene
scene.render.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 16
scene.render.resolution_x = 800
scene.render.resolution_y = 600
world = bpy.data.worlds.new("W")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (0.18, 0.18, 0.2, 1.0)
bg.inputs[1].default_value = 1.5

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = 'ORTHO'
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam_obj)
scene.camera = cam_obj

out_dir = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\renders")
out_dir.mkdir(parents=True, exist_ok=True)

for name, hide_other, scale_view, loc_cam, rot_cam in [
    ("H_shandian_G1_W1_Lod", "H_shandian_G1_W2_Lod", 0.06, (0.0, -0.2, 0.03), (math.radians(90), 0, 0)),
    ("H_shandian_G1_W2_Lod", "H_shandian_G1_W1_Lod", 0.05, (0.0, -0.2, 0.015), (math.radians(90), 0, 0)),
]:
    obj = bpy.data.objects[name]
    other = bpy.data.objects[hide_other]
    obj.hide_render = False
    other.hide_render = True
    obj.data.materials.clear()
    obj.data.materials.append(mat)
    cam_data.ortho_scale = scale_view
    cam_obj.location = loc_cam
    cam_obj.rotation_euler = rot_cam
    scene.render.filepath = str(out_dir / f"inspect_{name}.png")
    bpy.ops.render.render(write_still=True)
print("Rendered weapon inspection images.")
