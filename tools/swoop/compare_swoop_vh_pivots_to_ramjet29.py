import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
from io_scene_fbx import parse_fbx
from mathutils import Matrix, Vector

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DONOR_JET_JSON = ROOT_DIR / "tools/swoop/ramjet_jet_29_authoritative_bindposes.json"
FBX_SRC = ROOT_DIR / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

with open(DONOR_JET_JSON, "r", encoding="utf-8") as f:
    donor_data = json.load(f)
donor_bones = donor_data["bones"]

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
swoop_mesh = bpy.data.objects.get("Swoop.001")

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

depsgraph = bpy.context.evaluated_depsgraph_get()
eval_obj = swoop_mesh.evaluated_get(depsgraph)
eval_mesh = bpy.data.meshes.new_from_object(eval_obj)
m_world_100 = Matrix.Scale(100.0, 4) @ eval_obj.matrix_world
eval_mesh.transform(m_world_100)

xs = [v.co.x for v in eval_mesh.vertices]
ys = [v.co.y for v in eval_mesh.vertices]
zs = [v.co.z for v in eval_mesh.vertices]
span_x = max(xs) - min(xs)
scale_factor = 10.20 / span_x
center_x = (min(xs) + max(xs)) / 2.0
center_y = (min(ys) + max(ys)) / 2.0
min_z = min(zs)

def to_unity_mesh_pos(blender_world_100: Vector) -> Vector:
    bx = (blender_world_100.x - center_x) * scale_factor
    by = (blender_world_100.y - center_y) * scale_factor
    bz = (blender_world_100.z - min_z) * scale_factor + 0.28
    # In BuildGraftedMesh: Unity X = -bx, Unity Y = bz, Unity Z = -by
    return Vector((-bx, bz, -by))

print("\n=== Swoop Vehicle Bone Pivots in Unity Mesh Space (Frame 1) ===")
key_bones = [
    "Back", "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "L_missile",
    "Bone_R_Wing_01", "Bone_R_Wing_02", "R_missile",
    "bird_neck", "bird_Head", "beak", "beak_the bottom",
    "Bone_L_Thigh", "Bone_R_Thigh"
]
for bname in key_bones:
    pb = arm.pose.bones.get(bname)
    if pb:
        w100 = (Matrix.Scale(100.0, 4) @ arm.matrix_world @ pb.head)
        upos = to_unity_mesh_pos(w100)
        print(f"  {bname:<28} -> Unity Pos: ({upos.x:+7.3f}, {upos.y:+7.3f}, {upos.z:+7.3f})")

print("\n=== Donor Ramjet 29 Jet Bones in Unity Mesh Space ===")
for bname, binfo in donor_bones.items():
    ux, uy, uz = binfo["unity_world_pos"]
    p = binfo["parent"]
    e00 = binfo["bind_pose_matrix"]["e00"]
    print(f"  {bname:<28} (parent={p:<18}, e00={e00:5.2f}) -> Unity Pos: ({ux:+7.3f}, {uy:+7.3f}, {uz:+7.3f})")
