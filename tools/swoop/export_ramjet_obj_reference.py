import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
from pathlib import Path
import numpy as np
import UnityPy

DONOR_BUNDLE = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\ramjet_gs_deluxe2008_odr\ramjet_gs_deluxe2008.assetbundle")
OUT_DIR = Path(r"E:\Agent\TFTF-blender\3rd-party-models\swoop\01_master")
OUT_DIR.mkdir(parents=True, exist_ok=True)

env = UnityPy.load(str(DONOR_BUNDLE))

def parse_mesh_to_obj(mesh_obj, out_path):
    tt = mesh_obj.read_typetree()
    vd = tt["m_VertexData"]
    vc = int(vd["m_VertexCount"])
    buf = bytes(vd["m_DataSize"])
    chans = vd["m_Channels"]
    
    def elem_bytes(fmt: int) -> int:
        return {0: 4, 1: 2, 2: 1, 3: 1, 6: 1, 10: 2, 11: 4}.get(fmt, 4)

    streams = sorted(set(c["stream"] for c in chans if c["dimension"] > 0))
    stream_info = {}
    cursor = 0
    for st in streams:
        st_ch = [c for c in chans if c["dimension"] > 0 and c["stream"] == st]
        min_stride = max(c["offset"] + c["dimension"] * elem_bytes(c["format"]) for c in st_ch)
        if st == streams[-1] and vc > 0:
            rem = len(buf) - cursor
            actual_stride = rem // vc
            stride = actual_stride if actual_stride >= min_stride else min_stride
        else:
            stride = min_stride
        stream_info[st] = (cursor, stride)
        cursor += ((vc * stride + 15) & ~15)

    off0, st0 = stream_info[0]
    pts = np.zeros((vc, 3), dtype=np.float32)
    for i in range(vc):
        pts[i] = struct.unpack_from("<3f", buf, off0 + i * st0)

    # Index buffer
    idx_buf = bytes(tt["m_IndexBuffer"])
    triangles = []
    for sm in tt["m_SubMeshes"]:
        first_byte = int(sm["firstByte"])
        ic = int(sm["indexCount"])
        # In Unity 5.6, 16-bit indices
        for i in range(0, ic, 3):
            t = struct.unpack_from("<3H", idx_buf, first_byte + i * 2)
            triangles.append(t)

    # Export to OBJ (Unity: Y-up, +Z forward; Blender: Z-up, -Y forward)
    # Blender coords from Unity: (x, -z, y) or standard Unity coords (x, y, z)
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(f"# Exported from {tt['m_Name']}\n")
        for p in pts:
            f.write(f"v {p[0]:.6f} {p[1]:.6f} {p[2]:.6f}\n")
        for t in triangles:
            f.write(f"f {t[0]+1} {t[1]+1} {t[2]+1}\n")
    print(f"[✓] Exported {out_path} ({vc} vertices, {len(triangles)} triangles)")

for obj in env.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        if tt["m_Name"] == "cha_ramjet_gs_deluxe2008_00":
            parse_mesh_to_obj(obj, OUT_DIR / "ramjet_official_00.obj")
        elif tt["m_Name"] == "cha_ramjet_gs_deluxe2008_01":
            parse_mesh_to_obj(obj, OUT_DIR / "ramjet_official_01.obj")

print("[✓] Reference OBJs exported.")
