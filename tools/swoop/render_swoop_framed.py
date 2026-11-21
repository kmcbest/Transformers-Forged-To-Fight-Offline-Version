import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Matrix
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

# Hide unwanted
for o in bpy.data.objects:
    if o.name in ["Shadow", "Swoop_Weapon", "Symbol_DC"]:
        bpy.data.objects.remove(o, do_unlink=True)

arm = bpy.data.objects.get("Bip001")
swoop_mesh = bpy.data.objects.get("Swoop.001")

if arm:
    arm.animation_data_clear()
    arm.data.pose_position = 'REST'

bpy.context.view_layer.update()

# Get evaluated mesh vertices in world space
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop_mesh.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()

mw = eval_obj.matrix_world
world_verts = [mw @ v.co for v in eval_mesh.vertices]

xs = [v.x for v in world_verts]
ys = [v.y for v in world_verts]
zs = [v.z for v in world_verts]

min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
min_z, max_z = min(zs), max(zs)
print(f"WORLD EVAL BOUNDS: X=[{min_x:.3f}, {max_x:.3f}], Y=[{min_y:.3f}, {max_y:.3f}], Z=[{min_z:.3f}, {max_z:.3f}]")

center = Vector(((min_x + max_x) / 2, (min_y + max_y) / 2, (min_z + max_z) / 2))
size = max(max_x - min_x, max_z - min_z)

cam_data = bpy.data.cameras.new("FrontCam")
cam_obj = bpy.data.objects.new("FrontCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Camera looking at center from front (-Y)
cam_dist = size * 1.8
cam_obj.location = (center.x, center.y - cam_dist, center.z)
cam_obj.rotation_euler = (1.5708, 0, 0)
cam_data.clip_start = 0.01
cam_data.clip_end = 100.0

# Add 3-point lights
def add_sun(name, angles, energy):
    sd = bpy.data.lights.new(name, type='SUN')
    sd.energy = energy
    so = bpy.data.objects.new(name, sd)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = angles

add_sun("Key", (0.8, -0.4, 0.6), 3.0)
add_sun("Fill", (0.8, 0.4, -2.5), 1.5)
add_sun("Rim", (-0.8, 0.0, 0.0), 1.8)

out_png = ROOT / "renders/swoop/swoop_static_pose_framed.png"
bpy.context.scene.render.filepath = str(out_png)
bpy.context.scene.render.resolution_x = 1080
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered framed Static Pose to: {out_png}")
