import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)

ROOT = Path(r"E:\Agent\TFTF-blender")
ARTIFACTS_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d")
OUT_IMG = ARTIFACTS_DIR / "vortex_sbs_08_vehicle_mode_hover_corrected.png"

# Setup Scene & Render settings
scene = bpy.context.scene
scene.render.engine = 'BLENDER_EEVEE'
scene.eevee.use_bloom = True
scene.eevee.use_gtao = True
scene.render.resolution_x = 1280
scene.render.resolution_y = 720

# Dark studio background
world = bpy.data.worlds.new("StudioWorld")
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs["Color"].default_value = (0.05, 0.05, 0.06, 1.0)
    bg.inputs["Strength"].default_value = 1.0
scene.world = world

# Lights
sun_data = bpy.data.lights.new(name="KeySun", type='SUN')
sun_data.energy = 4.0
sun_data.color = (1.0, 0.98, 0.95)
sun_obj = bpy.data.objects.new(name="KeySun", object_data=sun_data)
sun_obj.rotation_euler = (math.radians(50), math.radians(20), math.radians(-35))
scene.collection.objects.link(sun_obj)

fill_data = bpy.data.lights.new(name="FillPoint", type='POINT')
fill_data.energy = 800
fill_data.color = (0.75, 0.85, 1.0)
fill_obj = bpy.data.objects.new(name="FillPoint", object_data=fill_data)
fill_obj.location = (0, -15, 10)
scene.collection.objects.link(fill_obj)

# 1. Import Grindor Vehicle OBJ
grindor_obj_path = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Vortex" / "Grindor" / "cha_grindor_cin_rotf_01.obj"
bpy.ops.wm.obj_import(filepath=str(grindor_obj_path))
grindor_objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']

# Material for Grindor
g_mat = bpy.data.materials.new("M_Grindor_Vh")
g_mat.use_nodes = True
g_tex_path = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Vortex" / "Grindor" / "tform_misc_A.png"
if g_tex_path.exists():
    ti = g_mat.node_tree.nodes.new("ShaderNodeTexImage")
    ti.image = bpy.data.images.load(str(g_tex_path))
    g_mat.node_tree.links.new(ti.outputs["Color"], g_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])

for o in grindor_objs:
    o.data.materials.clear()
    o.data.materials.append(g_mat)
    # Position Grindor on the Left: in Unity left was X = 6.0f (or in Blender X = -8.0)
    # In Blender: Unity (X, Y, Z) is (X, Z, Y)
    # Unity Grindor was at center (X=6.0f)
    o.location.x += 8.0

# 2. Import Vortex Transformed Vehicle OBJ
vortex_obj_path = ROOT / "tools" / "vortex" / "cha_vortex_vh_transformed.obj"
bpy.ops.wm.obj_import(filepath=str(vortex_obj_path))
vortex_objs = [o for o in bpy.context.selected_objects if o.type == 'MESH']

# Material for Vortex
v_mat = bpy.data.materials.new("M_Vortex_Vh")
v_mat.use_nodes = True
v_tex_path = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Vortex" / "cha_vortex_vh_a.png"
if v_tex_path.exists():
    ti = v_mat.node_tree.nodes.new("ShaderNodeTexImage")
    ti.image = bpy.data.images.load(str(v_tex_path))
    v_mat.node_tree.links.new(ti.outputs["Color"], v_mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"])

for o in vortex_objs:
    o.data.materials.clear()
    o.data.materials.append(v_mat)
    # Position Vortex on the Right (X = -8.0)
    o.location.x -= 8.0

# 3. Camera Setup: Front-top 3/4 view framing both helicopters
cam_data = bpy.data.cameras.new(name="PreviewCam")
cam_data.lens = 45
cam_obj = bpy.data.objects.new(name="PreviewCam", object_data=cam_data)
# Both helicopters face forward into Unity +Z (Blender +Y).
# Camera in front (looking from Blender -Y towards +Y):
cam_obj.location = (0.0, -22.0, 10.0)
cam_obj.rotation_euler = (math.radians(70), 0, 0)
scene.collection.objects.link(cam_obj)
scene.camera = cam_obj

# Render and save
scene.render.filepath = str(OUT_IMG)
print(f"[*] Rendering side-by-side vehicle comparison to {OUT_IMG}...")
bpy.ops.render.render(write_still=True)
print(f"[✓] Render finished successfully! Image size: {OUT_IMG.stat().st_size} bytes")
