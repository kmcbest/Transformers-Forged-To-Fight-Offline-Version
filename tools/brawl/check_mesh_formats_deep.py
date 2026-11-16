import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
import numpy as np
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "brawl_mesh.assetbundle"

print("=== 1. MEGATRON (UNITY 5.6) MESH STRUCTURE ===")
env_meg = UnityPy.load(str(MEG_BUNDLE))
for obj in env_meg.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        if "megatron" in tt["m_Name"]:
            print(f"Mesh: {tt['m_Name']} PID={obj.path_id}")
            print("  Keys:", list(tt.keys()))
            print("  m_Skin len:", len(tt.get("m_Skin", [])))
            vd = tt["m_VertexData"]
            print("  m_VertexData keys:", list(vd.keys()))
            print("  vcount:", vd["m_VertexCount"], "m_CurrentChannels:", vd.get("m_CurrentChannels"), "data_len:", len(vd["m_DataSize"]))
            for ci, ch in enumerate(vd.get("m_Channels", [])):
                if ch["dimension"] > 0:
                    print(f"    ch[{ci}]: stream={ch['stream']} off={ch['offset']} fmt={ch['format']} dim={ch['dimension']}")

print("\n=== 2. UNITY 2020 BRAWL_MESH STRUCTURE ===")
env_m = UnityPy.load(str(MESH_BUNDLE))
for obj in env_m.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        print(f"Mesh: {tt['m_Name']} vcount={tt['m_VertexData']['m_VertexCount']}")
        print("  m_Skin len:", len(tt.get("m_Skin", [])))
        vd = tt["m_VertexData"]
        for ci, ch in enumerate(vd.get("m_Channels", [])):
            if ch["dimension"] > 0:
                print(f"    ch[{ci}]: stream={ch['stream']} off={ch['offset']} fmt={ch['format']} dim={ch['dimension']}")
        # Inspect actual ch12 weights & ch13 boneIndices
        if tt["m_Name"] == "cha_brawl_gs_00":
            buf = bytes(vd["m_DataSize"])
            vc = vd["m_VertexCount"]
            # stream0=40, stream1=8, stream2=24
            s0 = (vc * 40 + 15) & ~15
            s1 = (vc * 8 + 15) & ~15
            s2_off = s0 + s1
            print(f"  s2_off={s2_off}, expected end={s2_off + vc*24}, actual={len(buf)}")
            for vi in range(5):
                ws = struct.unpack_from("<4f", buf, s2_off + vi * 24)
                bi = struct.unpack_from("<4H", buf, s2_off + vi * 24 + 16)
                p = struct.unpack_from("<3f", buf, vi * 40)
                print(f"    v[{vi}] pos={tuple(round(x,2) for x in p)} ws={tuple(round(x,2) for x in ws)} bi={bi}")

print("\n=== 3. EXISTING WORKING GENERATOR SCRIPTS IN REPO ===")
for p in sorted((ROOT / "tools").rglob("generate_*_bundle.py")):
    print(" ", p)
