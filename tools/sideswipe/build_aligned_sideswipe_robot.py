import os
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
import json
import math
import numpy as np
from mathutils import Vector, Matrix, Euler
from pathlib import Path

print("=== [Sideswipe] Stage 2: Master Robot Pipeline (FBX -> 77-Bone Retarget -> Gate 2 FBX) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "Sideswipe" / "01_source" / "Sideswipe.fbx"
DONOR_JSON = ROOT / "3rd-party-models" / "Sideswipe" / "00_donor_reference" / "donor_summary.json"
DONOR_OBJ = ROOT / "3rd-party-models" / "Sideswipe" / "00_donor_reference" / "cha_barricade_cin_dotm_00_robot.obj"
TEX_DIR = ROOT / "3rd-party-models" / "Sideswipe" / "02_textures"
ALIGNED_DIR = ROOT / "3rd-party-models" / "Sideswipe" / "01_aligned_mesh"
FBX_OUT_DIR = ROOT / "3rd-party-models" / "Sideswipe" / "03_fbx_exports"
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Sideswipe"
RENDERS_DIR = ROOT / "renders" / "sideswipe"

for d in (ALIGNED_DIR, FBX_OUT_DIR, UNITY_DIR, RENDERS_DIR):
    d.mkdir(parents=True, exist_ok=True)

BARRICADE_77_BONES = [
    "LeftShoulder", "LeftArm", "Spine1", "Head", "Neck", "Spine", "LeftForeArm", "LeftArmRoll",
    "Hips", "LeftUpLeg", "LeftLeg", "LeftProp", "LeftHandThumb2", "LeftForeArmRoll", "LeftHandThumb3",
    "LeftHand", "LeftHandThumb1", "LeftInBrow", "LeftLowEyeLid", "LeftOutBrow", "LeftUpperLip",
    "LeftCornerLip", "LeftUpEyeLid", "RightLowerLip", "Jaw", "LeftFoot", "RightFoot", "RightLeg",
    "LeftHandPinky3", "LeftHandRing3", "LeftHandMiddle3", "LeftHandPinky2", "LeftToeBase",
    "Left_FootFx", "LeftToe", "LeftEye", "RightToeBase", "LeftHandIndex2", "LeftHandIndex1",
    "LeftHandPinky1", "LeftHandMiddle1", "LeftHandMiddle2", "LeftHandRing2", "LeftHandRing1",
    "LeftHandIndex3", "RightShoulder", "RightArm", "RightForeArm", "RightArmRoll", "RightUpLeg",
    "RightProp", "RightHandThumb2", "RightForeArmRoll", "RightHandThumb3", "RightHand",
    "RightHandThumb1", "RightInBrow", "RightLowEyeLid", "RightOutBrow", "RightUpperLip",
    "RightCornerLip", "RightUpEyeLid", "RightHandPinky3", "RightHandRing3", "RightHandMiddle3",
    "RightHandPinky2", "Right_FootFx", "RightToe", "RightEye", "RightHandIndex2", "RightHandIndex1",
    "RightHandPinky1", "RightHandMiddle1", "RightHandMiddle2", "RightHandRing2", "RightHandRing1",
    "RightHandIndex3"
]

BARRICADE_PARENT_MAP = {
    "Hips": None,
    "Spine": "Hips",
    "Spine1": "Spine",
    "Neck": "Spine1",
    "Head": "Neck",
    "Jaw": "Head",
    "LeftInBrow": "Head", "LeftLowEyeLid": "Head", "LeftOutBrow": "Head", "LeftUpperLip": "Head",
    "LeftCornerLip": "Head", "LeftUpEyeLid": "Head", "LeftEye": "Head",
    "RightInBrow": "Head", "RightLowEyeLid": "Head", "RightOutBrow": "Head", "RightUpperLip": "Head",
    "RightCornerLip": "Head", "RightUpEyeLid": "Head", "RightEye": "Head",
    "RightLowerLip": "Jaw",
    "LeftShoulder": "Spine1",
    "LeftArm": "LeftShoulder",
    "LeftArmRoll": "LeftArm",
    "LeftForeArm": "LeftArmRoll",
    "LeftForeArmRoll": "LeftForeArm",
    "LeftHand": "LeftForeArmRoll",
    "LeftProp": "LeftHand",
    "LeftHandThumb1": "LeftHand",
    "LeftHandThumb2": "LeftHandThumb1",
    "LeftHandThumb3": "LeftHandThumb2",
    "LeftHandIndex1": "LeftHand",
    "LeftHandIndex2": "LeftHandIndex1",
    "LeftHandIndex3": "LeftHandIndex2",
    "LeftHandMiddle1": "LeftHand",
    "LeftHandMiddle2": "LeftHandMiddle1",
    "LeftHandMiddle3": "LeftHandMiddle2",
    "LeftHandRing1": "LeftHand",
    "LeftHandRing2": "LeftHandRing1",
    "LeftHandRing3": "LeftHandRing2",
    "LeftHandPinky1": "LeftHand",
    "LeftHandPinky2": "LeftHandPinky1",
    "LeftHandPinky3": "LeftHandPinky2",
    "RightShoulder": "Spine1",
    "RightArm": "RightShoulder",
    "RightArmRoll": "RightArm",
    "RightForeArm": "RightArmRoll",
    "RightForeArmRoll": "RightForeArm",
    "RightHand": "RightForeArmRoll",
    "RightProp": "RightHand",
    "RightHandThumb1": "RightHand",
    "RightHandThumb2": "RightHandThumb1",
    "RightHandThumb3": "RightHandThumb2",
    "RightHandIndex1": "RightHand",
    "RightHandIndex2": "RightHandIndex1",
    "RightHandIndex3": "RightHandIndex2",
    "RightHandMiddle1": "RightHand",
    "RightHandMiddle2": "RightHandMiddle1",
    "RightHandMiddle3": "RightHandMiddle2",
    "RightHandRing1": "RightHand",
    "RightHandRing2": "RightHandRing1",
    "RightHandRing3": "RightHandRing2",
    "RightHandPinky1": "RightHand",
    "RightHandPinky2": "RightHandPinky1",
    "RightHandPinky3": "RightHandPinky2",
    "LeftUpLeg": "Hips",
    "LeftLeg": "LeftUpLeg",
    "LeftFoot": "LeftLeg",
    "LeftToeBase": "LeftFoot",
    "Left_FootFx": "LeftToeBase",
    "LeftToe": "LeftToeBase",
    "RightUpLeg": "Hips",
    "RightLeg": "RightUpLeg",
    "RightFoot": "RightLeg",
    "RightToeBase": "RightFoot",
    "Right_FootFx": "RightToeBase",
    "RightToe": "RightToeBase",
}


def unity_to_blender(upos):
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))


