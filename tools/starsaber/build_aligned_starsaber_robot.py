import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import bmesh
import json
import math
from mathutils import Vector, Matrix, Quaternion
from pathlib import Path

print("=== [StarSaber] Stage 2 Master Robot Pipeline (FBX -> Jetfire 54-Bone Alignment) ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_SRC = ROOT / "3rd-party-models" / "StarSaber" / "source" / "StarSaber.fbx"
DONOR_REF_DIR = ROOT / "3rd-party-models" / "StarSaber" / "00_donor_reference"
OUT_FBX_DIR = ROOT / "3rd-party-models" / "StarSaber" / "03_fbx_exports"
OUT_FBX_DIR.mkdir(parents=True, exist_ok=True)
UNITY_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "StarSaber"
UNITY_DIR.mkdir(parents=True, exist_ok=True)

# Load Jetfire 54 bones ground truths
with open(DONOR_REF_DIR / "jetfire_54_bones_truth.json", "r", encoding="utf-8") as f:
    donor_bones_data = json.load(f)

with open(DONOR_REF_DIR / "jetfire_donor_summary.json", "r", encoding="utf-8") as f:
    donor_summary = json.load(f)

JETFIRE_54_BONES = donor_summary["bone_names"]

def unity_to_blender(upos):
    return Vector((-float(upos[0]), -float(upos[2]), float(upos[1])))

# Map from Star Saber original 69 vertex groups to Jetfire 54 standard bones
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
    
    # Left Arm & Hand (Track B: Fingers folded to LeftHand to prevent disjointed distortion)
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
    
    # Right Arm & Hand (Track B: Fingers folded to RightHand to maintain solid grip on King's Sword)
    "Dummy_Shoulder_004": "RightShoulder",
    "Dummy_Shoulder_0042": "RightShoulderPad",
    "UpperArmR": "RightArm",
    "Dummy_Arm_003": "RightForeArm",
    "Dummy_hand_002": "RightHand",
    "Hand_R_1": "RightHand",
    "Hand_R_4": "RightHand",
    "Hand_R_5": "RightHand",
    "Hand_R_2": "RightHand",
    "Hand_R_6": "RightHand",
    "Hand_R_7": "RightHand",
    "Hand_R_3": "RightHand",
    "Hand_R_8": "RightHand",
    "Hand_R_9": "RightHand",
}

