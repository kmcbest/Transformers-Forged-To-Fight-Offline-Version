import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import json
import math
from pathlib import Path
import numpy as np
import bpy
import mathutils
from mathutils import Vector, Matrix, Quaternion

print("=== BUILDING 30-FINGER ARTICULATED TARN FOR ULTRA MAGNUS (53 BONES) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
TARN_DIR = ROOT / "3rd-party-models" / "Tarn"
BAKED_BLEND = TARN_DIR / "06_working" / "tarn_workspace_baked.blend"
UM_BONES_JSON = TARN_DIR / "04_donor_reference" / "ultramagnus_gs_leader" / "cha_ultramagnus_gs_leader_00_bones.json"
UM_OBJ = TARN_DIR / "04_donor_reference" / "ultramagnus_gs_leader" / "cha_ultramagnus_gs_leader_00_robot.obj"
TEX_DIR = TARN_DIR / "06_working" / "unified_textures"
FBX_EXPORT_DIR = TARN_DIR / "06_working" / "fbx_exports"
UNITY_TARN_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Tarn"
SCRATCH_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\66aaeff3-2652-4f24-8fc9-00b0ef375582\scratch")

FBX_EXPORT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_TARN_DIR.mkdir(parents=True, exist_ok=True)
SCRATCH_DIR.mkdir(parents=True, exist_ok=True)


def um_unity_to_blender(upos):
    """Unity (ux, uy, uz) -> Blender (-ux, -uz, uy): Left=+X, Forward=-Y, Up=+Z."""
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))


def pose_segment_world(arm_obj, bname, child_bname, target_head_w, target_end_w, thickness_scale=1.0, preserve_length=False):
    bpy.context.view_layer.update()
    pb = arm_obj.pose.bones[bname]
    pb_child = arm_obj.pose.bones[child_bname]
    w_old = arm_obj.matrix_world @ pb.matrix
    curr_head = w_old.translation.copy()
    curr_end = (arm_obj.matrix_world @ pb_child.matrix).translation.copy()

    v_curr = curr_end - curr_head
    v_targ = target_end_w - target_head_w
    len_curr = v_curr.length
    len_targ = v_targ.length

    q_rot = v_curr.rotation_difference(v_targ) if (len_curr > 1e-5 and len_targ > 1e-5) else Quaternion()
    s_len = 1.0 if preserve_length else ((len_targ / len_curr) if len_curr > 1e-5 else 1.0)

    d = v_curr.normalized() if len_curr > 1e-5 else Vector((0, 0, -1))
    S = Matrix.Identity(3) * thickness_scale
    for r in range(3):
        for c in range(3):
            S[r][c] += (s_len - thickness_scale) * d[r] * d[c]

    R_new = q_rot.to_matrix() @ S @ w_old.to_3x3()
    M_new_w = R_new.to_4x4()
    M_new_w.translation = target_head_w
    pb.matrix = arm_obj.matrix_world.inverted() @ M_new_w
    bpy.context.view_layer.update()


