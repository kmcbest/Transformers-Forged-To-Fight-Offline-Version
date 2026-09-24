# -*- coding: utf-8 -*-
import bpy
import mathutils
import math
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Ironhide OBJ
ironhide_obj_path = r"d:\Agent\tftf\tools\demolishor\ironhide_extracted\ironhide.obj"
bpy.ops.wm.obj_import(filepath=ironhide_obj_path)
ironhide = bpy.context.selected_objects[0]
ironhide.name = "Ironhide_Ref"
ironhide.location.x = -6.5

# 2. Import Demolishor Old (Scale 1.85, +0.45 offset, leg narrowed)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)
dem_old = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
dem_old.name = "Demolishor_Old"

for obj in list(bpy.data.objects):
    if obj not in [ironhide, dem_old]:
        bpy.data.objects.remove(obj, do_unlink=True)

dem_old.scale = (1.85, 1.85, 1.85)
bpy.context.view_layer.objects.active = dem_old
bpy.ops.object.transform_apply(scale=True)
dem_old.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)
min_z = min(v.co.z for v in dem_old.data.vertices)
dem_old.location.z -= (min_z - 0.45)
bpy.ops.object.transform_apply(location=True)
for v in dem_old.data.vertices:
    if v.co.z < 4.5:
        t = max(0.0, min(1.0, (4.5 - v.co.z) / 3.5))
        v.co.x *= (1.0 - 0.20 * t)
dem_old.location.x = 0.0

# 3. Import Demolishor New (Scale 1.775, grounded at 0, no leg narrowing)
bpy.ops.import_scene.fbx(filepath=fbx_path)
dem_new = [obj for obj in bpy.data.objects if "RB_DemolishorWeaponArm" in obj.name and obj != dem_old][0]
dem_new.name = "Demolishor_New"

for obj in list(bpy.data.objects):
    if obj not in [ironhide, dem_old, dem_new]:
        bpy.data.objects.remove(obj, do_unlink=True)

dem_new.scale = (1.775, 1.775, 1.775)
bpy.context.view_layer.objects.active = dem_new
bpy.ops.object.transform_apply(scale=True)
dem_new.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)
min_z_new = min(v.co.z for v in dem_new.data.vertices)
dem_new.location.z -= min_z_new
bpy.ops.object.transform_apply(location=True)
dem_new.location.x = 6.5

# Setup solid shading materials without textures for clear silhouette viewing
mat_white = bpy.data.materials.new("White")
mat_white.diffuse_color = (0.9, 0.9, 0.9, 1.0)
mat_red = bpy.data.materials.new("Red")
mat_red.diffuse_color = (0.8, 0.3, 0.3, 1.0)
mat_green = bpy.data.materials.new("Green")
mat_green.diffuse_color = (0.3, 0.8, 0.4, 1.0)

ironhide.data.materials.clear()
ironhide.data.materials.append(mat_white)
dem_old.data.materials.clear()
dem_old.data.materials.append(mat_red)
dem_new.data.materials.clear()
dem_new.data.materials.append(mat_green)

if bpy.context.scene.world is None:
    bpy.context.scene.world = bpy.data.worlds.new("World")
bpy.context.scene.world.color = (0.2, 0.2, 0.25)

# Setup Camera & Light
cam_data = bpy.data.cameras.new("Camera")
cam_obj = bpy.data.objects.new("Camera", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0, -26.0, 5.5)
cam_obj.rotation_euler = (math.radians(90), 0, 0)

light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
light_data.energy = 5.0
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (0, -20, 15)
light_obj.rotation_euler = (math.radians(60), 0, 0)

out_img = r"d:\Agent\tftf\tools\demolishor\posture_comparison_3way.png"
bpy.context.scene.render.filepath = out_img
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered 3-way posture comparison to {out_img}")