# Jetfire hierarchy
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
    JETFIRE_PARENT_MAP[f"RightHand{fn}1"] = "RightHand"
    JETFIRE_PARENT_MAP[f"RightHand{fn}2"] = f"RightHand{fn}1"
    JETFIRE_PARENT_MAP[f"RightHand{fn}3"] = f"RightHand{fn}2"


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    
    print("[*] Importing StarSaber.fbx...")
    bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
    
    for o in bpy.data.objects:
        if o.animation_data:
            o.animation_data_clear()
            
    mesh = bpy.data.objects.get("StarSaber.001")
    sword = bpy.data.objects.get("StarSaberSword")
    ab_sym = bpy.data.objects.get("Symbol_AB.001")
    assert mesh and sword, "Missing required StarSaber meshes!"
    
    keep_objs = {mesh, sword}
    if ab_sym:
        keep_objs.add(ab_sym)
        
    for o in list(bpy.data.objects):
        if o not in keep_objs:
            bpy.data.objects.remove(o, do_unlink=True)
            
    for o in keep_objs:
        o.parent = None
        o.matrix_world = Matrix.Identity(4)
        
    # Scale calculation:
    # Jetfire Head Z = 11.499, Foot contact Z = 0.000 (total height ~11.5m, cannons ~14.1m).
    # StarSaber raw: Head VG Z ~ 2.824, maximum crown Z ~ 3.390, Foot Z ~ 0.106.
    # Grounded raw: Head Z = 2.717m, Shoulders Z = 2.474m, Hand Z = 1.436m, Crown Z = 3.283m.
    # Uniform scale ~ 4.12x matches Head Z to 11.63m (Jetfire 11.50m), Hand Z to 6.24m (Jetfire 6.29m),
    # Shoulder Z to 11.02m (Jetfire 10.79m), and Crown to 13.97m (Autobot Supreme Commander aura).
    SCALE_FACTOR = 4.12
    print(f"[*] Applying uniform scale factor: {SCALE_FACTOR:.4f} (keeping native Blender axes: Left=+X, Right=-X, Fwd=-Y, Up=+Z)")
    
    scale_mat = Matrix.Scale(SCALE_FACTOR, 4)
    mesh.data.transform(scale_mat)
    mesh.data.update()
    
    if ab_sym:
        ab_sym.data.transform(scale_mat)
        ab_sym.data.update()
        
    # Calculate foot bottom min_z and ground strictly at Z = 0.000m
    min_z = min(v.co.z for v in mesh.data.vertices)
    print(f"[*] Min Z before grounding: {min_z:.4f}m")
    ground_mat = Matrix.Translation(Vector((0.0, 0.0, -min_z)))
    mesh.data.transform(ground_mat)
    mesh.data.update()
    if ab_sym:
        ab_sym.data.transform(ground_mat)
        ab_sym.data.update()
        
    new_zs = [v.co.z for v in mesh.data.vertices]
    print(f"[✓] Grounded mesh! New Z span: [{min(new_zs):.3f}, {max(new_zs):.3f}]")

    # Verify Blender axis contract: Left = +X, Right = -X, Forward = -Y
    lh_vg = mesh.vertex_groups.get("Dummy_hand_01")
    rh_vg = mesh.vertex_groups.get("Dummy_hand_002")
    lh_xs = [v.co.x for v in mesh.data.vertices if any(g.group == lh_vg.index and g.weight > 0.4 for g in v.groups)]
    rh_xs = [v.co.x for v in mesh.data.vertices if any(g.group == rh_vg.index and g.weight > 0.4 for g in v.groups)]
    lh_mx = sum(lh_xs) / len(lh_xs)
    rh_mx = sum(rh_xs) / len(rh_xs)
    print(f"[*] Axis Check: LeftHand mean X={lh_mx:.3f} (+X), RightHand mean X={rh_mx:.3f} (-X)")
    assert lh_mx > 1.0 and rh_mx < -1.0, f"Axis alignment violated! LH={lh_mx}, RH={rh_mx}"
    print("[✓] Left/Right axis contract (Left=+X, Right=-X) PASS!")

    # Merge Autobot symbol into main mesh
    if ab_sym:
        # Offset forward along -Y by 0.015m (scaled space) to lift emblem off plate & eliminate Z-fighting
        ab_sym.data.transform(Matrix.Translation(Vector((0.0, -0.015, 0.0))))
        ab_sym.data.update()

        # Assign clean palette UVs based on material index BEFORE clearing materials:
        # Mat 0 (raised Autobot crest, 496 polys) -> clean vibrant red patch at U=0.362, V=0.425
        # Mat 1 (dark charcoal backing, 34 polys) -> clean dark charcoal patch at U=0.388, V=0.425
        if not ab_sym.data.uv_layers:
            ab_sym.data.uv_layers.new(name="UVMap")
        uvl = ab_sym.data.uv_layers.active.data
        for p in ab_sym.data.polygons:
            target_uv = (0.362, 0.425) if p.material_index == 0 else (0.388, 0.425)
            for li in p.loop_indices:
                uvl[li].uv = target_uv

        ab_sym.data.materials.clear()
        if mesh.data.materials:
            ab_sym.data.materials.append(mesh.data.materials[0])
        bpy.ops.object.select_all(action='DESELECT')
        ab_sym.select_set(True)
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = mesh
        bpy.ops.object.join()
        print("[✓] Prepared and merged clean 3D Autobot emblems into StarSaber main mesh.")

    # Explicit material setup
    mesh.data.materials.clear()
    mat_main = bpy.data.materials.new(name="cha_starsaber_main")
    mesh.data.materials.append(mat_main)

    sword.data.materials.clear()
    mat_wpn = bpy.data.materials.new(name="cha_starsaber_wpns")
    sword.data.materials.append(mat_wpn)

    # 2. Position and Scale StarSaberSword in Right Hand
    # Sword geometry in raw local coords: Grip Z in [-0.39, 0.0], Crossguard at Z=0.0, Blade Z in [0.0, 3.23].
    # Pitch forward 65 deg around X (-Y in Blender, +Z in Unity) so the 7m blade extends forward/upward,
    # completely clearing the forearm and elbow (>0.5m clearance in I-pose, and heroic ready-stance in idle).
    # Hand & fingers cavity at SCALE_FACTOR=4.12: X=-1.95, Y=-0.04, Z=6.02
    SWORD_SCALE = 2.0
    sword_scale = Matrix.Scale(SWORD_SCALE, 4)
    rot_x = Matrix.Rotation(math.radians(65.0), 4, 'X')
    rot_z = Matrix.Rotation(math.radians(-6.0), 4, 'Z')
    sword_rot = rot_z @ rot_x
    # Right palm grasp cavity center at SCALE_FACTOR=4.12: X=-2.12, Y=-0.04, Z=5.88
    palm_target = Vector((-2.12, -0.04, 5.88))
    local_grip = Vector((0.0, 0.0, -0.20))
    world_grip = sword_rot @ (sword_scale @ local_grip)
    sword_trans = Matrix.Translation(palm_target - world_grip)
    sword_mat = sword_trans @ sword_rot @ sword_scale
    
    sword.data.transform(sword_mat)
    sword.data.update()
    print(f"[✓] Transformed and positioned StarSaberSword precisely in RightHand palm!")

    # 3. Bone Weights Remapping
    print("[*] Remapping vertex groups to Jetfire 54 bones...")
    vg_dict = {vg.name: vg for vg in mesh.vertex_groups}
    
    target_vgs = {}
    for bn in JETFIRE_54_BONES:
        target_vgs[bn] = mesh.vertex_groups.new(name=bn)
        
    old_to_target = {}
    for old_name, target_name in VGROUP_MAP.items():
        if old_name in vg_dict:
            old_to_target[vg_dict[old_name].index] = target_vgs[target_name]
            
    for v in mesh.data.vertices:
        weights_to_add = {}
        for g in v.groups:
            if g.group in old_to_target:
                tgt_vg = old_to_target[g.group]
                weights_to_add[tgt_vg] = weights_to_add.get(tgt_vg, 0.0) + g.weight
                
        for tvg, w in weights_to_add.items():
            tvg.add([v.index], w, 'REPLACE')
            
    old_names = [vg.name for vg in mesh.vertex_groups if vg.name not in JETFIRE_54_BONES]
    for on in old_names:
        vg = mesh.vertex_groups.get(on)
        if vg:
            mesh.vertex_groups.remove(vg)
            
    # Zero weight audit
    zero_w_count = 0
    hips_vg = target_vgs["Hips"]
    for v in mesh.data.vertices:
        tot_w = sum(g.weight for g in v.groups)
        if tot_w < 1e-4:
            hips_vg.add([v.index], 1.0, 'REPLACE')
            zero_w_count += 1
            
    print(f"[*] Zero weight audit: fixed {zero_w_count} vertices (bound to Hips).")
    
    # Sword weights
    sword.vertex_groups.clear()
    sword_rh_vg = sword.vertex_groups.new(name="RightHand")
    all_sword_verts = [v.index for v in sword.data.vertices]
    sword_rh_vg.add(all_sword_verts, 1.0, 'REPLACE')
    print("[✓] Assigned 100% rigid weight on StarSaberSword to RightHand!")

    # 4. Build Armature for Jetfire 54 Bones
    print("[*] Creating 54-bone Jetfire Armature in Blender...")
    arm_data = bpy.data.armatures.new("cha_jetfire_gs_leader2014_00_arm")
    arm_obj = bpy.data.objects.new("cha_jetfire_gs_leader2014_00_arm", arm_data)
    bpy.context.scene.collection.objects.link(arm_obj)
    
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode='EDIT')
    
    edit_bones = {}
    for bn in JETFIRE_54_BONES:
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
                
    bpy.ops.object.mode_set(mode='OBJECT')
    print(f"[✓] Created Armature with {len(arm_data.bones)} bones!")

    # Merge sword into main mesh as Submesh 1
    bpy.ops.object.select_all(action='DESELECT')
    sword.select_set(True)
    mesh.select_set(True)
    bpy.context.view_layer.objects.active = mesh
    bpy.ops.object.join()
    print(f"[✓] Merged StarSaberSword into main mesh! Materials: {[m.name for m in mesh.data.materials if m]}")

    mesh.parent = arm_obj
    mod = mesh.modifiers.new("Armature", 'ARMATURE')
    mod.object = arm_obj

    # 5. Export FBX
    for out_fbx in (OUT_FBX_DIR / "starsaber_robot_prepared.fbx", UNITY_DIR / "starsaber_robot_prepared.fbx"):
        print(f"[*] Exporting prepared robot FBX to {out_fbx}...")
        bpy.ops.object.select_all(action='DESELECT')
        arm_obj.select_set(True)
        mesh.select_set(True)
        bpy.context.view_layer.objects.active = arm_obj
        
        bpy.ops.export_scene.fbx(
            filepath=str(out_fbx),
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
    print(f"[✓] Exported {out_fbx} successfully!")


if __name__ == "__main__":
    main()
