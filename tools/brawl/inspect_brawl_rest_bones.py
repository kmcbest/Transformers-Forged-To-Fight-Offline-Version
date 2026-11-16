import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)

fbx_path = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

armature = bpy.data.objects.get("brawl_ARM")

key_bones = [
    'bip_pelvis', 'bip_spine_0', 'bip_spine_1', 'bip_neck', 'bip_head',
    'bip_collar_L', 'bip_upperArm_L', 'bip_lowerArm_L', 'bip_hand_L',
    'bip_collar_R', 'bip_upperArm_R', 'bip_lowerArm_R', 'bip_hand_R',
    'bip_hip_L', 'bip_knee_L', 'bip_foot_L', 'bip_toe_L',
    'bip_hip_R', 'bip_knee_R', 'bip_foot_R', 'bip_toe_R'
]

print("--- BRAWL_ARM REST POSE BONE HEAD POSITIONS (Blender space) ---")
for bname in key_bones:
    b = armature.data.bones.get(bname)
    if b:
        # In Blender: +X is right, +Y is forward, +Z is up (or depending on FBX import)
        head = b.head_local
        print(f"{bname:<16}: ({head.x:8.4f}, {head.y:8.4f}, {head.z:8.4f})")

print("\n--- BRAWL ROBOT MESHES BOUNDS ---")
brawl_mesh_names = [
    'RB_Brawl_CHARSKEL_Head.mo.dmx',
    'RB_Brawl_CHARSKEL_Chest.mo.dmx',
    'RB_Brawl_CHARSKEL_CapL.mo.dmx',
    'RB_Brawl_CHARSKEL_CapR.mo.dmx',
    'RB_Brawl_CHARSKEL_ArmLoL.mo.dmx',
    'RB_Brawl_CHARSKEL_ArmLoR.mo.dmx',
    'RB_Brawl_CHARSKEL_Legs.mo.dmx',
    'BrawlCannon_STAT.mo.dmx',
    'BrawlCannon_STAT.mo.001.dmx'
]
min_v = [1e9, 1e9, 1e9]
max_v = [-1e9, -1e9, -1e9]
for name in brawl_mesh_names:
    obj = bpy.data.objects.get(name)
    if obj:
        for v in obj.data.vertices:
            co = obj.matrix_world @ v.co
            for i in range(3):
                min_v[i] = min(min_v[i], co[i])
                max_v[i] = max(max_v[i], co[i])

print(f"Overall Robot Bounds:")
print(f"  X: [{min_v[0]:.4f}, {max_v[0]:.4f}] (span={max_v[0]-min_v[0]:.4f})")
print(f"  Y: [{min_v[1]:.4f}, {max_v[1]:.4f}] (span={max_v[1]-min_v[1]:.4f})")
print(f"  Z: [{min_v[2]:.4f}, {max_v[2]:.4f}] (span={max_v[2]-min_v[2]:.4f})")
