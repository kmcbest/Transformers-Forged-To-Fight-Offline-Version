import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
import mathutils
import numpy as np

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = r"e:\Agent\TFTF-blender\3rd-party-models\swoop\01_master\Swoop_pbr.fbx"
bpy.ops.import_scene.fbx(filepath=fbx_path)

arm = bpy.data.objects.get("Bip001")
action = bpy.data.actions.get("Bip001|vehicle_idle01|Base Layer")
if action and arm:
    arm.animation_data.action = action
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()

mesh = bpy.data.objects.get("Swoop.001")
dg = bpy.context.evaluated_depsgraph_get()
eval_mesh = mesh.evaluated_get(dg)
m_data = eval_mesh.to_mesh()

pts = np.array([eval_mesh.matrix_world @ v.co for v in m_data.vertices])
print(f"Pteranodon Evaluated Mesh Bounds (Frame 1):")
print(f"  X: [{pts[:,0].min():.4f}, {pts[:,0].max():.4f}], span={np.ptp(pts[:,0]):.4f}")
print(f"  Y: [{pts[:,1].min():.4f}, {pts[:,1].max():.4f}], span={np.ptp(pts[:,1]):.4f}")
print(f"  Z: [{pts[:,2].min():.4f}, {pts[:,2].max():.4f}], span={np.ptp(pts[:,2]):.4f}")

# Check beak / head vs tail
beak = arm.pose.bones.get("beak")
pelvis = arm.pose.bones.get("Bip001 Pelvis")
if beak and pelvis:
    b_pos = arm.matrix_world @ beak.matrix.to_translation()
    p_pos = arm.matrix_world @ pelvis.matrix.to_translation()
    print(f"  Beak world pos: {b_pos}")
    print(f"  Pelvis world pos: {p_pos}")
    print(f"  Delta (Beak - Pelvis): {b_pos - p_pos}")

eval_mesh.to_mesh_clear()
