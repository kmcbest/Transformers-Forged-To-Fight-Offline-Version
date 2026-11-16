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

# Build map from any bone to its closest ancestor bip bone (or itself)
bip_bones = set([
    'bip_pelvis', 'bip_spine_0', 'bip_spine_1', 'bip_neck', 'bip_head', 'bip_Jaw',
    'bip_collar_L', 'bip_upperArm_L', 'bip_lowerArm_L', 'bip_hand_L',
    'bip_thumb_0_L', 'bip_thumb_1_L', 'bip_index_0_L', 'bip_index_1_L', 'bip_middle_0_L', 'bip_middle_1_L', 'bip_ring_0_L', 'bip_ring_1_L', 'bip_pinky_0_L', 'bip_pinky_1_L',
    'bip_collar_R', 'bip_upperArm_R', 'bip_lowerArm_R', 'bip_hand_R',
    'bip_thumb_0_R', 'bip_thumb_1_R', 'bip_index_0_R', 'bip_index_1_R', 'bip_middle_0_R', 'bip_middle_1_R', 'bip_ring_0_R', 'bip_ring_1_R', 'bip_pinky_0_R', 'bip_pinky_1_R',
    'bip_hip_L', 'bip_knee_L', 'bip_foot_L', 'bip_toe_L',
    'bip_hip_R', 'bip_knee_R', 'bip_foot_R', 'bip_toe_R'
])

def find_bip_ancestor(b):
    curr = b
    while curr:
        if curr.name in bip_bones:
            return curr.name
        curr = curr.parent
    return 'bip_spine_1' # fallback

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

print("Checking mesh vertex groups and ancestor mapping:")
unmapped = set()
for name in brawl_mesh_names:
    obj = bpy.data.objects.get(name)
    if not obj:
        print(f"Missing {name}")
        continue
    for vg in obj.vertex_groups:
        b = armature.data.bones.get(vg.name)
        if b:
            ancestor = find_bip_ancestor(b)
        else:
            ancestor = 'bip_spine_1'
            unmapped.add(vg.name)
        # print(f"  {name} -> {vg.name} maps to {ancestor}")

print("Unmapped bone names in armature:", unmapped)
print("Finished check successfully.")
