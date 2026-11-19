import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import copy
import json
from pathlib import Path
import numpy as np
import UnityPy

ORIG_BUNDLE = Path("backup/windblade_gs.assetbundle.orig")
if not ORIG_BUNDLE.exists():
    ORIG_BUNDLE = Path("extracted_apk/assets/assetpack/windblade_gs_odr/windblade_gs.assetbundle")
ANIM_JSON = Path("build/windblade_anim_pose5_export.json")
OUT_BUNDLE = Path("assets_redeco/windblade_gs.assetbundle")

NEW_CLIP_PID = 8888777766665555

def build_attr_map(frame_data: dict) -> dict[int, float]:
    m = {}
    for i, v in enumerate(frame_data["rootT"]):
        m[7 + i] = float(v)
    for i, v in enumerate(frame_data["rootQ"]):
        m[10 + i] = float(v)
    for i, v in enumerate(frame_data["leftFootT"]):
        m[14 + i] = float(v)
    for i, v in enumerate(frame_data["leftFootQ"]):
        m[17 + i] = float(v)
    for i, v in enumerate(frame_data["rightFootT"]):
        m[21 + i] = float(v)
    for i, v in enumerate(frame_data["rightFootQ"]):
        m[24 + i] = float(v)
    for i, v in enumerate(frame_data["leftHandT"]):
        m[28 + i] = float(v)
    for i, v in enumerate(frame_data["leftHandQ"]):
        m[31 + i] = float(v)
    for i, v in enumerate(frame_data["rightHandT"]):
        m[35 + i] = float(v)
    for i, v in enumerate(frame_data["rightHandQ"]):
        m[38 + i] = float(v)
    for i, v in enumerate(frame_data["muscles"]):
        m[42 + i] = float(v)
    return m

