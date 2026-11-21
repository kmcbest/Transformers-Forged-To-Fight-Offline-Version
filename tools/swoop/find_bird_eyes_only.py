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

def uv_px(u, v):
    return ((u - 0.004) / (0.746 - 0.004)) * tw, (1.0 - (v - 0.254) / (0.996 - 0.254)) * th

# Check Robot Head exact eye-visor polys vs any Spine1/Foot/Hand overlap in px=[885,995], py=[645,680]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
me = rob.data
uvl = me.uv_layers["UV0"].data
vg_names = {vg.index: vg.name for vg in rob.vertex_groups}

print("=== Robot polygons inside px=[880,995], py=[645,678] ===")
by_vg = {}
for p in me.polygons:
    pts = [uv_px(uvl[li].uv.x, uvl[li].uv.y) for li in p.loop_indices]
    cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
    if 880 <= cx <= 995 and 645 <= cy <= 678:
        v0 = me.vertices[p.vertices[0]]
        bname = vg_names[max(v0.groups, key=lambda g: g.weight).group]
        rgb = tuple(int(c) for c in tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))])
        by_vg.setdefault(bname, []).append((cx, cy, p.center.x, p.center.y, p.center.z, rgb, pts))

for bn, items in sorted(by_vg.items()):
    all_x = [pt[0] for it in items for pt in it[6]]
    all_y = [pt[1] for it in items for pt in it[6]]
    print(f"  {bn:15s}: n={len(items):3d} px=[{min(all_x):.1f},{max(all_x):.1f}] py=[{min(all_y):.1f},{max(all_y):.1f}] Z=[{min(i[4] for i in items):.2f},{max(i[4] for i in items):.2f}]")

# In Swoop_pbr.fbx, inspect bird_Head bone vertex group directly! (Before Ramjet remapping merged bird_Head -> Spine1 or chop1_chest_center)
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/01_master/Swoop_pbr.fbx"))
sw = bpy.data.objects.get("Swoop.001")
sme = sw.data
suvl = sme.uv_layers["UV0"].data
print("\n=== Raw Swoop.001 vertex groups matching Head/bird ===")
for vg in sw.vertex_groups:
    if any(k in vg.name.lower() for k in ("head", "bird", "jaw", "eye")):
        polys = [p for p in sme.polygons if any(g.group == vg.index and g.weight > 0.3 for g in sme.vertices[p.vertices[0]].groups)]
        dark_polys = []
        for p in polys:
            pts = [(suvl[li].uv.x * tw, (1.0 - suvl[li].uv.y) * th) for li in p.loop_indices]
            cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
            rgb = tex[int(np.clip(cy,0,1023)), int(np.clip(cx,0,1023))]
            if rgb.max() < 75 and (int(rgb.max()) - int(rgb.min())) < 18:
                dark_polys.append((cx, cy, pts, tuple(int(c) for c in rgb)))
        print(f"  VG '{vg.name}': total_polys={len(polys)}, dark_polys={len(dark_polys)}")
        if dark_polys:
            # group by (cx//30, cy//30)
            cl = {}
            for dp in dark_polys:
                cl.setdefault((int(dp[0]//30), int(dp[1]//30)), []).append(dp)
            for k, items in sorted(cl.items()):
                all_x = [pt[0] for it in items for pt in it[2]]
                all_y = [pt[1] for it in items for pt in it[2]]
                print(f"    dark cluster {k}: n={len(items):3d} px=[{min(all_x):.1f},{max(all_x):.1f}] py=[{min(all_y):.1f},{max(all_y):.1f}] sampleRGB={items[0][3]}")
