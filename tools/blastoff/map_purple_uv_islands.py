import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import bpy
import numpy as np
from pathlib import Path

SRC_TEX = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

BLASTOFF_MESH_NAMES = [
    "RB_Blastoff_CHARSKEL_Head.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx",
    "RB_Blastoff_CHARSKEL_ArmLoR.001.dmx",
    "RB_BlastoffWing_STAT.001.dmx",
    "RB_BlastoffWing_STAT.dmx",
]

TEX_BY_MAT = {
    "RB_Blastoff_Chest_Cust_MatINST": "rb_blastoff_chest_cust_matinst.jpg",
    "RB_Blastoff_Legs_Cust_MatINST": "rb_blastoff_legs_cust_matinst.jpg",
    "RB_Blastoff_Head_Cust_MatINST": "rb_blastoff_head_cust_matinst.jpg",
    "RB_Blastoff_ArmLo_Cust_MatINST": "rb_blastoff_armlo_cust_matinst.jpg",
    "RB_Blastoff_ArmUp_Cust_MatINST": "rb_blastoff_armup_cust_matinst.jpg",
    "VH_Blastoff_Cust_MatINST": "vh_blastoff_cust_matinst.jpg",
}

tex_imgs = {}
for mname, fname in TEX_BY_MAT.items():
    im = bpy.data.images.load(str(SRC_TEX / fname))
    w, h = im.size
    arr = (np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, :3] * 255.0)
    # Flip vertically so row 0 is top (PIL Y convention)
    arr = arr[::-1].copy()
    tex_imgs[mname] = ((w, h), arr)

print("=== Mapping Purple Polygons to 3D Body Parts ===")
clusters = {}

for oname in BLASTOFF_MESH_NAMES + ["VH_Blastoff.001.dmx"]:
    obj = bpy.data.objects.get(oname)
    if not obj:
        continue
    uv_layer = obj.data.uv_layers.active
    mat_slots = [s.material.name if s.material else "" for s in obj.material_slots]
    mw = obj.matrix_world
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        if mname not in tex_imgs:
            continue
        (w, h), arr = tex_imgs[mname]
        us = [uv_layer.data[li].uv.x for li in poly.loop_indices]
        vs = [uv_layer.data[li].uv.y for li in poly.loop_indices]
        u = (sum(us) / len(us)) % 1.0
        v = (sum(vs) / len(vs)) % 1.0
        px = min(w - 1, max(0, int(u * w)))
        py = min(h - 1, max(0, int((1.0 - v) * h)))
        r, g, b = arr[py, px]
        if b > g + 12 and b > r * 0.88 and b > 40:
            cw = mw @ poly.center
            clusters.setdefault((oname, mname), []).append((px, py, cw.x, cw.y + 10.0118, cw.z, r, g, b))

for (oname, mname), pts in clusters.items():
    print(f"\n[{oname}] {mname}: {len(pts)} purple polys")
    bins = {}
    for px, py, x, y, z, r, g, b in pts:
        key = (px // 80, py // 80)
        bins.setdefault(key, []).append((px, py, x, y, z, r, g, b))
    for k, bpts in sorted(bins.items(), key=lambda kv: -len(kv[1])):
        if len(bpts) < 2 and len(bins) > 8:
            continue
        pxm = sum(p[0] for p in bpts) / len(bpts)
        pym = sum(p[1] for p in bpts) / len(bpts)
        xm = sum(p[2] for p in bpts) / len(bpts)
        ym = sum(p[3] for p in bpts) / len(bpts)
        zm = sum(p[4] for p in bpts) / len(bpts)
        rm = sum(p[5] for p in bpts) / len(bpts)
        gm = sum(p[6] for p in bpts) / len(bpts)
        bm = sum(p[7] for p in bpts) / len(bpts)
        print(f"  count={len(bpts):4d} UV_PIL=({pxm:5.0f},{pym:5.0f}) World=(fwd={xm:+.2f}, left={ym:+.2f}, up={zm:+.2f}) RGB=({rm:.0f},{gm:.0f},{bm:.0f})")
