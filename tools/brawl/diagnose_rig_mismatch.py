import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
import json
import numpy as np
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "brawl_mesh.assetbundle"
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
DONOR_JSON = ROOT / "3rd-party-models" / "Brawl" / "00_donor_reference" / "donor_summary.json"

donor = json.loads(DONOR_JSON.read_text(encoding='utf-8'))
mesh00 = donor["meshes"]["cha_megatron_cin_rotf_00"]
avatar_tos = donor["avatars"]["cha_megatron_cin_rotf_00Avatar"]["tos"]
bone_names = [avatar_tos.get(str(h), f"hash_{h}").split("/")[-1] for h in mesh00["boneHashes"]]

def analyze_mesh(tt, label, s1_stride, has_skin=True):
    vd = tt["m_VertexData"]
    vc = vd["m_VertexCount"]
    buf = bytes(vd["m_DataSize"])
    s0 = (vc * 40 + 15) & ~15
    s1 = (vc * s1_stride + 15) & ~15
    s2_off = s0 + s1
    s2_stride = (len(buf) - s2_off) // vc if has_skin else 0
    print(f"\n=== {label} (vc={vc}, s1_stride={s1_stride}, s2_off={s2_off}, s2_stride={s2_stride}, buf={len(buf)}) ===")
    pts = np.frombuffer(buf[:vc*40], dtype=np.float32).reshape(vc, 10)[:, :3]
    uvs = np.frombuffer(buf[s0:s0+vc*s1_stride], dtype=np.float32).reshape(vc, s1_stride//4)[:, :2]
    print(f"  Pos bounds: X=[{pts[:,0].min():.2f},{pts[:,0].max():.2f}] Y=[{pts[:,1].min():.2f},{pts[:,1].max():.2f}] Z=[{pts[:,2].min():.2f},{pts[:,2].max():.2f}]")
    print(f"  UV0 bounds: U=[{uvs[:,0].min():.3f},{uvs[:,0].max():.3f}] V=[{uvs[:,1].min():.3f},{uvs[:,1].max():.3f}]")
    if has_skin and s2_stride == 32:
        for i in range(3):
            ws = struct.unpack_from("<4f", buf, s2_off + i * 32)
            # Check both <4I and <4H at +16 and +24
            raw16 = buf[s2_off + i * 32 + 16 : s2_off + i * 32 + 32]
            b_u32 = struct.unpack_from("<4I", raw16)
            b_u16 = struct.unpack_from("<8H", raw16)
            print(f"  v[{i}] ws={tuple(round(x,2) for x in ws)} u32={b_u32} u16={b_u16}")
        b0 = np.array([struct.unpack_from("<H", buf, s2_off + i * 32 + 16)[0] for i in range(vc)])
        print(f"  b0 min={b0.min()}, max={b0.max()}, unique={len(np.unique(b0))}")
        for idx in [2, 0, 1, 4, 13, 14, 8, 15, 11, 12, 35, 34, 31, 32, 6, 7, 10]:
            m = (b0 == idx)
            if m.any():
                sub = pts[m]
                bp = mesh00["bindposes"][idx]
                inv = np.linalg.inv(np.array([
                    [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
                    [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
                    [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
                    [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
                ]))[:3, 3]
                print(f"  [{idx:2d}] {bone_names[idx]:14s}: n={m.sum():4d} Verts X=[{sub[:,0].min():6.2f},{sub[:,0].max():6.2f}] Y=[{sub[:,1].min():6.2f},{sub[:,1].max():6.2f}] Z=[{sub[:,2].min():6.2f},{sub[:,2].max():6.2f}] | Bone=({inv[0]:6.2f},{inv[1]:6.2f},{inv[2]:6.2f})")

env_meg = UnityPy.load(str(MEG_BUNDLE))
for o in env_meg.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_megatron_cin_rotf_00":
            analyze_mesh(tt, "MEGATRON DONOR 00", 16)

env_m = UnityPy.load(str(MESH_BUNDLE))
for o in env_m.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_brawl_gs_00":
            analyze_mesh(tt, "BRAWL GRAFTED 00", 8)
        elif tt["m_Name"] == "cha_brawl_gs_01":
            analyze_mesh(tt, "BRAWL GRAFTED 01 (TANK)", 8, has_skin=False)
