import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy, math
from pathlib import Path
from mathutils import Vector, Matrix

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
FBX_PATH = WR_DIR / "source" / "WildRider_pbr.fbx"
TEX_DIR = WR_DIR / "02_textures"
RENDER_DIR = ROOT / "renders" / "wildrider"
RENDER_DIR.mkdir(parents=True, exist_ok=True)

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

# Clean animations -> Rest pose for Robot preview, and bake evaluated vehicle separately
arm = bpy.data.objects["Bip001"]
veh_act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
idle_act = bpy.data.actions.get("Bip001|idle01|Base Layer")

# Evaluate idle01 frame 1 for robot preview (so arms/chest show naturally without 0.01x issues)
if idle_act:
    arm.animation_data.action = idle_act
    bpy.context.scene.frame_set(1)

# Load new 2048 PBR textures
img_diff = bpy.data.images.load(str(TEX_DIR / "cha_wildrider_main_Diffuse.png"))
img_norm = bpy.data.images.load(str(TEX_DIR / "cha_wildrider_main_Normal_unity.png"))
img_norm.colorspace_settings.name = "Non-Color"
img_raoe = bpy.data.images.load(str(TEX_DIR / "cha_wildrider_main_RAOE.png"))
img_raoe.colorspace_settings.name = "Non-Color"

mat = bpy.data.materials.new("WildRider_Gate1_PBR")
mat.use_nodes = True
nt = mat.node_tree
nt.nodes.clear()
out = nt.nodes.new("ShaderNodeOutputMaterial")
bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
bsdf.inputs["Specular"].default_value = 0.5
nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

t_d = nt.nodes.new("ShaderNodeTexImage"); t_d.image = img_diff
t_n = nt.nodes.new("ShaderNodeTexImage"); t_n.image = img_norm
t_r = nt.nodes.new("ShaderNodeTexImage"); t_r.image = img_raoe
sep = nt.nodes.new("ShaderNodeSeparateColor")
nmap = nt.nodes.new("ShaderNodeNormalMap")
emis_col = nt.nodes.new("ShaderNodeMix")
emis_col.data_type = "RGBA"
emis_col.blend_type = "MULTIPLY"
emis_col.inputs["Factor"].default_value = 1.0
emis_mul = nt.nodes.new("ShaderNodeMath")
emis_mul.operation = "MULTIPLY"
emis_mul.inputs[1].default_value = 3.5

nt.links.new(t_d.outputs["Color"], bsdf.inputs["Base Color"])
nt.links.new(t_r.outputs["Color"], sep.inputs["Color"])
nt.links.new(sep.outputs["Red"], bsdf.inputs["Roughness"])
nt.links.new(t_n.outputs["Color"], nmap.inputs["Color"])
nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])
nt.links.new(t_d.outputs["Color"], bsdf.inputs["Emission"])
nt.links.new(sep.outputs["Blue"], emis_mul.inputs[0])
nt.links.new(emis_mul.outputs["Value"], bsdf.inputs["Emission Strength"])

# Remove AB emblems & shadow for clean Decepticon preview
for drop_name in ["Symbol_AB", "Symbol_AB001", "Shadow"]:
    if drop_name in bpy.data.objects:
        bpy.data.objects.remove(bpy.data.objects[drop_name], do_unlink=True)

# Assign clean Decepticon palette UVs to Symbol_DC & Symbol_DC001 and lift slightly
for sym_name in ["Symbol_DC", "Symbol_DC001"]:
    so = bpy.data.objects.get(sym_name)
    if so:
        if not so.data.uv_layers:
            so.data.uv_layers.new(name="UVMap")
        uvl = so.data.uv_layers.active.data
        for p in so.data.polygons:
            t_uv = (0.296875, 0.9375) if p.material_index == 0 else (0.34375, 0.9375)
            for li in p.loop_indices:
                uvl[li].uv = t_uv
        so.data.materials.clear()
        so.data.materials.append(mat)

# Assign PBR mat to body & gun
for name in ["WildRider.001", "WildRider_Gun"]:
    o = bpy.data.objects[name]
    o.data.materials.clear()
    o.data.materials.append(mat)