def main():
    if not ORIG_BUNDLE.exists():
        raise FileNotFoundError(f"Missing backup bundle: {ORIG_BUNDLE}")
    if not ANIM_JSON.exists():
        raise FileNotFoundError(f"Missing exported animation JSON: {ANIM_JSON}")

    print(f"Loading animation JSON from {ANIM_JSON}...")
    anim_data = json.loads(ANIM_JSON.read_text(encoding="utf-8-sig"))
    frames = anim_data["frames"]
    frame_count = len(frames)
    duration = float(anim_data.get("duration", 2.5))
    sample_rate = float(anim_data.get("sampleRate", 30.0))
    print(f"Loaded {frame_count} frames, duration={duration:.3f}s, sampleRate={sample_rate}")

    # Load authentic genericBindings template from Frontend_Sword_idle (PathID 4726225886941715276)
    proc_bundle = Path("extracted_apk/assets/assetpack/characters_procedural_odr/character_anim_procedural.assetbundle")
    proc_env = UnityPy.load(str(proc_bundle))
    sword_tree = None
    for obj in proc_env.objects:
        if obj.type.name == "AnimationClip" and obj.path_id == 4726225886941715276:
            sword_tree = obj.read_typetree()
            break
    assert sword_tree is not None, "Failed to load Frontend_Sword_idle template!"

    bind = sword_tree["m_ClipBindingConstant"]["genericBindings"]
    num_bindings = len(bind)
    assert num_bindings == 130, f"Expected 130 bindings, got {num_bindings}"

    # Build dense array (frame_count, 130)
    d_samples = np.zeros((frame_count, num_bindings), dtype=np.float32)
    for f_idx, f_data in enumerate(frames):
        attr_map = build_attr_map(f_data)
        for b_idx, b in enumerate(bind):
            attr = b["attribute"]
            d_samples[f_idx, b_idx] = attr_map[attr]

    # Load windblade bundle
    env = UnityPy.load(str(ORIG_BUNDLE))
    ser_file = None
    for f in env.file.files.values():
        if hasattr(f, "objects"):
            ser_file = f
            break

    # Find sample clip reader to clone
    sample_clip_reader = None
    for obj in ser_file.objects.values():
        if obj.type.name == "AnimationClip":
            sample_clip_reader = obj
            break

    # Clone reader for new clip
    cloned_reader = copy.copy(sample_clip_reader)
    cloned_reader.path_id = NEW_CLIP_PID

    # Configure cloned clip tree as pure DenseClip
    new_clip_tree = sword_tree
    new_clip_tree["m_Name"] = "Frontend_Windblade_Showroom_idle"

    mc = new_clip_tree["m_MuscleClip"]
    clip_data = mc["m_Clip"]["data"]
    streamed = clip_data["m_StreamedClip"]
    dense = clip_data["m_DenseClip"]
    constant = clip_data["m_ConstantClip"]

    # 1. StreamedClip -> 0 curves, sentinel infinity stream
    streamed["curveCount"] = 0
    streamed["data"] = [2139095040, 0]

    # 2. DenseClip -> all 130 curves, full frame count
    dense["m_CurveCount"] = num_bindings
    dense["m_FrameCount"] = frame_count
    dense["m_SampleRate"] = sample_rate
    dense["m_SampleArray"] = d_samples.flatten().tolist()

    # 3. ConstantClip -> 0 curves
    constant["data"] = []

    # 4. Deltas & Times
    mc["m_StartTime"] = 0.0
    mc["m_StopTime"] = duration
    mc["m_LoopTime"] = True
    mc["m_LoopBlend"] = False
    mc["m_LoopBlendOrientation"] = True
    mc["m_LoopBlendPositionY"] = True
    mc["m_LoopBlendPositionXZ"] = True
    mc["m_KeepOriginalOrientation"] = True
    mc["m_KeepOriginalPositionY"] = True
    mc["m_KeepOriginalPositionXZ"] = False

    deltas = mc.get("m_ValueArrayDelta", [])
    assert len(deltas) == num_bindings, f"Expected {num_bindings} deltas"
    end_idx = min(75, frame_count - 1)
    for b_idx in range(num_bindings):
        deltas[b_idx]["m_Start"] = float(d_samples[0, b_idx])
        deltas[b_idx]["m_Stop"]  = float(d_samples[end_idx, b_idx])
    mc["m_ValueArrayDelta"] = deltas

    # 5. Start/Stop transforms & Root/Foot start poses
    f0 = frames[0]
    f_end = frames[end_idx]
    rt0, rq0 = f0["rootT"], f0["rootQ"]
    rt_end, rq_end = f_end["rootT"], f_end["rootQ"]
    lft0, lfq0 = f0["leftFootT"], f0["leftFootQ"]
    rft0, rfq0 = f0["rightFootT"], f0["rightFootQ"]

    mc["m_StartX"] = {"t": {"x": rt0[0], "y": rt0[1], "z": rt0[2]}, "q": {"x": rq0[0], "y": rq0[1], "z": rq0[2], "w": rq0[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}
    mc["m_StopX"]  = {"t": {"x": rt_end[0], "y": rt_end[1], "z": rt_end[2]}, "q": {"x": rq_end[0], "y": rq_end[1], "z": rq_end[2], "w": rq_end[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}
    mc["m_LeftFootStartX"]  = {"t": {"x": lft0[0], "y": lft0[1], "z": lft0[2]}, "q": {"x": lfq0[0], "y": lfq0[1], "z": lfq0[2], "w": lfq0[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}
    mc["m_RightFootStartX"] = {"t": {"x": rft0[0], "y": rft0[1], "z": rft0[2]}, "q": {"x": rfq0[0], "y": rfq0[1], "z": rfq0[2], "w": rfq0[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}

    new_clip_tree["m_MuscleClip"] = mc
    cloned_reader.save_typetree(new_clip_tree)
    ser_file.objects[NEW_CLIP_PID] = cloned_reader
    print(f"[+] Cloned and configured new internal clip (PID={NEW_CLIP_PID}, {frame_count} frames)")

    # Update override_WindBlade_GS_lw
    aoc_updated = False
    for obj in ser_file.objects.values():
        if obj.type.name == "AnimatorOverrideController":
            tree = obj.read_typetree()
            if tree.get("m_Name") == "override_WindBlade_GS_lw":
                for pair in tree.get("m_Clips", []):
                    if pair.get("m_OriginalClip", {}).get("m_PathID") == 7553958901562232755:
                        print("Updating FE_Idle override from", pair["m_OverrideClip"], f"to {{m_FileID: 0, m_PathID: {NEW_CLIP_PID}}}")
                        pair["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": NEW_CLIP_PID}
                        aoc_updated = True
                obj.save_typetree(tree)
                break
    assert aoc_updated, "Failed to update override_WindBlade_GS_lw!"

    OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    out_bytes = env.file.save(packer="lz4")
    OUT_BUNDLE.write_bytes(out_bytes)
    print(f"[SUCCESS] Saved {OUT_BUNDLE} ({len(out_bytes)} bytes, LZ4 packed)")

if __name__ == "__main__":
    main()
