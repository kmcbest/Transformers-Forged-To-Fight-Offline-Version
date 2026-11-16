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
MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "brawl_mesh.assetbundle"
MEG_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "megatron_cin_rotf_odr" / "megatron_cin_rotf.assetbundle"

def read_mesh_verts_and_bw(mesh_tt):
    vd = mesh_tt["m_VertexData"]
    vcount = vd["m_VertexCount"]
    buf = bytes(vd["m_DataSize"])
    channels = vd["m_Channels"]
    print(f"  verts={vcount}, buf_len={len(buf)}, channels={len(channels)}")
    # Find stream 0 & stream 2 strides
    for ci, ch in enumerate(channels):
        if ch["dimension"] > 0:
            print(f"    ch[{ci}]: stream={ch['stream']} off={ch['offset']} fmt={ch['format']} dim={ch['dimension']}")
    # Stream 0: pos(3f), norm(3f), uv(2f), tan(4f) -> check offsets
    s0_stride = max((ch["offset"] + ch["dimension"] * 4 for ch in channels if ch["stream"] == 0 and ch["dimension"] > 0), default=0)
    s0_size = (vcount * s0_stride + 15) & ~15
    s1_stride = max((ch["offset"] + ch["dimension"] * (2 if ch["format"]==1 else 4) for ch in channels if ch["stream"] == 1 and ch["dimension"] > 0), default=0)
    s1_size = (vcount * s1_stride + 15) & ~15
    # Wait Unity 2020 vs 5.6 layout: let's read streams from channel info
    stream_strides = {}
    for ch in channels:
        if ch["dimension"] > 0:
            bps = 4 if ch["format"] == 0 else (2 if ch["format"] == 1 else (1 if ch["format"] in (2, 11) else 4))
            # Unity VertexAttributeFormat: Float32=0(4B), Float16=1(2B), UNorm8=2(1B), UInt32=11? Wait
            # Actually in 2020 Skin is stream 1 or 2? Let's inspect stride per stream
            pass
    pos_ch = channels[0]
    # Compute stride of stream 0
    s0_chans = [ch for ch in channels if ch["dimension"] > 0 and ch["stream"] == 0]
    def elem_bytes(fmt):
        # Unity 2020: 0=Float32(4), 1=Float16(2), 2=UNorm8(1), 6=UInt8(1), 10=UInt16(2), 11=UInt32(4), 9=SInt32(4)?
        return {0: 4, 1: 2, 2: 1, 3: 1, 6: 1, 10: 2, 11: 4}.get(fmt, 4)
    streams = sorted(set(ch["stream"] for ch in channels if ch["dimension"] > 0))
    offsets = {}
    cur = 0
    for st in streams:
        st_chans = [ch for ch in channels if ch["dimension"] > 0 and ch["stream"] == st]
        stride = max(ch["offset"] + ch["dimension"] * elem_bytes(ch["format"]) for ch in st_chans)
        offsets[st] = (cur, stride)
        print(f"    stream {st}: offset={cur}, stride={stride}")
        cur += ((vcount * stride + 15) & ~15)

    pts = np.zeros((vcount, 3), dtype=np.float32)
    off0, st0 = offsets[0]
    for i in range(vcount):
        pts[i] = struct.unpack_from("<3f", buf, off0 + i * st0)
    return pts, offsets, buf, channels

print("=== INSPECTING brawl_mesh.assetbundle ===")
env_m = UnityPy.load(str(MESH_BUNDLE))
for obj in env_m.objects:
    if obj.type.name == "Mesh":
        tt = obj.read_typetree()
        print(f"Mesh: {tt['m_Name']}")
        pts, offsets, buf, channels = read_mesh_verts_and_bw(tt)
        print(f"  Bounds X=[{pts[:,0].min():.3f}, {pts[:,0].max():.3f}] Y=[{pts[:,1].min():.3f}, {pts[:,1].max():.3f}] Z=[{pts[:,2].min():.3f}, {pts[:,2].max():.3f}]")
        # Check bone indices if skin channel present
        # Channel 12/13 in Unity 2020: blendWeight (ch12) blendIndices (ch13)
        if len(channels) > 13 and channels[13]["dimension"] > 0:
            ch13 = channels[13]
            st_off, st_str = offsets[ch13["stream"]]
            # Look at first few and check LeftArm(14) vs RightArm(12)
            # In Megatron 39 bones: 14=LeftArm, 12=RightArm, 8=LeftForeArm, 35=RightForeArm
            b0 = np.array([struct.unpack_from("<4I" if ch13["format"] in (0, 11, 9) else "<4H", buf, st_off + i * st_str + ch13["offset"])[0] for i in range(len(pts))])
            for bname, bidx in [("LeftArm", 14), ("RightArm", 12), ("LeftForeArm", 8), ("RightForeArm", 35), ("LeftHand", 15)]:
                mask = (b0 == bidx)
                if mask.any():
                    sub = pts[mask]
                    print(f"  Bone[{bidx:2d}] {bname:13s}: n={mask.sum():4d} X=[{sub[:,0].min():.2f},{sub[:,0].max():.2f}] Y=[{sub[:,1].min():.2f},{sub[:,1].max():.2f}] Z=[{sub[:,2].min():.2f},{sub[:,2].max():.2f}]")