# Add evaluated vehicle copy at X = +0.032m (since root scale is 0.01) -> actually let's render in meters by moving/scaling camera to robot at origin
# First let's bake a snapshot of robot meshes at scale ~3.2x (9.3m tall) and a snapshot of vehicle at X=+5m so lighting/shadows behave normally!
deps = bpy.context.evaluated_depsgraph_get()
def bake_snapshot(obj_names, offset_vec, label):
    objs_out = []
    for n in obj_names:
        o = bpy.data.objects[n]
        eo = o.evaluated_get(deps)
        me = eo.to_mesh().copy()
        new_o = bpy.data.objects.new(f"{label}_{n}", me)
        bpy.context.collection.objects.link(new_o)
        # Apply world transform scaled by 325x (0.01 * 325 = 3.25x unscaled ~9.3m)
        m = Matrix.Scale(325.0, 4) @ o.matrix_world
        me.transform(m)
        new_o.location = offset_vec
        eo.to_mesh_clear()
        objs_out.append(new_o)
    return objs_out

robot_snaps = bake_snapshot(["WildRider.001", "Symbol_DC"], Vector((-2.5, 0, 0)), "Robot")

# Switch to vehicle_idle01 and bake vehicle snapshot at +2.5
if veh_act:
    arm.animation_data.action = veh_act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
veh_snaps = bake_snapshot(["WildRider.001", "Symbol_DC001"], Vector((3.2, 0, 0)), "Veh")
gun_snaps = bake_snapshot(["WildRider_Gun"], Vector((3.2, 0, 3.0)), "Gun")

# Hide original armature hierarchy
for o in list(bpy.data.objects):
    if not (o.name.startswith("Robot_") or o.name.startswith("Veh_") or o.name.startswith("Gun_")):
        o.hide_render = True
        o.hide_viewport = True

# Setup clean studio lighting & Cycles/EEVEE render
scene = bpy.context.scene
scene.render.engine = "BLENDER_EEVEE"
scene.eevee.taa_render_samples = 32
scene.render.resolution_x = 1600
scene.render.resolution_y = 900
scene.world = bpy.data.worlds.new("World")
scene.world.use_nodes = True
bg = scene.world.node_tree.nodes["Background"]
bg.inputs["Color"].default_value = (0.12, 0.14, 0.18, 1.0)
bg.inputs["Strength"].default_value = 1.0

def add_light(name, ltype, loc, rot_deg, energy):
    ld = bpy.data.lights.new(name, type=ltype)
    ld.energy = energy
    lo = bpy.data.objects.new(name, ld)
    bpy.context.collection.objects.link(lo)
    lo.location = loc
    lo.rotation_euler = [math.radians(r) for r in rot_deg]
    return lo

add_light("SunKey", "SUN", (5, -8, 10), (50, 0, 30), 3.2)
add_light("SunFill", "SUN", (-6, -5, 6), (65, 0, -45), 1.5)
add_light("SunRim", "SUN", (0, 8, 8), (-55, 0, 180), 2.0)

cam_data = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
scene.camera = cam

def look_at(cam_obj, pos, target, lens=45.0):
    cam_obj.data.lens = lens
    cam_obj.location = Vector(pos)
    direction = Vector(target) - Vector(pos)
    cam_obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()

# View 1: Full Dual Showcase (Robot full height + Vehicle + Gun)
look_at(cam, (0.4, -18.5, 5.2), (0.4, 0.0, 4.6), lens=38.0)
scene.render.filepath = str(RENDER_DIR / "gate1_front_overview.png")
bpy.ops.render.render(write_still=True)

# View 2: Face + Eyes + Chest Emblem Close-up
look_at(cam, (-2.5, -5.8, 7.8), (-2.5, 0.0, 7.6), lens=50.0)
scene.render.filepath = str(RENDER_DIR / "gate1_head_chest_closeup.png")
bpy.ops.render.render(write_still=True)

# View 3: 3/4 Vehicle Close-up & Gun
look_at(cam, (7.5, -6.5, 3.8), (3.2, 0.0, 1.5), lens=45.0)
scene.render.filepath = str(RENDER_DIR / "gate1_back_vehicle_3q.png")
bpy.ops.render.render(write_still=True)

print("[✓] Gate 1 3-view renders saved to renders/wildrider/")
