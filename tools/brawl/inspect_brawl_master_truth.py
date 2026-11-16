import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import json
from pathlib import Path
from mathutils import Vector

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
donor_json = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Brawl\00_donor_reference\donor_summary.json")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)

print("=== ALL BRAWL / TANK / WEP OBJECTS IN COMBATICONS FBX ===")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    n = o.name.lower()
    if "brawl" in n or "wep_" in n or "cannon" in n:
        mats = [m.name if m else "None" for m in getattr(o.data, "materials", [])] if o.type == 'MESH' else []
        par = o.parent.name if o.parent else "None"
        print(f"  [{o.type:8s}] {o.name:38s} par={par:18s} mats={mats}")

arm = bpy.data.objects.get("brawl_ARM")
scene_y = arm.matrix_world.translation.y
print(f"\nbrawl_ARM world loc: {arm.matrix_world.translation}, rot_euler: {arm.matrix_world.to_euler()}")

print("\n=== BRAWL RAW BONE WORLD POSITIONS (relative to arm Y) ===")
key_bones = [
    "bip_pelvis", "bip_spine_0", "bip_spine_1", "bip_neck", "bip_head", "bip_Jaw",
    "bip_collar_L", "bip_upperArm_L", "bip_lowerArm_L", "bip_hand_L",
    "bip_thumb_0_L", "bip_thumb_1_L", "bip_thumb_1_L_end",
    "bip_index_0_L", "bip_index_1_L", "bip_index_1_L_end",
    "bip_middle_0_L", "bip_middle_1_L", "bip_middle_1_L_end",
    "bip_collar_R", "bip_upperArm_R", "bip_lowerArm_R", "bip_hand_R",
    "bip_hip_L", "bip_knee_L", "bip_foot_L", "bip_toe_L", "bip_toe_L_end",
    "bip_hip_R", "bip_knee_R", "bip_foot_R", "bip_toe_R", "bip_toe_R_end",
]
for bname in key_bones:
    b = arm.data.bones.get(bname)
    if b:
        w = arm.matrix_world @ b.head_local
        print(f"  {bname:20s}: raw=({w.x:7.4f}, {w.y - scene_y:7.4f}, {w.z:7.4f})")

# Check forward direction: compare heel vs toe X
foot_l = arm.matrix_world @ arm.data.bones["bip_foot_L"].head_local
toe_l = arm.matrix_world @ arm.data.bones["bip_toe_L"].head_local
jaw = arm.matrix_world @ arm.data.bones["bip_Jaw"].head_local if "bip_Jaw" in arm.data.bones else None
head = arm.matrix_world @ arm.data.bones["bip_head"].head_local
print(f"\nDirection check:")
print(f"  foot_L.x={foot_l.x:.4f}, toe_L.x={toe_l.x:.4f} -> foot-to-toe dX = {toe_l.x - foot_l.x:.4f}")
print(f"  collar_L relY={ (arm.matrix_world @ arm.data.bones['bip_collar_L'].head_local).y - scene_y :.4f}")
print(f"  collar_R relY={ (arm.matrix_world @ arm.data.bones['bip_collar_R'].head_local).y - scene_y :.4f}")
if jaw:
    print(f"  head.x={head.x:.4f}, jaw.x={jaw.x:.4f}")

# Check UV bounds & material slot counts on Brawl robot meshes & tank mesh
print("\n=== BRAWL MESH UV BOUNDS & MATERIAL SLOTS ===")
for o in bpy.data.objects:
    if o.type == 'MESH' and ("brawl" in o.name.lower()):
        uvs = o.data.uv_layers.active
        if uvs:
            us = [d.uv.x for d in uvs.data]
            vs = [d.uv.y for d in uvs.data]
            u_rng = f"[{min(us):.3f}, {max(us):.3f}]"
            v_rng = f"[{min(vs):.3f}, {max(vs):.3f}]"
        else:
            u_rng = v_rng = "NO UV"
        # Check empty vertex groups
        zero_w = 0
        for v in o.data.vertices:
            if sum(g.weight for g in v.groups) < 1e-5:
                zero_w += 1
        ms = [s.material.name if s.material else "None" for s in o.material_slots]
        print(f"  {o.name:35s} verts={len(o.data.vertices):5d} zeroW={zero_w:4d} U={u_rng} V={v_rng} mats={ms}")
