import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json
import math
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path

print("=== [StarSaber] Building HITL Posing Rig FBX for Unity (v2 Exact Knuckle Pivots) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models" / "StarSaber" / "source" / "StarSaber.fbx"
DONOR_REF_DIR = ROOT / "3rd-party-models" / "StarSaber" / "00_donor_reference"
UNITY_ASSETS = ROOT / "toolchain" / "unity_build_project" / "Assets" / "StarSaber"
UNITY_ASSETS.mkdir(parents=True, exist_ok=True)

with open(DONOR_REF_DIR / "jetfire_54_bones_truth.json", "r", encoding="utf-8") as f:
    donor_bones_data = json.load(f)

with open(DONOR_REF_DIR / "jetfire_donor_summary.json", "r", encoding="utf-8") as f:
    donor_summary = json.load(f)

# Keep 39 non-right-finger Jetfire bones (omit unused RightHandThumb..Pinky clutter for clean HITL hierarchy)
JETFIRE_BASE_BONES = [
    bn for bn in donor_summary["bone_names"]
    if not (bn.startswith("RightHand") and bn != "RightHand")
]

def unity_to_blender(upos):
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))

# Map from Star Saber original vertex groups to Jetfire bones,
# EXCEPT the 9 right hand finger groups which remain independent bones for HITL posing!
VGROUP_MAP = {
    # Head & Neck
    "Dummy_Head_01": "Head",
    "Dummy_Head_02": "Head",

    # Spine & Torso & Hips
    "Dummy_Root": "Hips",
    "Dummy297": "Hips",
    "Dummy298": "Hips",
    "Dummy299": "Hips",
    "PelvisL": "Hips",
    "PelvisR": "Hips",
    "Dummy_Spine": "Spine",
    "Dummy_Body_04": "Spine",
    "Dummy_Body_05": "Spine1",
    "Point005": "Spine1",
    "Point006": "Spine1",
    "Point008": "Spine1",
    "Dummy_Back pack_01": "Spine1",
    "Dummy_Back pack_02": "Spine1",
    "Dummy_Back pack_03": "Spine1",
    "FrontL": "Hips",
    "FrontWingL": "Spine1",
    "FrontR": "Hips",
    "FrontWingR": "Spine1",

    # Left Leg
    "Dummy_Leg_01": "LeftUpLeg",
    "Dummy_Leg_02": "LeftUpLeg",
    "Dummy_Leg_03": "LeftLeg",
    "Dummy_Leg_05": "LeftLeg",
    "BoosterL": "LeftLeg",
    "LegWingL": "LeftLeg",
    "LegWingL2": "LeftLeg",
    "Dummy_Foot_02": "LeftFoot",
    "Dummy_Foot_03": "LeftFoot",
    "Dummy_Foot_01": "LeftToeBase",

    # Right Leg
    "Dummy_Leg_007": "RightUpLeg",
    "Dummy_Leg_008": "RightUpLeg",
    "Dummy_Leg_009": "RightLeg",
    "Dummy_Leg_011": "RightLeg",
    "BoosterR": "RightLeg",
    "LegWingL003": "RightLeg",
    "LegWingR": "RightLeg",
    "Dummy_Foot_005": "RightFoot",
    "Dummy_Foot_006": "RightFoot",
    "Dummy_Foot_004": "RightToeBase",

    # Left Arm & Hand (Track B: folded to LeftHand)
    "Dummy_Shoulder_01": "LeftShoulder",
    "Dummy_Shoulder_012": "LeftShoulder",
    "UpperArmL": "LeftArm",
    "Dummy_Arm_01": "LeftForeArm",
    "Dummy_hand_01": "LeftHand",
    "Hand_L_1": "LeftHand",
    "Hand_L_4": "LeftHand",
    "Hand_L_5": "LeftHand",
    "Hand_L_2": "LeftHand",
    "Hand_L_6": "LeftHand",
    "Hand_L_7": "LeftHand",
    "Hand_L_3": "LeftHand",
    "Hand_L_8": "LeftHand",
    "Hand_L_9": "LeftHand",

    # Right Arm & Palm
    "Dummy_Shoulder_004": "RightShoulder",
    "Dummy_Shoulder_0042": "RightShoulderPad",
    "UpperArmR": "RightArm",
    "Dummy_Arm_003": "RightForeArm",
    "Dummy_hand_002": "RightHand",
}

