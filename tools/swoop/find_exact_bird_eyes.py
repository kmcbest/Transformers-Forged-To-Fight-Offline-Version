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

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))
sw = bpy.data.objects.get("Swoop.001")
sme = sw.data
suvl = sme.uv_layers["UV0"].data
bh_vg = sw.vertex_groups["bird_Head"]

# Get all bird_Head polys in raw unposed / posed Swoop.001
# Wait: swoop_vh_prepared has bird_Head posed upright as the flying Pteranodon! Let's inspect BOTH.
bh_polys = [p for p in sme.polygons if any(g.group == bh_vg.index and g.weight > 0.3 for g in sme.vertices[p.vertices[0]].groups)]
print(f"Raw bird_Head polys: {len(bh_polys)}")
# Group ALL bird_Head polys by (px//16, py//16) to see EVERY UV island of bird_Head!
islands = {}
for p in bh_polys:
    pts = [(suvl[li].uv.x * tw, (1.0 - suvl[li].uv.y) * th) for li in p.loop_indices]
    cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
    rgb = tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))]
    islands.setdefault((int(cx//16), int(cy//16)), []).append((cx, cy, pts, tuple(int(c) for c in rgb)))

print("=== ALL bird_Head UV islands (16x16 bins) ===")
for k, items in sorted(islands.items()):
    all_x = [pt[0] for it in items for pt in it[2]]
    all_y = [pt[1] for it in items for pt in it[2]]
    rgbs = [it[3] for it in items]
    mrgb = tuple(int(sum(c[j] for c in rgbs)/len(rgbs)) for j in range(3))
    print(f"  bin {k}: polys={len(items):3d} px=[{min(all_x):5.1f},{max(all_x):5.1f}] py=[{min(all_y):5.1f},{max(all_y):5.1f}] meanRGB={mrgb}")

# Also inspect Robot Head ALL UV islands (16x16 bins) on Bone_Head!
hd_vg = sw.vertex_groups["Bone_Head"]
hd_polys = [p for p in sme.polygons if any(g.group == hd_vg.index and g.weight > 0.3 for g in sme.vertices[p.vertices[0]].groups)]
hislands = {}
for p in hd_polys:
    pts = [(suvl[li].uv.x * tw, (1.0 - suvl[li].uv.y) * th) for li in p.loop_indices]
    cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
    rgb = tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))]
    hislands.setdefault((int(cx//16), int(cy//16)), []).append((cx, cy, pts, tuple(int(c) for c in rgb)))

print("\n=== ALL Bone_Head dark/neutral UV islands (mean<90) ===")
for k, items in sorted(hislands.items()):
    rgbs = [it[3] for it in items]
    mrgb = tuple(int(sum(c[j] for c in rgbs)/len(rgbs)) for j in range(3))
    if max(mrgb) < 95:
        all_x = [pt[0] for it in items for pt in it[2]]
        all_y = [pt[1] for it in items for pt in it[2]]
        print(f"  bin {k}: polys={len(items):3d} px=[{min(all_x):5.1f},{max(all_x):5.1f}] py=[{min(all_y):5.1f},{max(all_y):5.1f}] meanRGB={mrgb}")
