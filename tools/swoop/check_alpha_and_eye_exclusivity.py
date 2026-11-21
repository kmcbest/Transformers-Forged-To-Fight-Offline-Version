import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
import bpy

ROOT = Path(r"E:\Agent\TFTF-blender")
im_bl = bpy.data.images.load(str(ROOT / "3rd-party-models/swoop/01_master/textures/Tx_Swoop_D.png"))
tw, th = im_bl.size[0], im_bl.size[1]
arr_d = (np.array(im_bl.pixels[:], dtype=np.float32).reshape((th, tw, 4)) * 255.0).astype(np.uint8)[::-1].copy()
a = arr_d[:, :, 3]
print(f"Tx_Swoop_D.png Alpha>20 count={(a>20).sum()}")
# Check Robot Eyes [639:650, 949:990] Alpha & RGB
re = arr_d[638:652, 948:992]
print(f"Robot Eyes ROI alpha>20 count={(re[:,:,3]>20).sum()}, dark(maxRGB<45)={(re[:,:,:3].max(axis=2)<45).sum()}")
be = arr_d[5:34, 600:666]
print(f"Bird Eyes ROI alpha>20 count={(be[:,:,3]>20).sum()}, dark(maxRGB<45)={(be[:,:,:3].max(axis=2)<45).sum()}")

# Check if ANY non-Head polygon on swoop_prepared touches [949..990, 639..650]
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(ROOT / "3rd-party-models/swoop/03_fbx/swoop_prepared.fbx"))
rob = bpy.data.objects.get("cha_swoop_robot")
me = rob.data; uvl = me.uv_layers["UV0"].data
vgn = {vg.index: vg.name for vg in rob.vertex_groups}
def uv_px(u, v):
    return ((u - 0.004) / (0.746 - 0.004)) * 1024, (1.0 - (v - 0.254) / (0.996 - 0.254)) * 1024

hits = {}
for p in me.polygons:
    pts = [uv_px(uvl[li].uv.x, uvl[li].uv.y) for li in p.loop_indices]
    cx = sum(pt[0] for pt in pts)/len(pts); cy = sum(pt[1] for pt in pts)/len(pts)
    if 949 <= cx <= 990 and 639 <= cy <= 650:
        v0 = me.vertices[p.vertices[0]]
        bn = vgn[max(v0.groups, key=lambda g: g.weight).group]
        rgb = tuple(int(c) for c in arr_d[int(cy), int(cx), :3])
        hits.setdefault((bn, int(max(rgb)<45)), []).append((p.center.x, p.center.y, p.center.z, rgb))
print("Robot polygons inside px=[949..990], py=[639..650]:")
for k, items in sorted(hits.items()):
    print(f"  {k}: n={len(items)} Z=[{min(i[2] for i in items):.2f},{max(i[2] for i in items):.2f}] sampleRGB={items[0][3]}")
