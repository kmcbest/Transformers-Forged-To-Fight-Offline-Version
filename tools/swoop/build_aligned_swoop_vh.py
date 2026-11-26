import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
import shutil
from pathlib import Path

import bpy
from io_scene_fbx import parse_fbx
from mathutils import Matrix, Quaternion, Vector

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
DONOR_JET_JSON = ROOT_DIR / "tools/swoop/ramjet_jet_29_authoritative_bindposes.json"
FBX_SRC = ROOT_DIR / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"
FBX_OUT_DIR = ROOT_DIR / "3rd-party-models/swoop/03_fbx"
FBX_OUT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_OUT_DIR = ROOT_DIR / "toolchain/unity_build_project/Assets/Swoop"
UNITY_OUT_DIR.mkdir(parents=True, exist_ok=True)

print("=== [Swoop] Stage 2: Building Aligned Vehicle FBX + Extracting Native 58-Frame Wing-Flapping Animation ===")

with open(DONOR_JET_JSON, "r", encoding="utf-8") as f:
    donor_data = json.load(f)

donor_bones = donor_data["bones"]
donor_bone_names = donor_data["bone_names"]
print(f"Loaded {len(donor_bone_names)} donor jet bones from {DONOR_JET_JSON}")

# Convert Unity world pos to Blender coords: bx = -ux, by = -uz, bz = uy
donor_blender_pos = {}
for bname, binfo in donor_bones.items():
    ux, uy, uz = binfo["unity_world_pos"]
    donor_blender_pos[bname] = Vector((-ux, -uz, uy))

donor_parent_map = {}
for bname, binfo in donor_bones.items():
    p = binfo["parent"]
    donor_parent_map[bname] = p if p != "None" and p != "Reference" else None

# 1. Parse raw FBX Model Properties70 + AnimationStack("vehicle_idle01") curves directly in pure Python
#    This completely bypasses Blender io_scene_fbx EditBone/PoseBone orthonormalization that corrupts
#    bones with negative 3ds Max Lcl Scaling (e.g. Bone_R_Thigh: S=(-1,-1,-1), Rz=180 deg).
import bisect
from mathutils import Euler

elem, _ = parse_fbx.parse(str(FBX_SRC))
objects = next(e for e in elem.elems if e.id == b'Objects')
conns = next(e for e in elem.elems if e.id == b'Connections')
FBX_SECOND = 46186158000

id_to_elem = {int(e.props[0]): e for e in objects.elems if e.props and isinstance(e.props[0], (int,))}
parent_to_children = {}
child_to_parents = {}
for c in conns.elems:
    if c.id == b'C' and len(c.props) >= 3:
        ch, pa = int(c.props[1]), int(c.props[2])
        prop = c.props[3].decode('utf-8', errors='replace') if len(c.props) >= 4 else ""
        parent_to_children.setdefault(pa, []).append((ch, prop))
        child_to_parents.setdefault(ch, []).append((pa, prop))

fbx_models = {}
fbx_name_to_id = {}
for e in objects.elems:
    if e.id == b'Model':
        mid = int(e.props[0])
        nm = e.props[1].split(b'\x00')[0].decode('utf-8', errors='replace')
        p70 = next((s for s in e.elems if s.id == b'Properties70'), None)
        tr = Vector((0.0, 0.0, 0.0))
        rot = Vector((0.0, 0.0, 0.0))
        pre = Vector((0.0, 0.0, 0.0))
        post = Vector((0.0, 0.0, 0.0))
        sca = Vector((1.0, 1.0, 1.0))
        if p70:
            for p in p70.elems:
                pn = p.props[0].decode('utf-8', errors='replace')
                if pn == 'Lcl Translation':
                    tr = Vector((float(p.props[4]), float(p.props[5]), float(p.props[6])))
                elif pn == 'Lcl Rotation':
                    rot = Vector((float(p.props[4]), float(p.props[5]), float(p.props[6])))
                elif pn == 'PreRotation':
                    pre = Vector((float(p.props[4]), float(p.props[5]), float(p.props[6])))
                elif pn == 'PostRotation':
                    post = Vector((float(p.props[4]), float(p.props[5]), float(p.props[6])))
                elif pn == 'Lcl Scaling':
                    sca = Vector((float(p.props[4]), float(p.props[5]), float(p.props[6])))
        fbx_models[mid] = {"name": nm, "T": tr, "R": rot, "Pre": pre, "Post": post, "S": sca}
        fbx_name_to_id[nm] = mid

