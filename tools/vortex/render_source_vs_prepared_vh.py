import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import zipfile
import tempfile
import os
import math
from mathutils import Vector

OUT_DIR = r"e:\Agent\TFTF-blender\tools\vortex\diag\bundle_3d"
os.makedirs(OUT_DIR, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
with zipfile.ZipFile(r"O:\agent\transformers-fall-of-cybertron-combaticons.zip", "r") as z:
    tmp_dir = tempfile.mkdtemp()
    fbx_name = "source/transformers fall of cybertron convaticons .fbx"
    z.extract(fbx_name, tmp_dir)
    bpy.ops.import_scene.fbx(filepath=os.path.join(tmp_dir, fbx_name))

src = bpy.data.objects.get("VH_Vortex_SKEL.001.dmx")
# Hide everything except VH_Vortex_SKEL.001.dmx
for o in list(bpy.data.objects):
    if o != src:
        o.hide_render = True

def make_tex_mat(name, img_path, tint=(1,1,1)):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(img_path)
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    return mat

# Materials on VH_Vortex_SKEL.001.dmx:
# Mat[0] = TR_FactionLogo_Mat_INST.004
# Mat[1] = VH_VortexBase_MAT -> diag/head_vh_diff.png
# Mat[2] = TR_Test_Mat_INST -> diag/orig_vh_interior_mat.jpg
src.data.materials[0] = make_tex_mat("Src_Logo", os.path.join(OUT_DIR, "emb_diff.png"))
src.data.materials[1] = make_tex_mat("Src_Base", r"e:\Agent\TFTF-blender\tools\vortex\diag\head_vh_diff.png")
src.data.materials[2] = make_tex_mat("Src_Int",  r"e:\Agent\TFTF-blender\tools\vortex\diag\orig_vh_interior_mat.jpg")

pts = [src.matrix_world @ Vector(v.co) for v in src.data.vertices]
center = sum(pts, Vector((0,0,0))) / len(pts)
size = max((max(p[i] for p in pts) - min(p[i] for p in pts)) for i in range(3))
target = center + Vector((0.3, 0.0, 0.2))
# Left side camera facing nose (+X/+Y in source?) Wait in source nose is +X, left side is +Y or -Y!
cam_pos = target + Vector((0.45, -1.0, 0.35)).normalized() * (size * 0.78)

world = bpy.data.worlds.new("W")
bpy.context.scene.world = world
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.04, 0.04, 0.06, 1.0)

sun_data = bpy.data.lights.new("Sun", type="SUN")
sun_data.energy = 3.0
sun = bpy.data.objects.new("Sun", sun_data)
bpy.context.collection.objects.link(sun)
sun.location = cam_pos
sun.rotation_euler = (target - cam_pos).to_track_quat("-Z", "Y").to_euler()

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
cam.location = cam_pos
cam.rotation_euler = (target - cam_pos).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 960
scene.render.resolution_y = 720
scene.render.filepath = os.path.join(OUT_DIR, "verify_SOURCE_vh.png")
bpy.ops.render.render(write_still=True)

# ALSO print UV comparison between Source VH_Vortex_SKEL.001.dmx and Prepared vortex_vh_prepared.fbx!
src_uvs = [(round(src.data.uv_layers.active.data[i].uv.x, 4), round(src.data.uv_layers.active.data[i].uv.y, 4)) for i in range(len(src.data.uv_layers.active.data))]
src_poly_count = len(src.data.polygons)
src_vert_count = len(src.data.vertices)
src_poly_mats = [p.material_index for p in src.data.polygons]

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Vortex\vortex_vh_prepared.fbx")
prep = bpy.data.objects.get("cha_vortex_gs_01")
prep_uvs = [(round(prep.data.uv_layers.active.data[i].uv.x, 4), round(prep.data.uv_layers.active.data[i].uv.y, 4)) for i in range(len(prep.data.uv_layers.active.data))]

print(f"Source polys={src_poly_count}, verts={src_vert_count}, loops={len(src_uvs)}")
print(f"Prepared polys={len(prep.data.polygons)}, verts={len(prep.data.vertices)}, loops={len(prep_uvs)}")
diff_loops = sum(1 for a, b in zip(src_uvs, prep_uvs) if abs(a[0]-b[0]) > 1e-3 or abs(a[1]-b[1]) > 1e-3)
print(f"UV loop mismatches between Source and Prepared: {diff_loops}")
