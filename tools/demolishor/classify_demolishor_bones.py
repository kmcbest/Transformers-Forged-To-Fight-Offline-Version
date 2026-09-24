# -*- coding: utf-8 -*-
import bpy
import sys

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"d:\Agent\tftf\3rd-party-models\transformers-fall-of-cybertron-demolishor\source\transformers fall of cybertron Demolishor.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Demolishor_ARM")
print(f"Demolishor Armature: {arm.name}, total bones: {len(arm.data.bones)}")

# Group bones by main categories
categories = {
    "Spine / Hips / Head": [],
    "Left Arm": [],
    "Right Arm": [],
    "Left Leg": [],
    "Right Leg": [],
    "Other / Treads / Extra": []
}

for b in arm.data.bones:
    name = b.name
    lower = name.lower()
    if any(k in lower for k in ["hip", "pelvis", "lumbar", "spine", "chest", "torso", "neck", "head", "face", "jaw"]):
        categories["Spine / Hips / Head"].append(name)
    elif name.startswith("L_") and any(k in lower for k in ["shoulder", "arm", "elbow", "forearm", "hand", "finger", "wrist"]):
        categories["Left Arm"].append(name)
    elif name.startswith("R_") and any(k in lower for k in ["shoulder", "arm", "elbow", "forearm", "hand", "finger", "wrist"]):
        categories["Right Arm"].append(name)
    elif name.startswith("L_") and any(k in lower for k in ["leg", "thigh", "knee", "calf", "foot", "toe", "ankle"]):
        categories["Left Leg"].append(name)
    elif name.startswith("R_") and any(k in lower for k in ["leg", "thigh", "knee", "calf", "foot", "toe", "ankle"]):
        categories["Right Leg"].append(name)
    else:
        categories["Other / Treads / Extra"].append(name)

for cat, bones in categories.items():
    print(f"\n--- {cat} ({len(bones)}) ---")
    for b in bones[:15]:
        print(" ", b)
    if len(bones) > 15:
        print(f"  ... and {len(bones)-15} more")
