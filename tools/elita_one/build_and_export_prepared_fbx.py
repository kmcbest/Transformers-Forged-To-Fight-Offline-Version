import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
import mathutils
import bpy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"
REST_JSON = ROOT / "tools" / "elita_one" / "arcee_unity_rest_matrices.json"
HIERARCHY_JSON = ROOT / "tools" / "elita_one" / "arcee_bone_hierarchy.json"
MAPPING_JSON = ROOT / "tools" / "elita_one" / "elita_to_arcee_mapping.json"
OUT_FBX = ROOT / "toolchain" / "unity_build_project" / "Assets" / "ElitaOne" / "elita_one_prepared.fbx"

print(f"=== Building and Exporting Prepared FBX with Knuckle-Aligned Finger Bones ===")
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load Metadata
with open(HIERARCHY_JSON, "r", encoding="utf-8") as f:
    hierarchy = json.load(f)

with open(REST_JSON, "r", encoding="utf-8") as f:
    rest_data = json.load(f)

with open(MAPPING_JSON, "r", encoding="utf-8") as f:
    bone_mapping = json.load(f)

with open(ROOT / "tools" / "elita_one" / "arcee_63_bones.json", "r", encoding="utf-8") as f:
    arcee_63_bones = json.load(f)
valid_bones = set(arcee_63_bones) | {"Reference"}

# Solid overrides
bone_mapping["l_lower_cover_wheel_skin"] = "LeftArm"
bone_mapping["l_lower_wheel_skin"] = "LeftArm"
bone_mapping["l_lower_wheel_skin_end"] = "LeftArm"
bone_mapping["r_lower_cover_wheel_skin"] = "RightArm"
bone_mapping["r_lower_wheel_skin"] = "RightArm"
bone_mapping["r_lower_wheel_skin_end"] = "RightArm"

bone_mapping["l_piston_lower_arm_start_skin"] = "LeftForeArm"
bone_mapping["l_piston_lower_arm_start_skin_end"] = "LeftForeArm"
bone_mapping["r_piston_lower_arm_start_skin"] = "RightForeArm"
bone_mapping["r_piston_lower_arm_start_skin_end"] = "RightForeArm"

for p_name in [
    "l_piston_leg_end_01_skin", "l_piston_leg_end_01_skin_end",
    "l_piston_leg_end_02_skin", "l_piston_leg_end_02_skin_end",
    "r_piston_leg_end_01_skin", "r_piston_leg_end_01_skin_end",
    "r_piston_leg_end_02_skin", "r_piston_leg_end_02_skin_end",
    "l_piston_leg_start_01_skin3", "l_piston_leg_start_01_skin3_end",
    "l_piston_leg_start_02_skin4", "l_piston_leg_start_02_skin4_end",
    "r_piston_leg_start_01_skin7", "r_piston_leg_start_01_skin7_end",
    "r_piston_leg_start_02_skin8", "r_piston_leg_start_02_skin8_end",
    "l_cover_hips_skin", "r_cover_hips_skin"
]:
    bone_mapping[p_name] = "Hips"

bone_mapping["l_shoulder_pistons_skin"] = "Spine1"
bone_mapping["l_shoulder_pistons_skin_end"] = "Spine1"
bone_mapping["r_shoulder_pistons_skin"] = "Spine1"
bone_mapping["r_shoulder_pistons_skin_end"] = "Spine1"

for p_name in [
    "l_piston_leg_start_01_skin", "l_piston_leg_start_01_skin_end",
    "l_piston_leg_start_02_skin", "l_piston_leg_start_02_skin_end",
    "l_foot_skin", "l_foot_heel_skin", "l_foot_heel_skin_end"
]:
    bone_mapping[p_name] = "LeftFoot"

for p_name in [
    "r_piston_leg_start_01_skin", "r_piston_leg_start_01_skin_end",
    "r_piston_leg_start_02_skin", "r_piston_leg_start_02_skin_end",
    "r_foot_skin", "r_foot_heel_skin", "r_foot_heel_skin_end"
]:
    bone_mapping[p_name] = "RightFoot"

# 2. Import Elita One FBX First to extract Posed Hand Transforms!
print("[*] Importing Elita One FBX...")
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

fbx_arm = bpy.data.objects.get("SK_CH_11")
elita_mesh = bpy.data.objects.get("SK_CH_11.001")

orig_mat_slots = [p.material_index for p in elita_mesh.data.polygons]
new_poly_slots = [0 if idx in (0, 1) else 1 for idx in orig_mat_slots]