fbx_model_parent = {
    ch: pa
    for pa, clist in parent_to_children.items() if pa in fbx_models
    for ch, _ in clist if ch in fbx_models
}

idle_stack = next(e for e in objects.elems if e.id == b'AnimationStack' and b'vehicle_idle01' in e.props[1])
idle_layers = set(
    ch for ch, _ in parent_to_children[int(idle_stack.props[0])]
    if id_to_elem[ch].id == b'AnimationLayer'
)

fbx_curves = {}
for mid in fbx_models:
    for ch, prop in parent_to_children.get(mid, []):
        ce = id_to_elem.get(ch)
        if ce and ce.id == b'AnimationCurveNode':
            if any(pa in idle_layers for pa, _ in child_to_parents.get(ch, [])):
                for cch, cprop in parent_to_children.get(ch, []):
                    cce = id_to_elem.get(cch)
                    if cce and cce.id == b'AnimationCurve':
                        kt = [t / FBX_SECOND for t in next(x.props[0] for x in cce.elems if x.id == b'KeyTime')]
                        kv = list(next(x.props[0] for x in cce.elems if x.id == b'KeyValueFloat'))
                        fbx_curves[(mid, prop, cprop)] = (kt, kv)

def eval_fbx_scalar(mid: int, prop_name: str, axis_idx: int, t_sec: float, default_val: float) -> float:
    axis_key = ('d|X', 'd|Y', 'd|Z')[axis_idx]
    entry = fbx_curves.get((mid, prop_name, axis_key))
    if not entry:
        return default_val
    kt, kv = entry
    n = len(kt)
    if n == 0:
        return default_val
    if t_sec <= kt[0]:
        return kv[0]
    if t_sec >= kt[-1]:
        return kv[-1]
    i = bisect.bisect_right(kt, t_sec) - 1
    i = max(0, min(i, n - 2))
    t0, t1 = kt[i], kt[i + 1]
    v0, v1 = kv[i], kv[i + 1]
    u = (t_sec - t0) / max(t1 - t0, 1e-9)
    def slope(idx):
        if idx == 0:
            return (kv[1] - kv[0]) / max(kt[1] - kt[0], 1e-9) if n > 1 else 0.0
        if idx == n - 1:
            return (kv[-1] - kv[-2]) / max(kt[-1] - kt[-2], 1e-9)
        return (kv[idx + 1] - kv[idx - 1]) / max(kt[idx + 1] - kt[idx - 1], 1e-9)
    m0 = slope(i) * (t1 - t0)
    m1 = slope(i + 1) * (t1 - t0)
    u2, u3 = u * u, u * u * u
    return (2 * u3 - 3 * u2 + 1) * v0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * v1 + (u3 - u2) * m1

def euler_deg_xyz(v: Vector) -> Matrix:
    return Euler((math.radians(v.x), math.radians(v.y), math.radians(v.z)), 'XYZ').to_matrix().to_4x4()

def scale_mat(s: Vector) -> Matrix:
    m = Matrix.Identity(4)
    m[0][0], m[1][1], m[2][2] = s.x, s.y, s.z
    return m

def fbx_local_mat(mid: int, t_sec=None) -> Matrix:
    info = fbx_models[mid]
    if t_sec is None:
        t, r, s = info["T"], info["R"], info["S"]
    else:
        t = Vector((eval_fbx_scalar(mid, 'Lcl Translation', i, t_sec, info["T"][i]) for i in range(3)))
        r = Vector((eval_fbx_scalar(mid, 'Lcl Rotation', i, t_sec, info["R"][i]) for i in range(3)))
        s = Vector((eval_fbx_scalar(mid, 'Lcl Scaling', i, t_sec, info["S"][i]) for i in range(3)))
    return (
        Matrix.Translation(t)
        @ euler_deg_xyz(info["Pre"])
        @ euler_deg_xyz(r)
        @ euler_deg_xyz(info["Post"]).inverted()
        @ scale_mat(s)
    )

