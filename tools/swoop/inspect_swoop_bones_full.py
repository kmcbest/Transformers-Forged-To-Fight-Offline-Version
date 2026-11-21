import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import bpy
from mathutils import Vector

ROOT = Path("e:/Agent/TFTF-blender")
BP_JSON = ROOT / "tools/swoop/ramjet_78_authoritative_bindposes.json"
FBX_SRC = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

with open(BP_JSON, "r", encoding="utf-8") as f:
    ramjet_data = json.load(f)["bones"]

print("=== 1. Ramjet 78 Donor Key Bone World Positions (Blender Coords: +X=Left, -Y=Fwd, +Z=Up) ===")
key_r = [
    "Hips", "Spine", "Spine1", "Neck", "Head",
    "LeftShoulder", "LeftShoulderPad", "LeftArm", "LeftArmRoll", "LeftForeArm", "LeftHand",
    "LeftUpLeg", "LeftLeg", "LeftFoot", "LeftToeBase", "LeftToe",
]
for b in key_r:
    ux, uy, uz = ramjet_data[b]["unity_world_pos"]
    print(f"  {b:16s}: X={-ux:+7.3f}, Y={-uz:+7.3f}, Z={uy:+7.3f} (parent={ramjet_data[b]['parent']})")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))
mesh = bpy.data.objects.get("Swoop.001")
arm = bpy.data.objects.get("Bip001")

vs = [v.co for v in mesh.data.vertices]
min_z = min(v.z for v in vs)
max_z = max(v.z for v in vs)
raw_h = max_z - min_z

# Also check head bone vs crest tip height
head_vg = mesh.vertex_groups.get("Bone_Head")
if not head_vg:
    head_vg = mesh.vertex_groups.get("Bip001 Head")
# Find eye/face vertices vs crest vertices
print(f"\n=== 2. Swoop Raw Static Pose Vertices ===")
print(f"  min_z={min_z:.4f}, max_z={max_z:.4f}, raw_h={raw_h:.4f}")
for vgn in ["Bip001 Head", "Bone_Head", "Bone_L_UpperArm", "Bone_L_Forearm", "Bone_L_Hand", "Bone_Pelvis", "Bone_L_Thigh", "Bone_L_Calf", "Bone_L_Foot00"]:
    vg = mesh.vertex_groups.get(vgn)
    if vg:
        pts = [v.co for v in mesh.data.vertices if any(g.group == vg.index and g.weight > 0.4 for g in v.groups)]
        if pts:
            print(f"  {vgn:18s}: n={len(pts):4d}, raw_X=[{min(p.x for p in pts):+.3f},{max(p.x for p in pts):+.3f}], raw_Z=[{min(p.z for p in pts):+.3f},{max(p.z for p in pts):+.3f}]")

# Check arm bone heads in Swoop raw space (from mesh skinning vs armature)
print("\n=== 3. Swoop Bip001 Bone Heads in World Space vs Local Bone Matrix ===")
# Put mesh world transform to identity to see where armature bones map
mat_inv = mesh.matrix_world.inverted()
for bname in ["Bip001 Pelvis", "Bip001 Spine", "Bip001 Spine1", "Bip001 Neck", "Bip001 Head",
              "Bip001 L Clavicle", "Bone_L_Clavicle01", "Bone_L_Clavicle02", "Bip001 L UpperArm", "Bip001 L Forearm", "Bip001 L Hand",
              "Bip001 L Thigh", "Bip001 L Calf", "Bip001 L Foot", "Bip001 L Toe0"]:
    b = arm.data.bones.get(bname)
    if b:
        # Bone head in mesh local space
        p = mat_inv @ (arm.matrix_world @ b.head_local)
        print(f"  {bname:20s}: mesh_local=({p.x:+.4f}, {p.y:+.4f}, {p.z:+.4f}) (grounded Z={p.z - min_z:.4f})")

print("\n=== 4. Inspect Vehicle Actions & Wing/Beak Bones ===")
veh_acts = [a.name for a in bpy.data.actions if "vehicle_idle01" in a.name]
print(f"  Actions containing 'vehicle_idle01': {len(veh_acts)}")
for an in veh_acts:
    print(f"    {an}")

print("\n=== 5. Check Objects & Wing/Beak Bone Transforms in vehicle_idle01 Frame 1 ===")
act = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
arm.animation_data.action = act
bpy.context.scene.frame_set(1)
bpy.context.view_layer.update()
for bname in ["Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "Bone_R_Wing_01", "Bone_R_Wing_02", "beak", "beak_the bottom", "bird_Head", "bird_Head_02"]:
    pb = arm.pose.bones.get(bname)
    if pb:
        wpos = arm.matrix_world @ pb.head
        print(f"  {bname:26s}: parent={pb.parent.name if pb.parent else None:26s}, world_head=({wpos.x:+.4f}, {wpos.y:+.4f}, {wpos.z:+.4f}), pb_loc={tuple(round(x,4) for x in pb.location)}")
