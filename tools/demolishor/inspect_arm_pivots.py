# -*- coding: utf-8 -*-
import sys
import bpy
import mathutils
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent.parent
BLEND_PATH = ROOT / "tools" / "demolishor" / "demolishor_phase1.blend"

bpy.ops.wm.open_mainfile(filepath=str(BLEND_PATH))

arm_obj = bpy.data.objects.get("Ironhide_Reference_Armature")
mesh_obj = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")

print("=== Ironhide Key Bone Positions (World) ===")
key_bones = [
    "L_shoulder_cin", "L_forearm_cin", "L_hand_cin",
    "R_shoulder_cin", "R_forearm_cin", "R_hand_cin",
    "L_thigh_cin", "L_foot_cin",
    "R_thigh_cin", "R_foot_cin"
]
for name in key_bones:
    b = arm_obj.pose.bones.get(name) or arm_obj.data.bones.get(name)
    if b:
        head_world = arm_obj.matrix_world @ b.head
        tail_world = arm_obj.matrix_world @ b.tail
        print(f"  {name:18s}: Head={head_world}, Tail={tail_world}")

print("\n=== Demolishor Arm Vertex Groups & Centroids ===")
for vg in mesh_obj.vertex_groups:
    if any(k in vg.name for k in ["L_Arm", "R_Arm", "L_Leg", "R_Leg"]):
        pts = [v.co for v in mesh_obj.data.vertices if any(g.group == vg.index and g.weight > 0.3 for g in v.groups)]
        if pts:
            c = mesh_obj.matrix_world @ (sum(pts, mathutils.Vector()) / len(pts))
            print(f"  {vg.name:24s} ({len(pts):4d} verts): Centroid={c}")
