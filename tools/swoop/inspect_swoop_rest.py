import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = bpy.data.objects.get("Bip001")
swoop_mesh = bpy.data.objects.get("Swoop.001")

print(f"Armature animation data: {arm.animation_data}")
# Clear action
arm.animation_data_clear()
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

# Inspect vertices in REST pose
bpy.context.view_layer.objects.active = swoop_mesh
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop_mesh.evaluated_get(depsgraph)
eval_mesh = eval_obj.to_mesh()

verts = [v.co for v in eval_mesh.vertices]
xs = [v.x for v in verts]
ys = [v.y for v in verts]
zs = [v.z for v in verts]

print(f"\nREST POSE VERTEX BOUNDS:")
print(f"  X: [{min(xs):.3f}, {max(xs):.3f}] span={max(xs)-min(xs):.3f}")
print(f"  Y: [{min(ys):.3f}, {max(ys):.3f}] span={max(ys)-min(ys):.3f}")
print(f"  Z: [{min(zs):.3f}, {max(zs):.3f}] span={max(zs)-min(zs):.3f}")

# Check key bones in REST pose
print(f"\nREST POSE BONES (matrix_local):")
for bname in ["Bip001", "Bip001 Pelvis", "Bip001 Spine", "Bip001 Head", "Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand"]:
    b = arm.data.bones.get(bname)
    if b:
        print(f"  {bname}: head={b.head_local} tail={b.tail_local}")

# Let's render a quick snapshot of this REST pose to see what it looks like!
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

# Setup light
light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.rotation_euler = (0.7, 0.2, 0.5)

# Place camera looking at center
cx = (min(xs) + max(xs)) / 2
cy = (min(ys) + max(ys)) / 2
cz = (min(zs) + max(zs)) / 2
cam_obj.location = (cx, cy - max(max(xs)-min(xs), max(zs)-min(zs))*2.0, cz)
cam_obj.rotation_euler = (1.5708, 0, 0)
cam_data.clip_start = 0.001
cam_data.clip_end = 100.0

out_png = ROOT / "renders/swoop/debug_swoop_raw_rest_pose.png"
bpy.context.scene.render.filepath = str(out_png)
bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 800
bpy.ops.render.render(write_still=True)
print(f"\nRendered raw REST pose to: {out_png}")
