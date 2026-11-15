import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

"""
Phase 3A: Export clean connected Humanoid FBXs (bw_sp3_actor0.fbx & bw_sp3_actor1.fbx)
from the synthesized 222-frame SP3 timeline for Unity ModelImporter Humanoid compilation.
"""

import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Quaternion, Vector

TOOLS_BW = Path(r"E:\Agent\TFTF-blender\tools\blitzwing")
if str(TOOLS_BW) not in sys.path:
    sys.path.insert(0, str(TOOLS_BW))

import sp3_curves as M
import sp3_timeline as TL

REST_JSON = TOOLS_BW / "megatron_humanoid_rest.json"
OUT_DIR = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\Assets\Blitzwing\SP3")

P4 = Matrix((
    (-1.0, 0.0, 0.0, 0.0),
    ( 0.0, 0.0,-1.0, 0.0),
    ( 0.0, 1.0, 0.0, 0.0),
    ( 0.0, 0.0, 0.0, 1.0),
))
P4_T = P4.transposed()

# Core connected Humanoid + Finger skeleton (55 bones matching Megatron_GS_Leader2015)
KEEP_BONES = [
    "character_model", "Reference", "Hips",
    "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase",
    "RightUpLeg", "RightLeg", "RightFoot", "RightToeBase",
    "Spine", "Spine1", "Neck", "Head",
    "LeftShoulder", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftForeArmRoll", "LeftHand",
    "LeftHandIndex1", "LeftHandIndex2", "LeftHandIndex3",
    "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandMiddle3",
    "LeftHandPinky1", "LeftHandPinky2", "LeftHandPinky3",
    "LeftHandRing1", "LeftHandRing2", "LeftHandRing3",
    "LeftHandThumb1", "LeftHandThumb2", "LeftHandThumb3",
    "RightShoulder", "RightArm", "RightArmRoll", "RightForeArm", "RightForeArmRoll", "RightHand",
    "RightHandIndex1", "RightHandIndex2", "RightHandIndex3",
    "RightHandMiddle1", "RightHandMiddle2", "RightHandMiddle3",
    "RightHandPinky1", "RightHandPinky2", "RightHandPinky3",
    "RightHandRing1", "RightHandRing2", "RightHandRing3",
    "RightHandThumb1", "RightHandThumb2", "RightHandThumb3",
]

HUMAN_SCALE_BW = 7.196131229400635
VICTIM_AVS = 6.808372


def build_unity_rest_world(rest_dict: dict) -> dict:
    w_rest = {}
    for bname in KEEP_BONES:
        info = rest_dict[bname]
        lp = Vector(info["localPos"])
        lx, ly, lz, lw = info["localRot"]
        m_loc = Matrix.Translation(lp) @ Quaternion((lw, lx, ly, lz)).to_matrix().to_4x4()
        p = info["parent"]
        if p is None or p not in w_rest:
            w_rest[bname] = m_loc
        else:
            w_rest[bname] = w_rest[p] @ m_loc
    return w_rest


def create_clean_humanoid_armature(name: str, rest_dict: dict, w_u_rest: dict):
    arm_data = bpy.data.armatures.new(name + "_Data")
    arm_obj = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')

    # Map children to compute nice bone tail visual lengths
    children = {}
    for bn in KEEP_BONES:
        p = rest_dict[bn]["parent"]
        if p in KEEP_BONES:
            children.setdefault(p, []).append(bn)

    ebs = {}
    for bn in KEEP_BONES:
        eb = arm_data.edit_bones.new(bn)
        pos_u = w_u_rest[bn].to_translation()
        head_b = Vector(M.u_pos_to_b(pos_u))
        # Choose a clean non-zero tail pointing toward first child or upward
        ch_list = children.get(bn, [])
        tail_b = None
        if ch_list:
            c_avg = Vector((0.0, 0.0, 0.0))
            for ch in ch_list:
                c_avg += Vector(M.u_pos_to_b(w_u_rest[ch].to_translation()))
            c_avg /= len(ch_list)
            if (c_avg - head_b).length > 0.05:
                tail_b = c_avg
        if tail_b is None:
            if "Toe" in bn or "Foot" in bn:
                tail_b = head_b + Vector((0.0, -0.35, 0.0))
            elif "LeftHand" in bn:
                tail_b = head_b + Vector((0.35, 0.0, 0.0))
            elif "RightHand" in bn:
                tail_b = head_b + Vector((-0.35, 0.0, 0.0))
            else:
                tail_b = head_b + Vector((0.0, 0.0, 0.45))

        eb.head = head_b
        eb.tail = tail_b
        eb.use_connect = False
        p = rest_dict[bn]["parent"]
        if p in ebs:
            eb.parent = ebs[p]
        ebs[bn] = eb

    bpy.ops.object.mode_set(mode='OBJECT')
    arm_obj.rotation_mode = 'QUATERNION'
    for pb in arm_obj.pose.bones:
        pb.rotation_mode = 'QUATERNION'
    return arm_obj


