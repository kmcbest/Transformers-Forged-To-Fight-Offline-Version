import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import bpy
from pathlib import Path
import numpy as np

ROOT = Path(r"E:\Agent\TFTF-blender")
WR_DIR = ROOT / "3rd-party-models" / "WildRider"
FBX_PATH = WR_DIR / "source" / "WildRider_pbr.fbx"

bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=str(FBX_PATH))

arm = bpy.data.objects["Bip001"]
if arm.animation_data:
    arm.animation_data_clear()

wr = bpy.data.objects["WildRider.001"]
gun = bpy.data.objects["WildRider_Gun"]

def dump_mesh_uv_bones(obj):
    uvl = obj.data.uv_layers.active.data
    vg_names = {g.index: g.name for g in obj.vertex_groups}
    uv_list = []
    bone_idx_list = []
    bnames = sorted(set(vg_names.values()))
    b2i = {n: i for i, n in enumerate(bnames)}
    for poly in obj.data.polygons:
        for li in poly.loop_indices:
            uv = uvl[li].uv
            uv_list.append([uv.x, uv.y])
            vi = obj.data.loops[li].vertex_index
            v = obj.data.vertices[vi]
            if v.groups:
                top_g = max(v.groups, key=lambda g: g.weight)
                bone_idx_list.append(b2i[vg_names[top_g.group]])
            else:
                bone_idx_list.append(-1)
    return np.array(uv_list, dtype=np.float32), np.array(bone_idx_list, dtype=np.int32), np.array(bnames)

uv_wr, bi_wr, bn_wr = dump_mesh_uv_bones(wr)
uv_gun, bi_gun, bn_gun = dump_mesh_uv_bones(gun)
out_npz = ROOT / "scratch" / "wildrider_uv_dump.npz"
np.savez(out_npz, uv_wr=uv_wr, bi_wr=bi_wr, bn_wr=bn_wr, uv_gun=uv_gun)
print(f"Dumped UV & bone data to {out_npz}: wr loops={len(uv_wr)}, gun loops={len(uv_gun)}")
