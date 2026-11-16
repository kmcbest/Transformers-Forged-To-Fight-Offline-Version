import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
from mathutils import Vector
import numpy as np

print("=== [Brawl] Building Rigged Robot and Tank FBX with EXACT Donor 39-Bone Ordering ===")

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR_REF_DIR = ROOT / "3rd-party-models" / "Brawl" / "00_donor_reference"
WORKING_DIR = ROOT / "3rd-party-models" / "Brawl" / "01_aligned_mesh"
FBX_EXPORT_DIR = ROOT / "3rd-party-models" / "Brawl" / "03_fbx_exports"
UNITY_BRAWL_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Brawl"

# Exact Megatron 39 bones order from cha_megatron_cin_rotf_00
MEGATRON_39_BONES = [
    "Spine",           # 0
    "Spine1",          # 1
    "Hips",            # 2
    "Neck",            # 3
    "Head",            # 4
    "Jaw",             # 5
    "RightUpLeg",      # 6
    "RightLeg",        # 7
    "LeftForeArm",     # 8
    "RightToeBase",    # 9
    "RightFoot",       # 10
    "RightShoulder",   # 11
    "RightArm",        # 12
    "LeftShoulder",    # 13
    "LeftArm",         # 14
    "LeftHand",        # 15
    "LeftHandMiddle1", # 16
    "LeftHandMiddle2", # 17
    "LeftHandMiddle3", # 18
    "LeftHandThumb1",  # 19
    "LeftHandThumb2",  # 20
    "LeftHandThumb3",  # 21
    "LeftHandIndex1",  # 22
    "LeftHandIndex2",  # 23
    "LeftHandIndex3",  # 24
    "LeftHandRing1",   # 25
    "LeftHandRing2",   # 26
    "LeftHandRing3",   # 27
    "LeftHandPinky1",  # 28
    "LeftHandPinky2",  # 29
    "LeftHandPinky3",  # 30
    "LeftLeg",         # 31
    "LeftFoot",        # 32
    "LeftToeBase",     # 33
    "LeftUpLeg",       # 34
    "RightForeArm",    # 35
    "LeftToe",         # 36
    "LeftArmRoll",     # 37
    "RightArmRoll",    # 38
]

# Load donor rest positions
with open(DONOR_REF_DIR / "donor_summary.json", "r", encoding="utf-8") as f:
    donor = json.load(f)

mesh_00 = donor["meshes"]["cha_megatron_cin_rotf_00"]
avatar_tos = donor["avatars"]["cha_megatron_cin_rotf_00Avatar"]["tos"]

