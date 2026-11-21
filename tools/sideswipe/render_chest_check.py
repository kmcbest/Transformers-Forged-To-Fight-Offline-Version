import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector, Euler

blend_path = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_aligned_mesh\sideswipe_robot_aligned.blend")
bpy.ops.wm.open_mainfile(filepath=str(blend_path))

scene = bpy.context.scene
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
scene.cycles.samples = 32
scene.render.resolution_x = 1080
scene.render.resolution_y = 1080

if scene.world:
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs["Color"].default_value = (0.05, 0.05, 0.07, 1.0)
        bg.inputs["Strength"].default_value = 0.6

for o in list(scene.objects):
    if o.type in ["LIGHT", "CAMERA"]:
        bpy.data.objects.remove(o, do_unlink=True)

key_d = bpy.data.lights.new("KeyLight", type="SUN")
key_d.energy = 4.5
key_d.color = (1.0, 0.98, 0.95)
key_o = bpy.data.objects.new("KeyLight", key_d)
key_o.rotation_euler = Euler((0.6, 0.4, 0.0), 'XYZ')
scene.collection.objects.link(key_o)

fill_d = bpy.data.lights.new("FillLight", type="SUN")
fill_d.energy = 2.0
fill_d.color = (0.85, 0.92, 1.0)
fill_o = bpy.data.objects.new("FillLight", fill_d)
fill_o.rotation_euler = Euler((0.4, -0.6, 0.0), 'XYZ')
scene.collection.objects.link(fill_o)

rim_d = bpy.data.lights.new("RimLight", type="SUN")
rim_d.energy = 3.5
rim_d.color = (0.95, 0.95, 1.0)
rim_o = bpy.data.objects.new("RimLight", rim_d)
rim_o.rotation_euler = Euler((-0.8, 0.0, 3.14), 'XYZ')
scene.collection.objects.link(rim_o)

cam_d = bpy.data.cameras.new("Cam")
cam_d.lens = 70
cam = bpy.data.objects.new("Cam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam

# Chest Headlights Close-up
cam.location = Vector((0.0, -4.5, 9.5))
target = Vector((0.0, 0.0, 9.3))
cam.rotation_euler = (target - cam.location).to_track_quat("-Z", "Y").to_euler()

OUT_FILE = Path(r"E:\Agent\TFTF-blender\renders\sideswipe\sideswipe_tuned_03_chest_closeup.png")
scene.render.filepath = str(OUT_FILE)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered: {OUT_FILE}")
