import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\01_source\H_shandian_G1_M_LOD.fbx")

for name in ("H_shandian_G1_W1_Lod", "H_shandian_G1_W2_Lod"):
    obj = bpy.data.objects[name]
    # Clear parent/armature deformation if any (check local coordinates vs world coordinates)
    arm = bpy.data.objects.get("floor")
    if arm:
        # evaluate mesh in rest pose!
        arm.data.pose_position = 'REST'
        bpy.context.view_layer.update()
    deps = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(deps)
    mesh = obj_eval.to_mesh()
    mw = obj_eval.matrix_world
    pts = [mw @ v.co for v in mesh.vertices]
    xs = [p.x for p in pts]
    ys = [p.y for p in pts]
    zs = [p.z for p in pts]
    print(f"\n=== REST WORLD {name} ===")
    print(f"  verts={len(pts)}, polys={len(mesh.polygons)}")
    print(f"  X: [{min(xs):.5f}, {max(xs):.5f}] span={max(xs)-min(xs):.5f}")
    print(f"  Y: [{min(ys):.5f}, {max(ys):.5f}] span={max(ys)-min(ys):.5f}")
    print(f"  Z: [{min(zs):.5f}, {max(zs):.5f}] span={max(zs)-min(zs):.5f}")
    if arm and obj.vertex_groups:
        vg_name = obj.vertex_groups[0].name
        b = arm.data.bones.get(vg_name)
        if b:
            print(f"  bone '{vg_name}': head_w={arm.matrix_world @ b.head_local}, tail_w={arm.matrix_world @ b.tail_local}")
    uv_layer = mesh.uv_layers.active
    if uv_layer:
        us = [d.uv.x for d in uv_layer.data]
        vs = [d.uv.y for d in uv_layer.data]
        print(f"  UV U=[{min(us):.4f}, {max(us):.4f}], V=[{min(vs):.4f}, {max(vs):.4f}]")
    obj_eval.to_mesh_clear()

# Also print body Height for scale reference
body = bpy.data.objects["H_shandian_G1_M_Lod"]
arm = bpy.data.objects["floor"]
arm.data.pose_position = 'REST'
bpy.context.view_layer.update()
pts_b = [body.matrix_world @ v.co for v in body.data.vertices]
print(f"\nBody height Z=[{min(p.z for p in pts_b):.5f}, {max(p.z for p in pts_b):.5f}]")
