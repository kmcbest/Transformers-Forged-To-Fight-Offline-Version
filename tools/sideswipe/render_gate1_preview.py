import bpy
import sys
import os
import math
from mathutils import Vector

robot_fbx = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe.fbx"
car_fbx = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\01_source\Sideswipe_Car.fbx"
tex_dir = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\02_textures"
out_png = r"E:\Agent\TFTF-blender\3rd-party-models\Sideswipe\gate1_blender_preview.png"

bpy.ops.wm.read_factory_settings(use_empty=True)

# Render settings
bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.eevee.use_gtao = True
bpy.context.scene.eevee.use_bloom = True

# World background
world = bpy.data.worlds.new("World")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.10, 0.11, 0.13, 1.0)

# Import Robot
bpy.ops.import_scene.fbx(filepath=robot_fbx)
for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    bpy.data.objects.remove(a, do_unlink=True)

robot_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
bpy.ops.object.select_all(action='DESELECT')
for o in robot_meshes:
    o.modifiers.clear()
    o.select_set(True)

bpy.context.view_layer.objects.active = robot_meshes[0]
bpy.ops.transform.rotate(value=math.pi, orient_axis='Y')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Scale robot to 10.4m
r_min_z = min(min((o.matrix_world @ v.co).z for v in o.data.vertices) for o in robot_meshes)
r_max_z = max(max((o.matrix_world @ v.co).z for v in o.data.vertices) for o in robot_meshes)
scale_factor = 10.4 / max(r_max_z - r_min_z, 0.01)
bpy.ops.transform.resize(value=(scale_factor, scale_factor, scale_factor))
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Ground robot at Z=0, move to Left: X = -4.5m
r_min_z = min(min((o.matrix_world @ v.co).z for v in o.data.vertices) for o in robot_meshes)
for o in robot_meshes:
    o.location.z -= r_min_z
    o.location.x -= 4.5
bpy.ops.object.select_all(action='DESELECT')
for o in robot_meshes:
    o.select_set(True)
bpy.ops.object.transform_apply(location=True, rotation=False, scale=False)

# Setup Robot Material
r_diff_p = os.path.join(tex_dir, "cha_sideswipe_main_Diffuse.png")
r_norm_p = os.path.join(tex_dir, "cha_sideswipe_main_Normal_unity.png")
r_raoe_p = os.path.join(tex_dir, "cha_sideswipe_main_RAOE.png")
r_emis_p = os.path.join(tex_dir, "cha_sideswipe_main_Emission.png")

r_mat = bpy.data.materials.new("cha_sideswipe_main_mat")
r_mat.use_nodes = True
nodes = r_mat.node_tree.nodes
links = r_mat.node_tree.links
bsdf = nodes.get("Principled BSDF")

t_diff = nodes.new('ShaderNodeTexImage')
t_diff.image = bpy.data.images.load(r_diff_p)
links.new(t_diff.outputs['Color'], bsdf.inputs['Base Color'])

t_norm = nodes.new('ShaderNodeTexImage')
t_norm.image = bpy.data.images.load(r_norm_p)
t_norm.image.colorspace_settings.name = 'Non-Color'
norm_node = nodes.new('ShaderNodeNormalMap')
links.new(t_norm.outputs['Color'], norm_node.inputs['Color'])
links.new(norm_node.outputs['Normal'], bsdf.inputs['Normal'])

t_raoe = nodes.new('ShaderNodeTexImage')
t_raoe.image = bpy.data.images.load(r_raoe_p)
t_raoe.image.colorspace_settings.name = 'Non-Color'
sep_rgb = nodes.new('ShaderNodeSeparateColor')
links.new(t_raoe.outputs['Color'], sep_rgb.inputs['Color'])
links.new(sep_rgb.outputs['Red'], bsdf.inputs['Roughness'])
bsdf.inputs['Metallic'].default_value = 0.65

t_emis = nodes.new('ShaderNodeTexImage')
t_emis.image = bpy.data.images.load(r_emis_p)
links.new(t_emis.outputs['Color'], bsdf.inputs['Emission'])
bsdf.inputs['Emission Strength'].default_value = 4.0

