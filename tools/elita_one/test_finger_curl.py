import bpy
import math
import mathutils
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
FBX_PATH = ROOT / "3rd-party-models" / "transformers-galatic-trials-elita-one" / "source" / "Elita_One.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = bpy.data.objects.get("SK_CH_11")
mesh = bpy.data.objects.get("SK_CH_11.001")

# Check bone axes for fingers
for bname in ["l_index_01_skin", "l_middle_01_skin", "l_thumb_01_skin"]:
    b = arm.data.bones.get(bname)
    print(f"Bone {bname}: head={b.head_local}, tail={b.tail_local}")

# Let's test rotating finger joints in POSE mode
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='POSE')

# In local bone space, what axis curls the fingers?
# A standard finger curls around local X or local Z:
for f_base in ["l_index", "l_middle", "l_ring", "l_pinky", "r_index", "r_middle", "r_ring", "r_pinky"]:
    for seg in ["01", "02", "03"]:
        bname = f"{f_base}_{seg}_skin"
        pb = arm.pose.bones.get(bname)
        if pb:
            # Let's check rotation modes
            print(f"PB {bname} rot mode: {pb.rotation_mode}")
