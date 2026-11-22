import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
import os

BUNDLE_PATH = r"e:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle"
OUT_DIR = r"e:\Agent\TFTF-blender\tools\vortex\diag\bundle_3d"
os.makedirs(OUT_DIR, exist_ok=True)

env = UnityPy.load(BUNDLE_PATH)
obj_map = {obj.path_id: obj for obj in env.objects}

def align16(n):
    return (n + 15) & ~15

def export_mesh_obj(mesh_pid, out_name):
    m = obj_map[mesh_pid].read()
    tt = obj_map[mesh_pid].read_typetree()
    vd = tt["m_VertexData"]
    vc = vd["m_VertexCount"]
    s1_off = align16(vc * 40)
    raw = bytes(vd["m_DataSize"])
    pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
    uv  = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4),  offset=s1_off)
    ib  = np.frombuffer(bytes(m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

    obj_path = os.path.join(OUT_DIR, f"{out_name}.obj")
    with open(obj_path, "w", encoding="utf-8") as f:
        for p in pos:
            f.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
        for u in uv:
            f.write(f"vt {u[0]:.6f} {u[1]:.6f}\n")
        for sm_i, sm in enumerate(tt["m_SubMeshes"]):
            start_tri = (sm["firstByte"] // 2) // 3
            tri_cnt = sm["indexCount"] // 3
            f.write(f"g submesh_{sm_i}\nusemtl sub_{sm_i}\n")
            for tri in ib[start_tri : start_tri + tri_cnt]:
                a, b, c = tri[0] + 1, tri[1] + 1, tri[2] + 1
                f.write(f"f {a}/{a} {b}/{b} {c}/{c}\n")
    print(f"Exported {obj_path} ({len(tt['m_SubMeshes'])} submeshes, s1_off={s1_off})")

export_mesh_obj(-2766188856892899435, "vortex_vh")
export_mesh_obj(5703189533076905359, "vortex_rob")

for pid, fname in [
    (-7643335609835079515, "vh_diff.png"),
    (3025951477767776163,  "vh_raoe.png"),
    (6239694728433603131,  "emb_diff.png"),
    (-8672171104083879485, "emb_raoe.png"),
    (5741437468734501436,  "int_diff.png"),
    (696671028566742258,   "int_raoe.png"),
    (-527106191474585865,  "rob_diff.png"),
    (-2574972184015167263, "rob_raoe.png"),
]:
    obj_map[pid].read().image.save(os.path.join(OUT_DIR, fname))
print("Exported all bundle textures cleanly!")
