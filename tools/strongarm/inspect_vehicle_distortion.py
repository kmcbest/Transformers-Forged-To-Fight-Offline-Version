import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import numpy as np
import UnityPy
from pathlib import Path

p_prowl = Path(r"E:\Agent\TFTF\extracted_apk\assets\assetpack\prowl_gs_deluxe2016_odr\prowl_gs_deluxe2016.assetbundle")
p_sa = Path(r"E:\Agent\TFTF-blender\assets_redeco\strongarm_gs.assetbundle")

env_p = UnityPy.load(str(p_prowl))
gos = {o.path_id: o.read_typetree() for o in env_p.objects if o.type.name == "GameObject"}
trs = {o.path_id: o.read_typetree() for o in env_p.objects if o.type.name == "Transform"}
tr_to_go = {pid: t.get("m_GameObject", {}).get("m_PathID") for pid, t in trs.items()}

# 1. Inspect Vehicle SMR 26 bones + Transform localScale / localPosition / localRotation + m_BindPose!
for o in env_p.objects:
    if o.type.name == "Mesh":
        m = o.read_typetree()
        if m.get("m_Name") == "cha_prowl_gs_deluxe2016_01":
            print(f"Prowl Vehicle Mesh LocalAABB: {m.get('m_LocalAABB')}, submeshes={len(m.get('m_SubMeshes', []))}")
            bps = m.get("m_BindPose", [])
    elif o.type.name == "SkinnedMeshRenderer":
        s = o.read_typetree()
        if len(s.get("m_Bones", [])) == 26:
            root_b = s.get("m_RootBone", {}).get("m_PathID")
            go_id = s.get("m_GameObject", {}).get("m_PathID")
            print(f"\nProwl Vehicle SMR on GO '{gos[go_id]['m_Name']}' RootBone={gos.get(tr_to_go.get(root_b,0),{}).get('m_Name')} AABB={s.get('m_AABB')}")
            for idx, b in enumerate(s["m_Bones"]):
                pid = b["m_PathID"]
                tr = trs.get(pid, {})
                bname = gos.get(tr_to_go.get(pid, 0), {}).get("m_Name", "?")
                ls = tr.get("m_LocalScale", {})
                lp = tr.get("m_LocalPosition", {})
                lr = tr.get("m_LocalRotation", {})
                print(f"  [{idx:2d}] {bname:24s} pos=({lp.get('x',0):.2f},{lp.get('y',0):.2f},{lp.get('z',0):.2f}) scale=({ls.get('x',1):.3f},{ls.get('y',1):.3f},{ls.get('z',1):.3f}) rot=({lr.get('x',0):.2f},{lr.get('y',0):.2f},{lr.get('z',0):.2f},{lr.get('w',1):.2f})")
            break

# 2. Check AnimationClip frontend_Prowl_levelup_vehicle_idle_transformed for any bone position/scale curves!
print("\n=== Vehicle Idle Clip Curves ===")
for o in env_p.objects:
    if o.type.name == "AnimationClip":
        c = o.read_typetree()
        if "vehicle_idle" in c.get("m_Name", "").lower():
            print(f"Clip '{c['m_Name']}' len={c.get('m_MuscleClip',{}).get('m_StopTime')} bindings:")
            # Also check Raw/Generic bindings in m_ClipBindingConstant
            bindings = c.get("m_ClipBindingConstant", {}).get("genericBindings", [])
            print(f"  genericBindings count={len(bindings)}")
            # Check old-style curves if any
            print(f"  posCurves={len(c.get('m_PositionCurves', []))}, rotCurves={len(c.get('m_RotationCurves', []))}, scaleCurves={len(c.get('m_ScaleCurves', []))}, floatCurves={len(c.get('m_FloatCurves', []))}")
            # StreamedClip check:
            clip = c.get("m_MuscleClip", {}).get("m_Clip", {})
            print(f"  StreamedClip frameCount? streamFrames={len(clip.get('m_StreamedClip',{}).get('data',[]))}, denseFrames={clip.get('m_DenseClip',{}).get('m_FrameCount')}")
            for sc in c.get("m_ScaleCurves", []):
                print("  scaleCurve:", sc.get("path"))

# 3. Inspect Strongarm Vehicle Mesh vertex weights & bone distribution inside strongarm_gs.assetbundle
env_s = UnityPy.load(str(p_sa))
for o in env_s.objects:
    if o.type.name == "Mesh" and o.read_typetree().get("m_Name") == "cha_prowl_gs_deluxe2016_01":
        m = o.read()
        print(f"\nStrongarm Vehicle Mesh in bundle: verts={len(m.m_Vertices)//3 if hasattr(m,'m_Vertices') else '?'}")
        # Read typetree skin weights
        mt = o.read_typetree()
        print(f"  LocalAABB={mt.get('m_LocalAABB')}, submeshes={len(mt.get('m_SubMeshes', []))}")
        skin = mt.get("m_Skin", [])
        if skin:
            counts = {}
            for sk in skin:
                b0 = sk.get("boneIndex[0]")
                counts[b0] = counts.get(b0, 0) + 1
            print("  Vertex boneIndex[0] distribution:", counts)
        else:
            # Check Unity 2019+ m_VariableBoneCountWeights / m_BonesPerVertex
            vd = mt.get("m_VertexData", {})
            print("  m_VertexData channels:", [(ch.get("stream"), ch.get("offset"), ch.get("format"), ch.get("dimension")) for ch in vd.get("m_Channels", [])])
            vb = mt.get("m_VariableBoneCountWeights", {})
            print("  m_VariableBoneCountWeights:", len(vb.get("m_Data", [])))
