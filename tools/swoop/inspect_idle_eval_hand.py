import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

FBX_SRC = Path("e:/Agent/TFTF-blender/3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_SRC))

arm = bpy.data.objects.get("Bip001")
mesh = bpy.data.objects.get("Swoop.001")

# Apply idle01 action to arm
act = bpy.data.actions.get("Bip001|idle01|Base Layer")
arm.animation_data_create()
arm.animation_data.action = act
bpy.context.scene.frame_set(0)

# Evaluate armature modifier
depsgraph = bpy.context.evaluated_depsgraph_get()
eval_mesh = mesh.evaluated_get(depsgraph)

# Let's inspect the bounding box of the hand verts under idle01
def eval_hand_bounds(prefix):
    vg_names = [f"Bone_{prefix}_Hand"] + [f"Bone_{prefix}_Finger{i}" for i in ["0", "01", "02", "1", "11", "12", "2", "21", "22"]]
    vg_indices = {mesh.vertex_groups[name].index for name in vg_names if name in mesh.vertex_groups}
    pts = [eval_mesh.matrix_world @ v.co for v in eval_mesh.data.vertices if any(g.group in vg_indices and g.weight > 0.4 for g in v.groups)]
    print(f"Eval Hand {prefix} (idle01): count={len(pts)}")
    print(f"  X: [{min(p.x for p in pts):.3f}, {max(p.x for p in pts):.3f}] (size: {max(p.x for p in pts)-min(p.x for p in pts):.3f})")
    print(f"  Y: [{min(p.y for p in pts):.3f}, {max(p.y for p in pts):.3f}] (size: {max(p.y for p in pts)-min(p.y for p in pts):.3f})")
    print(f"  Z: [{min(p.z for p in pts):.3f}, {max(p.z for p in pts):.3f}] (size: {max(p.z for p in pts)-min(p.z for p in pts):.3f})")

eval_hand_bounds("L")
eval_hand_bounds("R")