# 2. Import Swoop source FBX into clean scene (for Swoop.001 vertices, UVs & vertex groups)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
swoop_mesh = bpy.data.objects.get("Swoop.001")

for o in list(bpy.data.objects):
    if o.name in ["Symbol_DC", "Shadow", "Swoop_Weapon", "Symbol_AB"]:
        bpy.data.objects.remove(o, do_unlink=True)

# 3. Compute exact FBX Rest Pose & 58-frame Anim matrices purely in FBX math, then convert Y-up -> Blender Z-up via Rx(+90 deg)
Rx90 = Euler((math.radians(90.0), 0.0, 0.0), 'XYZ').to_matrix().to_4x4()

fbx_w_rest = {}
def get_fbx_rest(mid: int) -> Matrix:
    if mid in fbx_w_rest:
        return fbx_w_rest[mid]
    m = fbx_local_mat(mid, None)
    if mid in fbx_model_parent:
        m = get_fbx_rest(fbx_model_parent[mid]) @ m
    fbx_w_rest[mid] = m
    return m

mesh_model_id = fbx_name_to_id["Swoop"]
m_mesh_fbx = get_fbx_rest(mesh_model_id)

def evaluate_frame_matrices(frame_num: int):
    t_sec = (frame_num - 1) / 30.0
    fbx_w_anim = {}
    def get_fbx_anim(mid: int) -> Matrix:
        if mid in fbx_w_anim:
            return fbx_w_anim[mid]
        m = fbx_local_mat(mid, t_sec)
        if mid in fbx_model_parent:
            m = get_fbx_anim(fbx_model_parent[mid]) @ m
        fbx_w_anim[mid] = m
        return m

    skin_m = {}
    world_b = {}
    for mid, minfo in fbx_models.items():
        bname = minfo["name"]
        wr = get_fbx_rest(mid)
        wa = get_fbx_anim(mid)
        skin_m[bname] = Rx90 @ wa @ wr.inverted() @ m_mesh_fbx
        world_b[bname] = Rx90 @ wa
    return skin_m, world_b

# 4. Evaluate exact FBX skinning at Frame 1 of vehicle_idle01 into upright horizontal world orientation (+Z=Up, -Y=Forward)
skin_m1, world_b1 = evaluate_frame_matrices(1)

baked_data = swoop_mesh.data.copy()
baked_swoop = bpy.data.objects.new("cha_swoop_vh_baked", baked_data)
bpy.context.scene.collection.objects.link(baked_swoop)
baked_swoop.matrix_world = Matrix.Identity(4)

for vg in swoop_mesh.vertex_groups:
    baked_swoop.vertex_groups.new(name=vg.name)
vg_name_by_idx = {vg.index: vg.name for vg in swoop_mesh.vertex_groups}

for vi, v in enumerate(swoop_mesh.data.vertices):
    p = v.co
    acc = Vector((0.0, 0.0, 0.0))
    tot_w = 0.0
    for g in v.groups:
        vgn = vg_name_by_idx.get(g.group)
        if vgn:
            baked_swoop.vertex_groups[vgn].add([v.index], g.weight, 'REPLACE')
            if vgn in skin_m1 and g.weight > 1e-5:
                acc += (skin_m1[vgn] @ p) * g.weight
                tot_w += g.weight
    if tot_w > 1e-5:
        baked_data.vertices[vi].co = acc / tot_w

baked_data.update()

# 5. Scale wingspan to 10.20m (proportional to Ramjet Jet 8.86m wingspan), center X/Y, ground Z at 0.28m
xs = [v.co.x for v in baked_swoop.data.vertices]
ys = [v.co.y for v in baked_swoop.data.vertices]
zs = [v.co.z for v in baked_swoop.data.vertices]
span_x = max(xs) - min(xs)
scale_factor = 10.20 / span_x
print(f"Baked Swoop Pteranodon raw wingspan: {span_x:.4f}m -> Target scale_factor: {scale_factor:.4f}")

center_x = (min(xs) + max(xs)) / 2.0
center_y = (min(ys) + max(ys)) / 2.0
min_z = min(zs)

