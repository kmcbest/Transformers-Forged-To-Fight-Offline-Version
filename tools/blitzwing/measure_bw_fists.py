import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import bpy
from mathutils import Vector

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=r"E:\Agent\TFTF-blender\3rd-party-models\Blitzwing_EW\03_fbx_exports\cha_blitzwing_gs_00_robot.fbx")

arm = next(o for o in bpy.data.objects if o.type == 'ARMATURE')
mesh = next(o for o in bpy.data.objects if o.type == 'MESH')
bpy.context.view_layer.update()

for bname in ("LeftHand", "RightHand"):
    pb = arm.pose.bones[bname]
    M_w = arm.matrix_world @ pb.matrix
    print(f"\n=== Blitzwing Baked {bname} World Matrix ===")
    print(f"  pos_w = {M_w.translation}")
    # Also find vertices weighted to LeftHand / RightHand in mesh!
    vg_idx = mesh.vertex_groups[bname].index
    # Filter vertices closest to the wrist (palm/fingers) vs forearm end
    hand_pts_local = []
    for v in mesh.data.vertices:
        w = 0.0
        for g in v.groups:
            if g.group == vg_idx:
                w = g.weight
        if w > 0.5:
            pw = mesh.matrix_world @ v.co
            pl = M_w.inverted() @ pw
            hand_pts_local.append(pl)
    xs = [p.x for p in hand_pts_local]
    ys = [p.y for p in hand_pts_local]
    zs = [p.z for p in hand_pts_local]
    print(f"  verts weighted to {bname}: count={len(hand_pts_local)}")
    print(f"  in {bname} local space: X=[{min(xs):.3f}, {max(xs):.3f}], Y=[{min(ys):.3f}, {max(ys):.3f}], Z=[{min(zs):.3f}, {max(zs):.3f}]")
    # Mean of distal finger region (x < -0.5)
    fist_pts = [p for p in hand_pts_local if p.x < -0.4]
    if fist_pts:
        c = sum(fist_pts, Vector((0,0,0))) / len(fist_pts)
        print(f"  fist center in {bname} local space: {c}")
        print(f"  fist bbox: X=[{min(p.x for p in fist_pts):.3f},{max(p.x for p in fist_pts):.3f}], Y=[{min(p.y for p in fist_pts):.3f},{max(p.y for p in fist_pts):.3f}], Z=[{min(p.z for p in fist_pts):.3f},{max(p.z for p in fist_pts):.3f}]")