RIGHT_FINGER_BONES = [
    "Hand_R_1", "Hand_R_4", "Hand_R_5",  # Thumb (base -> mid -> tip)
    "Hand_R_2", "Hand_R_6", "Hand_R_7",  # Index (base -> mid -> tip)
    "Hand_R_3", "Hand_R_8", "Hand_R_9",  # Middle/Ring/Pinky 3-in-1 (base -> mid -> tip)
]

JETFIRE_PARENT_MAP = {
    "Hips": None,
    "Spine": "Hips",
    "Spine1": "Spine",
    "Neck": "Spine1",
    "Head": "Neck",
    "LeftUpLeg": "Hips",
    "LeftLeg": "LeftUpLeg",
    "LeftFoot": "LeftLeg",
    "LeftToeBase": "LeftFoot",
    "RightUpLeg": "Hips",
    "RightLeg": "RightUpLeg",
    "RightFoot": "RightLeg",
    "RightToeBase": "RightFoot",
    "LeftShoulder": "Spine1",
    "LeftArm": "LeftShoulder",
    "LeftArmRoll": "LeftArm",
    "LeftForeArm": "LeftArmRoll",
    "LeftHand": "LeftForeArm",
    "RightShoulder": "Spine1",
    "RightShoulderPad": "RightShoulder",
    "RightArm": "RightShoulder",
    "RightArmRoll": "RightArm",
    "RightForeArm": "RightArmRoll",
    "RightHand": "RightForeArm",
}
for fn in ("Thumb", "Index", "Middle", "Ring", "Pinky"):
    JETFIRE_PARENT_MAP[f"LeftHand{fn}1"] = "LeftHand"
    JETFIRE_PARENT_MAP[f"LeftHand{fn}2"] = f"LeftHand{fn}1"
    JETFIRE_PARENT_MAP[f"LeftHand{fn}3"] = f"LeftHand{fn}2"


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("[*] Importing StarSaber.fbx...")
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

    orig_arm = bpy.data.objects.get("Bip001")
    if orig_arm and orig_arm.animation_data:
        orig_arm.animation_data_clear()

    mesh = bpy.data.objects.get("StarSaber.001")
    sword = bpy.data.objects.get("StarSaberSword")
    ab_sym = bpy.data.objects.get("Symbol_AB.001")
    assert mesh and sword and orig_arm, "Missing required StarSaber objects!"

    SCALE_FACTOR = 4.12
    min_z_raw = min(v.co.z for v in mesh.data.vertices)
    ground_z_offset = -min_z_raw * SCALE_FACTOR

    # CRITICAL FIX: Convert Bip001 bone coordinates into StarSaber.001 local mesh space
    # via mesh.matrix_local.inverted(), BEFORE clearing parents/transforms!
    # Otherwise StarSaber_pbr's 0.01 scale shrinks bones down onto the floor near (0,0,0).
    inv_mesh_loc = mesh.matrix_local.inverted()

    def arm_to_new_world(p_arm):
        return (inv_mesh_loc @ p_arm) * SCALE_FACTOR + Vector((0.0, 0.0, ground_z_offset))

    finger_heads = {}
    for bn in RIGHT_FINGER_BONES:
        b = orig_arm.data.bones.get(bn)
        assert b is not None, f"Missing bone {bn} in StarSaber.fbx!"
        finger_heads[bn] = arm_to_new_world(b.head_local)
        print(f"  [Knuckle Pivot] {bn:10s} -> {finger_heads[bn]}")

    # Unlink everything except mesh, sword, ab_sym
    keep_objs = {mesh, sword}
    if ab_sym:
        keep_objs.add(ab_sym)
    for o in list(bpy.data.objects):
        if o not in keep_objs:
            bpy.data.objects.remove(o, do_unlink=True)

    for o in keep_objs:
        o.parent = None
        o.matrix_world = Matrix.Identity(4)

    scale_mat = Matrix.Scale(SCALE_FACTOR, 4)
    ground_mat = Matrix.Translation(Vector((0.0, 0.0, ground_z_offset)))
    body_xform = ground_mat @ scale_mat

    mesh.data.transform(body_xform)
    mesh.data.update()
    if ab_sym:
        ab_sym.data.transform(body_xform)
        ab_sym.data.update()

    # Merge Autobot chest symbol into main mesh
    if ab_sym:
        ab_sym.data.materials.clear()
        if mesh.data.materials:
            ab_sym.data.materials.append(mesh.data.materials[0])
        bpy.ops.object.select_all(action='DESELECT')
        ab_sym.select_set(True)
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh
        bpy.ops.object.join()

    # Materials
    mesh.data.materials.clear()
    mat_main = bpy.data.materials.new(name="cha_starsaber_main")
    mesh.data.materials.append(mat_main)

    sword.data.materials.clear()
    mat_wpn = bpy.data.materials.new(name="cha_starsaber_wpns")
    sword.data.materials.append(mat_wpn)

    # Set up Sword geometry:
    # Center local pivot at grip handle center (Z = -0.20 raw) BEFORE scaling by 2.0x
    SWORD_SCALE = 2.0
    sword_scale_mat = Matrix.Scale(SWORD_SCALE, 4)
    center_grip = Matrix.Translation(Vector((0.0, 0.0, 0.20)))
    sword.data.transform(sword_scale_mat @ center_grip)
    sword.data.update()
    print("[✓] Sword pivot centered cleanly at grip midpoint and scaled 2.0x.")

    # 3. Bone Weights Remapping
    print("[*] Remapping vertex groups...")
    vg_dict = {vg.name: vg for vg in mesh.vertex_groups}

    ALL_TARGET_BONES = list(JETFIRE_BASE_BONES) + RIGHT_FINGER_BONES
    target_vgs = {}
    for bn in ALL_TARGET_BONES:
        target_vgs[bn] = mesh.vertex_groups.new(name=bn)

    old_to_target = {}
    for old_name, target_name in VGROUP_MAP.items():
        if old_name in vg_dict:
            old_to_target[vg_dict[old_name].index] = target_vgs[target_name]

    for bn in RIGHT_FINGER_BONES:
        if bn in vg_dict:
            old_to_target[vg_dict[bn].index] = target_vgs[bn]

    for v in mesh.data.vertices:
        weights_to_add = {}
        for g in v.groups:
            if g.group in old_to_target:
                tgt_vg = old_to_target[g.group]
                weights_to_add[tgt_vg] = weights_to_add.get(tgt_vg, 0.0) + g.weight
        for tvg, w in weights_to_add.items():
            tvg.add([v.index], w, 'REPLACE')

    old_names = [vg.name for vg in mesh.vertex_groups if vg.name not in ALL_TARGET_BONES]
    for on in old_names:
        vg = mesh.vertex_groups.get(on)
        if vg:
            mesh.vertex_groups.remove(vg)

    # Zero-weight safety net -> Hips
    hips_vg = target_vgs["Hips"]
    zero_fixed = 0
    for v in mesh.data.vertices:
        if sum(g.weight for g in v.groups) < 1e-4:
            hips_vg.add([v.index], 1.0, 'REPLACE')
            zero_fixed += 1
    print(f"[✓] Remapped vertex groups! Fixed {zero_fixed} zero-weight verts; preserved 9 right finger groups.")

    # 4. Build Armature
    print("[*] Creating HITL Armature...")
    arm_data = bpy.data.armatures.new("cha_jetfire_gs_leader2014_00_arm")
    arm_obj = bpy.data.objects.new("cha_jetfire_gs_leader2014_00_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    edit_bones = {}
    for bn in JETFIRE_BASE_BONES:
        b = arm_data.edit_bones.new(bn)
        w_pos = unity_to_blender(donor_bones_data[bn]["world_pos"])
        b.head = w_pos
        b.tail = w_pos + Vector((0.0, 0.0, 0.25))
        edit_bones[bn] = b

    for bn, parent_name in JETFIRE_PARENT_MAP.items():
        if bn in edit_bones and parent_name in edit_bones:
            edit_bones[bn].parent = edit_bones[parent_name]
            p_bone = edit_bones[parent_name]
            if (edit_bones[bn].head - p_bone.head).length > 0.05:
                p_bone.tail = edit_bones[bn].head

    # Create Right Finger bones chained cleanly from knuckle -> next knuckle -> tip!
    FINGER_CHAINS = [
        ("Hand_R_1", "Hand_R_4", "Hand_R_5"),  # Thumb
        ("Hand_R_2", "Hand_R_6", "Hand_R_7"),  # Index
        ("Hand_R_3", "Hand_R_8", "Hand_R_9"),  # Main 3 fingers
    ]
    for b1, b2, b3 in FINGER_CHAINS:
        h1, h2, h3 = finger_heads[b1], finger_heads[b2], finger_heads[b3]
        tip_dir = (h3 - h2).normalized() * 0.20

        eb1 = arm_data.edit_bones.new(b1)
        eb1.head = h1
        eb1.tail = h2
        eb1.parent = edit_bones["RightHand"]

        eb2 = arm_data.edit_bones.new(b2)
        eb2.head = h2
        eb2.tail = h3
        eb2.parent = eb1

        eb3 = arm_data.edit_bones.new(b3)
        eb3.head = h3
        eb3.tail = h3 + tip_dir
        eb3.parent = eb2

        if b1 == "Hand_R_1":
            for eb in (eb1, eb2, eb3):
                eb.align_roll(Vector((0.0, 0.0, 1.0)))
        else:
            for eb in (eb1, eb2, eb3):
                eb.align_roll(Vector((0.0, -1.0, 0.0)))

        edit_bones[b1] = eb1
        edit_bones[b2] = eb2
        edit_bones[b3] = eb3

    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"[✓] Created Armature with {len(arm_data.bones)} bones (39 base + 9 right finger bones)!")

    mesh.parent = arm_obj
    mod = mesh.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj

    # Export FBXs
    hitl_robot_fbx = UNITY_ASSETS / "starsaber_hitl_robot.fbx"
    hitl_sword_fbx = UNITY_ASSETS / "starsaber_hitl_sword.fbx"

    print(f"[*] Exporting Robot FBX to {hitl_robot_fbx}...")
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.export_scene.fbx(
        filepath=str(hitl_robot_fbx),
        use_selection=True,
        use_active_collection=False,
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
        axis_forward='-Z',
        axis_up='Y',
        armature_nodetype='NULL',
        bake_anim=False
    )
    print(f"[✓] Exported {hitl_robot_fbx} successfully!")

    print(f"[*] Exporting Sword FBX to {hitl_sword_fbx}...")
    bpy.ops.object.select_all(action='DESELECT')
    sword.location = Vector((0.0, 0.0, 0.0))
    sword.rotation_euler = (0.0, 0.0, 0.0)
    sword.select_set(True)
    bpy.context.view_layer.objects.active = sword
    bpy.ops.export_scene.fbx(
        filepath=str(hitl_sword_fbx),
        use_selection=True,
        use_active_collection=False,
        global_scale=1.0,
        apply_unit_scale=True,
        apply_scale_options='FBX_SCALE_ALL',
        bake_space_transform=False,
        object_types={'MESH'},
        use_mesh_modifiers=True,
        mesh_smooth_type='FACE',
        axis_forward='-Z',
        axis_up='Y',
        bake_anim=False
    )
    print(f"[✓] Exported {hitl_sword_fbx} successfully!")


if __name__ == "__main__":
    main()