bone_unity_pos = {}
for idx, (h, bp) in enumerate(zip(mesh_00["boneHashes"], mesh_00["bindposes"])):
    mat = np.array([
        [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
        [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
        [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
        [bp["e30"], bp["e31"], bp["e32"], bp["e33"]]
    ])
    inv_mat = np.linalg.inv(mat)
    pos = inv_mat[:3, 3]
    h_str = str(h)
    bone_path = avatar_tos.get(h_str, "")
    bname = bone_path.split("/")[-1] if bone_path else f"bone_{idx}"
    bone_unity_pos[bname] = Vector((float(pos[0]), float(pos[1]), float(pos[2])))

bone_parent_map = {
    "Hips": None,  # root of humanoid skeleton
    "Spine": "Hips",
    "Spine1": "Spine",
    "Neck": "Spine1",
    "Head": "Neck",
    "Jaw": "Head",
    "LeftShoulder": "Spine1",
    "LeftArm": "LeftShoulder",
    "LeftArmRoll": "LeftArm",
    "LeftForeArm": "LeftArmRoll",
    "LeftHand": "LeftForeArm",
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
    "LeftUpLeg": "Hips",
    "LeftLeg": "LeftUpLeg",
    "LeftFoot": "LeftLeg",
    "LeftToeBase": "LeftFoot",
    "LeftToe": "LeftToeBase",
    "RightUpLeg": "Hips",
    "RightLeg": "RightUpLeg",
    "RightFoot": "RightLeg",
    "RightToeBase": "RightFoot",
}

# -------------------------------------------------------------------------
# 1. RIG ROBOT MESH (EXACT 39 BONES)
# -------------------------------------------------------------------------
bpy.ops.wm.open_mainfile(filepath=str(WORKING_DIR / "brawl_robot_aligned.blend"))
if "Megatron_Donor_Ref" in bpy.data.objects:
    bpy.data.objects.remove(bpy.data.objects["Megatron_Donor_Ref"], do_unlink=True)

robot = bpy.data.objects.get("Brawl_Robot_Raw") or bpy.data.objects.get("cha_brawl_gs_00")
robot.name = "cha_brawl_gs_00"

# Preserve existing vertex weights mapping
v_weights_saved = []
vg_name_map = {vg.index: vg.name for vg in robot.vertex_groups}
for v in robot.data.vertices:
    wdict = {}
    for g in v.groups:
        if g.group in vg_name_map:
            wdict[vg_name_map[g.group]] = g.weight
    v_weights_saved.append(wdict)

# Remove any old armature objects
for o in list(bpy.data.objects):
    if o.type == 'ARMATURE':
        bpy.data.objects.remove(o, do_unlink=True)

# Create Armature
arm_data = bpy.data.armatures.new("ARM_Brawl_Robot_Data")
arm_obj = bpy.data.objects.new("ARM_Brawl_Robot", arm_data)
bpy.context.scene.collection.objects.link(arm_obj)
bpy.context.view_layer.objects.active = arm_obj
bpy.ops.object.mode_set(mode='EDIT')

ebs = arm_data.edit_bones

# Create bones in the EXACT MEGATRON 39 order
for bname in MEGATRON_39_BONES:
    p = bone_unity_pos[bname]
    eb = ebs.new(bname)
    eb.head = p
    if "Toe" in bname:
        eb.tail = p + Vector((0, 0, 0.2))
    elif "Thumb" in bname:
        eb.tail = p + Vector((0, 0, 0.15))
    elif "Finger" in bname or "Index" in bname or "Middle" in bname or "Ring" in bname or "Pinky" in bname:
        eb.tail = p + Vector((0, -0.15, 0))
    elif "Leg" in bname or "Foot" in bname:
        eb.tail = p + Vector((0, -0.3, 0))
    elif "Arm" in bname or "Hand" in bname:
        eb.tail = p + Vector((0, -0.3, 0))
    else:
        eb.tail = p + Vector((0, 0.3, 0))

# Wire parent-child relationships
for bname in MEGATRON_39_BONES:
    par_name = bone_parent_map.get(bname)
    if par_name and par_name in ebs:
        ebs[bname].parent = ebs[par_name]
        ebs[bname].use_connect = False

bpy.ops.object.mode_set(mode='OBJECT')

# Re-create vertex groups in the exact 39-bone order
robot.vertex_groups.clear()
new_vgs = {bname: robot.vertex_groups.new(name=bname) for bname in MEGATRON_39_BONES}

for v_idx, wdict in enumerate(v_weights_saved):
    for bname, w in wdict.items():
        if bname in new_vgs and w > 0.001:
            new_vgs[bname].add([v_idx], w, 'REPLACE')

robot.parent = arm_obj
mod = robot.modifiers.new("Armature", "ARMATURE")
mod.object = arm_obj

# Consolidate to exactly 1 material so Unity builds exactly 1 Submesh covering 100% of the mesh
robot.data.materials.clear()
mat_robot = bpy.data.materials.new(name="cha_brawl_main")
robot.data.materials.append(mat_robot)
for poly in robot.data.polygons:
    poly.material_index = 0


# Export FBX
bpy.ops.object.select_all(action='DESELECT')
robot.select_set(True)
arm_obj.select_set(True)
bpy.context.view_layer.objects.active = arm_obj

for out_fbx in (FBX_EXPORT_DIR / "brawl_robot.fbx", UNITY_BRAWL_DIR / "brawl_robot.fbx"):
    bpy.ops.export_scene.fbx(
        filepath=str(out_fbx),
        use_selection=True,
        object_types={'ARMATURE', 'MESH'},
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='Z',
        axis_up='Y',
        add_leaf_bones=False,
        bake_anim=False
    )
print(f"[✓] Exported Rigged Robot FBX (39 bones in exact Megatron order): {UNITY_BRAWL_DIR / 'brawl_robot.fbx'}")


# -------------------------------------------------------------------------
# 2. RIG TANK MESH
# -------------------------------------------------------------------------
bpy.ops.wm.open_mainfile(filepath=str(WORKING_DIR / "brawl_tank_aligned.blend"))
tank = bpy.data.objects.get("VH_BrawlCINE_SKEL.001.dmx") or bpy.data.objects.get("cha_brawl_gs_01")
tank.name = "cha_brawl_gs_01"

for o in list(bpy.data.objects):
    if o.type == 'ARMATURE':
        bpy.data.objects.remove(o, do_unlink=True)

t_arm_data = bpy.data.armatures.new("ARM_Brawl_Tank_Data")
t_arm_obj = bpy.data.objects.new("ARM_Brawl_Tank", t_arm_data)
bpy.context.scene.collection.objects.link(t_arm_obj)
bpy.context.view_layer.objects.active = t_arm_obj
bpy.ops.object.mode_set(mode='EDIT')

t_ebs = t_arm_data.edit_bones
cog_eb = t_ebs.new("Reference/COG")
cog_eb.head = Vector((0, 0, 0))
cog_eb.tail = Vector((0, 0, 1.0))

bpy.ops.object.mode_set(mode='OBJECT')

tank.vertex_groups.clear()
vg = tank.vertex_groups.new(name="Reference/COG")
vg.add(list(range(len(tank.data.vertices))), 1.0, 'REPLACE')

tank.parent = t_arm_obj
t_mod = tank.modifiers.new("Armature", "ARMATURE")
t_mod.object = t_arm_obj

# Consolidate to exactly 1 material so Unity builds exactly 1 Submesh covering 100% of the mesh
tank.data.materials.clear()
mat_tank = bpy.data.materials.new(name="cha_brawl_tank")
tank.data.materials.append(mat_tank)
for poly in tank.data.polygons:
    poly.material_index = 0


bpy.ops.object.select_all(action='DESELECT')
tank.select_set(True)
t_arm_obj.select_set(True)
bpy.context.view_layer.objects.active = t_arm_obj

for out_fbx in (FBX_EXPORT_DIR / "brawl_tank.fbx", UNITY_BRAWL_DIR / "brawl_tank.fbx"):
    bpy.ops.export_scene.fbx(
        filepath=str(out_fbx),
        use_selection=True,
        object_types={'ARMATURE', 'MESH'},
        apply_scale_options='FBX_SCALE_ALL',
        axis_forward='Z',
        axis_up='Y',
        add_leaf_bones=False,
        bake_anim=False
    )
print(f"[✓] Exported Rigged Tank FBX (1 bone): {UNITY_BRAWL_DIR / 'brawl_tank.fbx'}")
