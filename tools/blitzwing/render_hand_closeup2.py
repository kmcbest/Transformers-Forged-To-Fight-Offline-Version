import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'stderr'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector
from pathlib import Path

SRC = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")
OUT_IMG = Path(r"E:\Agent\TFTF-blender\tools\blitzwing\renders\hand_source_closeup.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(SRC))

mesh = bpy.data.objects['H_shandian_G1_M_Lod']
vg_lhand = mesh.vertex_groups['Bip001 L Hand'].index

# Get all vertices with weight in L Hand or L Fingers
hand_vg_indices = {vg.index for vg in mesh.vertex_groups if "L Finger" in vg.name or "L Hand" in vg.name}
hand_verts = [v.co for v in mesh.data.vertices if any(g.group in hand_vg_indices and g.weight > 0.05 for g in v.groups)]

center = sum(hand_verts, Vector()) / len(hand_verts)
print(f"Hand center: {center}, count: {len(hand_verts)}")

cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = center + Vector((0.0, -1.2, 0.2))
# look at center
d = center - cam_obj.location
rot_quat = Vector((0, 0, -1)).rotation_difference(d)
# or look_at constraint
cam_obj.rotation_euler = (math.radians(80), 0, 0)

# Add 3-point light
for loc, en in [((center + Vector((1, -1, 1))), 5.0), ((center + Vector((-1, -1, 1))), 3.0), ((center + Vector((0, 1, 1))), 2.0)]:
    light_data = bpy.data.lights.new("Light", 'POINT')
    light_data.energy = en * 20.0
    light_obj = bpy.data.objects.new("Light", light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = loc

bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800
bpy.context.scene.render.filepath = str(OUT_IMG)
bpy.ops.render.render(write_still=True)
print("Rendered successfully")
