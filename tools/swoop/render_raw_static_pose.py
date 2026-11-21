import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Matrix
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

swoop_mesh = bpy.data.objects.get("Swoop.001")
sym_ab = bpy.data.objects.get("Symbol_AB")

# Remove all modifiers from swoop_mesh
swoop_mesh.modifiers.clear()
sym_ab.modifiers.clear()

# Clear parent
swoop_mesh.parent = None
sym_ab.parent = None
swoop_mesh.matrix_world = Matrix.Identity(4)
sym_ab.matrix_world = Matrix.Identity(4)

# Remove everything else
for o in list(bpy.data.objects):
    if o not in [swoop_mesh, sym_ab]:
        bpy.data.objects.remove(o, do_unlink=True)

# Join sym into swoop
bpy.ops.object.select_all(action='DESELECT')
swoop_mesh.select_set(True)
sym_ab.select_set(True)
bpy.context.view_layer.objects.active = swoop_mesh
bpy.ops.object.join()

# Now inspect raw mesh bounds
vs = [v.co for v in swoop_mesh.data.vertices]
min_x, max_x = min(v.x for v in vs), max(v.x for v in vs)
min_y, max_y = min(v.y for v in vs), max(v.y for v in vs)
min_z, max_z = min(v.z for v in vs), max(v.z for v in vs)
print(f"RAW STATIC POSE BOUNDS:")
print(f"  X: [{min_x:.3f}, {max_x:.3f}] span={max_x - min_x:.3f}")
print(f"  Y: [{min_y:.3f}, {max_y:.3f}] span={max_y - min_y:.3f}")
print(f"  Z: [{min_z:.3f}, {max_z:.3f}] span={max_z - min_z:.3f}")

# Center and scale to 11.40m height, grounded at Z=0
scale = 11.40 / (max_z - min_z)
swoop_mesh.scale = Vector((scale, scale, scale))
swoop_mesh.location = Vector((-(min_x + max_x)*scale/2, -(min_y + max_y)*scale/2, -min_z*scale))
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Add camera looking from -Y (front) towards (0, 0, 5.7)
cam_data = bpy.data.cameras.new("FrontCam")
cam_obj = bpy.data.objects.new("FrontCam", cam_data)
bpy.context.scene.collection.objects.link(cam_obj)
bpy.context.scene.camera = cam_obj

cam_obj.location = (0.0, -18.0, 5.7)
cam_obj.rotation_euler = (1.5708, 0, 0)
cam_data.lens = 45.0
cam_data.clip_start = 0.1
cam_data.clip_end = 100.0

# Add lighting
def add_light(name, pos, energy):
    ld = bpy.data.lights.new(name, type='POINT')
    ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(lo)
    lo.location = pos

add_light("Key", (-5.0, -12.0, 9.0), 5000.0)
add_light("Fill", (5.0, -10.0, 6.0), 2500.0)
add_light("Rim", (0.0, 8.0, 10.0), 3000.0)

# Add material with texture
mat = bpy.data.materials.new("Swoop_Mat")
mat.use_nodes = True
bsdf = mat.node_tree.nodes.get("Principled BSDF")
tex_img = bpy.data.images.load(str(ROOT / "3rd-party-models/swoop/02_textures/cha_swoop_main_Diffuse.png"))
tex_node = mat.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = tex_img
mat.node_tree.links.new(tex_node.outputs["Color"], bsdf.inputs["Base Color"])

swoop_mesh.data.materials.clear()
swoop_mesh.data.materials.append(mat)

out_png = ROOT / "renders/swoop/swoop_raw_static_pose_render.png"
bpy.context.scene.render.filepath = str(out_png)
bpy.context.scene.render.resolution_x = 1080
bpy.context.scene.render.resolution_y = 1080
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered raw Static Pose to: {out_png}")
