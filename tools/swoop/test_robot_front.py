import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Matrix, Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

# Strip parent transforms
for o in [o for o in bpy.data.objects if o.type == 'MESH']:
    mw = o.matrix_world.copy()
    o.parent = None
    o.matrix_world = mw

for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow"] or o.type == 'EMPTY':
        bpy.data.objects.remove(o, do_unlink=True)

swoop_mesh = bpy.data.objects.get("Swoop.001")
bb = [swoop_mesh.matrix_world @ Vector(c) for c in swoop_mesh.bound_box]
curr_h = max(c.z for c in bb) - min(c.z for c in bb)
scale_factor = 11.40 / curr_h
S_mat = Matrix.Scale(scale_factor, 4)

for m in bpy.data.objects:
    if m.type == 'MESH':
        m.matrix_world = S_mat @ m.matrix_world

# Find lowest foot Z on Swoop.001
min_z = min(v.co.z for v in swoop_mesh.data.vertices)
for m in bpy.data.objects:
    if m.type == 'MESH':
        for v in m.data.vertices:
            v.co.z -= min_z

# Find Bone_R_Hand center
rh_vg = swoop_mesh.vertex_groups.get("Bone_R_Hand")
rh_pts = [v.co for v in swoop_mesh.data.vertices if any(g.group == rh_vg.index and g.weight > 0.4 for g in v.groups)]
rh_center = sum(rh_pts, Vector((0,0,0))) / len(rh_pts)
print(f"Right Hand center: {rh_center}")

wpn_mesh = bpy.data.objects.get("Swoop_Weapon")
if wpn_mesh:
    wpn_pts = [v.co for v in wpn_mesh.data.vertices]
    wpn_center = sum(wpn_pts, Vector((0,0,0))) / len(wpn_pts)
    print(f"Swoop_Weapon raw center: {wpn_center}")
    # Translate weapon to right hand
    delta = rh_center - wpn_center
    for v in wpn_mesh.data.vertices:
        v.co += delta
    wpn_new_pts = [v.co for v in wpn_mesh.data.vertices]
    wpn_new_center = sum(wpn_new_pts, Vector((0,0,0))) / len(wpn_new_pts)
    print(f"Swoop_Weapon adjusted center: {wpn_new_center}")

# Render front view
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = Vector((0, -18, 6))
cam.rotation_euler = (1.5708, 0, 0)
bpy.context.scene.camera = cam

light_data = bpy.data.lights.new("Sun", type='SUN')
light_data.energy = 4.0
light = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light)
light.rotation_euler = (0.785, 0.5, 0)

bpy.context.scene.render.resolution_x = 1024
bpy.context.scene.render.resolution_y = 1024
bpy.context.scene.render.filepath = "e:/Agent/TFTF-blender/renders/swoop/swoop_robot_front_test.png"
bpy.ops.render.render(write_still=True)
print("Rendered swoop_robot_front_test.png")
