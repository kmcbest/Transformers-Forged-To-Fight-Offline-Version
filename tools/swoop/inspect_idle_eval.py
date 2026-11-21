import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath="3rd-party-models/swoop/01_master/Swoop_pbr.fbx")

arm = bpy.data.objects.get("Bip001")
swoop = bpy.data.objects.get("Swoop.001")

act = bpy.data.actions.get("Bip001|idle01|Base Layer")
if act and arm.animation_data:
    arm.animation_data.action = act
    bpy.context.scene.frame_set(1)
    bpy.context.view_layer.update()
    
    # Check evaluated mesh vertices
    depsgraph = bpy.context.evaluated_depsgraph_get()
    eval_obj = swoop.evaluated_get(depsgraph)
    eval_mesh = eval_obj.to_mesh()
    
    pts = [eval_obj.matrix_world @ v.co for v in eval_mesh.vertices]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    print(f"Evaluated Swoop mesh in idle01 frame 1:")
    print(f"  X bounds: [{min(xs):.4f}, {max(xs):.4f}] (span: {max(xs)-min(xs):.4f})")
    print(f"  Y bounds: [{min(ys):.4f}, {max(ys):.4f}] (span: {max(ys)-min(ys):.4f})")
    print(f"  Z bounds: [{min(zs):.4f}, {max(zs):.4f}] (span: {max(zs)-min(zs):.4f})")
    
    # Check Head vs Feet in idle01
    head_b = arm.pose.bones.get("Bone_Head")
    foot_l = arm.pose.bones.get("Bone_L_Foot00")
    foot_r = arm.pose.bones.get("Bone_R_Foot00")
    print(f"  Bone_Head world: {arm.matrix_world @ head_b.head}")
    print(f"  Bone_L_Foot world: {arm.matrix_world @ foot_l.head}")
    print(f"  Bone_R_Foot world: {arm.matrix_world @ foot_r.head}")
    eval_obj.to_mesh_clear()
