import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parent.parent.parent

bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Import Ramjet official robot OBJ
ramjet_obj_path = ROOT / "3rd-party-models/swoop/01_master/ramjet_official_00.obj"
bpy.ops.wm.obj_import(filepath=str(ramjet_obj_path))
ramjet_mesh = bpy.context.selected_objects[0]
ramjet_mesh.name = "Ramjet_Official_00"
ramjet_mesh.location = Vector((-4.5, 0.0, 0.0))

# 2. Import Swoop prepared robot FBX
swoop_fbx_path = ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"
bpy.ops.import_scene.fbx(filepath=str(swoop_fbx_path))
swoop_arm = [o for o in bpy.context.selected_objects if o.type == 'ARMATURE'][0]
swoop_mesh = [o for o in bpy.context.selected_objects if o.type == 'MESH'][0]
swoop_arm.location = Vector((4.5, 0.0, 0.0))

# Materials
mat_ramjet = bpy.data.materials.new("M_Ramjet_Wire")
mat_ramjet.use_nodes = True
bsdf_r = mat_ramjet.node_tree.nodes.get("Principled BSDF")
bsdf_r.inputs["Base Color"].default_value = (0.3, 0.5, 0.7, 1.0)
ramjet_mesh.data.materials.append(mat_ramjet)

mat_swoop = bpy.data.materials.new("M_Swoop_Textured")
mat_swoop.use_nodes = True
bsdf_s = mat_swoop.node_tree.nodes.get("Principled BSDF")
tex_node = mat_swoop.node_tree.nodes.new("ShaderNodeTexImage")
tex_node.image = bpy.data.images.load(str(ROOT / "3rd-party-models/swoop/02_textures/cha_swoop_main_Diffuse.png"))
mat_swoop.node_tree.links.new(tex_node.outputs["Color"], bsdf_s.inputs["Base Color"])
swoop_mesh.data.materials.clear()
swoop_mesh.data.materials.append(mat_swoop)

# Camera centered at (0, -25, 5.7) looking at (0, 0, 5.7)
cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.scene.collection.objects.link(cam)
cam.location = Vector((0.0, -25.0, 5.7))
cam.rotation_euler = (1.5708, 0, 0)
bpy.context.scene.camera = cam

# Lighting
sun = bpy.data.lights.new("Sun", type='SUN')
sun.energy = 4.0
sun_obj = bpy.data.objects.new("Sun", sun)
bpy.context.scene.collection.objects.link(sun_obj)
sun_obj.rotation_euler = (0.785, 0.5, 0.0)

sun2 = bpy.data.lights.new("Sun2", type='SUN')
sun2.energy = 1.5
sun2_obj = bpy.data.objects.new("Sun2", sun2)
bpy.context.scene.collection.objects.link(sun2_obj)
sun2_obj.rotation_euler = (0.785, -0.5, 3.14159)

out_png = ROOT / "renders/swoop/gate2_blender_robot_sbs.png"
out_png.parent.mkdir(parents=True, exist_ok=True)
bpy.context.scene.render.resolution_x = 1920
bpy.context.scene.render.resolution_y = 1080
bpy.context.scene.render.filepath = str(out_png)
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered Gate 2 Side-by-Side: {out_png}")
