import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import math
from pathlib import Path
import bpy
from io_scene_fbx import parse_fbx
from mathutils import Euler, Matrix, Vector

ROOT = Path("e:/Agent/TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"
OUT_SIDE = ROOT / "renders/swoop/debug_pteranodon_side.png"
OUT_VENTRAL = ROOT / "renders/swoop/debug_pteranodon_ventral.png"

elem, _ = parse_fbx.parse(str(FBX_SRC))
objects = next(e for e in elem.elems if e.id == b'Objects')
connections = next(e for e in elem.elems if e.id == b'Connections')

models = {}
clusters = {}
for e in objects.elems:
    if e.id == b'Model':
        models[e.props[0]] = e.props[1].split(b'\x00')[0].decode('utf-8', errors='replace')
    elif e.id == b'Deformer' and len(e.props) >= 3 and e.props[2] == b'Cluster':
        for sub in e.elems:
            if sub.id == b'TransformLink':
                clusters[e.props[0]] = sub.props[0]

c_to_m = {}
tl_scales = {}
for c in connections.elems:
    if c.id == b'C':
        src, dst = c.props[1], c.props[2]
        if src in models and dst in clusters:
            bname = models[src]
            tl = clusters[dst]
            c_to_m[bname] = tl
            tl_scales[bname] = (tl[0] ** 2 + tl[1] ** 2 + tl[2] ** 2) ** 0.5

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow", "Swoop_Weapon", "Symbol_AB"]:
        bpy.data.objects.remove(o, do_unlink=True)

bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
for eb in arm.data.edit_bones:
    tl = c_to_m.get(eb.name)
    if tl:
        tx, ty, tz = tl[12], tl[13], tl[14]
        true_head = Vector((tz, tx, ty - 1.8050))
        if (eb.head - true_head).length > 1e-3:
            delta = true_head - eb.head
            eb.head = true_head
            eb.tail = eb.tail + delta
bpy.ops.object.mode_set(mode='OBJECT')

act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

for bname in ["bird_Head", "beak_the bottom", "bird_neck", "Bone_Head", "Bone_L_Hand", "Bone_R_Hand"]:
    if bname in arm.pose.bones and bname in tl_scales:
        arm.pose.bones[bname].location *= tl_scales[bname]
for bname in ["beak_the bottom", "bird_Head_02"]:
    if bname in arm.pose.bones:
        arm.pose.bones[bname].scale = Vector((1.0, 1.0, 1.0))
if "bird_neck" in arm.pose.bones and "bird_neck" in tl_scales:
    arm.pose.bones["bird_neck"].scale *= tl_scales["bird_neck"]

bpy.context.view_layer.update()
deps = bpy.context.evaluated_depsgraph_get()
ev = mesh.evaluated_get(deps)
ev_mesh = bpy.data.meshes.new_from_object(ev)
baked = bpy.data.objects.new("BakedPtera", ev_mesh)
bpy.context.scene.collection.objects.link(baked)
m_world_100 = Matrix.Scale(100.0, 4) @ ev.matrix_world
baked.data.transform(m_world_100)
baked.data.update()
baked.matrix_world = Matrix.Identity(4)
mesh.hide_render = True

vg_map = {vg.name: vg.index for vg in mesh.vertex_groups}
print("\n=== Baked Vehicle Vertex Bounds (Blender +Z=Up, -Y=Forward) ===")
for vgn, vgi in vg_map.items():
    pts = [baked.data.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vgi and g.weight > 0.5 for g in v.groups)]
    if pts:
        print(f"  {vgn:<26} ({len(pts):4d}v): X=[{min(p.x for p in pts):+6.3f},{max(p.x for p in pts):+6.3f}] Y=[{min(p.y for p in pts):+6.3f},{max(p.y for p in pts):+6.3f}] Z=[{min(p.z for p in pts):+6.3f},{max(p.z for p in pts):+6.3f}]")

tex_path = ROOT / "3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png"
if tex_path.exists():
    for mat in baked.data.materials:
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes.get("Principled BSDF")
        if bsdf:
            tn = mat.node_tree.nodes.new("ShaderNodeTexImage")
            tn.image = bpy.data.images.load(str(tex_path))
            mat.node_tree.links.new(bsdf.inputs["Base Color"], tn.outputs["Color"])

cam_d = bpy.data.cameras.new("Cam")
cam = bpy.data.objects.new("Cam", cam_d)
bpy.context.scene.collection.objects.link(cam)
bpy.context.scene.camera = cam

ld = bpy.data.lights.new("Sun", 'SUN')
l = bpy.data.objects.new("Sun", ld)
bpy.context.scene.collection.objects.link(l)
l.rotation_euler = Euler((math.radians(35), 0, math.radians(25)), 'XYZ')
ld.energy = 4.5

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

# Side view (+X looking at 0)
cam.location = Vector((4.5, -0.2, 2.0))
direction = Vector((0.0, -0.2, 2.0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.render.filepath = str(OUT_SIDE)
bpy.ops.render.render(write_still=True)

# Ventral view (-Z looking up at 0, same angle as 09_vehicle_sbs when tilted!)
l.rotation_euler = Euler((math.radians(145), 0, math.radians(25)), 'XYZ')
cam.location = Vector((0.0, -0.2, -4.5))
direction = Vector((0.0, -0.2, 2.0)) - cam.location
cam.rotation_euler = direction.to_track_quat('-Z', 'Y').to_euler()
bpy.context.scene.render.filepath = str(OUT_VENTRAL)
bpy.ops.render.render(write_still=True)
