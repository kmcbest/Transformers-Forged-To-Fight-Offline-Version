import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path

FBX_PATH = r"O:\agent\transformers-fall-of-cybertron-combaticons\source\transformers fall of cybertron convaticons .fbx"
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=FBX_PATH)

head_obj = bpy.data.objects["RB_Blastoff_CHARSKEL_Head.001.dmx"]
arml_obj = bpy.data.objects["RB_Blastoff_CHARSKEL_ArmLoL.001.dmx"]
wing_obj = bpy.data.objects["RB_BlastoffWing_STAT.001.dmx"]

# Use Bone Weights to classify each polygon by anatomical bone!
def dominant_bone(obj, poly):
    acc = {}
    for vi in poly.vertices:
        for g in obj.data.vertices[vi].groups:
            bname = obj.vertex_groups[g.group].name
            acc[bname] = acc.get(bname, 0.0) + g.weight
    if not acc:
        return "NONE"
    return max(acc.items(), key=lambda x: x[1])[0]

print("=== Mapping Mat+Bone -> UV centroids for purple-ish / vent parts ===")
import json

SRC_TEX = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
import numpy as np

TEX_BY_MAT = {
    "RB_Blastoff_Chest_Cust_MatINST": ("rb_blastoff_chest_cust_matinst.jpg", 1024),
    "RB_Blastoff_Legs_Cust_MatINST": ("rb_blastoff_legs_cust_matinst.jpg", 1024),
    "RB_Blastoff_Head_Cust_MatINST": ("rb_blastoff_head_cust_matinst.jpg", 512),
    "RB_Blastoff_ArmLo_Cust_MatINST": ("rb_blastoff_armlo_cust_matinst.jpg", 512),
    "RB_Blastoff_ArmUp_Cust_MatINST": ("rb_blastoff_armup_cust_matinst.jpg", 512),
    "VH_Blastoff_Cust_MatINST": ("vh_blastoff_cust_matinst.jpg", 1024),
}

tex_imgs = {}
for mname, (fname, sz) in TEX_BY_MAT.items():
    im = bpy.data.images.load(str(SRC_TEX / fname))
    w, h = im.size
    arr = (np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4)[:, :, :3] * 255.0)[::-1].copy()
    tex_imgs[mname] = (w, h, arr)

# Also scan VH_Blastoff vehicle
for oname in ["RB_Blastoff_CHARSKEL_Head.001.dmx", "RB_Blastoff_CHARSKEL_ArmLoL.001.dmx", "RB_BlastoffWing_STAT.001.dmx"]:
    obj = bpy.data.objects[oname]
    uv_layer = obj.data.uv_layers.active
    mat_slots = [s.material.name if s.material else "" for s in obj.material_slots]
    mw = obj.matrix_world
    buckets = {}
    for poly in obj.data.polygons:
        mname = mat_slots[poly.material_index] if poly.material_index < len(mat_slots) else ""
        if mname not in tex_imgs:
            continue
        w, h, arr = tex_imgs[mname]
        # sample all loops and polygon center
        us = [uv_layer.data[li].uv.x for li in poly.loop_indices]
        vs = [uv_layer.data[li].uv.y for li in poly.loop_indices]
        u = (sum(us) / len(us)) % 1.0
        v = (sum(vs) / len(vs)) % 1.0
        px = min(w - 1, max(0, int(u * w)))
        py = min(h - 1, max(0, int((1.0 - v) * h)))
        r, g, b = arr[py, px]
        # Looser check: any bluish/purplish/violet pixel (b > g + 6 and b > r * 0.80)
        if b > g + 6 and b > r * 0.80 and b > 28:
            bone = dominant_bone(obj, poly)
            cw = mw @ poly.center
            key = (mname, bone, px // 64, py // 64)
            buckets.setdefault(key, []).append((px, py, cw.x, cw.y + 10.0118, cw.z, r, g, b))
    print(f"\n--- {oname} ---")
    for (mname, bone, bx, by), pts in sorted(buckets.items(), key=lambda x: (x[0][0], x[0][1], -len(x[1]))):
        pxs = [p[0] for p in pts]; pys = [p[1] for p in pts]
        xm = sum(p[2] for p in pts)/len(pts)
        ym = sum(p[3] for p in pts)/len(pts)
        zm = sum(p[4] for p in pts)/len(pts)
        rm = sum(p[5] for p in pts)/len(pts)
        gm = sum(p[6] for p in pts)/len(pts)
        bm = sum(p[7] for p in pts)/len(pts)
        print(f"  {mname:32s} | bone={bone:18s} | n={len(pts):3d} | UV=[{min(pxs):4d}..{max(pxs):4d}, {min(pys):4d}..{max(pys):4d}] | W=(f{xm:+.2f},l{ym:+.2f},u{zm:+.2f}) | RGB=({rm:.0f},{gm:.0f},{bm:.0f})")
