# -*- coding: utf-8 -*-
import sys
import math
from pathlib import Path
import bpy
import mathutils

sys.stdout.reconfigure(encoding='utf-8')

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

# Scale by 1.80
scale_factor = 1.80
mesh.scale = (scale_factor, scale_factor, scale_factor)
bpy.context.view_layer.objects.active = mesh
bpy.ops.object.transform_apply(scale=True)

mesh.rotation_euler = (0, 0, math.radians(90))
bpy.ops.object.transform_apply(rotation=True)

# Ground feet firmly at Z = 0 (no upward stretch!)
min_z = min(v.co.z for v in mesh.data.vertices)
mesh.location.z -= min_z
bpy.ops.object.transform_apply(location=True)

# Find elbow pivot points
l_forearm_vgs = ["L_Arm03_Elbow_XB", "L_ElbowRobo01_XT", "L_ElbowRobo02_XT", "L_Arm04_Hand_XB"]
r_forearm_vgs = ["R_Arm03_Elbow_XB", "R_ElbowRobo01_XT", "R_Arm04_Hand_XB"]

l_elbow_verts = []
for vg in mesh.vertex_groups:
    if "L_Arm03_Elbow" in vg.name:
        for v in mesh.data.vertices:
            for g in v.groups:
                if g.group == vg.index and g.weight > 0.5:
                    l_forearm_verts.append(v)
                    l_elbow_verts.append(v.co)

# Rotate forearms forward around X axis
# In Blender coords: X=Right, Y=Depth (forward is -Y), Z=Up
# Bending elbow forward means rotating around X axis by -20 deg (tilting -Y down / forward)
l_forearm_vg_indices = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Arm03", "L_Arm04", "L_Elbow", "L_Finger"])]
r_forearm_vg_indices = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Arm03", "R_Arm04", "R_Elbow", "R_Finger"])]

# Calculate elbow pivots
l_elbow_verts_co = [v.co for v in mesh.data.vertices for g in v.groups if g.group in l_forearm_vg_indices and v.co.z > 4.5 and v.co.z < 6.0]
r_elbow_verts_co = [v.co for v in mesh.data.vertices for g in v.groups if g.group in r_forearm_vg_indices and v.co.z > 4.5 and v.co.z < 6.0]

l_pivot = sum(l_elbow_verts_co, mathutils.Vector((0, 0, 0))) / len(l_elbow_verts_co) if l_elbow_verts_co else mathutils.Vector((-2.5, -0.3, 5.0))
r_pivot = sum(r_elbow_verts_co, mathutils.Vector((0, 0, 0))) / len(r_elbow_verts_co) if r_elbow_verts_co else mathutils.Vector((2.5, -0.3, 5.0))

print(f"L Elbow pivot: {l_pivot}")
print(f"R Elbow pivot: {r_pivot}")

# Rotate left forearm forward by 22 degrees
rot_mat_l = mathutils.Matrix.Rotation(math.radians(-22.0), 4, 'X')
for v in mesh.data.vertices:
    for g in v.groups:
        if g.group in l_forearm_vg_indices and g.weight > 0.3:
            rel = v.co - l_pivot
            v.co = l_pivot + (rot_mat_l @ rel)
            break

# Rotate right forearm forward by 22 degrees
rot_mat_r = mathutils.Matrix.Rotation(math.radians(-22.0), 4, 'X')
for v in mesh.data.vertices:
    for g in v.groups:
        if g.group in r_forearm_vg_indices and g.weight > 0.3:
            rel = v.co - r_pivot
            v.co = r_pivot + (rot_mat_r @ rel)
            break

# Feet slight outward flare (out-toeing 8 deg)
l_foot_vg_indices = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["L_Leg03", "L_Leg04"])]
r_foot_vg_indices = [vg.index for vg in mesh.vertex_groups if any(k in vg.name for k in ["R_Leg03", "R_Leg04"])]

l_ankle_verts = [v.co for v in mesh.data.vertices for g in v.groups if g.group in l_foot_vg_indices]
r_ankle_verts = [v.co for v in mesh.data.vertices for g in v.groups if g.group in r_foot_vg_indices]
l_foot_pivot = sum(l_ankle_verts, mathutils.Vector((0, 0, 0))) / len(l_ankle_verts)
r_foot_pivot = sum(r_ankle_verts, mathutils.Vector((0, 0, 0))) / len(r_ankle_verts)

rot_foot_l = mathutils.Matrix.Rotation(math.radians(10.0), 4, 'Z')
for v in mesh.data.vertices:
    for g in v.groups:
        if g.group in l_foot_vg_indices and g.weight > 0.3:
            rel = v.co - l_foot_pivot
            v.co = l_foot_pivot + (rot_foot_l @ rel)
            break

rot_foot_r = mathutils.Matrix.Rotation(math.radians(-10.0), 4, 'Z')
for v in mesh.data.vertices:
    for g in v.groups:
        if g.group in r_foot_vg_indices and g.weight > 0.3:
            rel = v.co - r_foot_pivot
            v.co = r_foot_pivot + (rot_foot_r @ rel)
            break

# Camera setup for rendering full-body test
cam_data = bpy.data.cameras.new("Cam")
cam_obj = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = (0, -12, 5)
cam_obj.rotation_euler = (math.radians(85), 0, 0)

light_data = bpy.data.lights.new("Sun", type='SUN')
light_obj = bpy.data.objects.new("Sun", light_data)
light_data.energy = 3.5
bpy.context.scene.collection.objects.link(light_obj)
light_obj.location = (5, -8, 10)

out_img = r"d:\Agent\tftf\tools\demolishor\posture_test.png"
bpy.context.scene.render.filepath = out_img
bpy.context.scene.render.resolution_x = 720
bpy.context.scene.render.resolution_y = 960
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered posture preview to {out_img}")
