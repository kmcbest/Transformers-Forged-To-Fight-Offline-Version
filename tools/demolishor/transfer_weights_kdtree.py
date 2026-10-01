import bpy
import json
import mathutils
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_FILE = ROOT / "tools" / "demolishor" / "demolishor_ironhide_side_by_side.blend"
PHASE1_FILE = ROOT / "tools" / "demolishor" / "demolishor_phase1.blend"
JSON_FILE = ROOT / "tools" / "demolishor" / "ironhide_unity_verts_skin.json"

print("=== Transferring Official Weights via KD-Tree ===")
bpy.ops.wm.open_mainfile(filepath=str(BLEND_FILE))

# Reload clean Ironhide mesh from phase 1 to avoid any previous corrupted groups
with bpy.data.libraries.load(str(PHASE1_FILE), link=False) as (data_from, data_to):
    if "Ironhide_Ghost_Reference" in data_from.objects:
        data_to.objects = ["Ironhide_Ghost_Reference"]

clean_iron = bpy.data.objects.get("Ironhide_Ghost_Reference")
old_iron = bpy.data.objects.get("Ironhide_Mesh")

# Replace old mesh data with clean mesh data
old_iron.data = clean_iron.data.copy()
bpy.data.objects.remove(clean_iron, do_unlink=True)
print(f"Re-initialized Ironhide_Mesh with clean geometry ({len(old_iron.data.vertices)} verts).")

iron_mesh = old_iron
iron_arm = bpy.data.objects.get("Ironhide_Armature")
iron_mesh.parent = iron_arm
iron_mesh.matrix_parent_inverse = mathutils.Matrix.Identity(4)
iron_mesh.location = (0.0, 0.0, 0.0)

# Load Unity verts and skin weights
with open(JSON_FILE, "r") as f:
    u_data = json.load(f)
u_verts = u_data["verts"]

# Build KD-tree
kd = mathutils.kdtree.KDTree(len(u_verts))
for i, v in enumerate(u_verts):
    kd.insert((v["x"], v["z"], v["y"]), i)
kd.balance()

# Clear vertex groups on Ironhide
iron_mesh.vertex_groups.clear()

# Find all bone names present in Unity skin
all_bone_names = set()
for v in u_verts:
    for b in v["b"]:
        all_bone_names.add(b)

vg_map = {}
for bname in sorted(all_bone_names):
    vg_map[bname] = iron_mesh.vertex_groups.new(name=bname)

print(f"Created {len(vg_map)} vertex groups on Ironhide.")

# Assign weights via KD-tree nearest neighbor
for v in iron_mesh.data.vertices:
    co, u_idx, dist = kd.find(v.co)
    u_v = u_verts[u_idx]
    for b, w in zip(u_v["b"], u_v["w"]):
        if w > 0.001 and b in vg_map:
            vg_map[b].add([v.index], w, 'REPLACE')

print("[✓] Transferred official Kabam weights to all Ironhide vertices via KD-tree!")

# Ensure Armature modifier exists on Ironhide
arm_mod = None
for m in iron_mesh.modifiers:
    if m.type == 'ARMATURE':
        arm_mod = m
        break
if not arm_mod:
    arm_mod = iron_mesh.modifiers.new(name="Armature", type='ARMATURE')
arm_mod.object = iron_arm

# Material for Ironhide
iron_mat = bpy.data.materials.get("Ironhide_Armor_Mat")
if iron_mat and not iron_mesh.data.materials:
    iron_mesh.data.materials.append(iron_mat)

# 2. Restore Demolishor Finger Weights
print("\n--- Restoring Demolishor Finger Weights ---")
demo_mesh = bpy.data.objects.get("Demolishor_Mesh")
with bpy.data.libraries.load(str(PHASE1_FILE), link=False) as (data_from, data_to):
    if "RB_DemolishorWeaponArm_SKEL.mo.dmx" in data_from.objects:
        data_to.objects = ["RB_DemolishorWeaponArm_SKEL.mo.dmx"]

p1_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
FINGER_MAP = {
    "R_Finger01_Thumb01_XL2": "RightHandThumb1",
    "R_Finger01_Thumb02_XL2": "RightHandThumb2",
    "R_Finger02_Index01_XL2": "RightHandIndex1",
    "R_Finger02_Index02_XL2": "RightHandIndex2",
    "R_Finger03_Middle01_XL2": "RightHandMiddle1",
    "R_Finger03_Middle02_XL2": "RightHandMiddle2",
    "R_Finger04_Ring01_XL2": "RightHandRing1",
    "R_Finger04_Ring02_XL2": "RightHandRing2",
    "R_Finger05_Pinky01_XL2": "RightHandPinky1",
    "R_Finger05_Pinky02_XL2": "RightHandPinky2",
    "L_Finger01_Thumb01_XL2": "LeftHandThumb1",
    "L_Finger01_Thumb02_XL2": "LeftHandThumb2",
    "L_Finger02_Index01_XL2": "LeftHandIndex1",
    "L_Finger02_Index02_XL2": "LeftHandIndex2",
    "L_Finger03_Middle01_XL2": "LeftHandMiddle1",
    "L_Finger03_Middle02_XL2": "LeftHandMiddle2",
    "L_Finger04_Ring01_XL2": "LeftHandRing1",
    "L_Finger04_Ring02_XL2": "LeftHandRing2",
    "L_Finger05_Pinky01_XL2": "LeftHandPinky1",
    "L_Finger05_Pinky02_XL2": "LeftHandPinky2",
}

demo_vg_map = {}
for target_bone in FINGER_MAP.values():
    demo_vg_map[target_bone] = demo_mesh.vertex_groups.get(target_bone) or demo_mesh.vertex_groups.new(name=target_bone)

vg_rhand = demo_mesh.vertex_groups.get("RightHand")
vg_lhand = demo_mesh.vertex_groups.get("LeftHand")

reassigned = 0
for src_name, tgt_name in FINGER_MAP.items():
    src_vg = p1_mesh.vertex_groups.get(src_name)
    if not src_vg:
        continue
    tgt_vg = demo_vg_map[tgt_name]
    hand_vg = vg_rhand if tgt_name.startswith("Right") else vg_lhand
    for v in p1_mesh.data.vertices:
        for g in v.groups:
            if g.group == src_vg.index and g.weight > 0.05:
                w = g.weight
                tgt_vg.add([v.index], w, 'REPLACE')
                if hand_vg:
                    hand_vg.remove([v.index])
                reassigned += 1

print(f"[✓] Reassigned {reassigned} Demolishor finger weights!")
bpy.data.objects.remove(p1_mesh, do_unlink=True)

# Save blend file
bpy.ops.wm.save_as_mainfile(filepath=str(BLEND_FILE))
print(f"[✓] Saved updated blend file to: {BLEND_FILE}")
