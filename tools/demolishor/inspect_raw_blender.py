# -*- coding: utf-8 -*-
import sys
import json
import math
from pathlib import Path
import bpy
import mathutils

sys.stdout.reconfigure(encoding='utf-8')

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)

# 1. Load Ironhide bone data
with open("tools/demolishor/ironhide_80_bones.json", "r", encoding="utf-8") as f:
    bones_data = json.load(f)

# In Ironhide: Unity coords: X=Right, Y=Up, Z=Forward
# If we keep Unity coords directly in Blender (or with Y-up / Z-up):
print("Ironhide bone positions in Unity space:")
for b in ['Hips', 'Head', 'LeftArm', 'RightArm', 'LeftFoot', 'RightFoot']:
    m = bones_data['bones'][b]['matrix']
    print(f"  {b:12s}: Unity (X={m[0][3]:6.2f}, Y={m[1][3]:6.2f}, Z={m[2][3]:6.2f})")

# 2. Load Demolishor FBX
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

demo_mesh = bpy.data.objects.get("RB_DemolishorWeaponArm_SKEL.mo.dmx")
demo_arm = bpy.data.objects.get("Demolishor_ARM")

print(f"\nDemolishor raw mesh bbox in Blender:")
for i, corner in enumerate(demo_mesh.bound_box):
    print(f"  corner {i}: ({corner[0]:.2f}, {corner[1]:.2f}, {corner[2]:.2f})")

print(f"\nDemolishor raw Armature bones (sample):")
for b in demo_arm.data.bones:
    if any(k in b.name for k in ['Hips', 'Head', 'Clav', 'Shoulder', 'Hand', 'Thigh', 'Foot']):
        head = b.head_local
        print(f"  {b.name:30s}: head=({head[0]:6.2f}, {head[1]:6.2f}, {head[2]:6.2f})")
