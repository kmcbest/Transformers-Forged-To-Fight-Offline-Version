import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
from mathutils import Vector

ROOT = Path(r"E:\Agent\TFTF-blender")

print("=== 1. Inspecting Raw Swoop_pbr.fbx Materials, Eyes, Symbol_AB ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))

for obj in bpy.data.objects:
    if obj.type == 'MESH':
        mats = [ms.material.name if ms.material else "None" for ms in obj.material_slots]
        print(f"Mesh '{obj.name}': verts={len(obj.data.vertices)}, polys={len(obj.data.polygons)}, mats={mats}")
        if obj.name == "Symbol_AB":
            wmat = obj.matrix_world
            wpts = [wmat @ v.co for v in obj.data.vertices]
            print(f"  Symbol_AB world X=[{min(p.x for p in wpts):.4f}, {max(p.x for p in wpts):.4f}], Y=[{min(p.y for p in wpts):.4f}, {max(p.y for p in wpts):.4f}], Z=[{min(p.z for p in wpts):.4f}, {max(p.z for p in wpts):.4f}]")
            avg_n = sum((wmat.to_3x3() @ p.normal for p in obj.data.polygons), Vector((0,0,0))) / max(len(obj.data.polygons), 1)
            print(f"  Symbol_AB avg world normal = {avg_n.normalized()}")

sw = bpy.data.objects.get("Swoop.001")
if sw:
    me = sw.data
    wmat = sw.matrix_world
    uvl = me.uv_layers.active.data if me.uv_layers else None
    # Count polys per material
    mat_cnt = {}
    for p in me.polygons:
        mn = me.materials[p.material_index].name if p.material_index < len(me.materials) and me.materials[p.material_index] else str(p.material_index)
        mat_cnt[mn] = mat_cnt.get(mn, 0) + 1
    print("  Swoop.001 poly counts by mat:", mat_cnt)

    # Check faces weighted to Head bone or near head height
    # Find bone names in Bip001
    arm = bpy.data.objects.get("Bip001")
    if arm:
        print("  Bip001 head-like bones:", [b.name for b in arm.data.bones if any(k in b.name.lower() for k in ("head", "jaw", "eye", "dino", "crest", "neck"))])
        # Print Head bone world pos
        for bn in arm.data.bones:
            if any(k in bn.name.lower() for k in ("head", "jaw")):
                wp = arm.matrix_world @ bn.head_local
                print(f"    Bone '{bn.name}': world_head={wp}")

    # Inspect Robot Head faces & UVs (around Swoop.001 top)
    wpts = [wmat @ v.co for v in me.vertices]
    print(f"  Swoop.001 world X=[{min(p.x for p in wpts):.3f}, {max(p.x for p in wpts):.3f}], Y=[{min(p.y for p in wpts):.3f}, {max(p.y for p in wpts):.3f}], Z=[{min(p.z for p in wpts):.3f}, {max(p.z for p in wpts):.3f}]")

print("\n=== 2. Inspecting Prepared Robot & Vehicle FBX ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
if rob:
    me = rob.data
    uvl = me.uv_layers.active.data
    # Find emblem polys (U > 0.75) vs chest beak polys near chest X/Z
    sym_polys = []
    beak_polys = []
    head_vg = rob.vertex_groups.get("Head")
    head_idx = head_vg.index if head_vg else -1
    head_polys = []
    for p in me.polygons:
        uvs = [uvl[li].uv for li in p.loop_indices]
        us = [u.x for u in uvs]
        vs = [u.y for u in uvs]
        if min(us) > 0.74:
            sym_polys.append(p)
        else:
            c = p.center
            if abs(c.x) < 0.8 and 4.0 < c.z < 6.8 and c.y < -0.2:
                beak_polys.append(p)
        v0 = me.vertices[p.vertices[0]]
        if any(g.group == head_idx and g.weight > 0.5 for g in v0.groups):
            head_polys.append(p)

    if sym_polys:
        spts = [me.vertices[vi].co for p in sym_polys for vi in p.vertices]
        print(f"  Prepared Symbol_AB polys={len(sym_polys)}, X=[{min(p.x for p in spts):.4f}, {max(p.x for p in spts):.4f}], Y=[{min(p.y for p in spts):.4f}, {max(p.y for p in spts):.4f}], Z=[{min(p.z for p in spts):.4f}, {max(p.z for p in spts):.4f}]")
        avg_n = sum((p.normal for p in sym_polys), Vector((0,0,0))).normalized()
        print(f"  Prepared Symbol_AB avg normal={avg_n}")
    if beak_polys:
        bpts = [me.vertices[vi].co for p in beak_polys for vi in p.vertices]
        print(f"  Prepared Chest Beak polys near emblem X/Z: count={len(beak_polys)}, minY(front)={min(p.y for p in bpts):.4f}, maxY={max(p.y for p in bpts):.4f}")
        # More exact: beak polys whose centroid falls inside Symbol_AB X/Z box
        if sym_polys:
            spts = [me.vertices[vi].co for p in sym_polys for vi in p.vertices]
            sx0, sx1 = min(p.x for p in spts), max(p.x for p in spts)
            sz0, sz1 = min(p.z for p in spts), max(p.z for p in spts)
            overlap = [p for p in beak_polys if sx0 - 0.15 <= p.center.x <= sx1 + 0.15 and sz0 - 0.15 <= p.center.z <= sz1 + 0.15]
            if overlap:
                opts = [me.vertices[vi].co for p in overlap for vi in p.vertices]
                print(f"  Overlapping Chest Beak polys inside Symbol box: count={len(overlap)}, minY(front)={min(p.y for p in opts):.4f}, centerY_min={min(p.center.y for p in overlap):.4f}")

    # Find Robot head eye polys by checking small recessed/front-facing polys near eye Z/X in Head!
    if head_polys:
        hpts = [me.vertices[vi].co for p in head_polys for vi in p.vertices]
        print(f"  Robot Head bbox: X=[{min(p.x for p in hpts):.3f}, {max(p.x for p in hpts):.3f}], Y=[{min(p.y for p in hpts):.3f}, {max(p.y for p in hpts):.3f}], Z=[{min(p.z for p in hpts):.3f}, {max(p.z for p in hpts):.3f}]")
        # Print UV bboxes of front-facing head clusters by Z band & pixel sampling in Tx_Swoop_D_RGB
        front_head = [p for p in head_polys if p.normal.y < -0.3 and p.center.y < -0.3]
        print(f"  Robot front-facing head polys: {len(front_head)}")
        # Group by quantized UV (16x16 bins in original [0..1] by inverting atlas remap)
        # Body atlas: u_atlas = 0.004 + cu*(0.746-0.004), v_atlas = 0.254 + cv*(0.996-0.254)
        bins = {}
        for p in front_head:
            us = [(uvl[li].uv.x - 0.004) / (0.746 - 0.004) for li in p.loop_indices]
            vs = [(uvl[li].uv.y - 0.254) / (0.996 - 0.254) for li in p.loop_indices]
            cu, cv = sum(us)/len(us), sum(vs)/len(vs)
            key = (int(cu * 32), int(cv * 32))
            bins.setdefault(key, []).append((cu, cv, p.center.x, p.center.y, p.center.z))
        for k, items in sorted(bins.items()):
            us = [x[0] for x in items]; vs = [x[1] for x in items]
            xs = [x[2] for x in items]; zs = [x[4] for x in items]
            print(f"    Head UV bin {k}: polys={len(items):3d}, src_u=[{min(us):.3f},{max(us):.3f}], src_v=[{min(vs):.3f},{max(vs):.3f}], X=[{min(xs):.3f},{max(xs):.3f}], Z=[{min(zs):.3f},{max(zs):.3f}]")

print("\n=== 3. Inspecting Prepared Vehicle FBX ===")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx"))
vh = bpy.data.objects.get("cha_swoop_vh")
if vh:
    me = vh.data
    uvl = me.uv_layers.active.data
    vh_head_vg = vh.vertex_groups.get("chop1_head_center")
    if vh_head_vg:
        hi = vh_head_vg.index
        hp = [p for p in me.polygons if any(g.group == hi and g.weight > 0.3 for g in me.vertices[p.vertices[0]].groups)]
        print(f"  Vehicle chop1_head_center polys: {len(hp)}")
        bins = {}
        for p in hp:
            us = [(uvl[li].uv.x - 0.004) / (0.746 - 0.004) for li in p.loop_indices]
            vs = [(uvl[li].uv.y - 0.254) / (0.996 - 0.254) for li in p.loop_indices]
            cu, cv = sum(us)/len(us), sum(vs)/len(vs)
            key = (int(cu * 32), int(cv * 32))
            bins.setdefault(key, []).append((cu, cv, p.center.x, p.center.y, p.center.z))
        for k, items in sorted(bins.items()):
            us = [x[0] for x in items]; vs = [x[1] for x in items]
            xs = [x[2] for x in items]; ys = [x[3] for x in items]; zs = [x[4] for x in items]
            print(f"    VH Head UV bin {k}: polys={len(items):3d}, src_u=[{min(us):.3f},{max(us):.3f}], src_v=[{min(vs):.3f},{max(vs):.3f}], X=[{min(xs):.2f},{max(xs):.2f}], Y=[{min(ys):.2f},{max(ys):.2f}], Z=[{min(zs):.2f},{max(zs):.2f}]")
