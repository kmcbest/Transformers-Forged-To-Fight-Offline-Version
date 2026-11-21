import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
best_frame = None
best_score = -999

for act in bpy.data.actions:
    if not act.name.startswith("Bip001|") or "vehicle" in act.name:
        continue
    arm.animation_data.action = act
    start, end = int(act.frame_range[0]), int(act.frame_range[1])
    for f in range(start, end + 1):
        bpy.context.scene.frame_set(f)
        bpy.context.view_layer.update()
        pb_lh = arm.pose.bones.get("Bone_L_Hand")
        pb_rh = arm.pose.bones.get("Bone_R_Hand")
        w_lh = (arm.matrix_world @ pb_lh.head).x * 340.16
        w_rh = (arm.matrix_world @ pb_rh.head).x * 340.16
        # We want w_lh > 1.0 and w_rh < -1.0, and w_lh - w_rh large
        if w_lh > 0.8 and w_rh < -0.8:
            score = (w_lh - (-w_rh)) # symmetry and width
            print(f"Candidate: {act.name} frame {f:2d}: L_Hand_X={w_lh:+.2f}m, R_Hand_X={w_rh:+.2f}m")