mat_scale = (
    Matrix.Translation(Vector((0.0, 0.0, 0.28)))
    @ Matrix.Scale(scale_factor, 4)
    @ Matrix.Translation(Vector((-center_x, -center_y, -min_z)))
)
baked_swoop.data.transform(mat_scale)
baked_swoop.data.update()

new_xs = [v.co.x for v in baked_swoop.data.vertices]
new_ys = [v.co.y for v in baked_swoop.data.vertices]
new_zs = [v.co.z for v in baked_swoop.data.vertices]
print(f"Vehicle bounds after scaling & grounding (Blender +Z=Up, -Y=Fwd):")
print(f"  X (wingspan): [{min(new_xs):.3f}, {max(new_xs):.3f}] (span: {max(new_xs)-min(new_xs):.3f}m)")
print(f"  Y (length)  : [{min(new_ys):.3f}, {max(new_ys):.3f}] (span: {max(new_ys)-min(new_ys):.3f}m)")
print(f"  Z (height)  : [{min(new_zs):.3f}, {max(new_zs):.3f}] (span: {max(new_zs)-min(new_zs):.3f}m)")

# 6. Extract all 58 frames of Bip001|vehicle_idle01|Base Layer into Unity COG-child localPosition & localRotation curves!
# Mapping of 10 unit-scale direct children of COG in Ramjet's 29-bone Jet rig to Swoop's animated vehicle bones:
RAMJET_JET_TO_SWOOP_DRIVER = {
    "chop1_chest_center": "Back",                       # Stationary Pteranodon torso, neck, head, crest, upper beak
    "chop1_back_center": "beak_the bottom",             # Articulated lower jaw (breathing in flight)
    "chop1_forearm_left": "Bone_L_Wing_01(mirrored)",   # Left inner wing + left under-wing missile (22.4 deg flap)
    "chop1_cannon_left": "Bone_L_Wing_02(mirrored)",    # Left outer wing tip (34.3 deg phase-whip flap)
    "chop1_forearm_right": "Bone_R_Wing_01",            # Right inner wing + right under-wing missile (22.4 deg flap)
    "chop1_cannon_right": "Bone_R_Wing_02",             # Right outer wing tip (34.3 deg phase-whip flap)
    "chop1_calf_left": "Bone_L_Thigh001",               # Left rear Pteranodon claw (13.9 deg flight kick)
    "chop1_calf_right": "Bone_R_Thigh001(mirrored)",    # Right rear Pteranodon claw (13.9 deg flight kick)
    "chop1_foot_left": "Bone_L_Thigh",                  # Left rear thigh (9.6 deg flight tuck)
    "chop1_foot_right": "Bone_R_Thigh",                 # Right rear thigh (10.0 deg flight tuck)
}

def dict_to_mat4(d):
    return Matrix([
        [d["e00"], d["e01"], d["e02"], d["e03"]],
        [d["e10"], d["e11"], d["e12"], d["e13"]],
        [d["e20"], d["e21"], d["e22"], d["e23"]],
        [d["e30"], d["e31"], d["e32"], d["e33"]],
    ])

b_cog = dict_to_mat4(donor_bones["COG"]["bind_pose_matrix"])
b_inv_map = {bn: dict_to_mat4(donor_bones[bn]["bind_pose_matrix"]).inverted() for bn in RAMJET_JET_TO_SWOOP_DRIVER}

# Coordinate conversion from scaled Blender (bx, by, bz) to Unitycha_swoop_gs_01 (ux=-bx, uy=bz, uz=-by)
c_b2u = Matrix([
    [-1.0,  0.0, 0.0, 0.0],
    [ 0.0,  0.0, 1.0, 0.0],
    [ 0.0, -1.0, 0.0, 0.0],
    [ 0.0,  0.0, 0.0, 1.0],
])
c_w100_to_unity = c_b2u @ mat_scale
c_unity_to_w100 = c_w100_to_unity.inverted()

flap_anim_data = {
    "clip_name": "Swoop_Vehicle_WingFlap_transformed",
    "fps": 30.0,
    "frame_count": 58,
    "duration": 57.0 / 30.0,
    "bones": {bn: [] for bn in RAMJET_JET_TO_SWOOP_DRIVER},
}