def bake_actor_to_fbx(
    fbx_path: Path,
    rest_dict: dict,
    w_u_rest: dict,
    frames: list,
    locator_pos_u,
    locator_rot_u_xyzw,
    is_actor1: bool,
):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.render.fps = 30
    scene.frame_start = 0
    scene.frame_end = M.TOTAL_FRAMES + 1

    # Root empty with exact FBX export scale=1.0
    arm_obj = create_clean_humanoid_armature("SP3_Rig", rest_dict, w_u_rest)

    # Keyframe pure Megatron T-Pose at frame 0 so Unity CreateFromThisModel Avatar builds exact humanScale=7.1961 T-pose!
    scene.frame_set(0)
    for pb in arm_obj.pose.bones:
        pb.location = (0.0, 0.0, 0.0)
        pb.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
        pb.scale = (1.0, 1.0, 1.0)
        pb.keyframe_insert(data_path="location", frame=0)
        pb.keyframe_insert(data_path="rotation_quaternion", frame=0)

    # Compute inverse locator transform W_loc^-1 so exported FBX starts cleanly at locator local (0,0,0), facing +Z_u!
    lx, ly, lz, lw = locator_rot_u_xyzw
    w_loc_u = Matrix.Translation(Vector(locator_pos_u)) @ Quaternion((lw, lx, ly, lz)).to_matrix().to_4x4()
    w_loc_inv_u = w_loc_u.inverted()

    # For Actor1, runtime MatineeAnimatorTransformMove multiplies delta(RootT) by VICTIM_AVS/HUMAN_SCALE_BW.
    # Since samples in wb1/mm1 already applied VICTIM_AVS/HUMAN_SCALE_BW, scale root displacement delta by inverse ratio!
    root_disp_scale = (HUMAN_SCALE_BW / VICTIM_AVS) if is_actor1 else 1.0
    a1_root0 = frames[0]["a1_root_rm"] if is_actor1 else None

    # Record last valid robot bone map for Actor0 during vehicle frames (35..177) so Hips tracks veh_pos smoothly
    last_bm = None

    for fr in frames:
        f = fr["frame"] + 1
        scene.frame_set(f)
        if is_actor1:
            bm = fr["a1_bones"]
            r_rm = fr["a1_root_rm"]
            disp = M.v_sub(r_rm, a1_root0)
            target_root_u = M.v_add(a1_root0, M.v_scale(disp, root_disp_scale))
            root_delta_u = M.v_sub(target_root_u, r_rm)
        else:
            bm = fr["a0_robot_bones"]
            root_delta_u = (0.0, 0.0, 0.0)
            if bm is not None:
                last_bm = bm
            else:
                # Vehicle interval (35..177): translate last robot pose so Hips follows veh_pos seamlessly!
                # This ensures Animator RootT/ContactShadow tracks Jet & Tank across the whole stage!
                hips_prev = last_bm["Hips"]["pos"]
                shift = M.v_sub(fr["veh_pos"], hips_prev)
                bm_veh = {}
                for k, v in last_bm.items():
                    bm_veh[k] = {"pos": M.v_add(v["pos"], shift), "rot": v["rot"], "path": v["path"]}
                bm = bm_veh

        # Compute target armature-space matrices in locator-local space
        target_arm_mats = {}
        for pb in arm_obj.pose.bones:
            bname = pb.name
            if bname in ("character_model", "Reference"):
                # Keep character_model & Reference fixed at local origin (0,0,0) Identity!
                target_arm_mats[bname] = pb.bone.matrix_local.copy()
                continue

            src_key = bname
            if src_key not in bm:
                if bname.startswith("LeftHand"):
                    src_key = "LeftHand"
                elif bname.startswith("RightHand"):
                    src_key = "RightHand"
                else:
                    # Fallback inherit parent rest offset cleanly
                    p = pb.bone.parent
                    if p is not None and p.name in target_arm_mats:
                        m_rel = p.matrix_local.inverted() @ pb.bone.matrix_local
                        target_arm_mats[bname] = target_arm_mats[p.name] @ m_rel
                    else:
                        target_arm_mats[bname] = pb.bone.matrix_local.copy()
                    continue

            entry = bm[src_key]
            wp = Vector(M.v_add(entry["pos"], root_delta_u))
            qx, qy, qz, qw = entry["rot"]
            w_u_world = Matrix.Translation(wp) @ Quaternion((qw, qx, qy, qz)).to_matrix().to_4x4()
            w_u_loc = w_loc_inv_u @ w_u_world
            delta_u = w_u_loc @ w_u_rest[src_key].inverted()
            delta_b = P4 @ delta_u @ P4_T
            target_arm_mats[bname] = delta_b @ pb.bone.matrix_local

        for pb in arm_obj.pose.bones:
            b = pb.bone
            m_target = target_arm_mats[pb.name]
            if b.parent is None:
                m_basis = b.matrix_local.inverted() @ m_target
            else:
                m_parent_target = target_arm_mats[b.parent.name]
                m_rest_rel = b.parent.matrix_local.inverted() @ b.matrix_local
                m_basis = (m_parent_target @ m_rest_rel).inverted() @ m_target
            loc, rot, sca = m_basis.decompose()
            pb.location = loc
            pb.rotation_quaternion = rot
            pb.scale = (1.0, 1.0, 1.0)
            pb.keyframe_insert(data_path="location", frame=f)
            pb.keyframe_insert(data_path="rotation_quaternion", frame=f)

    # Return to frame 0 (pure T-pose) before FBX export
    scene.frame_set(0)

    # Export clean FBX for Unity
    bpy.ops.object.select_all(action='DESELECT')
    arm_obj.select_set(True)
    bpy.context.view_layer.objects.active = arm_obj

    fbx_path.parent.mkdir(parents=True, exist_ok=True)
    bpy.ops.export_scene.fbx(
        filepath=str(fbx_path),
        use_selection=True,
        object_types={'ARMATURE'},
        use_mesh_modifiers=False,
        add_leaf_bones=False,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False,
        bake_anim_force_startend_keying=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,
        axis_forward='-Z',
        axis_up='Y',
        apply_scale_options='FBX_SCALE_ALL',
    )
    print(f"[export_sp3_humanoid_fbx] Exported {fbx_path} ({len(frames)} frames, is_actor1={is_actor1})")


def main():
    rest_dict = json.loads(REST_JSON.read_text(encoding="utf-8"))
    w_u_rest = build_unity_rest_world(rest_dict)
    tl = TL.synthesize_timeline()
    frames = tl["frames"]

    loc_rot = (0.0, 0.7071068, 0.0, 0.7071068)
    bake_actor_to_fbx(
        OUT_DIR / "bw_sp3_actor0.fbx",
        rest_dict, w_u_rest, frames,
        tl["wb_a0_locator"], loc_rot, is_actor1=False,
    )
    bake_actor_to_fbx(
        OUT_DIR / "bw_sp3_actor1.fbx",
        rest_dict, w_u_rest, frames,
        tl["wb_a1_locator"], loc_rot, is_actor1=True,
    )


if __name__ == "__main__":
    main()
