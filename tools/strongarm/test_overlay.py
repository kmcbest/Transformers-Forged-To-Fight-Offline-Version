import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import numpy as np
from pathlib import Path

fbx_path = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")
prowl_obj = Path(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_ref.obj")
out_img = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\strongarm_prowl_overlay.png")

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Prowl Reference (Ghost)
# Prowl was exported from Unity (Y up, Z fwd).
# When importing OBJ with Y up, Z fwd:
bpy.ops.wm.obj_import(filepath=str(prowl_obj))
prowl = bpy.data.objects[0]
prowl.name = "Prowl_Ref"
mat_p = bpy.data.materials.new("Mat_Prowl")
mat_p.use_nodes = True
bsdf_p = mat_p.node_tree.nodes.get("Principled BSDF")
bsdf_p.inputs["Base Color"].default_value = (0.8, 0.8, 0.8, 1.0)
prowl.data.materials.clear()
prowl.data.materials.append(mat_p)

# In prowl_ref.obj, Y was height, Z was depth!
# In Blender, rotate Prowl by 90 around X so Z is height:
prowl.rotation_euler = (1.5707963, 0, 0)
bpy.ops.object.select_all(action='DESELECT')
prowl.select_set(True)
bpy.context.view_layer.objects.active = prowl
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
prowl.location.x = -3.5

# 2. Import Strongarm FBX
bpy.ops.import_scene.fbx(filepath=str(fbx_path))
orig_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH' and o != prowl]

# Remove battle masks
for m in list(mesh_objs):
    if m.name in ["bot:mask_geo", "bot:faceMaskOn_jaw_geo"]:
        bpy.data.objects.remove(m, do_unlink=True)
        mesh_objs.remove(m)

# Apply and clear transforms
for m in mesh_objs:
    bpy.ops.object.select_all(action='DESELECT')
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    for mod in list(m.modifiers):
        if mod.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    bpy.ops.object.parent_clear(type='CLEAR_KEEP_TRANSFORM')

bpy.data.objects.remove(orig_arm, do_unlink=True)

# Join Strongarm into one mesh
bpy.ops.object.select_all(action='DESELECT')
for m in mesh_objs:
    m.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]
bpy.ops.object.join()
sa_mesh = bpy.context.view_layer.objects.active
sa_mesh.name = "Strongarm_Aligned"

# Ground to Z = 0 before scaling
min_z = min(v.co.z for v in sa_mesh.data.vertices)
max_z = max(v.co.z for v in sa_mesh.data.vertices)
raw_h = max_z - min_z
scale_s = 9.304 / raw_h
print(f"Raw Strongarm height in Blender = {raw_h:.4f}m. Scale = {scale_s:.4f}")

sa_mesh.scale = (-scale_s, scale_s, scale_s)
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Ground to Z = 0
min_z2 = min(v.co.z for v in sa_mesh.data.vertices)
for v in sa_mesh.data.vertices:
    v.co.z -= min_z2

# Flip normals because of negative X scale
bpy.ops.object.mode_set(mode='EDIT')
bpy.ops.mesh.select_all(action='SELECT')
bpy.ops.mesh.flip_normals()
bpy.ops.object.mode_set(mode='OBJECT')

sa_mesh.location.x = 3.5

# Setup material with texture
mat_sa = bpy.data.materials.new("Mat_SA")
mat_sa.use_nodes = True
bsdf_sa = mat_sa.node_tree.nodes.get("Principled BSDF")
bsdf_sa.inputs["Base Color"].default_value = (0.2, 0.5, 0.9, 1.0)
sa_mesh.data.materials.clear()
sa_mesh.data.materials.append(mat_sa)

# Setup Camera in Blender:
# Position: (0, -18.0, 4.65)
# Rotation: (90 deg, 0, 0) -> (1.5707963, 0, 0)
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj
cam_obj.location = (0.0, -18.0, 4.65)
cam_obj.rotation_euler = (1.5707963, 0.0, 0.0)

# Setup Sun Light
light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.scene.collection.objects.link(light_obj)
light_obj.rotation_euler = (0.7, 0.3, 0)

bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.filepath = str(out_img)
bpy.ops.render.render(write_still=True)
print(f"Rendered overlay test to {out_img}")
