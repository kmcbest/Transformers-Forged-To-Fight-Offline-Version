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

elem, _ = parse_fbx.parse(str(FBX_SRC))
objects = next(e for e in elem.elems if e.id == b'Objects')

lcl_scales = {}
for e in objects.elems:
    if e.id == b'Model':
        name = e.props[1].split(b'\x00')[0].decode('utf-8', errors='replace')
        p70 = next((s for s in e.elems if s.id == b'Properties70'), None)
        sca = Vector((1.0, 1.0, 1.0))
        if p70:
            for p in p70.elems:
                pname = p.props[0].decode('utf-8', errors='replace')
                if pname == 'Lcl Scaling':
                    sca = Vector((float(p.props[4]), float(p.props[5]), float(p.props[6])))
        lcl_scales[name] = sca

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow", "Swoop_Weapon", "Symbol_AB"]:
        bpy.data.objects.remove(o, do_unlink=True)

def scale_mat(s: Vector) -> Matrix:
    m = Matrix.Identity(4)
    m[0][0], m[1][1], m[2][2] = s.x, s.y, s.z
    return m

# 1. Exact FBX Rest Pose matrices in Armature space
w_rest = {}
def get_w_rest(b):
    if b.name in w_rest:
        return w_rest[b.name]
    s = lcl_scales.get(b.name, Vector((1.0, 1.0, 1.0)))
    if b.parent is None:
        w = b.matrix_local @ scale_mat(s)
    else:
        eb_rel = b.parent.matrix_local.inverted() @ b.matrix_local
        w = get_w_rest(b.parent) @ eb_rel @ scale_mat(s)
    w_rest[b.name] = w
    return w

for b in arm.data.bones:
    get_w_rest(b)

# 2. Evaluate vehicle_idle01 Frame 1
act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()

w_anim = {}
def get_w_anim(pb):
    if pb.name in w_anim:
        return w_anim[pb.name]
    b = pb.bone
    s = lcl_scales.get(b.name, Vector((1.0, 1.0, 1.0)))
    if b.parent is None:
        eb_rel = b.matrix_local
        w = eb_rel @ scale_mat(s) @ pb.matrix_basis
    else:
        eb_rel = b.parent.matrix_local.inverted() @ b.matrix_local
        w = get_w_anim(pb.parent) @ eb_rel @ scale_mat(s) @ pb.matrix_basis
    w_anim[pb.name] = w
    return w

for pb in arm.pose.bones:
    get_w_anim(pb)

# 3. Compute exact skinning matrices in mesh space -> world space (scaled by 100)
mat_mesh_to_arm = arm.matrix_world.inverted() @ mesh.matrix_world
mat_arm_to_world100 = Matrix.Scale(100.0, 4) @ arm.matrix_world

skin_mats = {}
for bname, wr in w_rest.items():
    wa = w_anim[bname]
    # Transform vertex from mesh local -> arm local -> deform by wa @ wr^-1 -> world100
    skin_mats[bname] = mat_arm_to_world100 @ wa @ wr.inverted() @ mat_mesh_to_arm

# 4. Deform mesh vertices directly using Linear Blend Skinning
baked_data = mesh.data.copy()
baked = bpy.data.objects.new("ExactPtera", baked_data)
bpy.context.scene.collection.objects.link(baked)
baked.matrix_world = Matrix.Identity(4)

vg_names = {vg.index: vg.name for vg in mesh.vertex_groups}
for vi, v in enumerate(mesh.data.vertices):
    p = v.co
    acc = Vector((0.0, 0.0, 0.0))
    tot_w = 0.0
    for g in v.groups:
        bname = vg_names.get(g.group)
        if bname in skin_mats and g.weight > 1e-5:
            acc += (skin_mats[bname] @ p) * g.weight
            tot_w += g.weight
    if tot_w > 1e-5:
        baked_data.vertices[vi].co = acc / tot_w
baked_data.update()
mesh.hide_render = True

vg_map = {vg.name: vg.index for vg in mesh.vertex_groups}
print("\n=== EXACT FBX Math Vehicle Bounds (Blender +Z=Up, -Y=Forward) ===")
for vgn in ["bird_chest", "bird_neck", "Bone_Head", "bird_Head", "bird_Head_02", "beak", "beak_the bottom", "Back", "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "L_missile"]:
    vgi = vg_map[vgn]
    pts = [baked_data.vertices[v.index].co for v in mesh.data.vertices if any(g.group == vgi and g.weight > 0.5 for g in v.groups)]
    print(f"  {vgn:<26} ({len(pts):4d}v): X=[{min(p.x for p in pts):+6.3f},{max(p.x for p in pts):+6.3f}] Y=[{min(p.y for p in pts):+6.3f},{max(p.y for p in pts):+6.3f}] Z=[{min(p.z for p in pts):+6.3f},{max(p.z for p in pts):+6.3f}]")

# Render 3 views with bright ambient + sun lights
world = bpy.data.worlds.new("BrightWorld")
bpy.context.scene.world = world
world.use_nodes = True
bg = world.node_tree.nodes.get("Background")
if bg:
    bg.inputs[0].default_value = (0.18, 0.20, 0.25, 1.0)
    bg.inputs[1].default_value = 1.2

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

for idx, eul in enumerate([(35, 0, 25), (145, 0, -35)]):
    ld = bpy.data.lights.new(f"Sun{idx}", 'SUN')
    l = bpy.data.objects.new(f"Sun{idx}", ld)
    bpy.context.scene.collection.objects.link(l)
    l.rotation_euler = Euler(tuple(math.radians(a) for a in eul), 'XYZ')
    ld.energy = 3.5

bpy.context.scene.render.engine = 'BLENDER_EEVEE'
bpy.context.scene.render.resolution_x = 1280
bpy.context.scene.render.resolution_y = 720

for name, loc, targ in [
    ("debug_exact_dorsal.png", Vector((3.2, -4.0, 4.2)), Vector((0.0, -0.2, 2.2))),
    ("debug_exact_side.png", Vector((4.2, -0.2, 2.3)), Vector((0.0, -0.2, 2.3))),
    ("debug_exact_ventral.png", Vector((0.0, -0.2, -4.2)), Vector((0.0, -0.2, 2.2))),
]:
    cam.location = loc
    cam.rotation_euler = (targ - loc).to_track_quat('-Z', 'Y').to_euler()
    bpy.context.scene.render.filepath = str(ROOT / "renders/swoop" / name)
    bpy.ops.render.render(write_still=True)
