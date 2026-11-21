import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

# Apply parent transform to keep world positions
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw

swoop_mesh = bpy.data.objects.get("Swoop.001")
bb = [swoop_mesh.matrix_world @ Vector(c) for c in swoop_mesh.bound_box]
curr_h = max(c.z for c in bb) - min(c.z for c in bb)
scale_factor = 11.40 / curr_h
S_mat = Matrix.Scale(scale_factor, 4)

for m in [o for o in bpy.data.objects if o.type == 'MESH']:
    m.matrix_world = S_mat @ m.matrix_world
    # Ground
pts = [v.co.z for m in bpy.data.objects if m.type == 'MESH' for v in m.data.vertices]
min_z = min(pts)
for m in bpy.data.objects:
    if m.type == 'MESH':
        for v in m.data.vertices:
            v.co.z -= min_z

# Camera
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = Vector((0, -18, 6))
cam.rotation_euler = (1.5708, 0, 0)
bpy.context.scene.camera = cam

# Light
light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 4.0
light = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.785, 0.5, 0)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = "renders/swoop/debug_swoop_weapon_pos.png"
bpy.ops.render.render(write_still=True)
print("Rendered debug_swoop_weapon_pos.png")