scale_s = 8.840 / 8.083
M_transform = mathutils.Matrix.Rotation(math.radians(90.0), 4, 'Z') @ mathutils.Matrix.Scale(scale_s, 4)

fbx_arm.data.transform(M_transform)
elita_mesh.data.transform(M_transform)

# Pose FBX Armature to rotate A-pose arms inward
bpy.context.view_layer.objects.active = fbx_arm
bpy.ops.object.mode_set(mode='POSE')

l_sh = fbx_arm.data.bones.get("l_upperarm_skin").head_local
r_sh = fbx_arm.data.bones.get("r_upperarm_skin").head_local
l_wr = fbx_arm.data.bones.get("l_hand_skin").head_local
r_wr = fbx_arm.data.bones.get("r_hand_skin").head_local

target_l_wrist = mathutils.Vector((-1.2848, -0.0372, 4.2729))
target_r_wrist = mathutils.Vector(( 1.2848, -0.0372, 4.2729))

v_l_curr = l_wr - l_sh
v_l_targ = target_l_wrist - l_sh
q_l = v_l_curr.rotation_difference(v_l_targ)

v_r_curr = r_wr - r_sh
v_r_targ = target_r_wrist - r_sh
q_r = v_r_curr.rotation_difference(v_r_targ)

pb_l = fbx_arm.pose.bones.get("l_upperarm_skin")
pb_r = fbx_arm.pose.bones.get("r_upperarm_skin")

R_l_rest = fbx_arm.data.bones.get("l_upperarm_skin").matrix_local.to_3x3()
q_l_local = (R_l_rest.inverted() @ q_l.to_matrix() @ R_l_rest).to_quaternion()
pb_l.rotation_quaternion = q_l_local

R_r_rest = fbx_arm.data.bones.get("r_upperarm_skin").matrix_local.to_3x3()
q_r_local = (R_r_rest.inverted() @ q_r.to_matrix() @ R_r_rest).to_quaternion()
pb_r.rotation_quaternion = q_r_local

bpy.context.view_layer.update()

# Extract 30 Posed Finger Bone Heads and Tails directly from Elita!
elita_finger_to_arcee = {
    "l_thumb_01_skin": "LeftHandThumb1",
    "l_thumb_02_skin": "LeftHandThumb2",
    "l_thumb_03_skin": "LeftHandThumb3",
    "l_index_01_skin": "LeftHandIndex1",
    "l_index_02_skin": "LeftHandIndex2",
    "l_index_03_skin": "LeftHandIndex3",
    "l_middle_01_skin": "LeftHandMiddle1",
    "l_middle_02_skin": "LeftHandMiddle2",
    "l_middle_03_skin": "LeftHandMiddle3",
    "l_ring_01_skin": "LeftHandRing1",
    "l_ring_02_skin": "LeftHandRing2",
    "l_ring_03_skin": "LeftHandRing3",
    "l_pinky_01_skin": "LeftHandPinky1",
    "l_pinky_02_skin": "LeftHandPinky2",
    "l_pinky_03_skin": "LeftHandPinky3",
    "r_thumb_01_skin": "RightHandThumb1",
    "r_thumb_02_skin": "RightHandThumb2",
    "r_thumb_03_skin": "RightHandThumb3",
    "r_index_01_skin": "RightHandIndex1",
    "r_index_02_skin": "RightHandIndex2",
    "r_index_03_skin": "RightHandIndex3",
    "r_middle_01_skin": "RightHandMiddle1",
    "r_middle_02_skin": "RightHandMiddle2",
    "r_middle_03_skin": "RightHandMiddle3",
    "r_ring_01_skin": "RightHandRing1",
    "r_ring_02_skin": "RightHandRing2",
    "r_ring_03_skin": "RightHandRing3",
    "r_pinky_01_skin": "RightHandPinky1",
    "r_pinky_02_skin": "RightHandPinky2",
    "r_pinky_03_skin": "RightHandPinky3",
}

finger_head_tail = {}
for e_name, a_name in elita_finger_to_arcee.items():
    pb = fbx_arm.pose.bones.get(e_name)
    if pb:
        finger_head_tail[a_name] = (pb.head.copy(), pb.tail.copy())

print(f"[✓] Extracted {len(finger_head_tail)} knuckle-aligned finger bone positions from Elita!")

bpy.ops.object.mode_set(mode='OBJECT')

# Apply armature deformation to mesh to bake the aligned rest pose
bpy.context.view_layer.objects.active = elita_mesh
for m in elita_mesh.modifiers:
    if m.type == 'ARMATURE':
        bpy.ops.object.modifier_apply(modifier=m.name)
        break

bpy.data.objects.remove(fbx_arm, do_unlink=True)

