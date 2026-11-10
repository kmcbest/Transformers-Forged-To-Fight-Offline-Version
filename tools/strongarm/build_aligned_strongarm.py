import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import bmesh
import json
import math
import mathutils
import numpy as np
from pathlib import Path

print("=== [Strongarm] Authoritative 1:1 Grafting onto Prowl Mother Chassis ===")

fbx_path = Path(r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")
prowl_rig_path = Path(r"E:\Agent\TFTF-blender\tools\strongarm\prowl_robot_rig.json")
uv_mapping_path = Path(r"E:\Agent\TFTF-blender\tools\strongarm\uv_atlas_mapping.json")
out_fbx_path = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Strongarm\strongarm_prepared.fbx")
out_fbx_path.parent.mkdir(parents=True, exist_ok=True)

# 1. Load Prowl authoritative rig data
with open(prowl_rig_path, "r", encoding="utf-8") as f:
    prowl_bones = json.load(f)

# Prowl authoritative rest positions in Unity:
# Left is -ux, Right is +ux.
# Height is +uy.
# Depth is +uz.
prowl_bone_pos_unity = {}
for b in prowl_bones:
    bp = b["bindpose"]
    mat = np.array([
        [bp['e00'], bp['e01'], bp['e02'], bp['e03']],
        [bp['e10'], bp['e11'], bp['e12'], bp['e13']],
        [bp['e20'], bp['e21'], bp['e22'], bp['e23']],
        [bp['e30'], bp['e31'], bp['e32'], bp['e33']]
    ])
    inv = np.linalg.inv(mat)
    prowl_bone_pos_unity[b["name"]] = (inv[0, 3], inv[1, 3], inv[2, 3])

# In Blender:
# We align so that after export to FBX and Unity import:
# X_unity = v.x, Y_unity = v.z, Z_unity = v.y
# Since Unity inverts X on FBX import (X_unity = -X_blender):
# In Blender: X_blender = -X_unity
# Y_blender = Z_unity (Forward/Depth)
# Z_blender = Y_unity (Height)
prowl_bone_pos_blender = {}
for bn, (ux, uy, uz) in prowl_bone_pos_unity.items():
    prowl_bone_pos_blender[bn] = (-ux, uz, uy)

# 2. Load UV atlas mapping
with open(uv_mapping_path, "r", encoding="utf-8") as f:
    uv_mapping = json.load(f)

mat_to_slot = {
    "chest_DK": "chest_MD",
    "face_maskOff_DK": "face_maskOn_MD",
    "bot_cc_faceMaskOn": "face_maskOn_MD",
    "body_DK": "body_MD",
    "bot_cc_bodyD": "body_MD",
    "hand_DK": "hand_MD",
    "leg_DK": "leg_MD",
    "head_DK": "head_MD",
    "doorWing_DK": "doorWing_MD",
    "bot_cc_doorWindow": "doorWing_MD",
    "blaster_DK": "blaster_MD",
}

# 3. Import Strongarm FBX
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

orig_arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
if orig_arm.animation_data:
    orig_arm.animation_data_clear()
orig_arm.data.pose_position = 'REST'
bpy.context.view_layer.update()

# Record Maya bone joints in raw Maya coords before deleting orig_arm
piv_l = orig_arm.data.bones["bot:jt_shoulder_L"].head_local.copy()
piv_r = orig_arm.data.bones["bot:jt_shoulder_R"].head_local.copy()
wr_l = orig_arm.data.bones["bot:jt_wrist_L"].head_local.copy()
wr_r = orig_arm.data.bones["bot:jt_wrist_R"].head_local.copy()

mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
print(f"Imported {len(mesh_objs)} mesh objects.")

# 4. Remove battle mask
mask_names = ["bot:mask_geo", "bot:faceMaskOn_jaw_geo"]
for m in list(mesh_objs):
    if m.name in mask_names:
        bpy.data.objects.remove(m, do_unlink=True)
        mesh_objs.remove(m)

# Apply modifiers and unparent (PRESERVING original Maya vertex groups!)
for m in mesh_objs:
    bpy.ops.object.select_all(action='DESELECT')
    m.select_set(True)
    bpy.context.view_layer.objects.active = m
    for mod in list(m.modifiers):
        if mod.type == 'ARMATURE':
            bpy.ops.object.modifier_apply(modifier=mod.name)
    m.parent = None
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

bpy.data.objects.remove(orig_arm, do_unlink=True)

# Identify arm-chain & clav objects directly from active Maya vertex groups
def mesh_has_any_vg(m, substrs):
    active = {m.vertex_groups[g.group].name for v in m.data.vertices for g in v.groups if g.weight > 0.05}
    return any(any(s in vg for s in substrs) for vg in active)

arm_vg_keys_l = ("jt_shoulder_L", "jt_elbow_L", "jt_wrist_L", "thumb1_L", "thumb2_L", "thumb3_L", "index1_L", "index2_L", "index3_L", "middle1_L", "middle2_L", "middle3_L", "ring1_L", "ring2_L", "ring3_L", "pinky1_L", "pinky2_L", "pinky3_L")
arm_vg_keys_r = tuple(k[:-2] + "_R" for k in arm_vg_keys_l)
left_arm_objs = [m.name for m in mesh_objs if mesh_has_any_vg(m, arm_vg_keys_l)]
right_arm_objs = [m.name for m in mesh_objs if mesh_has_any_vg(m, arm_vg_keys_r)]
print(f"Identified {len(left_arm_objs)} Left arm objects, {len(right_arm_objs)} Right arm objects")

# 5. Pose Strongarm Arms from Maya A-pose to relaxed +11.5 deg outward flare around jt_shoulder_L/R
# In raw Maya space: Y is Up, X is Left/Right (L is +X, R is -X), Z is Forward
arm_vec = wr_l - piv_l
cur_angle_rad = math.atan2(arm_vec.x, -arm_vec.y)
target_flare_rad = math.radians(11.5)
rot_delta_rad = cur_angle_rad - target_flare_rad
print(f"Detected shoulder->wrist angle: {math.degrees(cur_angle_rad):.2f} deg; rotating by -{math.degrees(rot_delta_rad):.2f} deg -> +11.50 deg relaxed outward flare")

R_l = mathutils.Matrix.Rotation(-rot_delta_rad, 4, 'Z')
M_l = mathutils.Matrix.Translation(piv_l) @ R_l @ mathutils.Matrix.Translation(-piv_l)
for name in left_arm_objs:
    o = bpy.data.objects.get(name)
    if o:
        for v in o.data.vertices:
            v.co = M_l @ v.co
        o.data.update()

arm_vec_r = wr_r - piv_r
cur_angle_r = math.atan2(-arm_vec_r.x, -arm_vec_r.y)
rot_delta_r = cur_angle_r - target_flare_rad
R_r = mathutils.Matrix.Rotation(rot_delta_r, 4, 'Z')
M_r = mathutils.Matrix.Translation(piv_r) @ R_r @ mathutils.Matrix.Translation(-piv_r)
for name in right_arm_objs:
    o = bpy.data.objects.get(name)
    if o:
        for v in o.data.vertices:
            v.co = M_r @ v.co
        o.data.update()

# 6. Remap UVs
for m in mesh_objs:
    mesh = m.data
    slot_name = None
    if m.material_slots and m.material_slots[0].material:
        mat_name = m.material_slots[0].material.name
        slot_name = mat_to_slot.get(mat_name)
        if not slot_name:
            for k, v in mat_to_slot.items():
                if k.lower() in mat_name.lower():
                    slot_name = v
                    break
    if not slot_name:
        slot_name = "body_MD"

    info = uv_mapping.get(slot_name, uv_mapping["body_MD"])
    scale_u = info["scale_u"]
    scale_v = info["scale_v"]
    offset_u = info["offset_u"]
    offset_v = info["offset_v"]

    if mesh.uv_layers.active:
        uv_data = mesh.uv_layers.active.data
        for loop in uv_data:
            loop.uv[0] = loop.uv[0] * scale_u + offset_u
            loop.uv[1] = loop.uv[1] * scale_v + offset_v

# 7. Coordinate alignment: Maya (Y up, Z fwd, X L/R) -> Blender (Z up, Y fwd, X L/R)
# Rotate +90 deg around X
R_maya_blender = mathutils.Matrix.Rotation(1.5707963, 4, 'X')
for m in mesh_objs:
    for v in m.data.vertices:
        v.co = R_maya_blender @ v.co
    m.data.update()

# Scale to match Prowl's anatomical height
# Head in Prowl: Y=8.399. Foot: 0.0.
# Strongarm head center in Blender:
head_o = bpy.data.objects["bot:face_geo"]
head_z = sum(v.co.z for v in head_o.data.vertices) / len(head_o.data.vertices)
min_foot_z = min(v.co.z for m in mesh_objs for v in m.data.vertices if "shoe" in m.name.lower())

print(f"Strongarm head_Z={head_z:.4f}, foot_Z={min_foot_z:.4f}")
scale_factor = 8.399 / (head_z - min_foot_z)
print(f"Calculated Anatomical Scale Factor = {scale_factor:.4f}")

# In Maya after +90 X: Face is at -Y.
# In Blender: Face should point +Y (Forward), Left is +X, Right is -X.
# Scale X by +scale_factor (Left is +X, Right is -X).
# Scale Y by -scale_factor (Face flips to +Y).
# Scale Z by +scale_factor (Height).
S_mat = mathutils.Matrix.Diagonal((scale_factor, -scale_factor, scale_factor, 1.0))
for m in mesh_objs:
    for v in m.data.vertices:
        v.co = S_mat @ v.co
    m.data.update()

# Ground feet to Z = 0
ground_z = min(v.co.z for m in mesh_objs for v in m.data.vertices if "shoe" in m.name.lower())
for m in mesh_objs:
    for v in m.data.vertices:
        v.co.z -= ground_z
    m.data.update()

# Offset arm assemblies outward to align with Prowl's shoulder width
# Prowl LeftArm in Blender is at X = -ux = -(-2.057) = +2.057.
# Strongarm Left shoulder ball center:
sb_l = bpy.data.objects["bot:shoulderBall_geo_L"]
cur_sb_l_x = sum(v.co.x for v in sb_l.data.vertices) / len(sb_l.data.vertices)
target_sb_l_x = prowl_bone_pos_blender["LeftShoulder"][0] # around +1.407
arm_dx_l = target_sb_l_x - cur_sb_l_x
print(f"Left Arm outward offset = {arm_dx_l:.3f}m")

for name in left_arm_objs + ["bot:shoulderBall_geo_L", "bot:shoulderJoint_geo_L"]:
    o = bpy.data.objects.get(name)
    if o:
        for v in o.data.vertices:
            v.co.x += arm_dx_l
        o.data.update()

for name in right_arm_objs + ["bot:shoulderBall_geo_R", "bot:shoulderJoint_geo_R"]:
    o = bpy.data.objects.get(name)
    if o:
        for v in o.data.vertices:
            v.co.x -= arm_dx_l
        o.data.update()

# Align Pelvis Y to Prowl Hips Y
waist_o = bpy.data.objects["bot:waist_geo"]
cur_waist_y = sum(v.co.y for v in waist_o.data.vertices) / len(waist_o.data.vertices)
target_waist_y = prowl_bone_pos_blender["Hips"][1]
offset_y = target_waist_y - cur_waist_y
print(f"Aligning Pelvis Y: current={cur_waist_y:.3f}, target={target_waist_y:.3f}, offset={offset_y:.3f}")
for m in mesh_objs:
    for v in m.data.vertices:
        v.co.y += offset_y
    m.data.update()

# 8. Authoritative Maya Skin-Weight Transfer onto Prowl 50-Bone Rig (preserving 3-knuckle fingers!)
MAYA_TO_PROWL_BONE = {
    "bot:jt_pelvis": "Hips",
    "bot:jt_hipArmor_L": "Hips",
    "bot:jt_hipArmor_R": "Hips",
    "bot:jt_spine1": "Spine",
    "bot:jt_spine2": "Spine1",
    "bot:jt_spine3": "Spine1",
    "bot:jt_wing_L": "Spine1",
    "bot:jt_wing_R": "Spine1",
    "bot:jt_neck": "Head",
    "bot:jt_head": "Head",
    "bot:jt_face": "Head",
}
for _s, _side in [("L", "Left"), ("R", "Right")]:
    MAYA_TO_PROWL_BONE[f"bot:jt_clav_{_s}"] = f"{_side}Shoulder"
    MAYA_TO_PROWL_BONE[f"bot:jt_shoulder_{_s}"] = f"{_side}Arm"
    MAYA_TO_PROWL_BONE[f"bot:jt_elbow_{_s}"] = f"{_side}ForeArm"
    MAYA_TO_PROWL_BONE[f"bot:jt_wrist_{_s}"] = f"{_side}Hand"
    MAYA_TO_PROWL_BONE[f"bot:jt_hip_{_s}"] = f"{_side}UpLeg"
    MAYA_TO_PROWL_BONE[f"bot:jt_knee_{_s}"] = f"{_side}Leg"
    for _aa in (1, 2, 4):
        MAYA_TO_PROWL_BONE[f"bot:jt_ankleArmor{_aa}_{_s}"] = f"{_side}Leg"
    MAYA_TO_PROWL_BONE[f"bot:jt_ankle_{_s}"] = f"{_side}ToeBase"
    MAYA_TO_PROWL_BONE[f"bot:jt_toe_{_s}"] = f"{_side}ToeBase"
    for _f_src, _f_dst in [("thumb", "Thumb"), ("index", "Index"), ("middle", "Middle"), ("ring", "Ring"), ("pinky", "Pinky")]:
        for _k in (1, 2, 3):
            MAYA_TO_PROWL_BONE[f"bot:jt_{_f_src}{_k}_{_s}"] = f"{_side}Hand{_f_dst}{_k}"

for m in mesh_objs:
    old_idx_to_name = {vg.index: vg.name for vg in m.vertex_groups}
    # Collect remapped per-vertex weights before clearing
    per_vert_weights = []
    for v in m.data.vertices:
        wmap = {}
        for g in v.groups:
            if g.weight <= 1e-4:
                continue
            src_name = old_idx_to_name.get(g.group, "")
            dst_name = MAYA_TO_PROWL_BONE.get(src_name)
            if dst_name:
                wmap[dst_name] = wmap.get(dst_name, 0.0) + g.weight
        if not wmap:
            wmap["Spine1"] = 1.0
        total_w = sum(wmap.values())
        if total_w > 0:
            for k in wmap:
                wmap[k] /= total_w
        # Smoothly anchor palm/wrist sleeve collar tucked inside hollow forearm cuff (Z > 4.34)
        # to LeftForeArm/RightForeArm so wrist bending cannot poke through the forearm box wall.
        # Exclude thumb vertices so the thumb root never gets pinned to ForeArm!
        w_thumb_pre = sum(val for key, val in wmap.items() if "Thumb" in key)
        if "palm_geo" in m.name.lower() and v.co.z > 4.34 and w_thumb_pre < 0.05:
            side_prefix = "Left" if ("_l" in m.name.lower() or v.co.x > 0) else "Right"
            hand_b = f"{side_prefix}Hand"
            forearm_b = f"{side_prefix}ForeArm"
            if hand_b in wmap and wmap[hand_b] > 0:
                blend_t = min(1.0, (v.co.z - 4.34) / 0.10)
                move_w = wmap[hand_b] * blend_t
                wmap[hand_b] -= move_w
                wmap[forearm_b] = wmap.get(forearm_b, 0.0) + move_w
                if wmap[hand_b] <= 1e-4:
                    del wmap[hand_b]
        per_vert_weights.append(wmap)

    # Align Strongarm downward-hanging rest-pose thumb (-Z) forward to +Y horizontal
    # so it matches Prowl's Avatar00 Humanoid Thumb bind pose (prevents thumb curling backward into forearm cuff!)
    if "palm_geo" in m.name.lower():
        sock_pts = []
        tip_pts = []
        for v_idx, v in enumerate(m.data.vertices):
            wm = per_vert_weights[v_idx]
            wt = sum(val for key, val in wm.items() if "Thumb" in key)
            wt3 = sum(val for key, val in wm.items() if "Thumb3" in key)
            if 0.15 <= wt <= 0.85:
                sock_pts.append(v.co.copy())
            if wt3 >= 0.80:
                tip_pts.append(v.co.copy())
        if sock_pts and tip_pts:
            piv = sum(sock_pts, sock_pts[0] * 0.0) / len(sock_pts)
            tip_c = sum(tip_pts, tip_pts[0] * 0.0) / len(tip_pts)
            tvec = tip_c - piv
            if math.hypot(tvec.y, tvec.z) > 1e-4:
                rot_x = -math.atan2(tvec.z, tvec.y)
                print(f"[*] Aligning thumb rest pose on {m.name}: piv=({piv.x:.3f},{piv.y:.3f},{piv.z:.3f}) tip=({tip_c.x:.3f},{tip_c.y:.3f},{tip_c.z:.3f}) rotX={math.degrees(rot_x):.1f} deg")
                for v_idx, v in enumerate(m.data.vertices):
                    wm = per_vert_weights[v_idx]
                    wt = sum(val for key, val in wm.items() if "Thumb" in key)
                    if wt <= 1e-4:
                        continue
                    ang = rot_x * wt
                    ca = math.cos(ang)
                    sa = math.sin(ang)
                    dy = v.co.y - piv.y
                    dz = v.co.z - piv.z
                    v.co.y = piv.y + dy * ca - dz * sa
                    v.co.z = piv.z + dy * sa + dz * ca
                m.data.update()

    m.vertex_groups.clear()
    dst_vgs = {}
    for v_idx, wmap in enumerate(per_vert_weights):
        for dst_name, w in wmap.items():
            if dst_name not in dst_vgs:
                dst_vgs[dst_name] = m.vertex_groups.new(name=dst_name)
            dst_vgs[dst_name].add([v_idx], w, 'REPLACE')

# 9. Join submeshes into single mesh
bpy.ops.object.select_all(action='DESELECT')
for m in mesh_objs:
    m.select_set(True)
bpy.context.view_layer.objects.active = mesh_objs[0]
bpy.ops.object.join()
robot_mesh = bpy.context.view_layer.objects.active
robot_mesh.name = "cha_prowl_gs_deluxe2016_00"

# 10. Create 50-Bone Armature in Blender
arm_data = bpy.data.armatures.new("character_model_arm")
new_arm = bpy.data.objects.new("character_model", arm_data)
bpy.context.scene.collection.objects.link(new_arm)
bpy.context.view_layer.objects.active = new_arm
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for b in prowl_bones:
    bn = b["name"]
    bx, by, bz = prowl_bone_pos_blender[bn]
    eb = arm_data.edit_bones.new(bn)
    eb.head = (bx, by, bz)
    eb.tail = (bx, by, bz + 0.15)
    edit_bones[bn] = eb

parent_map = {
    "Spine": "Hips",
    "Spine1": "Spine",
    "Head": "Spine1",
    "LeftShoulder": "Spine1",
    "LeftArm": "LeftShoulder",
    "LeftArmRoll": "LeftArm",
    "LeftForeArm": "LeftArm",
    "LeftHand": "LeftForeArm",
    "RightShoulder": "Spine1",
    "RightArm": "RightShoulder",
    "RightArmRoll": "RightArm",
    "RightForeArm": "RightArm",
    "RightHand": "RightForeArm",
    "LeftUpLeg": "Hips",
    "LeftLeg": "LeftUpLeg",
    "LeftToeBase": "LeftLeg",
    "RightUpLeg": "Hips",
    "RightLeg": "RightUpLeg",
    "RightToeBase": "RightLeg",
}
for side in ["Left", "Right"]:
    for finger in ["Thumb", "Index", "Middle", "Ring", "Pinky"]:
        parent_map[f"{side}Hand{finger}1"] = f"{side}Hand"
        parent_map[f"{side}Hand{finger}2"] = f"{side}Hand{finger}1"
        parent_map[f"{side}Hand{finger}3"] = f"{side}Hand{finger}2"

for child_name, p_name in parent_map.items():
    if child_name in edit_bones and p_name in edit_bones:
        edit_bones[child_name].parent = edit_bones[p_name]

bpy.ops.object.mode_set(mode='OBJECT')

robot_mesh.parent = new_arm
arm_mod = robot_mesh.modifiers.new(name="Armature", type='ARMATURE')
arm_mod.object = new_arm
arm_mod.use_vertex_groups = True

# Ensure consistent outward winding & normals for Robot mesh before FBX export
import bmesh as _bmesh
_bm_robot = _bmesh.new()
_bm_robot.from_mesh(robot_mesh.data)
_bmesh.ops.reverse_faces(_bm_robot, faces=_bm_robot.faces)
_bm_robot.to_mesh(robot_mesh.data)
_bm_robot.free()
robot_mesh.data.update()

# Material
mat = bpy.data.materials.new("M_Strongarm_Main")
mat.use_nodes = True
robot_mesh.data.materials.clear()
robot_mesh.data.materials.append(mat)

# Export FBX
bpy.ops.object.select_all(action='DESELECT')
new_arm.select_set(True)
robot_mesh.select_set(True)
bpy.context.view_layer.objects.active = new_arm

bpy.ops.export_scene.fbx(
    filepath=str(out_fbx_path),
    check_existing=False,
    use_selection=True,
    bake_anim=False,
    add_leaf_bones=False,
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y'
)

print(f"\n[✓] Successfully regenerated Strongarm FBX: {out_fbx_path}")
