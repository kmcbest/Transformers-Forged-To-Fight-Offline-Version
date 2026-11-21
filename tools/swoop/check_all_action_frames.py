import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from mathutils import Vector, Matrix
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FBX_PATH = ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = bpy.data.objects.get("Bip001")
swoop_mesh = bpy.data.objects.get("Swoop.001")

# Check all actions on Bip001 and sample their first and last frames
for act in bpy.data.actions:
    if not act.name.startswith("Bip001|"):
        continue
    act_name = act.name.split("|")[1]
    
    arm.animation_data.action = act
    bpy.context.scene.frame_set(int(act.frame_range[0]))
    bpy.context.view_layer.update()
    
    # Check Left Hand pos at start
    lh = arm.pose.bones.get("Bone_L_Hand") or arm.pose.bones.get("Bip001 L Hand")
    f0_pos = lh.matrix.translation.copy() if lh else Vector()
    
    bpy.context.scene.frame_set(int(act.frame_range[1]))
    bpy.context.view_layer.update()
    f1_pos = lh.matrix.translation.copy() if lh else Vector()
    
    print(f"Action: {act_name:<20} frames={act.frame_range[0]:.0f}..{act.frame_range[1]:.0f}  LH_start={f0_pos.z:.3f} LH_end={f1_pos.z:.3f}")
