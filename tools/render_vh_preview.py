# -*- coding: utf-8 -*-
import sys
from pathlib import Path
import bpy
import mathutils

sys.stdout.reconfigure(encoding='utf-8')

fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

# Hide robot objects, keep only vehicle
for obj in bpy.data.objects:
    if "VH" in obj.name:
        obj.hide_render = False
        obj.hide_viewport = False
    else:
        obj.hide_render = True
        obj.hide_viewport = True

vh_mesh = bpy.data.objects.get("VH_Demolishor_SKEL.mo.dmx")
if vh_mesh:
    # Set up camera and light
    cam_data = bpy.data.cameras.new("Cam")
    cam_obj = bpy.data.objects.new("Cam", cam_data)
    bpy.context.scene.collection.objects.link(cam_obj)
    bpy.context.scene.camera = cam_obj
    
    # Position camera
    cam_obj.location = (10, -10, 8)
    # Point at center of vh_mesh
    direction = mathutils.Vector((0, 6, 2)) - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    
    # Sun light
    light_data = bpy.data.lights.new("Sun", type='SUN')
    light_obj = bpy.data.objects.new("Sun", light_data)
    light_data.energy = 4.0
    bpy.context.scene.collection.objects.link(light_obj)
    light_obj.location = (5, -5, 10)
    
    out_img = r"d:\Agent\tftf\tools\demolishor\vh_preview.png"
    bpy.context.scene.render.filepath = out_img
    bpy.context.scene.render.resolution_x = 800
    bpy.context.scene.render.resolution_y = 600
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered vehicle preview to {out_img}")
