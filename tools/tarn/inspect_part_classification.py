import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import bpy
import mathutils

TARN_ROOT = Path(r"E:\Agent\TFTF-blender\3rd-party-models\Tarn")
SRC_BLEND = TARN_ROOT / "01_robot_source" / "source" / "last comp3.blend"
bpy.ops.wm.open_mainfile(filepath=str(SRC_BLEND))

# Check Armature.000 & Armature.001 bone positions and finger mapping
for aname, mname in [("Armature.000", "Cylinder.001"), ("Armature.001", "Cylinder.002")]:
    arm = bpy.data.objects[aname]
    mobj = bpy.data.objects[mname]
    print(f"=== {aname} ({mname}) ===")
    # Check vertex counts per vertex group in mesh
    vg_cnt = {vg.index: 0 for vg in mobj.vertex_groups}
    for v in mobj.data.vertices:
        for g in v.groups:
            if g.weight > 0.1:
                vg_cnt[g.group] += 1
    for b in arm.data.bones:
        hw = arm.matrix_world @ b.head_local
        tw = arm.matrix_world @ b.tail_local
        # Evaluate posed world pos
        pb = arm.pose.bones[b.name]
        hp = arm.matrix_world @ pb.head
        tp = arm.matrix_world @ pb.tail
        vg = mobj.vertex_groups.get(b.name)
        vc = vg_cnt[vg.index] if vg else 0
        pname = b.parent.name if b.parent else "None"
        print(f"  {b.name:10s} (parent={pname:8s}) | v={vc:5d} | rest_h=({hw.x:6.2f},{hw.y:6.2f},{hw.z:6.2f}) | pose_h=({hp.x:6.2f},{hp.y:6.2f},{hp.z:6.2f}) -> pose_t=({tp.x:6.2f},{tp.y:6.2f},{tp.z:6.2f})")

# Check ALL mesh objects and classify by Z, X_from_sym (-33.65), and modifiers
print("\n=== ALL MESHES WITH MIRROR MODIFIER OR SYMMETRY CHECK ===")
for o in sorted(bpy.data.objects, key=lambda x: x.name):
    if o.type != 'MESH':
        continue
    has_mirror = any(m.type == 'MIRROR' and m.show_viewport for m in o.modifiers)
    has_curve = any(m.type == 'CURVE' for m in o.modifiers)
    has_array = any(m.type == 'ARRAY' for m in o.modifiers)
    pts = [o.matrix_world @ v.co for v in o.data.vertices]
    if not pts:
        continue
    mn = [min(p[i] for p in pts) for i in range(3)]
    mx = [max(p[i] for p in pts) for i in range(3)]
    cx = 0.5*(mn[0]+mx[0]) - (-33.65)
    cy = 0.5*(mn[1]+mx[1])
    cz = 0.5*(mn[2]+mx[2])
    print(f"  {o.name:22s} | mirror={str(has_mirror):5s} curve={str(has_curve):5s} | v={len(pts):5d} | dX={cx:6.2f} [{mn[0]+33.65:6.2f},{mx[0]+33.65:6.2f}] | Y={cy:6.2f} | Z={cz:6.2f}")
