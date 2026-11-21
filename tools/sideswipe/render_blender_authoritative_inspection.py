import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import math
from mathutils import Vector
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
ALIGNED_BLEND = ROOT / "3rd-party-models" / "Sideswipe" / "01_aligned_mesh" / "sideswipe_robot_aligned.blend"
DONOR_OBJ = ROOT / "3rd-party-models" / "Sideswipe" / "00_donor_reference" / "cha_barricade_cin_dotm_00_robot.obj"
BARR_TEX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Sideswipe" / "Barricade"
RENDERS_DIR = ROOT / "renders" / "sideswipe"

bpy.ops.wm.open_mainfile(filepath=str(ALIGNED_BLEND))

arm = bpy.data.objects.get("ARM_Sideswipe_Robot")
robot = bpy.data.objects.get("cha_sideswipe_main")

# Import Barricade Donor Reference OBJ
bpy.ops.wm.obj_import(filepath=str(DONOR_OBJ))
barr_ref = bpy.context.selected_objects[0]
barr_ref.name = "Barricade_Official_Reference"

mat_barr = bpy.data.materials.new("M_Barricade_Donor")
mat_barr.use_nodes = True
nt_b = mat_barr.node_tree
nt_b.nodes.clear()
out_b = nt_b.nodes.new("ShaderNodeOutputMaterial")
bsdf_b = nt_b.nodes.new("ShaderNodeBsdfPrincipled")
nt_b.links.new(bsdf_b.outputs["BSDF"], out_b.inputs["Surface"])
tb_diff = nt_b.nodes.new("ShaderNodeTexImage")
tb_diff_path = BARR_TEX / "tex_cha_barricade_cin_dotm_main_a.png"
if tb_diff_path.exists():
    tb_diff.image = bpy.data.images.load(str(tb_diff_path))
    nt_b.links.new(tb_diff.outputs["Color"], bsdf_b.inputs["Base Color"])
bsdf_b.inputs["Roughness"].default_value = 0.4
bsdf_b.inputs["Metallic"].default_value = 0.5
barr_ref.data.materials.clear()
barr_ref.data.materials.append(mat_barr)

barr_ref.location = Vector((-3.8, 0.0, 0.0))
arm.location = Vector((3.8, 0.0, 0.0))
bpy.context.view_layer.update()

scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.render.resolution_x = 1920
scene.render.resolution_y = 1080
scene.eevee.use_gtao = True
scene.eevee.use_bloom = True
scene.eevee.bloom_intensity = 0.08

world = bpy.data.worlds.new("World_Studio")
scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.08, 0.09, 0.11, 1.0)
    bg.inputs[1].default_value = 0.7

for o in list(scene.collection.objects):
    if o.type == 'LIGHT' or o.type == 'CAMERA':
        bpy.data.objects.remove(o, do_unlink=True)

def add_light(name, ltype, pos, energy, color):
    ld = bpy.data.lights.new(name, type=ltype)
    ld.energy = energy
    ld.color = color
    lo = bpy.data.objects.new(name, ld)
    lo.location = pos
    scene.collection.objects.link(lo)
    return lo

add_light("Key_Front", "POINT", (4.0, -16.0, 10.0), 3800, (1.0, 0.98, 0.95))
add_light("Fill_Front", "POINT", (-6.0, -14.0, 7.0), 2200, (0.85, 0.92, 1.0))
add_light("Rim_Back", "POINT", (0.0, 14.0, 11.0), 3200, (0.95, 0.95, 1.0))

cam_d = bpy.data.cameras.new("RenderCam")
cam_d.lens = 38
cam = bpy.data.objects.new("RenderCam", cam_d)
scene.collection.objects.link(cam)
scene.camera = cam

# Shot 3: Dynamic 3/4 Front Full Body Perspective of Sideswipe
ss_center = Vector((3.8, 0.0, 5.4))
cam.location = Vector((3.8 - 7.5, -18.5, 6.2))
dir_vec = ss_center - cam.location
cam.rotation_euler = dir_vec.to_track_quat("-Z", "Y").to_euler()
out_path = RENDERS_DIR / "blender_03_sideswipe_34_front.png"
scene.render.filepath = str(out_path)
bpy.ops.render.render(write_still=True)
print(f"[✓] Re-rendered Shot 3: {out_path}")