prev_quats = {}
for f in range(1, 59):
    _, world_bf = evaluate_frame_matrices(f)
    t_sec = (f - 1) / 30.0
    for r_bone, s_bone in RAMJET_JET_TO_SWOOP_DRIVER.items():
        # Exact deformation in Blender world100 space from Frame 1 to Frame f
        delta_w100 = world_bf[s_bone] @ world_b1[s_bone].inverted()
        # Convert to Unity cha_swoop_gs_01 mesh space
        d_unity = c_w100_to_unity @ delta_w100 @ c_unity_to_w100
        # Compute local transform inside COG: T_{B|COG}(f) = B_COG @ D_unity(f) @ B_B^-1
        t_local_cog = b_cog @ d_unity @ b_inv_map[r_bone]
        loc, rot, _ = t_local_cog.decompose()
        if r_bone in prev_quats and prev_quats[r_bone].dot(rot) < 0.0:
            rot = -rot
        prev_quats[r_bone] = rot
        flap_anim_data["bones"][r_bone].append({
            "frame": f,
            "time": round(t_sec, 5),
            "pos": [round(loc.x, 6), round(loc.y, 6), round(loc.z, 6)],
            "rot": [round(rot.x, 6), round(rot.y, 6), round(rot.z, 6), round(rot.w, 6)],
            "px": round(loc.x, 6), "py": round(loc.y, 6), "pz": round(loc.z, 6),
            "rx": round(rot.x, 6), "ry": round(rot.y, 6), "rz": round(rot.z, 6), "rw": round(rot.w, 6),
        })

flap_anim_data["tracks"] = [
    {"bone": bn, "keys": klist} for bn, klist in flap_anim_data["bones"].items()
]

flap_json_path = UNITY_OUT_DIR / "swoop_native_wing_flap_58frames.json"
with open(flap_json_path, "w", encoding="utf-8") as f:
    json.dump(flap_anim_data, f, indent=2)
print(f"[✓] Exported 58-frame native Swoop wing-flapping curves to {flap_json_path}")

# Remove source objects now that mesh & animation curves are extracted
bpy.data.objects.remove(arm, do_unlink=True)
bpy.data.objects.remove(swoop_mesh, do_unlink=True)
for o in list(bpy.data.objects):
    if o.type == 'EMPTY':
        bpy.data.objects.remove(o, do_unlink=True)

# 7. Remap vertex groups to the 10 unit-scale Ramjet Jet bones
SWOOP_TO_RAMJET_JET_BONES = {vg.name: "chop1_chest_center" for vg in baked_swoop.vertex_groups}
SWOOP_TO_RAMJET_JET_BONES.update({
    "beak_the bottom": "chop1_back_center",
    "Bone_L_Wing_01(mirrored)": "chop1_forearm_left",
    "L_missile": "chop1_forearm_left",
    "Bone_L_Wing_02(mirrored)": "chop1_cannon_left",
    "Bone_R_Wing_01": "chop1_forearm_right",
    "R_missile": "chop1_forearm_right",
    "Bone_R_Wing_02": "chop1_cannon_right",
    "Bone_L_Thigh001": "chop1_calf_left",
    "Bone_L_Thigh002": "chop1_calf_left",
    "Bone_L_Thigh003": "chop1_calf_left",
    "Bone_L_Thigh004": "chop1_calf_left",
    "Bone_R_Thigh001(mirrored)": "chop1_calf_right",
    "Bone_R_Thigh002(mirrored)": "chop1_calf_right",
    "Bone_R_Thigh003(mirrored)": "chop1_calf_right",
    "Bone_R_Thigh004(mirrored)": "chop1_calf_right",
    "Bone_L_Thigh": "chop1_foot_left",
    "Bone_R_Thigh": "chop1_foot_right",
})

old_vg_names = [vg.name for vg in baked_swoop.vertex_groups]
vert_weights = [{} for _ in range(len(baked_swoop.data.vertices))]

for v in baked_swoop.data.vertices:
    for g in v.groups:
        vg_name = old_vg_names[g.group]
        target_bone = SWOOP_TO_RAMJET_JET_BONES.get(vg_name)
        if target_bone:
            vert_weights[v.index][target_bone] = vert_weights[v.index].get(target_bone, 0.0) + g.weight

