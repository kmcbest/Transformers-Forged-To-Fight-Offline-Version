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

def scale_mat(s: Vector) -> Matrix:
    m = Matrix.Identity(4)
    m[0][0], m[1][1], m[2][2] = s.x, s.y, s.z
    return m

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

act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act

mat_mesh_to_arm = arm.matrix_world.inverted() @ mesh.matrix_world
mat_arm_to_world100 = Matrix.Scale(100.0, 4) @ arm.matrix_world

def get_skin_mats_at_frame(frame_num: int):
    bpy.context.scene.frame_set(frame_num)
    bpy.context.view_layer.update()
    w_anim = {}
    def get_w_anim(pb):
        if pb.name in w_anim:
            return w_anim[pb.name]
        b = pb.bone
        s = lcl_scales.get(b.name, Vector((1.0, 1.0, 1.0)))
        if b.parent is None:
            w = b.matrix_local @ scale_mat(s) @ pb.matrix_basis
        else:
            eb_rel = b.parent.matrix_local.inverted() @ b.matrix_local
            w = get_w_anim(pb.parent) @ eb_rel @ scale_mat(s) @ pb.matrix_basis
        w_anim[pb.name] = w
        return w
    for pb in arm.pose.bones:
        get_w_anim(pb)
    sm = {}
    for bname, wr in w_rest.items():
        sm[bname] = mat_arm_to_world100 @ w_anim[bname] @ wr.inverted() @ mat_mesh_to_arm
    return sm, {bname: mat_arm_to_world100 @ w_anim[bname] for bname in w_anim}

sm1, w1 = get_skin_mats_at_frame(1)

# Base vertices at Frame 1
v1 = []
vg_names = {vg.index: vg.name for vg in mesh.vertex_groups}
for vi, v in enumerate(mesh.data.vertices):
    p = v.co
    acc = Vector((0.0, 0.0, 0.0))
    tot_w = 0.0
    for g in v.groups:
        bname = vg_names.get(g.group)
        if bname in sm1 and g.weight > 1e-5:
            acc += (sm1[bname] @ p) * g.weight
            tot_w += g.weight
    v1.append((acc / tot_w) if tot_w > 1e-5 else p.copy())

# Map every Swoop vertex group to its representative animated driver bone in Swoop's rig:
DRIVER_MAP = {vg.name: "Back" for vg in mesh.vertex_groups}
DRIVER_MAP.update({
    "Bone_L_Wing_01(mirrored)": "Bone_L_Wing_01(mirrored)",
    "L_missile": "Bone_L_Wing_01(mirrored)",
    "Bone_L_Wing_02(mirrored)": "Bone_L_Wing_02(mirrored)",
    "Bone_R_Wing_01": "Bone_R_Wing_01",
    "R_missile": "Bone_R_Wing_01",
    "Bone_R_Wing_02": "Bone_R_Wing_02",
    "beak_the bottom": "beak_the bottom",
    "Bone_L_Thigh001": "Bone_L_Thigh001",
    "Bone_L_Thigh002": "Bone_L_Thigh001",
    "Bone_L_Thigh003": "Bone_L_Thigh001",
    "Bone_L_Thigh004": "Bone_L_Thigh001",
    "Bone_R_Thigh001(mirrored)": "Bone_R_Thigh001(mirrored)",
    "Bone_R_Thigh002(mirrored)": "Bone_R_Thigh001(mirrored)",
    "Bone_R_Thigh003(mirrored)": "Bone_R_Thigh001(mirrored)",
    "Bone_R_Thigh004(mirrored)": "Bone_R_Thigh001(mirrored)",
})

# Compare exact 73-bone deformation vs 8-driver deformation at frames 10 and 23
for f in [10, 23, 38, 49]:
    sm_f, w_f = get_skin_mats_at_frame(f)
    delta_f = {bname: w_f[bname] @ w1[bname].inverted() for bname in w_f}
    max_err = 0.0
    wing_disp = 0.0
    for vi, v in enumerate(mesh.data.vertices):
        # True 73-bone pos at frame f
        p0 = v.co
        acc_true = Vector((0.0, 0.0, 0.0))
        tot_w = 0.0
        for g in v.groups:
            bname = vg_names.get(g.group)
            if bname in sm_f and g.weight > 1e-5:
                acc_true += (sm_f[bname] @ p0) * g.weight
                tot_w += g.weight
        p_true = acc_true / tot_w if tot_w > 1e-5 else p0
        disp = (p_true - v1[vi]).length
        if disp > wing_disp:
            wing_disp = disp

        # 8-driver pos from v1[vi]
        acc_drv = Vector((0.0, 0.0, 0.0))
        tot_dw = 0.0
        for g in v.groups:
            bname = vg_names.get(g.group)
            drv = DRIVER_MAP.get(bname, "Back")
            if drv in delta_f and g.weight > 1e-5:
                acc_drv += (delta_f[drv] @ v1[vi]) * g.weight
                tot_dw += g.weight
        p_drv = acc_drv / tot_dw if tot_dw > 1e-5 else v1[vi]
        err = (p_true - p_drv).length
        if err > max_err:
            max_err = err
    print(f"Frame {f:2d}: max wing tip displacement = {wing_disp:.4f}m | max error (8-bone vs 73-bone) = {max_err:.4f}m")
