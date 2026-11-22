import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import math
from mathutils import Vector, Matrix
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
TEX_DIR = ROOT / "3rd-party-models" / "BlastOff" / "02_textures"

BLASTOFF_MESH_NAMES = [
    "RB_Blastoff_CHARSKEL_Head.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoR.001.dmx",
    "RB_BlastoffWing_STAT.001.dmx",
    "RB_BlastoffWing_STAT.dmx",
]

ROBOT_UV_MAP = {
    "RB_Blastoff_Chest_Cust_MatINST":    (0.5,   0.0,   0.5,  0.5),   # (0, 0, 1024, 1024)
    "RB_Blastoff_Legs_Cust_MatINST":     (0.5,   0.0,   0.5,  0.0),   # (0, 1024, 1024, 1024)
    "RB_Blastoff_Head_Cust_MatINST":     (0.25,  0.5,   0.25, 0.75),  # (1024, 0, 512, 512)
    "RB_Blastoff_ArmLo_Cust_MatINST":    (0.25,  0.75,  0.25, 0.75),  # (1536, 0, 512, 512)
    "RB_Blastoff_ArmUp_Cust_MatINST":    (0.25,  0.5,   0.25, 0.5),   # (1024, 512, 512, 512)
    "VH_Blastoff_Cust_MatINST":          (0.25,  0.75,  0.25, 0.5),   # (1536, 512, 512, 512)
    "TR_FactionLogo_Mat_INST.001":       (0.125, 0.5,   0.125, 0.375), # (1024, 1280, 256, 256)
}

def remap_uvs_clean(obj, uv_map, default_box=(0.5, 0.0, 0.5, 0.5)):
    uv_layer = obj.data.uv_layers.active
    if not uv_layer:
        return
    mat_slots = [slot.material.name if slot.material else "" for slot in obj.material_slots]
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        u_sc, u_off, v_sc, v_off = uv_map.get(mname, default_box)
        pts = []
        for li in poly.loop_indices:
            uv = uv_layer.data[li].uv
            ux = 0.5 if (not math.isfinite(uv.x) or abs(uv.x) > 10.0) else uv.x
            vy = 0.5 if (not math.isfinite(uv.y) or abs(uv.y) > 10.0) else uv.y
            pts.append((li, ux, vy))
        mu = sum(p[1] for p in pts) / len(pts)
        mv = sum(p[2] for p in pts) / len(pts)
        du = math.floor(mu)
        dv = math.floor(mv)
        for li, ux, vy in pts:
            u_loc = min(0.994, max(0.006, ux - du))
            v_loc = min(0.994, max(0.006, vy - dv))
            uv_layer.data[li].uv = (u_loc * u_sc + u_off, v_loc * v_sc + v_off)
    obj.data.update()

def make_blastoff_preview_material(name, prefix):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Normal_unity.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nmap = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nmap.inputs["Color"])
    nt.links.new(nmap.outputs["Normal"], bsdf.inputs["Normal"])

    tem = nt.nodes.new("ShaderNodeTexImage")
    tem.image = bpy.data.images.load(str(TEX_DIR / f"{prefix}_Emission.png"))
    nt.links.new(tem.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 2.0
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.25
    return mat

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

arm = bpy.data.objects.get("Blast-off_ARM")
robot_objs = [bpy.data.objects[n] for n in BLASTOFF_MESH_NAMES if n in bpy.data.objects]

keep_objs = set(robot_objs) | {arm}
for o in list(bpy.data.objects):
    if o not in keep_objs:
        bpy.data.objects.remove(o, do_unlink=True)

# 0. Center
arm.location.y += 10.0118
for obj in robot_objs:
    obj.location.y += 10.0118

# 1. R_z(-90)
R_z90 = Matrix.Rotation(math.radians(-90), 4, 'Z')
arm.matrix_world = R_z90 @ arm.matrix_world
for obj in robot_objs:
    obj.matrix_world = R_z90 @ obj.matrix_world
bpy.context.view_layer.update()

bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

for obj in robot_objs:
    remap_uvs_clean(obj, ROBOT_UV_MAP)

SCALE_BLASTOFF = 2.2928
arm.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
for obj in robot_objs:
    obj.scale = (SCALE_BLASTOFF, SCALE_BLASTOFF, SCALE_BLASTOFF)
bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Grounding:
min_z = min([v.co.z for obj in robot_objs for v in obj.data.vertices])
arm.location.z -= min_z
for obj in robot_objs:
    obj.location.z -= min_z
bpy.context.view_layer.update()
bpy.ops.object.select_all(action="DESELECT")
for obj in robot_objs:
    obj.select_set(True)
arm.select_set(True)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

# Material
mat = make_blastoff_preview_material("mat_raw", "cha_blastoff_main")
for obj in robot_objs:
    obj.data.materials.clear()
    obj.data.materials.append(mat)

# Camera in front
cam_data = bpy.data.cameras.new("CamRaw")
cam_obj = bpy.data.objects.new("CamRaw", cam_data)
bpy.context.collection.objects.link(cam_obj)
cam_data.lens = 35.0
cam_obj.location = (0.0, -25.0, 7.5)
cam_obj.rotation_euler = (math.radians(88), 0, 0)
bpy.context.scene.camera = cam_obj

light_data = bpy.data.lights.new("Sun", "SUN")
light_data.energy = 3.5
light_obj = bpy.data.objects.new("Sun", light_data)
bpy.context.collection.objects.link(light_obj)
light_obj.rotation_euler = (math.radians(45), math.radians(25), 0)

bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 1080
out_img = str(ROOT / "renders" / "blastoff" / "raw_unposed_blastoff.png")
bpy.context.scene.render.filepath = out_img
bpy.ops.render.render(write_still=True)
print(f"[✓] Rendered raw unposed Blast Off to {out_img}")
