import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
import bpy

ROOT = Path(r"E:\Agent\TFTF-blender")
TEX_PATH = ROOT / "3rd-party-models/swoop/01_master/textures/Tx_Swoop_D_RGB.png"
img = bpy.data.images.load(str(TEX_PATH))
tw, th = img.size[0], img.size[1]
tex = (np.array(img.pixels[:], dtype=np.float32).reshape((th, tw, 4))[:, :, :3] * 255.0).astype(np.uint8)[::-1].copy()

def body_atlas_uv_to_px(u, v):
    cu = (u - 0.004) / (0.746 - 0.004)
    cv = (v - 0.254) / (0.996 - 0.254)
    return cu * tw, (1.0 - cv) * th

def inspect_obj_uv_box(fbx_path, obj_name, label):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.ops.import_scene.fbx(filepath=str(fbx_path))
    obj = bpy.data.objects.get(obj_name)
    me = obj.data
    uvl = me.uv_layers["UV0"].data
    vg_names = {vg.index: vg.name for vg in obj.vertex_groups}

    print(f"\n=== {label}: Polygons falling in px=[870,1010], py=[635,760] ===")
    by_bone = {}
    for p in me.polygons:
        pts = [body_atlas_uv_to_px(uvl[li].uv.x, uvl[li].uv.y) for li in p.loop_indices]
        cx = sum(pt[0] for pt in pts)/len(pts)
        cy = sum(pt[1] for pt in pts)/len(pts)
        if 870 <= cx <= 1010 and 635 <= cy <= 760:
            v0 = me.vertices[p.vertices[0]]
            best_vg = max(v0.groups, key=lambda g: g.weight).group if v0.groups else -1
            bname = vg_names.get(best_vg, "None")
            rgb = tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))]
            by_bone.setdefault(bname, []).append((cx, cy, p.center.x, p.center.y, p.center.z, tuple(int(c) for c in rgb), pts))

    for bname, items in sorted(by_bone.items()):
        all_px = [pt[0] for it in items for pt in it[6]]
        all_py = [pt[1] for it in items for pt in it[6]]
        xs = [it[2] for it in items]; ys = [it[3] for it in items]; zs = [it[4] for it in items]
        print(f"  Bone={bname:22s} polys={len(items):3d} px=[{min(all_px):.1f},{max(all_px):.1f}] py=[{min(all_py):.1f},{max(all_py):.1f}] 3D_X=[{min(xs):+.2f},{max(xs):+.2f}] Y=[{min(ys):+.2f},{max(ys):+.2f}] Z=[{min(zs):+.2f},{max(zs):+.2f}]")

    # Also find Pteranodon eye sockets specifically in Vehicle: looking sideways (|nx| > 0.4) near |X| in [0.10, 0.30], Y in [-1.15, -0.60], Z in [2.30, 2.75]
    if label == "Vehicle":
        print("\n=== Vehicle Side-facing head polys near eye position (|X| in [0.08,0.28], Y in [-1.15,-0.55], Z in [2.35,2.70]) ===")
        clusters = {}
        for p in me.polygons:
            if 0.08 <= abs(p.center.x) <= 0.28 and -1.15 <= p.center.y <= -0.55 and 2.35 <= p.center.z <= 2.70:
                pts = [body_atlas_uv_to_px(uvl[li].uv.x, uvl[li].uv.y) for li in p.loop_indices]
                cx = sum(pt[0] for pt in pts)/len(pts)
                cy = sum(pt[1] for pt in pts)/len(pts)
                rgb = tuple(int(c) for c in tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))])
                k = (int(cx//8), int(cy//8))
                clusters.setdefault(k, []).append((cx, cy, p.center.x, p.center.y, p.center.z, rgb, pts))
        for k, items in sorted(clusters.items()):
            all_px = [pt[0] for it in items for pt in it[6]]
            all_py = [pt[1] for it in items for pt in it[6]]
            xs = [it[2] for it in items]; ys = [it[3] for it in items]; zs = [it[4] for it in items]
            mrgb = tuple(int(sum(it[5][c] for it in items)/len(items)) for c in range(3))
            print(f"  cluster {k}: polys={len(items):3d} px=[{min(all_px):.1f},{max(all_px):.1f}] py=[{min(all_py):.1f},{max(all_py):.1f}] X=[{min(xs):+.3f},{max(xs):+.3f}] Y=[{min(ys):+.3f},{max(ys):+.3f}] Z=[{min(zs):+.3f},{max(zs):+.3f}] rgb={mrgb}")

inspect_obj_uv_box(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx", "cha_swoop_robot", "Robot")
inspect_obj_uv_box(ROOT / "3rd-party-models/swoop/03_fbx/swoop_vh_prepared.fbx", "cha_swoop_vh", "Vehicle")