for vi, wdict in enumerate(vert_weights):
    if not wdict:
        wdict["chop1_chest_center"] = 1.0

baked_swoop.vertex_groups.clear()
new_vg_map = {bname: baked_swoop.vertex_groups.new(name=bname) for bname in donor_bone_names}

# Keep smooth skin weights across wing joints so inner-to-outer wing bends seamlessly during flapping!
for vi, wdict in enumerate(vert_weights):
    tot = sum(wdict.values())
    if tot > 0:
        wdict = {k: v / tot for k, v in wdict.items()}
    else:
        wdict = {"chop1_chest_center": 1.0}
    for b, w in wdict.items():
        if b in new_vg_map and w > 1e-4:
            new_vg_map[b].add([vi], w, 'REPLACE')

print("[✓] Swoop vehicle vertex groups remapped to 10 unit-scale Ramjet jet bones (with smooth wing-joint weights).")

# 8. Remap UVs into Vehicle Atlas tile [0.004, 0.746] x [0.254, 0.996]
uvl_vh = baked_swoop.data.uv_layers.active.data
for p in baked_swoop.data.polygons:
    for li in p.loop_indices:
        u, v = uvl_vh[li].uv
        cu = min(max(u, 0.004), 0.996)
        cv = min(max(v, 0.004), 0.996)
        uvl_vh[li].uv = (0.004 + cu * (0.746 - 0.004), 0.254 + cv * (0.996 - 0.254))

print("[✓] All vehicle polygon UVs cleanly remapped and clamped into 2048 atlas tiles.")

unified_mesh = baked_swoop
unified_mesh.name = "cha_swoop_vh"

unified_mesh.data.materials.clear()
vh_mat = bpy.data.materials.new("M_Swoop_VH")
unified_mesh.data.materials.append(vh_mat)

# 9. Build Ramjet's clean 29-bone Jet Armature
arm_data = bpy.data.armatures.new("Ramjet_29_Jet_Armature")
new_arm = bpy.data.objects.new("cha_swoop_vh_Armature", arm_data)
bpy.context.scene.collection.objects.link(new_arm)
bpy.context.view_layer.objects.active = new_arm
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for bname in donor_bone_names:
    eb = arm_data.edit_bones.new(bname)
    head_pos = donor_blender_pos[bname]
    eb.head = head_pos
    eb.tail = head_pos + Vector((0.0, 0.0, 0.1))
    edit_bones[bname] = eb

for bname, eb in edit_bones.items():
    pname = donor_parent_map.get(bname)
    if pname and pname in edit_bones:
        eb.parent = edit_bones[pname]
        delta = eb.head - eb.parent.head
        if delta.length > 0.05 and (eb.parent.tail - eb.parent.head).length < 0.2:
            eb.parent.tail = eb.parent.head + delta * 0.35

bpy.ops.object.mode_set(mode='OBJECT')

unified_mesh.modifiers.clear()
arm_mod = unified_mesh.modifiers.new(name="Armature", type='ARMATURE')
arm_mod.object = new_arm
unified_mesh.parent = new_arm

# 10. Export FBX to 3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx
out_fbx = FBX_OUT_DIR / "swoop_vh_prepared.fbx"
unity_fbx = UNITY_OUT_DIR / "swoop_vh_prepared.fbx"

bpy.ops.object.select_all(action='DESELECT')
new_arm.select_set(True)
unified_mesh.select_set(True)
bpy.context.view_layer.objects.active = new_arm

bpy.ops.export_scene.fbx(
    filepath=str(out_fbx),
    use_selection=True,
    global_scale=1.0,
    apply_unit_scale=True,
    apply_scale_options='FBX_SCALE_ALL',
    bake_space_transform=False,
    object_types={'ARMATURE', 'MESH'},
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    add_leaf_bones=False,
    primary_bone_axis='Y',
    secondary_bone_axis='X',
    armature_nodetype='NULL',
    axis_forward='-Z',
    axis_up='Y',
)

shutil.copy2(out_fbx, unity_fbx)
print(f"[✓] Exported aligned Swoop Vehicle FBX to:\n  - {out_fbx}\n  - {unity_fbx}")