for o in robot_meshes:
    o.data.materials.clear()
    o.data.materials.append(r_mat)

# Import Car
bpy.ops.import_scene.fbx(filepath=car_fbx)
for a in [o for o in bpy.data.objects if o.type == 'ARMATURE']:
    bpy.data.objects.remove(a, do_unlink=True)

all_meshes = [o for o in bpy.data.objects if o.type == 'MESH']
car_meshes = [o for o in all_meshes if o not in robot_meshes]

bpy.ops.object.select_all(action='DESELECT')
for o in car_meshes:
    o.modifiers.clear()
    o.select_set(True)

bpy.context.view_layer.objects.active = car_meshes[0]

# Rotate car so it sits flat horizontally (+Y forward, +Z up)
# In raw FBX, check car dimensions
c_dx = max((o.matrix_world @ v.co).x for o in car_meshes for v in o.data.vertices) - min((o.matrix_world @ v.co).x for o in car_meshes for v in o.data.vertices)
c_dy = max((o.matrix_world @ v.co).y for o in car_meshes for v in o.data.vertices) - min((o.matrix_world @ v.co).y for o in car_meshes for v in o.data.vertices)
c_dz = max((o.matrix_world @ v.co).z for o in car_meshes for v in o.data.vertices) - min((o.matrix_world @ v.co).z for o in car_meshes for v in o.data.vertices)
print(f"Raw Car Dims: dx={c_dx:.3f}, dy={c_dy:.3f}, dz={c_dz:.3f}")

# Longest axis is length of car. In raw FBX, Z was longest (~0.11), Y was height (~0.02), X was width (~0.05).
# Rotate around X by -90 degrees so Z points along Y
bpy.ops.transform.rotate(value=math.radians(-90), orient_axis='X')
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Scale car length to ~10.8m
c_dy = max((o.matrix_world @ v.co).y for o in car_meshes for v in o.data.vertices) - min((o.matrix_world @ v.co).y for o in car_meshes for v in o.data.vertices)
c_scale = 10.8 / max(c_dy, 0.01)
bpy.ops.transform.resize(value=(c_scale, c_scale, c_scale))
bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

# Ground car at Z=0, move to Right: X = 4.8m, Y = 0.5m
c_min_z = min(min((o.matrix_world @ v.co).z for v in o.data.vertices) for o in car_meshes)
for o in car_meshes:
    o.location.z -= c_min_z
    o.location.x += 4.8
    o.location.y += 0.5

# Rotate car 30 degrees around Z for dynamic 3/4 front view
bpy.ops.transform.rotate(value=math.radians(30), orient_axis='Z')
bpy.ops.object.transform_apply(location=True, rotation=True, scale=False)

# Setup Car Material with baked vehicle atlas
v_diff_p = os.path.join(tex_dir, "cha_sideswipe_tform_misc_Diffuse.png")
v_norm_p = os.path.join(tex_dir, "cha_sideswipe_tform_misc_Normal_unity.png")
v_raoe_p = os.path.join(tex_dir, "cha_sideswipe_tform_misc_RAOE.png")
v_emis_p = os.path.join(tex_dir, "cha_sideswipe_tform_misc_Emission.png")

v_mat = bpy.data.materials.new("cha_sideswipe_tform_misc_mat")
v_mat.use_nodes = True
v_nodes = v_mat.node_tree.nodes
v_links = v_mat.node_tree.links
v_bsdf = v_nodes.get("Principled BSDF")

vt_diff = v_nodes.new('ShaderNodeTexImage')
vt_diff.image = bpy.data.images.load(v_diff_p)
v_links.new(vt_diff.outputs['Color'], v_bsdf.inputs['Base Color'])

vt_norm = v_nodes.new('ShaderNodeTexImage')
vt_norm.image = bpy.data.images.load(v_norm_p)
vt_norm.image.colorspace_settings.name = 'Non-Color'
v_norm_node = v_nodes.new('ShaderNodeNormalMap')
v_links.new(vt_norm.outputs['Color'], v_norm_node.inputs['Color'])
v_links.new(v_norm_node.outputs['Normal'], v_bsdf.inputs['Normal'])

