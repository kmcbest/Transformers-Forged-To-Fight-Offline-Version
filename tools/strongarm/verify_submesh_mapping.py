import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\RID_game\strongarm_zip_extracted\source\Strongarm.fbx")

# Mapping rules
def get_bone_for_submesh(name):
    lower = name.lower()
    if name in ["bot:mask_geo", "bot:faceMaskOn_jaw_geo"]:
        return None # deleted
    
    # Head parts
    if any(k in lower for k in ["face", "helmet", "crown", "eye", "neck"]):
        return "Head"
    
    # Left Arm hierarchy
    if "_l" in lower or lower.endswith("_l"):
        if "palm" in lower or "finger" in lower:
            return "LeftHand"
        if any(k in lower for k in ["hand", "arm_geo", "elbow_geo", "elbowjointb", "toplight"]):
            return "LeftForeArm"
        if any(k in lower for k in ["shoulderinner", "shoulderrim", "shouldertire", "wheeldeco", "fender", "elbowjointa"]):
            return "LeftArm"
        if any(k in lower for k in ["shoulderball", "shoulderjoint", "door", "holder", "window"]):
            return "LeftShoulder"
        if any(k in lower for k in ["upperleg", "pocketb"]):
            return "LeftUpLeg"
        if any(k in lower for k in ["leg_geo", "knee", "legjointb", "legtire", "legwheeldeco", "legfender"]):
            return "LeftLeg"
        if any(k in lower for k in ["shoes", "shoedeco"]):
            return "LeftToeBase"

    # Right Arm hierarchy
    if "_r" in lower or lower.endswith("_r"):
        if "palm" in lower or "finger" in lower:
            return "RightHand"
        if any(k in lower for k in ["hand", "arm_geo", "elbow_geo", "elbowjointb", "toplight"]):
            return "RightForeArm"
        if any(k in lower for k in ["shoulderinner", "shoulderrim", "shouldertire", "wheeldeco", "fender", "elbowjointa"]):
            return "RightArm"
        if any(k in lower for k in ["shoulderball", "shoulderjoint", "door", "holder", "window"]):
            return "RightShoulder"
        if any(k in lower for k in ["upperleg", "pocketb", "gun", "trigger", "lightb", "lightc"]):
            return "RightUpLeg"
        if any(k in lower for k in ["leg_geo", "knee", "legjointb", "legtire", "legwheeldeco", "legfender"]):
            return "RightLeg"
        if any(k in lower for k in ["shoes", "shoedeco"]):
            return "RightToeBase"

    # Torso parts
    if any(k in lower for k in ["collar", "chest", "boster", "ribcage", "autobotlogo", "bodyupper"]):
        return "Spine1"
    if "body_geo" in lower:
        return "Spine"
    if any(k in lower for k in ["waist", "belt", "pocketa", "pocketc"]):
        return "Hips"

    return "Spine1" # fallback

meshes = [o for o in bpy.data.objects if o.type == 'MESH']
unmapped = []
mapped_summary = {}

for m in meshes:
    target = get_bone_for_submesh(m.name)
    if target:
        mapped_summary[target] = mapped_summary.get(target, 0) + len(m.data.vertices)
    elif target is None and m.name not in ["bot:mask_geo", "bot:faceMaskOn_jaw_geo"]:
        unmapped.append(m.name)

print("Submesh mapping summary:")
for bname, vert_count in sorted(mapped_summary.items()):
    print(f"  {bname:20s}: {vert_count:5d} vertices")

print(f"\nUnmapped meshes: {len(unmapped)}")
if unmapped:
    print(f"  {unmapped}")