def extract_live_hand_joints(robot):
    """Extract live joint positions directly from scaled Tarn_Robot_LowPoly hand* vertex groups."""
    vg_map = {vg.name: vg.index for vg in robot.vertex_groups}

    def vg_pts(vgn, thresh=0.25):
        idx = vg_map[vgn]
        pts = [v.co.copy() for v in robot.data.vertices if any(g.group == idx and g.weight > thresh for g in v.groups)]
        if not pts:
            pts = [v.co.copy() for v in robot.data.vertices if any(g.group == idx and g.weight > 0.01 for g in v.groups)]
        return pts

    def shared_joint(vgn_a, vgn_b):
        ia, ib = vg_map[vgn_a], vg_map[vgn_b]
        shared = []
        for v in robot.data.vertices:
            wa = sum(g.weight for g in v.groups if g.group == ia)
            wb = sum(g.weight for g in v.groups if g.group == ib)
            if wa > 0.12 and wb > 0.12:
                shared.append(v.co.copy())
        if shared:
            return sum(shared, Vector()) / len(shared)
        pa = vg_pts(vgn_a)
        pb = vg_pts(vgn_b)
        ca = sum(pa, Vector()) / len(pa)
        cb = sum(pb, Vector()) / len(pb)
        return 0.5 * (ca + cb)

    def furthest_tip(vgn_tip, head_pt):
        pts = vg_pts(vgn_tip)
        # Average of the top 15% vertices farthest from head_pt for stable tip center
        pts.sort(key=lambda p: (p - head_pt).length, reverse=True)
        k = max(3, len(pts) // 6)
        return sum(pts[:k], Vector()) / k

    live = {}
    for side in ("L", "R"):
        p = f"hand{side}__"
        wrist_pts = vg_pts(f"{p}Bone", thresh=0.1)
        # Highest Z ~ cuff/wrist top, center X/Y at Z = mean+0.15
        wrist_pts.sort(key=lambda pt: pt.z, reverse=True)
        k_w = max(4, len(wrist_pts) // 3)
        wrist_head = sum(wrist_pts[:k_w], Vector()) / k_w

        info = {"wrist": wrist_head}
        chains = [
            ("Index", ("Bone.005", "Bone.006", "Bone.014", "Bone.016")),
            ("Middle", ("Bone.001", "Bone.004", "Bone.013", "Bone.015")),
            ("Ring", ("Bone.002", "Bone.003", "Bone.011", "Bone.012")),
            ("Pinky", ("Bone.007", "Bone.008", "Bone.009", "Bone.010")),
            ("Thumb", ("Bone.017", "Bone.019", "Bone.021", "Bone.022")),
        ]
        for fname, (b_pre, b1, b2, b3) in chains:
            j1 = shared_joint(f"{p}{b_pre}", f"{p}{b1}")
            j2 = shared_joint(f"{p}{b1}", f"{p}{b2}")
            j3 = shared_joint(f"{p}{b2}", f"{p}{b3}")
            jt = furthest_tip(f"{p}{b3}", j3)
            info[fname] = (j1, j2, j3, jt)
        live[side] = info
        print(
            f"[✓] Live hand {side}: wrist=({wrist_head.x:.2f},{wrist_head.y:.2f},{wrist_head.z:.2f}), "
            f"Index1=({info['Index'][0].x:.2f},{info['Index'][0].y:.2f},{info['Index'][0].z:.2f}), "
            f"Thumb1=({info['Thumb'][0].x:.2f},{info['Thumb'][0].y:.2f},{info['Thumb'][0].z:.2f})"
        )
    return live


def assign_rigid_parts_to_um_bones(robot, um_b_pos):
    PART_MAP = {
        "part__Cube.030": "LR:Foot",
        "part__Cube.047": "LR:Foot",
        "part__Cube.051": "LR:Foot",
        "part__Cylinder.054": "LR:Foot",
        "part__Plane.041": "LeftLeg",
        "part__Plane.023": "RightLeg",
        "part__Cylinder.045": "LR:Leg",
        "part__Cylinder.053": "LR:Leg",
        "part__Plane.019": "LR:Leg",
        "part__Plane.024": "LR:Leg",
        "part__Plane.025": "LR:Leg",
        "part__Plane.026": "LR:Leg",
        "part__Plane.027": "LR:Leg",
        "part__Plane.028": "LR:Leg",
        "part__Plane.029": "LR:Leg",
        "part__Plane.030": "LR:Leg",
        "part__Cube.055": "LR:Leg",
        "part__Cube.057": "LR:Leg",
        "part__Gear.000": "LR:Leg",
        "part__Cylinder.044": "LR:Leg",
        "part__Cube.045": "LR:UpLeg",
        "part__Cube.054": "LR:UpLeg",
        "part__Cube.049": "LR:UpLeg",
        "part__Cube.056": "LR:UpLeg",
        "part__Circle.000": "Hips",
        "part__Circle.001": "Hips",
        "part__Circle.002": "Hips",
        "part__Circle.003": "Hips",
        "part__BezierCurve.000": "Hips",
        "part__BezierCurve.001": "Hips",
        "part__BezierCurve.002": "Hips",
        "part__BezierCurve.003": "Hips",
        "part__Cube.019": "Hips",
        "part__Cube.004": "Hips",
        "part__Cylinder.011": "Hips",
        "part__Plane.013": "Hips",
        "part__Plane.014": "Hips",
        "part__Plane.015": "Hips",
        "part__Plane.057": "Hips",
        "part__Plane.018": "Hips",
        "part__Plane.020": "Hips",
        "part__Plane.021": "Hips",
        "part__Cube.005": "Spine",
        "part__Cylinder.007": "Spine",
        "part__Cube.003": "Spine1",
        "part__Cube.013": "Spine1",
        "part__Cube.016": "Spine1",
        "part__Cylinder.014": "Spine1",
        "part__Cylinder.015": "Spine1",
        "part__Cylinder.042": "Spine1",
        "part__Plane.004": "Spine1",
        "part__Plane.007": "Spine1",
        "part__Plane.008": "Spine1",
        "part__Plane.012": "Spine1",
        "part__Plane.036": "Spine1",
        "part__Plane.061": "Spine1",
        "part__Cube.007": "Spine1",
        "part__Torus.000": "Spine1",
        "part__Plane.000": "Head",
        "part__Plane.001": "Head",
        "part__Plane.002": "Head",
        "part__Plane.003": "Head",
        "part__Plane.050": "Head",
        "part__Cube.008": "Head",
        "part__Cube.028": "Head",
        "part__Cube.029": "Head",
        "part__Cylinder.040": "Head",
        "part__Sphere.001": "Head",
        "part__Sphere.003": "Head",
        "part__Plane.058": "LeftShoulderPad",
        "part__Plane.059": "LeftShoulderPad",
        "part__Cylinder.055": "LeftShoulderPad",
        "part__Cylinder.057": "LeftShoulderPad",
        "part__Cylinder.058": "LeftShoulderPad",
        "part__Cylinder.059": "LeftShoulderPad",
        "part__Cylinder.060": "LeftShoulderPad",
        "part__Cylinder.061": "LeftShoulderPad",
        "part__Cylinder.062": "LeftShoulderPad",
        "part__Cylinder.063": "LeftShoulderPad",
        "part__Cylinder.064": "LeftShoulderPad",
        "part__Cylinder.065": "LeftShoulderPad",
        "part__Cylinder.066": "LeftShoulderPad",
        "part__Cylinder.067": "LeftShoulderPad",
        "part__Cylinder.068": "LeftShoulderPad",
        "part__Cylinder.069": "LeftShoulderPad",
        "part__Cube.000": "LeftArm",
        "part__Cube.006": "LeftForeArm",
        "part__Cube.025": "LeftForeArm",
        "part__Cube.027": "LeftForeArm",
        "part__Plane.009": "RightShoulderPad",
        "part__Plane.010": "RightShoulderPad",
        "part__Cylinder.005": "RightShoulderPad",
        "part__Cylinder.010": "RightShoulderPad",
        "part__Cylinder.016": "RightShoulderPad",
        "part__Cylinder.017": "RightShoulderPad",
        "part__Cylinder.019": "RightShoulderPad",
        "part__Cylinder.021": "RightShoulderPad",
        "part__Cylinder.031": "RightShoulderPad",
        "part__Cylinder.033": "RightShoulderPad",
        "part__Cylinder.034": "RightShoulderPad",
        "part__Cylinder.036": "RightShoulderPad",
        "part__Cylinder.037": "RightShoulderPad",
        "part__Cylinder.038": "RightShoulderPad",
        "part__Cylinder.041": "RightShoulderPad",
        "part__Cube.017": "RightArm",
        "part__Cube.021": "RightForeArm",
        "part__Cube.020": "RightForeArm",
        "part__Cube.022": "RightForeArm",
        "part__Cube.001": "RightForeArm",
        "part__Cube.002": "RightForeArm",
        "part__Cylinder.003": "RightForeArm",
        "part__Cylinder.004": "RightForeArm",
        "part__Cylinder.001": "LeftHand",
        "part__Cylinder.002": "RightHand",
    }

    HAND_MAP = {}
    for side, pfx in [("L", "Left"), ("R", "Right")]:
        for src_b in ("Bone", "Bone.001", "Bone.002", "Bone.005", "Bone.007", "Bone.017"):
            HAND_MAP[f"hand{side}__{src_b}"] = f"{pfx}Hand"
        HAND_MAP[f"hand{side}__Bone.018"] = f"{pfx}HandThumb1"
        HAND_MAP[f"hand{side}__Bone.019"] = f"{pfx}HandThumb1"
        HAND_MAP[f"hand{side}__Bone.021"] = f"{pfx}HandThumb2"
        HAND_MAP[f"hand{side}__Bone.022"] = f"{pfx}HandThumb3"
        HAND_MAP[f"hand{side}__Bone.006"] = f"{pfx}HandIndex1"
        HAND_MAP[f"hand{side}__Bone.014"] = f"{pfx}HandIndex2"
        HAND_MAP[f"hand{side}__Bone.016"] = f"{pfx}HandIndex3"
        HAND_MAP[f"hand{side}__Bone.004"] = f"{pfx}HandMiddle1"
        HAND_MAP[f"hand{side}__Bone.013"] = f"{pfx}HandMiddle2"
        HAND_MAP[f"hand{side}__Bone.015"] = f"{pfx}HandMiddle3"
        HAND_MAP[f"hand{side}__Bone.003"] = f"{pfx}HandRing1"
        HAND_MAP[f"hand{side}__Bone.011"] = f"{pfx}HandRing2"
        HAND_MAP[f"hand{side}__Bone.012"] = f"{pfx}HandRing3"
        HAND_MAP[f"hand{side}__Bone.008"] = f"{pfx}HandPinky1"
        HAND_MAP[f"hand{side}__Bone.009"] = f"{pfx}HandPinky2"
        HAND_MAP[f"hand{side}__Bone.010"] = f"{pfx}HandPinky3"

    vg_names = [vg.name for vg in robot.vertex_groups]
    new_vgs = {}
    for bname in um_b_pos.keys():
        vg = robot.vertex_groups.get(bname) or robot.vertex_groups.new(name=bname)
        new_vgs[bname] = vg

    for spec in PART_MAP.values():
        if not spec.startswith("LR:"):
            assert spec in new_vgs, f"Missing target bone {spec}"

    unmapped_parts = set()
    zero_verts = 0

    for vi, v in enumerate(robot.data.vertices):
        hand_weights = {}
        part_weights = {}
        for g in v.groups:
            if g.weight <= 0.01:
                continue
            vname = vg_names[g.group]
            if vname in HAND_MAP:
                tb = HAND_MAP[vname]
                hand_weights[tb] = hand_weights.get(tb, 0.0) + g.weight
            elif vname.startswith("part__"):
                spec = PART_MAP.get(vname)
                if not spec:
                    unmapped_parts.add(vname)
                    continue
                if spec.startswith("LR:"):
                    sfx = spec[3:]
                    side_p = "Left" if v.co.x >= 0.0 else "Right"
                    if sfx == "Foot" and v.co.y < -0.58 and v.co.z < 0.48:
                        tb = f"{side_p}ToeBase"
                    else:
                        tb = f"{side_p}{sfx}"
                else:
                    tb = spec
                part_weights[tb] = part_weights.get(tb, 0.0) + g.weight

        bone_weights = hand_weights if hand_weights else part_weights
        if not bone_weights:
            zero_verts += 1
            bone_weights["Spine1"] = 1.0

        best_b = max(bone_weights, key=bone_weights.get)
        is_hand = ("Hand" in best_b)
        if not is_hand or bone_weights[best_b] >= 0.65:
            new_vgs[best_b].add([vi], 1.0, "REPLACE")
        else:
            tot = sum(bone_weights.values())
            for b, w in bone_weights.items():
                new_vgs[b].add([vi], w / tot, "REPLACE")

    assert not unmapped_parts, f"Unmapped part__* groups: {sorted(unmapped_parts)}"
    print(f"[✓] Mapped {len(robot.data.vertices)} verts onto UM 53 bones (unassigned={zero_verts})")
    for vg in list(robot.vertex_groups):
        if vg.name.startswith(("part__", "handL__", "handR__")):
            robot.vertex_groups.remove(vg)


def create_tarn_build_armature(live_hands, scale_f, robot):
    """Build temporary armature matching Tarn's EXACT live scaled mesh landmarks."""
    arm_data = bpy.data.armatures.new("ARM_Tarn_Build_Data")
    arm_obj = bpy.data.objects.new("ARM_Tarn_Build", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm_data.edit_bones

    def svec(pt):
        return Vector(pt) * scale_f

    def add_bone(name, head, tail, parent=None):
        eb = ebs.new(name)
        eb.head = Vector(head)
        eb.tail = Vector(tail) if (Vector(tail) - Vector(head)).length > 1e-4 else (Vector(head) + Vector((0, 0, 0.2)))
        if parent:
            eb.parent = ebs[parent]
        eb.use_connect = False
        eb.inherit_scale = "NONE"
        return eb

    def vg_center(bname):
        idx = robot.vertex_groups[bname].index
        pts = [v.co for v in robot.data.vertices if any(g.group == idx and g.weight > 0.4 for g in v.groups)]
        return (sum(pts, Vector()) / len(pts)) if pts else Vector()

    add_bone("Reference", (0, 0, 0), (0, 0, 1))
    add_bone("Hips", (0, -0.05, 6.7 * scale_f), (0, -0.05, 7.7 * scale_f), "Reference")
    add_bone("Spine", (0, -0.1, 7.8 * scale_f), (0, -0.1, 8.8 * scale_f), "Hips")
    add_bone("Spine1", (0, -0.05, 9.0 * scale_f), (0, -0.05, 10.2 * scale_f), "Spine")
    add_bone("Head", (0, -0.15, 10.5 * scale_f), (0, -0.15, 11.45 * scale_f), "Spine1")

    for side, sgn in [("Left", 1.0), ("Right", -1.0)]:
        add_bone(f"{side}UpLeg", (1.25 * sgn * scale_f, 0.05, 6.35 * scale_f), (1.42 * sgn * scale_f, 0.10, 3.74 * scale_f), "Hips")
        add_bone(f"{side}Leg", (1.42 * sgn * scale_f, 0.10, 3.74 * scale_f), (1.55 * sgn * scale_f, 0.15, 0.85 * scale_f), f"{side}UpLeg")
        add_bone(f"{side}Foot", (1.55 * sgn * scale_f, 0.15, 0.85 * scale_f), (1.55 * sgn * scale_f, -0.80, 0.35 * scale_f), f"{side}Leg")
        add_bone(f"{side}ToeBase", (1.55 * sgn * scale_f, -0.80, 0.35 * scale_f), (1.55 * sgn * scale_f, -1.60, 0.25 * scale_f), f"{side}Foot")

    for side_full, side_s, sgn in [("Left", "L", 1.0), ("Right", "R", -1.0)]:
        hb = live_hands[side_s]
        wrist = hb["wrist"]
        # Measure actual Arm and ForeArm centers on Tarn so elbow sits exactly at cuff top!
        fa_idx = robot.vertex_groups[f"{side_full}ForeArm"].index
        fa_top = max(v.co.z for v in robot.data.vertices if any(g.group == fa_idx and g.weight > 0.4 for g in v.groups) and v.co.x * sgn < 3.6)
        # Keep elbow right at top of forearm sleeve ~8.1, shoulder ball right inside bicep top ~9.35
        sh_c = vg_center(f"{side_full}ShoulderPad")
        arm_h = Vector((wrist.x * 0.96, wrist.y + 0.35, 9.35 * scale_f))
        elbow_h = Vector((wrist.x * 0.98, wrist.y + 0.15, 8.15 * scale_f))

        add_bone(f"{side_full}Shoulder", svec((1.80 * sgn, 0.15, 9.45)), arm_h, "Spine1")
        add_bone(f"{side_full}ShoulderPad", sh_c, sh_c + Vector((0.8 * sgn, 0, 0.8)), f"{side_full}Shoulder")
        add_bone(f"{side_full}Arm", arm_h, elbow_h, f"{side_full}Shoulder")
        add_bone(f"{side_full}ForeArm", elbow_h, wrist, f"{side_full}Arm")

        mid_knuckle = 0.5 * (hb["Index"][0] + hb["Pinky"][0])
        add_bone(f"{side_full}Hand", wrist, mid_knuckle, f"{side_full}ForeArm")

        for fname in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
            p1, p2, p3, pt = hb[fname]
            add_bone(f"{side_full}Hand{fname}1", p1, p2, f"{side_full}Hand")
            add_bone(f"{side_full}Hand{fname}2", p2, p3, f"{side_full}Hand{fname}1")
            add_bone(f"{side_full}Hand{fname}3", p3, pt, f"{side_full}Hand{fname}2")
            add_bone(f"{side_full}Hand{fname}Tip", pt, pt + (pt - p3) * 0.4, f"{side_full}Hand{fname}3")

    bpy.ops.object.mode_set(mode="OBJECT")
    return arm_obj


def main():
    bpy.ops.wm.open_mainfile(filepath=str(BAKED_BLEND))
    robot = bpy.data.objects.get("Tarn_Robot_LowPoly")
    assert robot is not None, "Missing Tarn_Robot_LowPoly"

    robo_spec = json.loads(UM_BONES_JSON.read_text(encoding="utf-8"))
    um_b_pos = {b["name"]: um_unity_to_blender(b["unity_bindpose_pos"]) for b in robo_spec["bones"]}

    # Scale Tarn cleanly so head & torso align closely with Ultra Magnus
    SCALE_UM = 1.038
    bpy.ops.object.select_all(action="DESELECT")
    robot.select_set(True)
    bpy.context.view_layer.objects.active = robot
    robot.location = (0.0, 0.0, 0.0)
    robot.scale = (SCALE_UM, SCALE_UM, SCALE_UM)
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    print(f"[✓] Scaled Tarn_Robot_LowPoly x{SCALE_UM}")

    # Assign unified baked material
    mat = bpy.data.materials.new("MAT_Tarn_Main")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_a.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_NM_std.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nrm_node = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nrm_node.inputs["Color"])
    nt.links.new(nrm_node.outputs["Normal"], bsdf.inputs["Normal"])
    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / "cha_tarn_main_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 3.0
    bsdf.inputs["Roughness"].default_value = 0.55
    robot.data.materials.clear()
    robot.data.materials.append(mat)

    # Extract LIVE hand joints directly from scaled mesh BEFORE dropping handL__/handR__ groups!
    live_hands = extract_live_hand_joints(robot)
    assign_rigid_parts_to_um_bones(robot, um_b_pos)

    # Raise forearm armor sleeves + Fusion Cannon slightly (+0.32m Z) AFTER rigid assignment so Left/RightForeArm
    # gauntlet cuff rim ends cleanly right at the wrist joint (without shifting hand vertices!).
    sleeve_vgs = {
        robot.vertex_groups[n].index
        for n in ("LeftForeArm", "RightForeArm")
        if n in robot.vertex_groups
    }
    for v in robot.data.vertices:
        if any(g.group in sleeve_vgs and g.weight > 0.3 for g in v.groups):
            v.co.z += 0.32
    robot.data.update()

    build_arm = create_tarn_build_armature(live_hands, SCALE_UM, robot)
    mod = robot.modifiers.new("TarnBuildArm", "ARMATURE")
    mod.object = build_arm

    bpy.ops.object.select_all(action="DESELECT")
    build_arm.select_set(True)
    bpy.context.view_layer.objects.active = build_arm
    bpy.ops.object.mode_set(mode="POSE")

    # Step 1: Align Legs FIRST & Ground cleanly via PoseBone Reference BEFORE Arms/Hands
    for side, sgn in [("Left", 1.0), ("Right", -1.0)]:
        hip_p = (build_arm.matrix_world @ build_arm.pose.bones[f"{side}UpLeg"].matrix).translation.copy()
        knee_t = Vector((1.05 * sgn, um_b_pos[f"{side}Leg"].y, um_b_pos[f"{side}Leg"].z))
        # Place ankle at 0.90m (matching Tarn sole-to-ankle height) and keep toe sole flat on floor!
        foot_t = Vector((1.05 * sgn, 0.08, 0.90))
        pose_segment_world(build_arm, f"{side}UpLeg", f"{side}Leg", Vector((1.02 * sgn, hip_p.y, 6.81)), knee_t, thickness_scale=0.92)
        pose_segment_world(build_arm, f"{side}Leg", f"{side}Foot", knee_t, foot_t, thickness_scale=0.92)
        pose_segment_world(build_arm, f"{side}Foot", f"{side}ToeBase", foot_t, Vector((1.05 * sgn, foot_t.y - 0.95, 0.38)), thickness_scale=0.94)

    deps = bpy.context.evaluated_depsgraph_get()
    ev = robot.evaluated_get(deps)
    em = ev.to_mesh()
    min_z = min((ev.matrix_world @ v.co).z for v in em.vertices)
    ev.to_mesh_clear()
    # Ground via Reference PoseBone so Armature modifier shifts vertices properly before baking!
    pb_ref = build_arm.pose.bones["Reference"]
    pb_ref.matrix = Matrix.Translation((0.0, 0.0, -min_z)) @ pb_ref.matrix
    bpy.context.view_layer.update()
    print(f"[✓] Grounded ARM_Tarn_Build via Reference PoseBone BEFORE hands (shifted Z by {-min_z:.4f}m)")

    # Step 2: Arms, ForeArms (KEEP preserve_length=True so Double Fusion Cannon NEVER stretches!), Wrists & Hands!
    for side, sgn in [("Left", 1.0), ("Right", -1.0)]:
        # Shift ShoulderPad lightly up/in to meet UM shoulders without cramping head
        pb_pad = build_arm.pose.bones[f"{side}ShoulderPad"]
        w_pad = build_arm.matrix_world @ pb_pad.matrix
        M_pad = w_pad.copy()
        M_pad.translation = w_pad.translation + Vector((-0.18 * sgn, 0.0, 0.20))
        pb_pad.matrix = build_arm.matrix_world.inverted() @ M_pad
        bpy.context.view_layer.update()

        # Find current forearm length so RightForeArm + Fusion Cannon keep exact 1.0x length and wrist reaches UM_Hand (5.91)!
        pb_fa = build_arm.pose.bones[f"{side}ForeArm"]
        pb_h = build_arm.pose.bones[f"{side}Hand"]
        fa_len = ((build_arm.matrix_world @ pb_h.matrix).translation - (build_arm.matrix_world @ pb_fa.matrix).translation).length
        wri_t = um_b_pos[f"{side}Hand"].copy()
        # Keep elbow above UM_Hand by exact fa_len (with slight backward Y offset matching forearm sleeve)
        elb_t = wri_t + Vector((0.0, 0.05, fa_len))
        arm_t = Vector((wri_t.x, um_b_pos[f"{side}Arm"].y + 0.15, um_b_pos[f"{side}Arm"].z * 0.96))

        pose_segment_world(build_arm, f"{side}Arm", f"{side}ForeArm", arm_t, elb_t, thickness_scale=1.0, preserve_length=False)
        pose_segment_world(build_arm, f"{side}ForeArm", f"{side}Hand", elb_t, wri_t, thickness_scale=1.0, preserve_length=True)

        # Rotate Hand (wrist) inside the forearm cuff so Tarn's palm pronates cleanly inward to match Ultra Magnus
        w_h = build_arm.matrix_world @ pb_h.matrix
        kn_i = (build_arm.matrix_world @ build_arm.pose.bones[f"{side}HandIndex1"].matrix).translation
        kn_p = (build_arm.matrix_world @ build_arm.pose.bones[f"{side}HandPinky1"].matrix).translation
        curr_kn = 0.5 * (kn_i + kn_p)
        targ_kn = 0.5 * (um_b_pos[f"{side}HandIndex1"] + um_b_pos[f"{side}HandPinky1"])

        v_ch = curr_kn - w_h.translation
        v_th = targ_kn - wri_t
        q_h = v_ch.rotation_difference(v_th)
        s_h = min(1.12, max(0.88, v_th.length / max(v_ch.length, 1e-5)))
        d_h = v_ch.normalized()
        S_h = Matrix.Identity(3)
        for r in range(3):
            for c in range(3):
                S_h[r][c] += (s_h - 1.0) * d_h[r] * d_h[c]
        M_h = (q_h.to_matrix() @ S_h @ w_h.to_3x3()).to_4x4()
        M_h.translation = wri_t
        pb_h.matrix = build_arm.matrix_world.inverted() @ M_h
        bpy.context.view_layer.update()

        # Yaw align around hand axis so Index->Pinky matches UM Index1->Pinky1 (front -Y -> back +Y)
        curr_span = (
            (build_arm.matrix_world @ build_arm.pose.bones[f"{side}HandIndex1"].matrix).translation
            - (build_arm.matrix_world @ build_arm.pose.bones[f"{side}HandPinky1"].matrix).translation
        )
        targ_span = um_b_pos[f"{side}HandIndex1"] - um_b_pos[f"{side}HandPinky1"]
        ah = v_th.normalized()
        c_perp = (curr_span - ah * curr_span.dot(ah)).normalized()
        t_perp = (targ_span - ah * targ_span.dot(ah)).normalized()
        q_y = c_perp.rotation_difference(t_perp)
        w_h_now = build_arm.matrix_world @ pb_h.matrix
        pb_h.matrix = build_arm.matrix_world.inverted() @ (
            Matrix.Translation(wri_t) @ q_y.to_matrix().to_4x4() @ Matrix.Translation(-wri_t) @ w_h_now
        )
        bpy.context.view_layer.update()

        # Pose ALL 15 finger phalanges per hand 1:1 onto Ultra Magnus's exact joints (preserving chunky thickness)!
        for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
            p1 = um_b_pos[f"{side}Hand{fn}1"]
            p2 = um_b_pos[f"{side}Hand{fn}2"]
            p3 = um_b_pos[f"{side}Hand{fn}3"]
            pt = p3 + (p3 - p2) * 0.90
            pose_segment_world(build_arm, f"{side}Hand{fn}1", f"{side}Hand{fn}2", p1, p2, thickness_scale=1.08)
            pose_segment_world(build_arm, f"{side}Hand{fn}2", f"{side}Hand{fn}3", p2, p3, thickness_scale=1.08)
            pose_segment_world(build_arm, f"{side}Hand{fn}3", f"{side}Hand{fn}Tip", p3, pt, thickness_scale=1.08)

    max_err_mm = 0.0
    for side in ("Left", "Right"):
        for fn in ("Index", "Middle", "Ring", "Pinky", "Thumb"):
            for k in ("1", "2", "3"):
                wp = (build_arm.matrix_world @ build_arm.pose.bones[f"{side}Hand{fn}{k}"].matrix).translation
                err = (wp - um_b_pos[f"{side}Hand{fn}{k}"]).length * 1000.0
                max_err_mm = max(max_err_mm, err)
    print(f"[✓] Max 30-finger joint alignment error: {max_err_mm:.4f} mm")

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action="DESELECT")
    robot.select_set(True)
    bpy.context.view_layer.objects.active = robot
    bpy.ops.object.modifier_apply(modifier="TarnBuildArm")
    bpy.data.objects.remove(build_arm, do_unlink=True)

    actual_min_z = min(v.co.z for v in robot.data.vertices)
    print(f"[✓] Post-bake Tarn floor Z = {actual_min_z:.4f}m")

    # Build final clean export armature ARM_Tarn_UM53
    exp_data = bpy.data.armatures.new("ARM_Tarn_UM53_Data")
    exp_arm = bpy.data.objects.new("ARM_Tarn_UM53", exp_data)
    bpy.context.scene.collection.objects.link(exp_arm)
    bpy.context.view_layer.objects.active = exp_arm
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = exp_data.edit_bones

    for nm in ("Reference",):
        eb = ebs.new(nm)
        eb.head = Vector((0, 0, 0))
        eb.tail = Vector((0, 0, 1))

    for b in robo_spec["bones"]:
        nm = b["name"]
        p = um_b_pos[nm]
        eb = ebs.get(nm) or ebs.new(nm)
        eb.head = p
        eb.tail = p + (Vector((0, -0.15, 0)) if "Toe" in nm else Vector((0, 0, -0.25)))

    PARENT_FALLBACK = {
        "Neck": "Spine1",
        "LeftArmRoll": "LeftArm",
        "LeftForeArmRoll": "LeftForeArm",
        "RightArmRoll": "RightArm",
        "RightForeArmRoll": "RightForeArm",
    }
    for b in robo_spec["bones"]:
        nm = b["name"]
        par = b["parent"]
        if par not in ebs:
            par = PARENT_FALLBACK.get(par, "Reference")
        ebs[nm].parent = ebs[par]
        ebs[nm].use_connect = False

    bpy.ops.object.mode_set(mode="OBJECT")

    for b in robo_spec["bones"]:
        if b["name"] not in robot.vertex_groups:
            robot.vertex_groups.new(name=b["name"])
    robot.parent = exp_arm
    final_mod = robot.modifiers.new("Armature", "ARMATURE")
    final_mod.object = exp_arm

    for o in list(bpy.data.objects):
        o.select_set(o in (exp_arm, robot))

    for out_fbx in (FBX_EXPORT_DIR / "tarn_robot_prepared.fbx", UNITY_TARN_DIR / "tarn_robot_prepared.fbx"):
        bpy.ops.export_scene.fbx(
            filepath=str(out_fbx),
            use_selection=True,
            object_types={"ARMATURE", "MESH"},
            apply_scale_options="FBX_SCALE_ALL",
            axis_forward="-Y",
            axis_up="Z",
            use_space_transform=False,
            add_leaf_bones=False,
            mesh_smooth_type="FACE",
            bake_anim=False,
        )
        print(f"[✓] Exported FBX: {out_fbx}")

    rigged_blend = TARN_DIR / "06_working" / "tarn_rigged_um53.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(rigged_blend))

    # Gate 2 Inspection Renders
    bpy.ops.wm.obj_import(filepath=str(UM_OBJ))
    um_ref = bpy.context.selected_objects[0]
    um_ref.name = "UM_REF_00_Gate2"
    um_ref.location = (5.2, 0.0, 0.0)
    clay = bpy.data.materials.new("UM_Clay_G2")
    clay.use_nodes = True
    clay.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (0.76, 0.80, 0.88, 1.0)
    um_ref.data.materials.clear()
    um_ref.data.materials.append(clay)

    for o in bpy.data.objects:
        if o.type == "MESH":
            o.hide_render = (o not in (robot, um_ref))

    scene = bpy.context.scene
    scene.cycles.device = "CPU"
    scene.cycles.samples = 48
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 860
    if not scene.camera:
        cd = bpy.data.cameras.new("G2Cam")
        cam = bpy.data.objects.new("G2Cam", cd)
        scene.collection.objects.link(cam)
        scene.camera = cam
    else:
        cam = scene.camera

    if not any(o.type == "LIGHT" for o in scene.objects):
        for nm, eng, loc in [("Key", 1800, (-8, -14, 15)), ("Fill", 900, (10, -12, 8)), ("Rim", 1100, (0, 12, 14))]:
            ld = bpy.data.lights.new(nm, type="AREA")
            ld.energy = eng
            ld.size = 6.0
            lo = bpy.data.objects.new(nm, ld)
            scene.collection.objects.link(lo)
            lo.location = Vector(loc)
            lo.rotation_euler = (Vector((0, 0, 6)) - lo.location).to_track_quat("-Z", "Y").to_euler()

    def render_cam(loc, target, fname):
        cam.location = Vector(loc)
        cam.data.lens = 45
        cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
        scene.render.filepath = str(SCRATCH_DIR / fname)
        bpy.ops.render.render(write_still=True)

    render_cam((2.2, -23.0, 6.8), (2.2, 0.0, 6.6), "gate2_tarn_vs_um_bind.png")

    um_ref.hide_render = True
    bpy.ops.object.select_all(action="DESELECT")
    exp_arm.select_set(True)
    bpy.context.view_layer.objects.active = exp_arm
    bpy.ops.object.mode_set(mode="POSE")

    for bname, deg_x in [("RightArm", -25), ("RightForeArm", -55), ("LeftArm", -20), ("LeftForeArm", -45), ("LeftUpLeg", -32), ("LeftLeg", 42)]:
        pb = exp_arm.pose.bones[bname]
        pb.rotation_mode = "XYZ"
        pb.rotation_euler = (math.radians(deg_x), 0, 0)
    for side, tsgn in [("Left", -1.0), ("Right", 1.0)]:
        for fn in ("Index", "Middle", "Ring", "Pinky"):
            for k, ang in [("1", 65), ("2", 75), ("3", 55)]:
                pb = exp_arm.pose.bones[f"{side}Hand{fn}{k}"]
                pb.rotation_mode = "XYZ"
                pb.rotation_euler = (0, math.radians(ang * (1 if side == "Left" else -1)), 0)
        for k, ang in [("1", 30), ("2", 55), ("3", 45)]:
            pb = exp_arm.pose.bones[f"{side}HandThumb{k}"]
            pb.rotation_mode = "XYZ"
            pb.rotation_euler = (0, 0, math.radians(ang * tsgn))
    bpy.context.view_layer.update()
    render_cam((9.5, -21.0, 7.2), (0.0, 0.0, 5.8), "gate2_tarn_fist_pose.png")

    for pb in exp_arm.pose.bones:
        pb.rotation_euler = (0, 0, 0)
    bpy.context.view_layer.update()
    # Camera slightly 3/4 outer-front on hands so all 5 fingers + thumb are clearly readable
    render_cam((4.8, -3.2, 5.2), (2.65, 0.0, 5.1), "gate2_tarn_left_hand_open.png")
    render_cam((-4.8, -3.2, 5.2), (-2.65, 0.0, 5.1), "gate2_tarn_right_hand_open.png")

    print("[OK] Phase 3 Robot Rigging + Gate 2 Renders complete!")


if __name__ == "__main__":
    main()
