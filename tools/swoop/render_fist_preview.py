import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Quaternion, Vector
from pathlib import Path

fbx_src = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx")
out_img = Path(r"E:\Agent\TFTF-blender\renders\swoop\debug_curled_hand_preview.png")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_src))

arm = bpy.data.objects.get("Bip001")
swoop_mesh = bpy.data.objects.get("Swoop.001")

for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow", "Swoop_Weapon", "Symbol_AB"]:
        bpy.data.objects.remove(o, do_unlink=True)

# Extract finger local rotations from idle01
act_idle = bpy.data.actions.get("Bip001|idle01|Base Layer")
arm.animation_data.action = act_idle
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

finger_rotations = {}
for pb in arm.pose.bones:
    if "finger" in pb.name.lower():
        finger_rotations[pb.name] = pb.rotation_quaternion.copy()

arm.animation_data_clear()
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

for bname, rot in finger_rotations.items():
    pb = arm.pose.bones.get(bname)
    if pb:
        pb.rotation_mode = 'QUATERNION'
        pb.rotation_quaternion = rot

bpy.context.view_layer.update()

# Bake mesh with curled fingers
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop_mesh.evaluated_get(depsgraph)
eval_mesh = bpy.data.meshes.new_from_object(eval_obj)

baked_swoop = bpy.data.objects.new("cha_swoop_preview", eval_mesh)
bpy.context.scene.collection.objects.link(baked_swoop)
baked_swoop.matrix_world = eval_obj.matrix_world

bpy.data.objects.remove(arm, do_unlink=True)
bpy.data.objects.remove(swoop_mesh, do_unlink=True)

# Find LeftHand vertices (X > 0.3, Z in [-0.2, 0.4])
lh_verts = [v.co for v in baked_swoop.data.vertices if v.co.x > 0.4 and -0.2 < v.co.z < 0.4]
cen = sum(lh_verts, Vector((0,0,0))) / len(lh_verts)
print("Left hand center:", cen)

cam_data = bpy.data.cameras.new("HandCam")
cam_data.lens = 75
cam_obj = bpy.data.objects.new("HandCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = cen + Vector((0.2, -0.45, 0.05))
dir_vec = cen - cam_obj.location
cam_obj.rotation_euler = dir_vec.to_track_quat('-Z', 'Y').to_euler()

light_data = bpy.data.lights.new(name="Light", type='POINT')
light_data.energy = 50.0
light_obj = bpy.data.objects.new(name="Light", object_data=light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = cam_obj.location + Vector((0, 0, 0.2))

bpy.context.scene.render.resolution_x = 800
bpy.context.scene.render.resolution_y = 600
bpy.context.scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print("Saved preview to", out_img)