# 3. Build 63-Bone Armature "character_model" with Knuckle-Aligned Fingers
C = mathutils.Matrix((
    (1, 0, 0, 0),
    (0, 0, 1, 0),
    (0, 1, 0, 0),
    (0, 0, 0, 1)
))

arm_data = bpy.data.armatures.new("character_model")
arm_obj = bpy.data.objects.new("character_model", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

edit_bones = {}
for b in rest_data["bones"]:
    bname = b["name"]
    if bname in edit_bones or bname not in valid_bones:
        continue
    
    eb = arm_data.edit_bones.new(bname)
    if bname in finger_head_tail:
        # Use Elita's exact knuckle head & tail!
        head, tail = finger_head_tail[bname]
        eb.head = head
        eb.tail = tail
    else:
        m_raw = b["m"]
        M_u = mathutils.Matrix((m_raw[0:4], m_raw[4:8], m_raw[8:12], m_raw[12:16]))
        M_b = C @ M_u @ C
        eb.head = M_b.translation
        eb.tail = M_b.translation + mathutils.Vector((0.0, 0.08, 0.0))
    edit_bones[bname] = eb

for bname, eb in edit_bones.items():
    eb.use_connect = False
    pname = hierarchy.get(bname)
    if pname and pname in edit_bones:
        eb.parent = edit_bones[pname]

bpy.ops.object.mode_set(mode='OBJECT')
print(f"[✓] Created 63-bone Armature 'character_model' with 30 knuckle-aligned finger bones!")

# 4. Remap Vertex Groups to 63 Arcee Bones
print("[*] Remapping Elita One vertex groups to 63 Arcee bones...")
remapped_weights = {v.index: {} for v in elita_mesh.data.vertices}
for v in elita_mesh.data.vertices:
    for g in v.groups:
        orig_name = elita_mesh.vertex_groups[g.group].name
        target_bone = bone_mapping.get(orig_name)
        if target_bone:
            remapped_weights[v.index][target_bone] = remapped_weights[v.index].get(target_bone, 0.0) + g.weight

elita_mesh.vertex_groups.clear()
new_vgs = {}
for bname in arcee_63_bones:
    if bname not in new_vgs:
        new_vgs[bname] = elita_mesh.vertex_groups.new(name=bname)

for v_idx, w_dict in remapped_weights.items():
    if not w_dict: continue
    top_4 = sorted(w_dict.items(), key=lambda kv: kv[1], reverse=True)[:4]
    sum_w = sum(w for _, w in top_4)
    if sum_w > 0:
        for bname, w in top_4:
            norm_w = w / sum_w
            if norm_w > 0.001 and bname in new_vgs:
                new_vgs[bname].add([v_idx], norm_w, 'REPLACE')

# Bind to character_model armature
mod_e = elita_mesh.modifiers.new(name="Armature", type='ARMATURE')
mod_e.object = arm_obj
mod_e.use_vertex_groups = True
elita_mesh.parent = arm_obj

# 5. Set up 2 Materials matching Arcee submesh contract
mat_main = bpy.data.materials.new(name="cha_elita_one_main")
mat_vh = bpy.data.materials.new(name="cha_elita_one_vh")

elita_mesh.data.materials.clear()
elita_mesh.data.materials.append(mat_main)
elita_mesh.data.materials.append(mat_vh)

for p, s_idx in zip(elita_mesh.data.polygons, new_poly_slots):
    p.material_index = s_idx

elita_mesh.name = "cha_elita_one_gs_00"
arm_obj.name = "character_model"

arm_obj.location = (0.0, 0.0, 0.0)
elita_mesh.location = (0.0, 0.0, 0.0)
bpy.context.view_layer.update()

# Limit influences & normalize in weight paint mode
bpy.context.view_layer.objects.active = elita_mesh
bpy.ops.object.mode_set(mode='WEIGHT_PAINT')
bpy.ops.object.vertex_group_limit_total(group_select_mode='ALL', limit=4)
bpy.ops.object.vertex_group_normalize_all(group_select_mode='ALL', lock_active=False)
bpy.ops.object.mode_set(mode='OBJECT')

# 6. Export FBX
bpy.ops.object.select_all(action='DESELECT')
elita_mesh.select_set(True)
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj

OUT_FBX.parent.mkdir(parents=True, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=str(OUT_FBX),
    use_selection=True,
    bake_anim=False,
    add_leaf_bones=False
)

print(f"[✓] SUCCESS: Exported knuckle-aligned prepared FBX to {OUT_FBX} ({OUT_FBX.stat().st_size / (1024*1024):.2f} MB)")