def load_barricade_bones():
    with open(DONOR_JSON, "r", encoding="utf-8") as f:
        donor = json.load(f)
    mesh_00 = donor["meshes"]["cha_barricade_cin_dotm_00"]
    tos_00 = donor["avatars"]["cha_barricade_cin_dotm_00Avatar"]["tos"]
    bpos = {}
    for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
        mat = np.array([
            [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
            [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
            [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
            [bp["e30"], bp["e31"], bp["e32"], bp["e33"]]
        ])
        inv_mat = np.linalg.inv(mat)
        bname = tos_00.get(str(h), f"bone_{idx}").split("/")[-1]
        bpos[bname] = unity_to_blender(inv_mat[:3, 3])
    return bpos


def make_sideswipe_preview_material():
    mat = bpy.data.materials.new("M_Sideswipe_Main")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / "cha_sideswipe_main_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = bpy.data.images.load(str(TEX_DIR / "cha_sideswipe_main_Normal_unity.png"))
    tn.image.colorspace_settings.name = "Non-Color"
    nm = nt.nodes.new("ShaderNodeNormalMap")
    nt.links.new(tn.outputs["Color"], nm.inputs["Color"])
    nt.links.new(nm.outputs["Normal"], bsdf.inputs["Normal"])

    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / "cha_sideswipe_main_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 3.0
    bsdf.inputs["Roughness"].default_value = 0.40
    bsdf.inputs["Metallic"].default_value = 0.30
    return mat


def make_sideswipe_lights_material():
    mat = bpy.data.materials.new("M_Sideswipe_Lights")
    mat.use_nodes = True
    nt = mat.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])

    ta = nt.nodes.new("ShaderNodeTexImage")
    ta.image = bpy.data.images.load(str(TEX_DIR / "cha_sideswipe_main_Diffuse.png"))
    nt.links.new(ta.outputs["Color"], bsdf.inputs["Base Color"])

    te = nt.nodes.new("ShaderNodeTexImage")
    te.image = bpy.data.images.load(str(TEX_DIR / "cha_sideswipe_main_Emission.png"))
    nt.links.new(te.outputs["Color"], bsdf.inputs["Emission"])
    bsdf.inputs["Emission Strength"].default_value = 4.0
    bsdf.inputs["Roughness"].default_value = 0.25
    bsdf.inputs["Metallic"].default_value = 0.0
    return mat


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

    donor_bones = load_barricade_bones()
    print(f"[✓] Loaded {len(donor_bones)} Barricade authoritative bone positions.")

    mesh_objs = [o for o in bpy.data.objects if o.type == 'MESH']
    arm = bpy.data.objects.get("Armature")
    for o in mesh_objs:
        o.modifiers.clear()
        o.parent = None
    if arm:
        bpy.data.objects.remove(arm, do_unlink=True)

    # 1. Coordinate alignment: R_x(180) to ground upright with +X=Left, -X=Right, -Y=Forward
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.transform.rotate(value=math.pi, orient_axis='X')
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=True)

    # 2. Ground feet at Z=0.000 and scale height to match Barricade (10.85m)
    all_z = [v.co.z for o in mesh_objs for v in o.data.vertices]
    z_min = min(all_z)
    z_max = max(all_z)
    scale_factor = 10.85 / (z_max - z_min)
    print(f"Grounding Z (min={z_min:.4f}) and scaling by {scale_factor:.4f} -> Height 10.85m")

    for o in mesh_objs:
        for v in o.data.vertices:
            v.co.z -= z_min
            v.co.x *= scale_factor
            v.co.y *= scale_factor
            v.co.z *= scale_factor
        o.data.update()

    # 2.5 Tag Mesh 20 (chest headlights) and remap UVs to isolated red vent coords (0.012, 0.011)
    for o in mesh_objs:
        if o.name == "20" or any(m and m.name == "Lights" for m in o.data.materials):
            vg = o.vertex_groups.new(name="VG_ChestLights")
            vg.add(list(range(len(o.data.vertices))), 1.0, "REPLACE")
            uvl = o.data.uv_layers.active
            if uvl:
                for p in o.data.polygons:
                    for li in p.loop_indices:
                        uvl.data[li].uv = (0.012, 0.011)
                o.data.update()
                print("[✓] Tagged Mesh 20 (VG_ChestLights) and remapped to isolated red vent coords (0.012, 0.011).")

    # 3. Join all submeshes into a single master mesh
    bpy.ops.object.select_all(action='DESELECT')
    for o in mesh_objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = mesh_objs[0]
    bpy.ops.object.join()
    robot = bpy.context.active_object
    robot.name = "cha_sideswipe_main"

    # 4. Rotate arms downward (~58 deg) around shoulder joints to align rest pose with Barricade (hang vertically)
    vg_map = {vg.name: vg.index for vg in robot.vertex_groups}
    l_arm_vgs = [vg_map[n] for n in ["Bip_UpperArm_L", "Bip_LowerArm_L", "Bip_Hand_L", "Bn_Sword_L", 
                                     "Bip_Thumb_0_L", "Bip_Thumb_1_L", "Bip_Index_0_L", "Bip_Index_1_L", 
                                     "Bip_Middle_0_L", "Bip_Middle_1_L"] if n in vg_map]

    r_arm_vgs = [vg_map[n] for n in ["Bip_UpperArm_R", "Bip_LowerArm_R", "Bip_Hand_R", "Bn_Sword_R", 
                                     "Bip_Thumb_0_R", "Bip_Thumb_1_R", "Bip_Index_0_R", "Bip_Index_1_R", 
                                     "Bip_Middle_0_R", "Bip_Middle_1_R"] if n in vg_map]

    pivot_L = Vector((2.05, -0.20, 8.69))
    R_L = Euler((0, math.radians(58), 0), 'XYZ').to_matrix()

    pivot_R = Vector((-2.05, -0.20, 8.69))
    R_R = Euler((0, math.radians(-58), 0), 'XYZ').to_matrix()

    for v in robot.data.vertices:
        is_l = any(g.group in l_arm_vgs and g.weight > 0.3 for g in v.groups)
        is_r = any(g.group in r_arm_vgs and g.weight > 0.3 for g in v.groups)
        if is_l:
            v.co = pivot_L + R_L @ (v.co - pivot_L)
        elif is_r:
            v.co = pivot_R + R_R @ (v.co - pivot_R)
    robot.data.update()
    print("[✓] Posed arms downward (58°) along Barricade vertical rest alignment.")

    # 5. Clean UV Clamping into [0.004, 0.996]
    uv_layer = robot.data.uv_layers.active
    assert uv_layer is not None, "Robot missing active UV layer!"
    for loop in robot.data.loops:
        uv = uv_layer.data[loop.index].uv
        u_clamped = min(0.996, max(0.004, uv.x))
        v_clamped = min(0.996, max(0.004, uv.y))
        uv_layer.data[loop.index].uv = (u_clamped, v_clamped)
    robot.data.update()
    print("[✓] UV clamped to [0.004, 0.996] successfully.")

    # 6. Retargeting Vertex Groups to Barricade 77 Bones (Plan A: 灵动三指映射)
    bone_mapping = {
        # Torso & Head
        "Root": "Hips",
        "Bip_Pelvis": "Hips",
        "Bn_Pelvis": "Hips",
        "Bip_Spine_0": "Spine",
        "Bip_Spine_1": "Spine1",
        "Bn_DoorL_1": "Spine1",
        "Bn_DoorL_2": "Spine1",
        "Bn_DoorR_1": "Spine1",
        "Bn_DoorR_2": "Spine1",
        "Bip_Neck": "Neck",
        "Bip_Head": "Head",
        # Arms
        "Bn_Shoulder_L": "LeftShoulder",
        "Bip_Collar_L": "LeftShoulder",
        "Bip_UpperArm_L": "LeftArm",
        "Bip_LowerArm_L": "LeftForeArm",
        "Bn_Sword_L": "LeftForeArm",
        "Bip_Hand_L": "LeftHand",
        "Bn_Shoulder_R": "RightShoulder",
        "Bip_Collar_R": "RightShoulder",
        "Bip_UpperArm_R": "RightArm",
        "Bip_LowerArm_R": "RightForeArm",
        "Bn_Sword_R": "RightForeArm",
        "Bip_Hand_R": "RightHand",
        # Left Hand & 3 Fingers (Solid Hand mapping - prevents finger segments floating/disconnecting)
        "Bip_Thumb_0_L": "LeftHand",
        "Bip_Thumb_1_L": "LeftHand",
        "Bip_Index_0_L": "LeftHand",
        "Bip_Index_1_L": "LeftHand",
        "Bip_Middle_0_L": "LeftHand",
        "Bip_Middle_1_L": "LeftHand",
        # Right Hand & 3 Fingers (Solid Hand mapping)
        "Bip_Thumb_0_R": "RightHand",
        "Bip_Thumb_1_R": "RightHand",
        "Bip_Index_0_R": "RightHand",
        "Bip_Index_1_R": "RightHand",
        "Bip_Middle_0_R": "RightHand",
        "Bip_Middle_1_R": "RightHand",
        # Legs & Feet
        "Bip_Hip_L": "LeftUpLeg",
        "Bip_Knee_L": "LeftLeg",
        "Bip_Foot_L": "LeftFoot",
        "Bn_Wheel_L": "LeftFoot",
        "Bn_PistonL_1": "LeftUpLeg",
        "Bn_PistonL_2": "LeftFoot",
        "Bip_Hip_R": "RightUpLeg",
        "Bip_Knee_R": "RightLeg",
        "Bip_Foot_R": "RightFoot",
        "Bn_Wheel_R": "RightFoot",
        "Bn_PistonR_1": "RightUpLeg",
        "Bn_PistonR_2": "RightFoot",
    }

    vg_idx_to_name = {vg.index: vg.name for vg in robot.vertex_groups}
    v_weights = []
    zero_w_count = 0
    rigid_count = 0

    for v in robot.data.vertices:
        wdict = {}
        for g in v.groups:
            orig_n = vg_idx_to_name.get(g.group, "")
            tgt_n = bone_mapping.get(orig_n, "Spine1")
            wdict[tgt_n] = wdict.get(tgt_n, 0.0) + g.weight
        tot = sum(wdict.values())
        if tot <= 1e-6:
            wdict = {"Spine1": 1.0}
            zero_w_count += 1
        else:
            for k in wdict:
                wdict[k] /= tot
            top_b, top_w = max(wdict.items(), key=lambda kv: kv[1])
            if top_w >= 0.65:
                wdict = {top_b: 1.0}
                rigid_count += 1
        v_weights.append(wdict)

    print(f"[✓] Audited weights: verts={len(v_weights)}, zero_w_fixed={zero_w_count}, rigid_snapped={rigid_count}")

    # 7. Build Authoritative 77-Bone Barricade Armature in Blender space
    arm_data = bpy.data.armatures.new("ARM_Sideswipe_Robot_Data")
    new_arm = bpy.data.objects.new("ARM_Sideswipe_Robot", arm_data)
    bpy.context.scene.collection.objects.link(new_arm)
    bpy.context.view_layer.objects.active = new_arm
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm_data.edit_bones

    for bname in BARRICADE_77_BONES:
        p = donor_bones[bname]
        eb = ebs.new(bname)
        eb.head = p
        if "Thumb" in bname:
            eb.tail = p + Vector((0, -0.15, 0))
        elif any(f in bname for f in ("Index", "Middle", "Ring", "Pinky")):
            eb.tail = p + Vector((0, 0, -0.15))
        elif "Leg" in bname or "Foot" in bname or "Arm" in bname or "Hand" in bname:
            eb.tail = p + Vector((0, 0, -0.30))
        else:
            eb.tail = p + Vector((0, 0, 0.30))

    for bname in BARRICADE_77_BONES:
        pn = BARRICADE_PARENT_MAP.get(bname)
        if pn and pn in ebs:
            ebs[bname].parent = ebs[pn]
            ebs[bname].use_connect = False
    bpy.ops.object.mode_set(mode="OBJECT")

    # Clear old vertex groups and create all 77 authoritative vertex groups
    robot.vertex_groups.clear()
    new_vgs = {bname: robot.vertex_groups.new(name=bname) for bname in BARRICADE_77_BONES}
    for vi, wd in enumerate(v_weights):
        for bn, w in wd.items():
            if bn in new_vgs and w > 0.001:
                new_vgs[bn].add([vi], w, "REPLACE")

    robot.parent = new_arm
    mod = robot.modifiers.new("Armature", "ARMATURE")
    mod.object = new_arm

    # Consolidate materials: Slot 0 = Main Body (Silver armor + Blue eyes), Slot 1 = Chest Headlights (Red lights)
    robot.data.materials.clear()
    mat_prev = make_sideswipe_preview_material()
    mat_lights = make_sideswipe_lights_material()
    robot.data.materials.append(mat_prev)
    robot.data.materials.append(mat_lights)

    uv_layer = robot.data.uv_layers.active.data
    lights_poly_count = 0
    for poly in robot.data.polygons:
        u_mean = sum(uv_layer[li].uv[0] for li in poly.loop_indices) / len(poly.loop_indices)
        v_mean = sum(uv_layer[li].uv[1] for li in poly.loop_indices) / len(poly.loop_indices)
        if u_mean < 0.025 and v_mean < 0.025:
            poly.material_index = 1
            lights_poly_count += 1
        else:
            poly.material_index = 0
    print(f"[✓] Assigned {lights_poly_count} polygons to Slot 1 (M_Sideswipe_Lights), {len(robot.data.polygons)-lights_poly_count} to Slot 0 (M_Sideswipe_Main)")

    # Verify bounds
    xs = [v.co.x for v in robot.data.vertices]
    ys = [v.co.y for v in robot.data.vertices]
    zs = [v.co.z for v in robot.data.vertices]
    print(f"[Bounds] Robot Blender space: X=[{min(xs):.3f},{max(xs):.3f}] Y=[{min(ys):.3f},{max(ys):.3f}] Z=[{min(zs):.3f},{max(zs):.3f}]")

    # 8. Export FBX (Standard axis_forward='-Z', axis_up='Y')
    bpy.ops.object.select_all(action="DESELECT")
    robot.select_set(True)
    new_arm.select_set(True)
    bpy.context.view_layer.objects.active = new_arm

    for fbx_out in (FBX_OUT_DIR / "sideswipe_robot_prepared.fbx", UNITY_DIR / "sideswipe_robot_prepared.fbx"):
        bpy.ops.export_scene.fbx(
            filepath=str(fbx_out),
            use_selection=True,
            object_types={"ARMATURE", "MESH"},
            apply_scale_options="FBX_SCALE_ALL",
            axis_forward="-Z",
            axis_up="Y",
            add_leaf_bones=False,
            bake_anim=False,
        )
    print(f"[✓] Exported Prepared Robot FBX: {UNITY_DIR / 'sideswipe_robot_prepared.fbx'}")
    bpy.ops.wm.save_as_mainfile(filepath=str(ALIGNED_DIR / "sideswipe_robot_aligned.blend"))

    # 9. Render Gate 2 Blender Side-by-Side Comparison (Barricade Donor OBJ + Sideswipe)
    bpy.ops.wm.obj_import(filepath=str(DONOR_OBJ))
    barr_ref = bpy.context.selected_objects[0]
    barr_ref.name = "Barricade_Donor_Ref"

    # Place side-by-side: Barricade at X = -3.8, Sideswipe at X = +3.8
    barr_ref.location = (-3.8, 0.0, 0.0)
    new_arm.location = (3.8, 0.0, 0.0)
    bpy.context.view_layer.update()

    scene = bpy.context.scene
    scene.render.engine = "BLENDER_EEVEE"
    scene.render.resolution_x = 1600
    scene.render.resolution_y = 900
    world = bpy.data.worlds.new("World")
    scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    if bg:
        bg.inputs[0].default_value = (0.12, 0.13, 0.16, 1.0)
        bg.inputs[1].default_value = 0.8

    for lx, ly, lz, energy in [(6, -14, 12, 3500), (-8, -12, 8, 2200), (0, 14, 10, 1800)]:
        ld = bpy.data.lights.new("L", type="POINT")
        ld.energy = energy
        lo = bpy.data.objects.new("Light", ld)
        lo.location = (lx, ly, lz)
        scene.collection.objects.link(lo)

    cam_d = bpy.data.cameras.new("Cam")
    cam_d.lens = 42
    cam = bpy.data.objects.new("Cam", cam_d)
    cam.location = (0.0, -24.0, 5.8)
    direction = Vector((0.0, 0.0, 5.4)) - cam.location
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
    scene.collection.objects.link(cam)
    scene.camera = cam

    out_sbs = RENDERS_DIR / "gate2_blender_robot_sbs.png"
    scene.render.filepath = str(out_sbs)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered Gate 2 Blender SBS: {out_sbs}")

    # Left Hand Closeup (Sideswipe offset at X=3.8, LeftHand at X ~ 3.8 + 3.25 = 7.05, Y ~ -0.4, Z ~ 6.18)
    lh_focus = Vector((3.8 + 3.25, -0.40, 6.18))
    cam.location = lh_focus + Vector((1.6, -2.2, 0.2))
    cam.rotation_euler = (lh_focus - cam.location).to_track_quat("-Z", "Y").to_euler()
    out_lh = RENDERS_DIR / "gate2_blender_lhand_closeup.png"
    scene.render.filepath = str(out_lh)
    bpy.ops.render.render(write_still=True)
    print(f"[✓] Rendered Gate 2 Left-Hand 3-Finger Closeup: {out_lh}")


if __name__ == "__main__":
    main()
