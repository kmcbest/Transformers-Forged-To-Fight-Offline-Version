import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import os
import math
from mathutils import Vector

OUT_DIR = r"e:\Agent\TFTF-blender\tools\vortex\diag\bundle_3d"

def setup_kabam_mat(name, diff_path, raoe_path, em_rgb, overbright=6.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()

    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    bsdf.inputs["Roughness"].default_value = 0.45
    bsdf.inputs["Metallic"].default_value = 0.3

    tex_d = nt.nodes.new("ShaderNodeTexImage")
    tex_d.image = bpy.data.images.load(diff_path)

    tex_r = nt.nodes.new("ShaderNodeTexImage")
    tex_r.image = bpy.data.images.load(raoe_path)
    tex_r.image.colorspace_settings.name = "Non-Color"

    sep = nt.nodes.new("ShaderNodeSeparateColor")
    nt.links.new(tex_r.outputs["Color"], sep.inputs["Color"])

    sq = nt.nodes.new("ShaderNodeMath")
    sq.operation = "MULTIPLY"
    nt.links.new(sep.outputs["Blue"], sq.inputs[0])
    nt.links.new(sep.outputs["Blue"], sq.inputs[1])

    mul_s = nt.nodes.new("ShaderNodeMath")
    mul_s.operation = "MULTIPLY"
    nt.links.new(sq.outputs["Value"], mul_s.inputs[0])
    mul_s.inputs[1].default_value = overbright

    col_em = nt.nodes.new("ShaderNodeCombineColor")
    col_em.inputs["Red"].default_value = em_rgb[0] ** 2
    col_em.inputs["Green"].default_value = em_rgb[1] ** 2
    col_em.inputs["Blue"].default_value = em_rgb[2] ** 2

    nt.links.new(tex_d.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(col_em.outputs["Color"], bsdf.inputs["Emission Color" if "Emission Color" in bsdf.inputs else "Emission"])
    nt.links.new(mul_s.outputs["Value"], bsdf.inputs["Emission Strength"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

def look_at(cam, target):
    direction = Vector(target) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

def render_with_auto_cam(obj_file, mat_fns, view_dir, target_offset, dist_scale, out_png):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.wm.obj_import(filepath=obj_file)
    mesh_obj = [o for o in bpy.context.scene.objects if o.type == "MESH"][0]
    for idx, fn in enumerate(mat_fns):
        m = fn()
        if idx < len(mesh_obj.data.materials):
            mesh_obj.data.materials[idx] = m
        else:
            mesh_obj.data.materials.append(m)

    pts = [mesh_obj.matrix_world @ Vector(v.co) for v in mesh_obj.data.vertices]
    center = sum(pts, Vector((0,0,0))) / len(pts)
    size = max((max(p[i] for p in pts) - min(p[i] for p in pts)) for i in range(3))
    target = center + Vector(target_offset) * size
    cam_pos = target + Vector(view_dir).normalized() * (size * dist_scale)

    world = bpy.data.worlds.new("W")
    bpy.context.scene.world = world
    world.use_nodes = True
    world.node_tree.nodes["Background"].inputs[0].default_value = (0.04, 0.04, 0.06, 1.0)

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 3.0
    sun = bpy.data.objects.new("Sun", sun_data)
    bpy.context.collection.objects.link(sun)
    sun.location = cam_pos
    look_at(sun, target)

    cam_data = bpy.data.cameras.new("Cam")
    cam = bpy.data.objects.new("Cam", cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = cam_pos
    look_at(cam, target)
    bpy.context.scene.camera = cam

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.eevee.use_bloom = True
    scene.eevee.bloom_intensity = 0.06
    scene.render.resolution_x = 960
    scene.render.resolution_y = 720
    scene.render.filepath = out_png
    bpy.ops.render.render(write_still=True)

vh_mats = [
    lambda: setup_kabam_mat("VH_Body",     os.path.join(OUT_DIR, "vh_diff.png"),  os.path.join(OUT_DIR, "vh_raoe.png"),  (0.70, 0.05, 1.0), overbright=10.0),
    lambda: setup_kabam_mat("VH_Emb",      os.path.join(OUT_DIR, "emb_diff.png"), os.path.join(OUT_DIR, "emb_raoe.png"), (0.70, 0.05, 1.0), overbright=10.0),
    lambda: setup_kabam_mat("VH_Interior", os.path.join(OUT_DIR, "int_diff.png"), os.path.join(OUT_DIR, "int_raoe.png"), (0.0, 0.0, 0.0),   overbright=0.0),
]

rob_mats = [
    lambda: setup_kabam_mat("Rob_Body", os.path.join(OUT_DIR, "rob_diff.png"), os.path.join(OUT_DIR, "rob_raoe.png"), (0.72, 0.08, 1.0), overbright=12.0),
    lambda: setup_kabam_mat("Rob_Eyes", os.path.join(OUT_DIR, "rob_diff.png"), os.path.join(OUT_DIR, "rob_raoe.png"), (1.00, 0.85, 0.12), overbright=12.0),
]

render_with_auto_cam(os.path.join(OUT_DIR, "vortex_vh.obj"),  vh_mats,  (-1.0, -0.45, 0.35), (0.0, 0.0, 0.05), 0.78, os.path.join(OUT_DIR, "verify_vh_left.png"))
render_with_auto_cam(os.path.join(OUT_DIR, "vortex_vh.obj"),  vh_mats,  (1.0, -0.45, 0.35),  (0.0, 0.0, 0.05), 0.78, os.path.join(OUT_DIR, "verify_vh_right.png"))
render_with_auto_cam(os.path.join(OUT_DIR, "vortex_rob.obj"), rob_mats, (0.0, -1.0, 0.15),   (0.0, 0.0, 0.25), 0.55, os.path.join(OUT_DIR, "verify_rob_upper.png"))
render_with_auto_cam(os.path.join(OUT_DIR, "vortex_rob.obj"), rob_mats, (0.0, -1.0, 0.10),   (0.0, 0.0, 0.40), 0.30, os.path.join(OUT_DIR, "verify_rob_head.png"))
render_with_auto_cam(os.path.join(OUT_DIR, "vortex_rob.obj"), rob_mats, (0.65, -0.75, 0.15),  (0.0, 0.0, 0.0),  1.15, os.path.join(OUT_DIR, "verify_rob_sword.png"))
