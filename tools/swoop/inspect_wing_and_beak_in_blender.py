import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

print("=== Parent Hierarchy of Wing & Bird Head Bones ===")
for bn in ["Back", "Bone_L_Wing_01(mirrored)", "Bone_L_Wing_02(mirrored)", "Bone_R_Wing_01", "Bone_R_Wing_02",
           "bird_chest", "bird_neck", "bird_Head", "bird_Head_02", "beak", "beak_the bottom", "Bone_Head", "Bone_Spine1"]:
    b = arm.data.bones.get(bn)
    if b:
        chain = []
        cur = b
        while cur:
            chain.append(cur.name)
            cur = cur.parent
        print(f"  {bn:26s}: {' -> '.join(chain)}")
