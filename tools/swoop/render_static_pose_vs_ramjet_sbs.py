import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector, Matrix

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"
RAMJET_OBJ = ROOT / "3rd-party-models/swoop/01_master/ramjet_official_00.obj"
SWOOP_DIFF = ROOT / "3rd-party-models/swoop/02_textures/cha_swoop_main_Diffuse.png"
RAMJET_DIFF = ROOT / "toolchain/unity_build_project/Assets/Swoop/Ramjet/cha_ramjet_gs_deluxe2008_main_a.png"

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Ramjet Official OBJ
bpy.ops.wm.obj_import(filepath=str(RAMJET_OBJ))
ramjet_mesh = bpy.context.selected_objects[0]
ramjet_mesh.name = "Ramjet_Official_00"
ramjet_mesh.location = Vector((-4.5, 0.0, 0.0))






# 2. Import Swoop FBX and isolate RAW STATIC POSE mesh
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))
swoop_mesh = bpy.data.objects.get("Swoop.001")
sym_ab = bpy.data.objects.get("Symbol_AB")

# Strip all modifiers and parent transforms
swoop_mesh.modifiers.clear()
sym_ab.modifiers.clear()
swoop_mesh.parent = None
sym_ab.parent = None
swoop_mesh.matrix_world = Matrix.Identity(4)
sym_ab.matrix_world = Matrix.Identity(4)

# Delete all other objects from FBX import except ramjet, swoop, sym_ab
for o in list(bpy.data.objects):
    if o not in [ramjet_mesh, swoop_mesh, sym_ab]:
        bpy.data.objects.remove(o, do_unlink=True)

# Join Symbol_AB into Swoop
bpy.ops.object.select_all(action='DESELECT')
swoop_mesh.select_set(True)
sym_ab.select_set(True)
bpy.context.view_layer.objects.active = swoop_mesh
bpy.ops.object.join()

# Inspect and normalize Swoop raw vertices
vs = [v.co for v in swoop_mesh.data.vertices]
min_x, max_x = min(v.x for v in vs), max(v.x for v in vs)
min_y, max_y = min(v.y for v in vs), max(v.y for v in vs)
min_z, max_z = min(v.z for v in vs), max(v.z for v in vs)
print(f"Swoop Raw Bounds: X=[{min_x:.3f}, {max_x:.3f}] Y=[{min_y:.3f}, {max_y:.3f}] Z=[{min_z:.3f}, {max_z:.3f}]")

# Scale and ground Swoop mesh vertices directly
scale = 11.40 / (max_z - min_z)
mat_s_xform = Matrix.Translation(Vector((-(min_x + max_x)*scale/2, -(min_y + max_y)*scale/2, -min_z*scale))) @ Matrix.Scale(scale, 4)
swoop_mesh.data.transform(mat_s_xform)

# Place Swoop at X = +4.5
swoop_mesh.matrix_world = Matrix.Translation(Vector((4.5, 0.0, 0.0)))

# Swoop Material
mat_swoop = bpy.data.materials.new("M_Swoop")
mat_swoop.use_nodes = True
bsdf_s = mat_swoop.node_tree.nodes.get("Principled BSDF")
if SWOOP_DIFF.exists():
    tex_s = mat_swoop.node_tree.nodes.new("ShaderNodeTexImage")
    tex_s.image = bpy.data.images.load(str(SWOOP_DIFF))
    mat_swoop.node_tree.links.new(tex_s.outputs["Color"], bsdf_s.inputs["Base Color"])
bsdf_s.inputs["Roughness"].default_value = 0.35
bsdf_s.inputs["Metallic"].default_value = 0.4
swoop_mesh.data.materials.clear()
swoop_mesh.data.materials.append(mat_swoop)

# Verify alignment metrics
v_ramjet = [ramjet_mesh.matrix_world @ v.co for v in ramjet_mesh.data.vertices]
v_swoop = [swoop_mesh.matrix_world @ v.co for v in swoop_mesh.data.vertices]
r_z_max = max(v.z for v in v_ramjet)
s_z_max = max(v.z for v in v_swoop)
r_z_min = min(v.z for v in v_ramjet)
s_z_min = min(v.z for v in v_swoop)
print(f"Alignment Comparison:")
print(f"  Ramjet Z range: [{r_z_min:.2f}, {r_z_max:.2f}]m (Height = {r_z_max - r_z_min:.2f}m)")
print(f"  Swoop  Z range: [{s_z_min:.2f}, {s_z_max:.2f}]m (Height = {s_z_max - s_z_min:.2f}m)")

# Camera centered at (0, -22, 5.7) looking at (0, 0, 5.7)
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = Vector((0.0, -28.0, 5.7))
cam.rotation_euler = (1.5708, 0, 0)
cam_data.lens = 42.0
cam_data.clip_start = 0.1
cam_data.clip_end = 100.0
bpy.context.scene.camera = cam

# Lighting
def add_sun(name, angles, energy, color=(1, 1, 1)):
    sd = bpy.data.lights.new(name, type='SUN')
    sd.energy = energy
    sd.color = color
    so = bpy.data.objects.new(name, sd)
    bpy.context.scene.collection.objects.link(so)
    so.rotation_euler = angles

add_sun("Key", (0.8, -0.4, 0.4), 4.0, (1.0, 0.98, 0.95))
add_sun("Fill", (0.8, 0.4, -2.5), 2.0, (0.85, 0.92, 1.0))
add_sun("Rim", (-0.8, 0.0, 0.0), 2.5, (1.0, 1.0, 1.0))

out_png = ROOT / "renders/swoop/swoop_static_pose_vs_ramjet_sbs.png"
out_png.parent.mkdir(parents=True, exist_ok=True)
bpy.context.scene.render.filepath = str(out_png)
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Successfully rendered Static Pose Side-by-Side: {out_png}")

# Also render 45-degree angle
cam.location = Vector((-14.0, -25.0, 6.5))
cam.rotation_euler = (1.45, 0.0, -0.52)
out_45 = ROOT / "renders/swoop/swoop_static_pose_vs_ramjet_45.png"
bpy.context.scene.render.filepath = str(out_45)
bpy.ops.render.render(write_still=True)
print(f"[✓] Successfully rendered 45-deg Static Pose Side-by-Side: {out_45}")
