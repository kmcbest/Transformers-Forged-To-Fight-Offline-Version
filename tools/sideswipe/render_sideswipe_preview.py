import bpy
import sys
import os
import math
from mathutils import Vector

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

robot_fbx_path = sys.argv[-2]
car_fbx_path = sys.argv[-1]
scratch_dir = os.path.dirname(robot_fbx_path)
tex_dir = os.path.join(scratch_dir, "textures")

def setup_render_settings():
    bpy.context.scene.render.engine = 'BLENDER_EEVEE'
    bpy.context.scene.render.resolution_x = 1280
    bpy.context.scene.render.resolution_y = 1024
    bpy.context.scene.eevee.use_gtao = True
    bpy.context.scene.eevee.use_bloom = True
    
    # World background
    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.15, 0.16, 0.18, 1.0)
        bg.inputs[1].default_value = 1.0

def frame_camera_to_objects(cam_obj, objects):
    min_co = Vector((float('inf'), float('inf'), float('inf')))
    max_co = Vector((float('-inf'), float('-inf'), float('-inf')))
    
    for obj in objects:
        if obj.type == 'MESH':
            for corner in obj.bound_box:
                world_co = obj.matrix_world @ Vector(corner)
                for i in range(3):
                    min_co[i] = min(min_co[i], world_co[i])
                    max_co[i] = max(max_co[i], world_co[i])
                    
    center = (min_co + max_co) / 2.0
    dim = max_co - min_co
    max_dim = max(dim.x, dim.y, dim.z)
    
    cam_dist = max_dim * 1.8
    cam_obj.location = center + Vector((0, -cam_dist, max_dim * 0.2))
    
    direction = center - cam_obj.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam_obj.rotation_euler = rot_quat.to_euler()
    return center, max_dim

def render_robot(fbx_path, out_png):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup_render_settings()
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun1 = bpy.context.active_object
    sun1.data.energy = 4.0
    
    bpy.ops.object.light_add(type='SUN', location=(-5, 5, 5))
    sun2 = bpy.context.active_object
    sun2.data.energy = 2.0
    
    diffuse_path = os.path.join(tex_dir, "Body_Diffuse.png")
    normal_path = os.path.join(tex_dir, "Body_Normal.png")
    spec_path = os.path.join(tex_dir, "Body_Specular.png")
    
    for mat in bpy.data.materials:
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        if not bsdf:
            continue
            
        if mat.name == "SideSwipe":
            if os.path.exists(diffuse_path):
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.image = bpy.data.images.load(diffuse_path)
                links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
            if os.path.exists(spec_path):
                s_node = nodes.new('ShaderNodeTexImage')
                s_node.image = bpy.data.images.load(spec_path)
                links.new(s_node.outputs['Color'], bsdf.inputs['Roughness'])
            if os.path.exists(normal_path):
                n_node = nodes.new('ShaderNodeTexImage')
                n_node.image = bpy.data.images.load(normal_path)
                n_node.image.colorspace_settings.name = 'Non-Color'
                norm_map = nodes.new('ShaderNodeNormalMap')
                links.new(n_node.outputs['Color'], norm_map.inputs['Color'])
                links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])
        elif mat.name == "Lights":
            bsdf.inputs['Emission'].default_value = (0.1, 0.6, 1.0, 1.0)
            bsdf.inputs['Emission Strength'].default_value = 5.0

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    
    mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    center, max_dim = frame_camera_to_objects(cam, mesh_objs)
    
    bpy.context.scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    print(f"Rendered robot preview: {out_png}")

def render_car(fbx_path, out_png):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    setup_render_settings()
    bpy.ops.import_scene.fbx(filepath=fbx_path)
    
    bpy.ops.object.light_add(type='SUN', location=(5, -5, 10))
    sun1 = bpy.context.active_object
    sun1.data.energy = 4.0
    
    bpy.ops.object.light_add(type='SUN', location=(-5, 5, 5))
    sun2 = bpy.context.active_object
    sun2.data.energy = 2.0
    
    mat_tex_map = {
        'Car': ('Car_Diffuse.png', 'Car_Normal.png', 'Car_Specular.png'),
        'Int': ('CarInt_Diffuse.png', 'CarInt_Normal.png', 'CarInt_Specular.png'),
        'Wheels': ('Wheel_Diffuse.png', 'Wheel_Normal.png', 'Wheel_Specular.png'),
    }
    
    for mat in bpy.data.materials:
        mat.use_nodes = True
        nodes = mat.node_tree.nodes
        links = mat.node_tree.links
        bsdf = nodes.get("Principled BSDF")
        if not bsdf:
            continue
            
        if mat.name in mat_tex_map:
            d_file, n_file, s_file = mat_tex_map[mat.name]
            d_path = os.path.join(tex_dir, d_file)
            n_path = os.path.join(tex_dir, n_file)
            s_path = os.path.join(tex_dir, s_file)
            
            if os.path.exists(d_path):
                tex_node = nodes.new('ShaderNodeTexImage')
                tex_node.image = bpy.data.images.load(d_path)
                links.new(tex_node.outputs['Color'], bsdf.inputs['Base Color'])
            if os.path.exists(s_path):
                s_node = nodes.new('ShaderNodeTexImage')
                s_node.image = bpy.data.images.load(s_path)
                links.new(s_node.outputs['Color'], bsdf.inputs['Roughness'])
            if os.path.exists(n_path):
                n_node = nodes.new('ShaderNodeTexImage')
                n_node.image = bpy.data.images.load(n_path)
                n_node.image.colorspace_settings.name = 'Non-Color'
                norm_map = nodes.new('ShaderNodeNormalMap')
                links.new(n_node.outputs['Color'], norm_map.inputs['Color'])
                links.new(norm_map.outputs['Normal'], bsdf.inputs['Normal'])
        elif mat.name == 'Glass':
            bsdf.inputs['Base Color'].default_value = (0.1, 0.15, 0.2, 1.0)
            bsdf.inputs['Roughness'].default_value = 0.05

    bpy.ops.object.camera_add()
    cam = bpy.context.active_object
    bpy.context.scene.camera = cam
    
    mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    center, max_dim = frame_camera_to_objects(cam, mesh_objs)
    
    cam_dist = max_dim * 1.8
    cam.location = center + Vector((cam_dist * 0.7, -cam_dist * 0.7, max_dim * 0.6))
    direction = center - cam.location
    rot_quat = direction.to_track_quat('-Z', 'Y')
    cam.rotation_euler = rot_quat.to_euler()
    
    bpy.context.scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)
    print(f"Rendered car preview: {out_png}")

render_robot(robot_fbx_path, os.path.join(scratch_dir, "sideswipe_robot_preview.png"))
render_car(car_fbx_path, os.path.join(scratch_dir, "sideswipe_car_preview.png"))
