import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy, math
from mathutils import Vector, Matrix
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
TEX_DIR = WR_DIR / "02_textures"
FBX_DIR = WR_DIR / "03_fbx_exports"
RENDER_DIR = ROOT / "renders" / "wildrider"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)

# Material for WildRider
img_diff = bpy.data.images.load(str(TEX_DIR / "cha_wildrider_main_Diffuse.png"))
img_norm = bpy.data.images.load(str(TEX_DIR / "cha_wildrider_main_Normal_unity.png"))
img_norm.colorspace_settings.name = "Non-Color"
img_raoe = bpy.data.images.load(str(TEX_DIR / "cha_wildrider_main_RAOE.png"))
img_raoe.colorspace_settings.name = "Non-Color"

mat_wr = bpy.data.materials.new("WR_Mat")
mat_wr.use_nodes = True
nt = mat_wr.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
td = nt.nodes.new("ShaderNodeTexImage"); td.image = img_diff
tn = nt.nodes.new("ShaderNodeTexImage"); tn.image = img_norm
tr = nt.nodes.new("ShaderNodeTexImage"); tr.image = img_raoe
sep = nt.nodes.new("ShaderNodeSeparateColor")
nmap = nt.nodes.new("ShaderNodeNormalMap")
emul = nt.nodes.new("ShaderNodeMath"); emul.operation = "MULTIPLY"; emul.inputs[1].default_value = 3.5
nt.links.new(td.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(tr.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Red"], bsdf.inputs["Roughness"])
nt.links.new(tn.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
nt.links.new(td.outputs["Color"], bsdf.inputs["Emission"])
nt.links.new(sep.outputs["Blue"], emul.inputs[0])
nt.links.new(emul.outputs["Value"], bsdf.inputs["Emission Strength"])

mat_ref = bpy.data.materials.new("Prowl_Ref_Mat")
mat_ref.use_nodes = True
mat_ref.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.45, 0.55, 0.65, 1.0)

# 1. Import Prowl Robot OBJ (note Unity OBJ (ux, uy, uz) imported by wm.obj_import with default forward=-Z, up=Y gives (-ux? no, +ux) -> check & mirror X if needed so Left/Right match!)
# Actually let's check both prowl_robot_ref.obj and our exported wildrider_robot_prepared.fbx!
bpy.ops.import_scene.fbx(filepath=str(FBX_DIR / "wildrider_robot_prepared.fbx"))
wr_rob = [o for o in bpy.data.objects if o.type == "MESH"][0]
wr_arm = [o for o in bpy.data.objects if o.type == "ARMATURE"][0]
wr_rob.data.materials.clear()
wr_rob.data.materials.append(mat_wr)
wr_arm.location = Vector((3.2, 0.0, 0.0))

bpy.ops.wm.obj_import(filepath=str(WR_DIR / "prowl_robot_ref.obj"))
pr_rob = [o for o in bpy.data.objects if "prowl_robot" in o.name][0]
pr_rob.data.materials.clear()
pr_rob.data.materials.append(mat_ref)
pr_rob.location = Vector((-3.2, 0.0, 0.0))

# 2. Import Vehicle comparison behind/aside (or render separate view!)
bpy.ops.import_scene.fbx(filepath=str(FBX_DIR / "wildrider_veh_prepared.fbx"))
wr_veh = [o for o in bpy.data.objects if o.type == "MESH" and "veh" in o.name][0]
wr_veh_arm = wr_veh.parent
wr_veh.data.materials.clear()
wr_veh.data.materials.append(mat_wr)
wr_veh_arm.location = Vector((3.0, 14.0, 0.0))

bpy.ops.wm.obj_import(filepath=str(WR_DIR / "prowl_veh_ref.obj"))
pr_veh = [o for o in bpy.data.objects if "prowl_veh" in o.name][0]
pr_veh.data.materials.clear()
pr_veh.data.materials.append(mat_ref)
pr_veh.location = Vector((-3.0, 14.0, 0.0))

# 3. Gun comparison at Y = 26
bpy.ops.import_scene.fbx(filepath=str(FBX_DIR / "wildrider_gun_prepared.fbx"))
wr_gun = [o for o in bpy.data.objects if o.type == "MESH" and "gun" in o.name.lower()][0]
wr_gun_arm = wr_gun.parent
wr_gun.data.materials.clear()
wr_gun.data.materials.append(mat_wr)
wr_gun_arm.location = Vector((1.5, 26.0, 2.0))

bpy.ops.wm.obj_import(filepath=str(WR_DIR / "prowl_shotgun_ref.obj"))
pr_gun = [o for o in bpy.data.objects if "prowl_shotgun" in o.name][0]
pr_gun.data.materials.clear()
pr_gun.data.materials.append(mat_ref)
pr_gun.location = Vector((-1.5, 26.0, 2.0))

# Lighting & Camera
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 24
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
scene.world.node_tree.nodes["Background"].inputs["Color"].default_value = (0.14, 0.16, 0.20, 1.0)

def add_sun(name, rot_deg, energy):
    ld = bpy.data.lights.new(name, type="SUN")
    ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.rotation_euler = [math.radians(r) for r in rot_deg]

add_sun("Key", (50, 0, 30), 3.0)
add_sun("Fill", (65, 0, -45), 1.5)
add_sun("Back", (-55, 0, 180), 2.0)

cam_d = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d)
bpy.context.collection.objects.link(cam)
scene.camera = cam

def look_at(pos, target, lens=40.0):
    cam.data.lens = lens
    cam.location = Vector(pos)
    cam.rotation_euler = (Vector(target) - Vector(pos)).to_track_quat("-Z", "Y").to_euler()

# Render 1: Robot Side-by-Side Front (Prowl Left vs WildRider Right)
look_at((0.0, -18.0, 4.8), (0.0, 0.0, 4.6), lens=40.0)
scene.render.filepath = str(RENDER_DIR / "gate2_robot_vs_prowl_front.png")
bpy.ops.render.render(write_still=True)

# Render 2: Vehicle Side-by-Side 3/4 Front (Prowl Left vs WildRider Right)
look_at((4.5, 4.5, 4.2), (0.0, 14.0, 1.2), lens=45.0)
scene.render.filepath = str(RENDER_DIR / "gate2_veh_vs_prowl_3q.png")
bpy.ops.render.render(write_still=True)

# Render 3: Gun Side-by-Side Profile
look_at((5.5, 25.0, 3.0), (0.0, 26.0, 1.2), lens=45.0)
scene.render.filepath = str(RENDER_DIR / "gate2_gun_vs_prowl_side.png")
bpy.ops.render.render(write_still=True)

print("[✓] Gate 2 comparison renders saved!")
