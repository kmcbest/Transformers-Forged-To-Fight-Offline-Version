import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path("tools/demolishor")
BLEND_PATH = ROOT / "demolishor_phase2_inspect.blend"
bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

# Clear old cameras and lights
for o in list(bpy.data.objects):
    if o.type in ['CAMERA', 'LIGHT']:
        bpy.data.objects.remove(o, do_unlink=True)

# Add Side-Front Camera (viewing from X=11, Y=4, Z=6.5)
cam_data = bpy.data.cameras.new("SideFrontCam")
cam_obj = bpy.data.objects.new("SideFrontCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = (11.0, 4.0, 6.5)
direction = mathutils.Vector((0, 0, 5.5)) - cam_obj.location
rot_quat = direction.to_track_quat('-Z', 'Y')
cam_obj.rotation_euler = rot_quat.to_euler()

# Three-point studio lighting:
key_light = bpy.data.lights.new("KeyLight", type='SUN')
key_obj = bpy.data.objects.new("KeyLight", key_light)
bpy.context.scene.collection.objects.link(key_obj)
key_obj.location = (10, 10, 15)
key_obj.rotation_euler = (math.radians(-35), math.radians(35), math.radians(65))
key_light.energy = 4.0

fill_light = bpy.data.lights.new("FillLight", type='SUN')
fill_obj = bpy.data.objects.new("FillLight", fill_light)
bpy.context.scene.collection.objects.link(fill_obj)
fill_obj.location = (-10, 8, 10)
fill_obj.rotation_euler = (math.radians(-35), math.radians(-35), math.radians(-45))
fill_light.energy = 2.0

rim_light = bpy.data.lights.new("RimLight", type='SUN')
rim_obj = bpy.data.objects.new("RimLight", rim_light)
bpy.context.scene.collection.objects.link(rim_obj)
rim_obj.location = (0, -12, 10)
rim_obj.rotation_euler = (math.radians(45), 0, math.radians(180))
rim_light.energy = 2.5

# World
if not bpy.context.scene.world:
    bpy.context.scene.world = bpy.data.worlds.new("World")
bpy.context.scene.world.use_nodes = True
bg_node = bpy.context.scene.world.node_tree.nodes.get("Background")
if bg_node:
    bg_node.inputs[0].default_value = (0.2, 0.22, 0.25, 1.0)
    bg_node.inputs[1].default_value = 1.0

# Hide ghost
ghost = bpy.data.objects.get("Ironhide_Ghost_Reference")
if ghost:
    ghost.hide_render = True

# Armature
arm = bpy.data.objects.get("Ironhide_Reference_Armature")
if arm:
    arm.show_in_front = True
    arm.data.display_type = 'OCTAHEDRAL'

bpy.context.scene.render.resolution_x = 1000
bpy.context.scene.render.resolution_y = 1000

# Render frame 20 (matching user's Image 2)
bpy.context.scene.frame_current = 20
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_elbow_fixed_frame20.png")
bpy.ops.render.render(write_still=True)

# Render frame 10 (Peak stride)
bpy.context.scene.frame_current = 10
bpy.context.scene.render.filepath = str(ROOT.resolve() / "preview_elbow_fixed_frame10.png")
bpy.ops.render.render(write_still=True)

# Save the blend file with this camera and lighting setup for user
bpy.context.scene.frame_current = 0
bpy.ops.wm.save_mainfile(filepath=str(BLEND_PATH))
print(f"[✓] Saved updated studio scene & rendered previews!")