vt_raoe = v_nodes.new('ShaderNodeTexImage')
vt_raoe.image = bpy.data.images.load(v_raoe_p)
vt_raoe.image.colorspace_settings.name = 'Non-Color'
v_sep_rgb = v_nodes.new('ShaderNodeSeparateColor')
v_links.new(vt_raoe.outputs['Color'], v_sep_rgb.inputs['Color'])
v_links.new(v_sep_rgb.outputs['Red'], v_bsdf.inputs['Roughness'])
v_bsdf.inputs['Metallic'].default_value = 0.70

vt_emis = v_nodes.new('ShaderNodeTexImage')
vt_emis.image = bpy.data.images.load(v_emis_p)
v_links.new(vt_emis.outputs['Color'], v_bsdf.inputs['Emission'])
v_bsdf.inputs['Emission Strength'].default_value = 3.0

# Remap Car UVs to quadrant boxes:
# Q0 (Car body): U in [0.0, 0.5], V in [0.5, 1.0]
# Q1 (Car interior): U in [0.5, 1.0], V in [0.5, 1.0]
# Q2 (Car wheels): U in [0.0, 0.5], V in [0.0, 0.5]
# Q3 (Glass): U in [0.5, 1.0], V in [0.0, 0.5]
for o in car_meshes:
    uvl = o.data.uv_layers.active
    if uvl:
        mat_name = o.data.materials[0].name if o.data.materials else ""
        if "Car" in mat_name or "Mesh_0" in o.name:
            # Q0
            u_min, u_max = 0.004, 0.496
            v_min, v_max = 0.504, 0.996
        elif "Int" in mat_name or "Mesh_1" in o.name:
            # Q1
            u_min, u_max = 0.504, 0.996
            v_min, v_max = 0.504, 0.996
        elif "Wheels" in mat_name or any(k in o.name for k in ["Mesh_2", "Mesh_3", "Mesh_4"]):
            # Q2
            u_min, u_max = 0.004, 0.496
            v_min, v_max = 0.004, 0.496
        else:
            # Q3
            u_min, u_max = 0.504, 0.996
            v_min, v_max = 0.004, 0.496
            
        for loop in uvl.data:
            loop.uv.x = u_min + loop.uv.x * (u_max - u_min)
            loop.uv.y = v_min + loop.uv.y * (v_max - v_min)
            
    o.data.materials.clear()
    o.data.materials.append(v_mat)

# Add Ground Plane
bpy.ops.mesh.primitive_plane_add(size=60, location=(0, 0, 0))
ground = bpy.context.active_object
g_mat = bpy.data.materials.new("Ground_Mat")
g_mat.use_nodes = True
g_bsdf = g_mat.node_tree.nodes.get("Principled BSDF")
g_bsdf.inputs['Base Color'].default_value = (0.06, 0.07, 0.08, 1.0)
g_bsdf.inputs['Roughness'].default_value = 0.35
ground.data.materials.append(g_mat)

# Lighting
bpy.ops.object.light_add(type='SUN', location=(12, -15, 20))
sun1 = bpy.context.active_object
sun1.data.energy = 4.5
sun1.data.color = (1.0, 0.98, 0.95)

bpy.ops.object.light_add(type='SUN', location=(-15, 12, 10))
sun2 = bpy.context.active_object
sun2.data.energy = 2.2
sun2.data.color = (0.6, 0.75, 1.0)

# Camera framing both Robot (10.4m tall) and Car (10.8m long)
bpy.ops.object.camera_add(location=(0, -28, 7.5), rotation=(math.radians(80), 0, 0))
cam = bpy.context.active_object
bpy.context.scene.camera = cam

bpy.context.scene.render.filepath = out_png
bpy.ops.render.render(write_still=True)
print(f"Rendered corrected Gate 1 preview to: {out_png}")
