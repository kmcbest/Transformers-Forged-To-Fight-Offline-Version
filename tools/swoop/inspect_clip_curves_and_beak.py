import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import struct
import UnityPy
from pathlib import Path

ROOT = Path(r"E:\Agent\TFTF-blender")
TFTF = Path(r"E:\Agent\TFTF")

MESH_BUNDLE = ROOT / "toolchain/unity_build_project/AssetBundles/swoop_mesh.assetbundle"
PROC = TFTF / "extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle"

# 1. Inspect cha_swoop_gs_01 vertex bounds from UnityPy Mesh
em = UnityPy.load(str(MESH_BUNDLE))
for o in em.objects:
    if o.type.name == "Mesh":
        tt = o.read_typetree()
        if tt["m_Name"] == "cha_swoop_gs_01":
            m = o.read()
            # Decode vertices from VertexData
            vd = tt["m_VertexData"]
            vcount = vd["m_VertexCount"]
            data = bytes(vd["m_DataSize"])
            # Channels: 0=pos (format=0 float32 x3)
            # Find stream 0 stride
            ch0 = vd["m_Channels"][0]
            # Calculate stride for stream 0
            # Unity VertexData stream layout
            print(f"cha_swoop_gs_01 vcount={vcount}, channels={[(c['stream'], c['offset'], c['format'], c['dimension']) for c in vd['m_Channels'][:4]]}")
            stride = sum(c["dimension"] * (4 if c["format"] == 0 else 2 if c["format"] == 1 else 1) for c in vd["m_Channels"] if c["stream"] == 0 and c["dimension"] > 0)
            print(f"Estimated stream0 stride = {stride}, data len = {len(data)}, expected min = {vcount * stride}")
            # Read positions if stream 0 starts at offset 0 and format 0 (float32)
            # Note: Unity stores streams sequentially (stream0 all verts, then stream1 all verts)
            if stride > 0 and len(data) >= vcount * stride:
                xs, ys, zs = [], [], []
                for i in range(0, vcount, 1):
                    x, y, z = struct.unpack_from("<fff", data, i * stride + ch0["offset"])
                    xs.append(x); ys.append(y); zs.append(z)
                print(f"  Local verts X: [{min(xs):.3f}, {max(xs):.3f}]")
                print(f"  Local verts Y: [{min(ys):.3f}, {max(ys):.3f}]")
                print(f"  Local verts Z: [{min(zs):.3f}, {max(zs):.3f}]")
                # Check vertices near max Z and min Z (beak vs tail!)
                top_z = sorted(zip(zs, xs, ys), reverse=True)[:5]
                bot_z = sorted(zip(zs, xs, ys))[:5]
                top_y = sorted(zip(ys, xs, zs), reverse=True)[:5]
                print(f"  Max Z (front?): {top_z[:3]}")
                print(f"  Min Z (back?): {bot_z[:3]}")
                print(f"  Max Y (top?): {top_y[:3]}")

# 2. Check StarScream_Normal_attackHeavy vs frontend_Jet_levelup_vehicle_idle vs Ramjet_Normal_attackHeavy clip structure
ep = UnityPy.load(str(PROC))
pmap = {o.path_id: o for o in ep.objects}
for name, pid in [
    ("StarScream_Normal_attackHeavy", 7645321843667068633),
    ("Ramjet_Normal_attackHeavy", -8287216037977883126),
    ("frontend_Jet_levelup_vehicle_idle", 57996331868624866),
    ("StarScream_Normal_attackHeavy_transformed", -7989888022101248653),
]:
    tt = pmap[pid].read_typetree()
    mc = tt["m_MuscleClip"]["m_Clip"]
    sc = mc.get("m_StreamedClip", mc.get("data", {}))
    dc = mc.get("m_DenseClip", {})
    cc = mc.get("m_ConstantClip", {})
    print(f"\nClip '{name}' (PID={pid}): keys={list(mc.keys())}")
    print(f"  Start={tt['m_MuscleClip']['m_StartTime']:.3f}, Stop={tt['m_MuscleClip']['m_StopTime']:.3f}, StartX pos={tt['m_MuscleClip']['m_StartX']['t']}, rot={tt['m_MuscleClip']['m_StartX']['q']}")
    if dc:
        dc_arr = dc.get("m_SampleArray", [])
        n_c = dc.get("m_CurveCount", 0)
        n_f = dc.get("m_FrameCount", 0)
        print(f"  Dense: curves={n_c}, frames={n_f}, samples={len(dc_arr)}")
        if n_c >= 3 and n_f > 0 and len(dc_arr) >= n_c * n_f:
            # First 3 curves of Humanoid MuscleClip are usually RootT (x, y, z)
            mid_f = int(n_f * 0.4 / max(tt['m_MuscleClip']['m_StopTime'], 0.01))
            mid_f = min(max(mid_f, 0), n_f - 1)
            print(f"  Sample f=0: {dc_arr[:min(7, n_c)]}")
            print(f"  Sample f={mid_f} (approx t=0.4s): {dc_arr[mid_f*n_c : mid_f*n_c + min(7, n_c)]}")
