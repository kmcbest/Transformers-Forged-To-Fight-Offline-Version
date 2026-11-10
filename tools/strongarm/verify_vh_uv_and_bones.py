import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import struct
import UnityPy
import numpy as np
from pathlib import Path
from PIL import Image, ImageDraw

SCRATCH = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\b1cc49d0-d381-4e8e-a8aa-42f4453e608d\scratch")

# 1. Decode vertices, UVs, triangles, and bone weights of cha_prowl_gs_deluxe2016_01 INSIDE strongarm_gs.assetbundle
bundle_path = r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle"
env = UnityPy.load(bundle_path)

for o in env.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        m = o.read()
        mt = o.read_typetree()
        vc = mt["m_VertexData"]["m_VertexCount"]
        data = bytes(mt["m_VertexData"]["m_DataSize"])
        channels = mt["m_VertexData"]["m_Channels"]
        print(f"Bundle Vehicle Mesh verts={vc}, data_len={len(data)}")
        print("Channels:", channels)
        # UnityPy attributes check
        print("Attrs:", [a for a in dir(m) if "UV" in a or "Vert" in a or "Skin" in a])
        # Decode channels from raw vertex data
        streams = {}
        for idx, ch in enumerate(channels):
            if ch["dimension"] > 0:
                s = ch["stream"]
                # Unity format: 0=float32, 1=float16, 2=unorm8, 3=snorm8, 4=unorm16, 5=snorm16, 6=uint8, 7=int8, 11=int32
                fmt_size = {0: 4, 1: 2, 2: 1, 3: 1, 4: 2, 5: 2, 6: 1, 7: 1, 10: 4, 11: 4}.get(ch["format"], 4)
                end_off = ch["offset"] + ch["dimension"] * fmt_size
                streams[s] = max(streams.get(s, 0), end_off)
        stream_offsets = {}
        cur = 0
        for s in sorted(streams.keys()):
            stream_offsets[s] = cur
            cur += streams[s] * vc
        print("Stream strides:", streams, "total expected:", cur, "actual:", len(data))

        # Parse Pos (ch 0) and UV0 (ch 4)
        def read_ch(ch_idx):
            ch = channels[ch_idx]
            if ch["dimension"] == 0:
                return None
            s = ch["stream"]
            stride = streams[s]
            base = stream_offsets[s] + ch["offset"]
            dt = {0: "<f4", 1: "<f2", 2: "u1", 10: "<u4", 11: "<i4"}[ch["format"]]
            out = np.zeros((vc, ch["dimension"]), dtype=np.float32)
            for i in range(vc):
                off = base + i * stride
                sz = np.dtype(dt).itemsize * ch["dimension"]
                out[i] = np.frombuffer(data[off:off+sz], dtype=dt).astype(np.float32)
            return out

        v = read_ch(0)
        uv = read_ch(4)
        weights = read_ch(12) if len(channels) > 12 else None
        bone_idxs = read_ch(13) if len(channels) > 13 else None
        print(f"Decoded Verts: X=[{v[:,0].min():.3f}, {v[:,0].max():.3f}] Y=[{v[:,1].min():.3f}, {v[:,1].max():.3f}] Z=[{v[:,2].min():.3f}, {v[:,2].max():.3f}]")
        if uv is not None:
            print(f"Decoded UV0: u=[{uv[:,0].min():.3f}, {uv[:,0].max():.3f}] v=[{uv[:,1].min():.3f}, {uv[:,1].max():.3f}]")
            # Also check SubMeshes!
            print("SubMeshes:", mt["m_SubMeshes"])
            idx_bytes = bytes(mt["m_IndexBuffer"])
            tris = np.frombuffer(idx_bytes, dtype=np.uint16).reshape(-1, 3)
            im = Image.open(SCRATCH / "bundle_tform_misc_A.png").convert("RGB").resize((1024, 1024))
            dr = ImageDraw.Draw(im)
            for t0, t1, t2 in tris:
                pts = [(uv[i,0]*1024, (1.0 - uv[i,1])*1024) for i in (t0, t1, t2)]
                dr.polygon(pts, outline=(0, 255, 0))
            im.save(SCRATCH / "verify_bundle_vh_uv_overlay.png")
            print("Saved scratch/verify_bundle_vh_uv_overlay.png")
            top_mask = v[:, 1] > 2.0
            if top_mask.any():
                print(f"Top vertices (Y>2.0, count={top_mask.sum()}) UV range: u=[{uv[top_mask,0].min():.3f}, {uv[top_mask,0].max():.3f}], v=[{uv[top_mask,1].min():.3f}, {uv[top_mask,1].max():.3f}]")

        if bone_idxs is not None:
            bcounts = {}
            for row in bone_idxs:
                b0 = int(row[0])
                bcounts[b0] = bcounts.get(b0, 0) + 1
            print("Bone[0] index counts (stream 13):", bcounts)
        elif mt.get("m_Skin"):
            bcounts = {}
            for s in mt["m_Skin"]:
                b0 = s["boneIndex[0]"]
                bcounts[b0] = bcounts.get(b0, 0) + 1
            print("Bone index counts (m_Skin):", bcounts)

        # Print vehicle SMR bone names & transform scale/pos in bundle
        for o2 in env.objects:
            if o2.type.name == "SkinnedMeshRenderer":
                st = o2.read_typetree()
                if st["m_Mesh"]["m_PathID"] == o.path_id:
                    print("Found vehicle SMR:", o2.path_id)
                    print("SMR m_RootBone path_id:", st["m_RootBone"]["m_PathID"])
                    print("SMR Materials:", st["m_Materials"])
                    bone_names = []
                    for bp in st["m_Bones"]:
                        pid = bp["m_PathID"]
                        for o3 in env.objects:
                            if o3.path_id == pid:
                                t3 = o3.read_typetree()
                                go_pid = t3["m_GameObject"]["m_PathID"]
                                name = "?"
                                for o4 in env.objects:
                                    if o4.path_id == go_pid:
                                        name = o4.read_typetree().get("m_Name", "?")
                                        break
                                bone_names.append((name, t3["m_LocalPosition"], t3["m_LocalRotation"], t3["m_LocalScale"]))
                                break
                    for idx, bn in enumerate(bone_names):
                        print(f"  Bone[{idx}]: {bn[0]} pos=({bn[1]['x']:.3f},{bn[1]['y']:.3f},{bn[1]['z']:.3f}) scale=({bn[3]['x']:.3f},{bn[3]['y']:.3f},{bn[3]['z']:.3f})")
                    # Check Material properties
                    for mp in st["m_Materials"]:
                        for o5 in env.objects:
                            if o5.path_id == mp["m_PathID"]:
                                mat_t = o5.read_typetree()
                                print("Material:", mat_t["m_Name"], "Shader:", mat_t["m_Shader"])
                                print("TexEnvs:", mat_t["m_SavedProperties"]["m_TexEnvs"])
                                print("Floats:", mat_t["m_SavedProperties"]["m_Floats"])
                                print("Colors:", mat_t["m_SavedProperties"]["m_Colors"])
                                break
        break

# 2. Check AnimationClips in strongarm_gs.assetbundle related to vehicle showcase/intro
print("\n--- Checking Vehicle AnimationClips ---")
for o in env.objects:
    if o.type.name == "AnimationClip":
        ct = o.read_typetree()
        nm = ct.get("m_Name", "")
        if "vehicle" in nm.lower() or "car_" in nm.lower() or "levelup" in nm.lower():
            print("Clip:", nm, "path_id:", o.path_id, "length:", ct.get("m_MuscleClip", {}).get("m_StopTime"))
            # Check GenericBindings paths for CenterBackCarFront or Wheel or COG
            gbs = ct.get("m_ClipBindingConstant", {}).get("genericBindings", [])
            print("  genericBindings count:", len(gbs), "sample paths:", [g.get("path") for g in gbs[:20]])
