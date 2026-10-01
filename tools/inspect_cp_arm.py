import bpy
from pathlib import Path

bpy.ops.wm.read_factory_settings(use_empty=True)
fbx_path = Path("3rd-party-models/transformers-fall-of-cybertron-demolishor/source/transformers fall of cybertron Demolishor.fbx").resolve()
bpy.ops.import_scene.fbx(filepath=str(fbx_path))

cp_arm = bpy.data.objects.get("CP_DemolishorArm_SKEL.mo.dmx")
if cp_arm:
    verts = cp_arm.data.vertices
    xs = [v.co.x for v in verts]
    ys = [v.co.y for v in verts]
    zs = [v.co.z for v in verts]
    print(f"CP_DemolishorArm_SKEL AABB:")
    print(f"  X: [{min(xs):.2f}, {max(xs):.2f}]")
    print(f"  Y: [{min(ys):.2f}, {max(ys):.2f}]")
    print(f"  Z: [{min(zs):.2f}, {max(zs):.2f}]")
    print(f"  Vertex count: {len(verts)}")
    for vg in cp_arm.vertex_groups:
        print(f"  VG: {vg.name}")
