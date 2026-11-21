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

# Remove unwanted
for o in list(bpy.data.objects):
    if o.name in ["Shadow", "Swoop_Weapon", "Symbol_DC"]:
        bpy.data.objects.remove(o, do_unlink=True)

arm = bpy.data.objects.get("Bip001")
swoop_mesh = bpy.data.objects.get("Swoop.001")
sym_ab = bpy.data.objects.get("Symbol_AB")

# Clear action on armature so it is in pure REST POSE
if arm:
    arm.animation_data_clear()
    arm.data.pose_position = 'REST'

bpy.context.view_layer.update()

# Bake rest pose mesh
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_swoop = swoop_mesh.evaluated_get(depsgraph)
mesh_data = bpy.data.meshes.new_from_object(eval_swoop)
new_swoop = bpy.data.objects.new("Swoop_Static", mesh_data)
new_swoop.matrix_world = swoop_mesh.matrix_world.copy()
bpy.context.scene.collection.objects.link(new_swoop)

# Also bake Symbol_AB
eval_sym = sym_ab.evaluated_get(depsgraph)
sym_data = bpy.data.meshes.new_from_object(eval_sym)
new_sym = bpy.data.objects.new("Symbol_AB_Static", sym_data)
new_sym.matrix_world = sym_ab.matrix_world.copy()
bpy.context.scene.collection.objects.link(new_sym)

# Remove all old objects
for o in list(bpy.data.objects):
    if o not in [new_swoop, new_sym]:
        bpy.data.objects.remove(o, do_unlink=True)

# Apply matrix_world to vertices so coords are purely in world space
for obj in [new_swoop, new_sym]:
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)

# Join sym into swoop
bpy.ops.object.select_all(action='DESELECT')
new_swoop.select_set(True)
new_sym.select_set(True)
bpy.context.view_layer.objects.active = new_swoop
bpy.ops.object.join()

# Inspect bounds
all_verts = [v.co for v in new_swoop.data.vertices]
xs = [v.x for v in all_verts]
ys = [v.y for v in all_verts]
zs = [v.z for v in all_verts]
min_x, max_x = min(xs), max(xs)
min_y, max_y = min(ys), max(ys)
min_z, max_z = min(zs), max(zs)
print(f"BAKED REST POSE BOUNDS (World):")
print(f"  X: [{min_x:+.4f}, {max_x:+.4f}] span={max_x - min_x:.4f}")
print(f"  Y: [{min_y:+.4f}, {max_y:+.4f}] span={max_y - min_y:.4f}")
print(f"  Z: [{min_z:+.4f}, {max_z:+.4f}] span={max_z - min_z:.4f}")

# Determine height axis
# In world space after FBX import:
# Let's see what the vertices look like
print(f"Spans: {spans}")

# Let's add camera and lights to render from +Y, -Y, +Z, -Z to see which side is front
# First ground at Z=0 and scale so height = 11.4m
# If Z is height:
scale_fac = 11.40 / (max_z - min_z)
new_swoop.scale = Vector((scale_fac, scale_fac, scale_fac))
new_swoop.location = Vector((-(min_x + max_x)*scale_fac/2, -min_y*scale_fac, -min_z*scale_fac))
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

v2 = [v.co for v in new_swoop.data.vertices]
print(f"SCALED BOUNDS: X=[{min(v.x for v in v2):.2f}, {max(v.x for v in v2):.2f}], Y=[{min(v.y for v in v2):.2f}, {max(v.y for v in v2):.2f}], Z=[{min(v.z for v in v2):.2f}, {max(v.z for v in v2):.2f}]")

cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Camera looking at center (Z=5.7m) from -Y (front)
cam_obj.location = (0.0, -18.0, 5.7)
cam_obj.rotation_euler = (1.5708, 0, 0)
cam_data.clip_start = 0.1
cam_data.clip_end = 100.0

# 3-point lighting
def add_sun(name, angles, energy):
    sd = bpy.data.lights.new(name, type='SUN')
    sd.energy = energy
    so = bpy.data.objects.new(name, sd)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = angles

add_sun("Key", (0.8, -0.4, 0.6), 3.0)
add_sun("Fill", (0.8, 0.4, -2.5), 1.5)
add_sun("Rim", (-0.8, 0.0, 0.0), 1.8)

out_png = ROOT / "renders/swoop/swoop_static_pose_verified.png"
bpy.context.scene.render.filepath = str(out_png)
bpy.context.scene.render.resolution_x = 1080
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered verified Static Pose to: {out_png}")

