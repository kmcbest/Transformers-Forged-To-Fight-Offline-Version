import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import os
from pathlib import Path
import math
import bpy
from mathutils import Vector, Matrix, Quaternion, Euler

ROOT = Path("E:/Agent/TFTF-blender")
OUT_DIR = ROOT / "renders/blitzwing"
OUT_DIR.mkdir(parents=True, exist_ok=True)

def setup_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    fbx_path = ROOT / "3rd-party-models/Blitzwing_EW/01_source/H_shandian_G1_M_LOD.fbx"
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))

    mesh_obj = bpy.data.objects['H_shandian_G1_M_Lod']
    arm_obj = bpy.data.objects['floor']

    # Unparent
    bpy.ops.object.select_all(action='DESELECT')
    for o in [mesh_obj, arm_obj]:
        o.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')
    for o in list(bpy.data.objects):
        if o not in [mesh_obj, arm_obj]:
            bpy.data.objects.remove(o, do_unlink=True)

    # Det=+1 alignment: Rz(-90 deg)
    arm_obj.rotation_euler = (0, 0, math.radians(-90))
    mesh_obj.rotation_euler = (0, 0, math.radians(-90))
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.transform_apply(rotation=True)

    # Ground Z=0
    min_z = min(v.co.z for v in mesh_obj.data.vertices)
    mesh_obj.location.z -= min_z
    arm_obj.location.z -= min_z
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Scale
    SCALE = 149.1728
    mesh_obj.scale = (SCALE, SCALE, SCALE)
    arm_obj.scale = (SCALE, SCALE, SCALE)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

    # Modifier
    mesh_obj.modifiers.clear()
    mesh_obj.parent = arm_obj
    arm_mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
    arm_mod.object = arm_obj

    return arm_obj, mesh_obj

def add_camera_and_lights(target_pos, cam_pos):
    # Camera
    cam_data = bpy.data.cameras.new("TestCam")
    cam_obj = bpy.data.objects.new("TestCam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    cam_obj.location = cam_pos
    
    # Point camera at target
    direction = target_pos - cam_pos
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()

    # Sun light
    light_data = bpy.data.lights.new(name="Sun", type='SUN')
    light_data.energy = 3.0
    light_obj = bpy.data.objects.new(name="Sun", object_data=light_data)
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = target_pos + Vector((0, -2, 2))
    light_obj.rotation_euler = (math.radians(45), 0, math.radians(45))

    # Fill light
    fill_data = bpy.data.lights.new(name="Fill", type='SUN')
    fill_data.energy = 1.5
    fill_obj = bpy.data.objects.new(name="Fill", object_data=fill_data)
    bpy.context.scene.collection.objects.link(fill_obj)
    fill_obj.location = target_pos + Vector((2, 2, 1))

    # Render settings
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 600
    bpy.context.scene.render.image_settings.file_format = 'PNG'

# Test variations
for test_name, (curl_axis, curl_deg, thumb_curl) in [
    ("z_neg", ("Z", -70, -45)),
    ("z_pos", ("Z", 70, 45)),
    ("x_neg", ("X", -70, -45)),
    ("x_pos", ("X", 70, 45)),
]:
    arm_obj, mesh_obj = setup_scene()
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='POSE')

    # Apply curls to Left hand fingers 1..4 (Index, Middle, Ring, Pinky)
    for fi in range(1, 5):
        for seg in ["", "1", "2"]:
            bname = f"Bip001 L Finger{fi}{seg}"
            pb = arm_obj.pose.bones.get(bname)
            if pb:
                pb.rotation_mode = 'XYZ'
                e = [0, 0, 0]
                idx = 0 if curl_axis == "X" else (1 if curl_axis == "Y" else 2)
                e[idx] = math.radians(curl_deg * (0.8 if seg == "" else 1.0))
                pb.rotation_euler = Euler(e, 'XYZ')

    # Thumb
    for seg in ["", "1", "2"]:
        bname = f"Bip001 L Finger0{seg}"
        pb = arm_obj.pose.bones.get(bname)
        if pb:
            pb.rotation_mode = 'XYZ'
            e = [0, 0, 0]
            idx = 0 if curl_axis == "X" else (1 if curl_axis == "Y" else 2)
            e[idx] = math.radians(thumb_curl)
            pb.rotation_euler = Euler(e, 'XYZ')

    bpy.context.view_layer.update()

    # Target position is Left Hand
    hand_pos = arm_obj.matrix_world @ arm_obj.pose.bones["Bip001 L Hand"].head
    print(f"Test {test_name}: Hand pos = {hand_pos}")

    add_camera_and_lights(hand_pos + Vector((0, 0, -0.2)), hand_pos + Vector((1.5, -1.8, 0.5)))

    out_path = OUT_DIR / f"test_curl_{test_name}.png"
    bpy.context.scene.render.filepath = str(out_path)
    bpy.ops.render.render(write_still=True)
    print(f"Saved: {out_path}")
