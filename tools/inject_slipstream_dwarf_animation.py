import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
from pathlib import Path
import numpy as np
import UnityPy

ORIG_BUNDLE = Path("backup/slipstream_gs.assetbundle.orig")
ANIM_JSON = Path("build/slipstream_anim_dwarf_export.json")
OUT_BUNDLE = Path("assets_redeco/slipstream_gs.assetbundle")

TARGET_CLIP_PID = -3168055133523594933  # Frontend_Tactical_idle

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
    duration = float(anim_data.get("duration", 4.433333))
    sample_rate = float(anim_data.get("sampleRate", 30.0))
    print(f"Loaded {frame_count} frames, duration={duration:.3f}s, sampleRate={sample_rate}")

    env = UnityPy.load(str(ORIG_BUNDLE))
    patched = False

    for obj in env.objects:
        if obj.type.name == "AnimationClip" and obj.path_id == TARGET_CLIP_PID:
            tree = obj.read_typetree()
            assert tree.get("m_Name") == "Frontend_Tactical_idle"

            bind = tree["m_ClipBindingConstant"]["genericBindings"]
            num_bindings = len(bind)
            print(f"Target clip bindings: {num_bindings}")
            assert num_bindings == 130, f"Expected 130 bindings, got {num_bindings}"

            # Build full (frame_count, 130) dense array
            d_samples = np.zeros((frame_count, num_bindings), dtype=np.float32)
            for f_idx, f_data in enumerate(frames):
                attr_map = build_attr_map(f_data)
                for b_idx, b in enumerate(bind):
                    attr = b["attribute"]
                    d_samples[f_idx, b_idx] = attr_map[attr]

            mc = tree["m_MuscleClip"]
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
            deltas = mc.get("m_ValueArrayDelta", [])
            assert len(deltas) == num_bindings, f"Expected {num_bindings} deltas"
            for b_idx in range(num_bindings):
                deltas[b_idx]["m_Start"] = float(d_samples[0, b_idx])
                deltas[b_idx]["m_Stop"]  = float(d_samples[-1, b_idx])
            mc["m_ValueArrayDelta"] = deltas

            # 5. Start/Stop transforms & Root/Foot start poses
            f0 = frames[0]
            f_last = frames[-1]
            rt0, rq0 = f0["rootT"], f0["rootQ"]
            rt_last, rq_last = f_last["rootT"], f_last["rootQ"]
            lft0, lfq0 = f0["leftFootT"], f0["leftFootQ"]
            rft0, rfq0 = f0["rightFootT"], f0["rightFootQ"]

            mc["m_StartX"] = {"t": {"x": rt0[0], "y": rt0[1], "z": rt0[2]}, "q": {"x": rq0[0], "y": rq0[1], "z": rq0[2], "w": rq0[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}
            mc["m_StopX"]  = {"t": {"x": rt_last[0], "y": rt_last[1], "z": rt_last[2]}, "q": {"x": rq_last[0], "y": rq_last[1], "z": rq_last[2], "w": rq_last[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}
            mc["m_LeftFootStartX"]  = {"t": {"x": lft0[0], "y": lft0[1], "z": lft0[2]}, "q": {"x": lfq0[0], "y": lfq0[1], "z": lfq0[2], "w": lfq0[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}
            mc["m_RightFootStartX"] = {"t": {"x": rft0[0], "y": rft0[1], "z": rft0[2]}, "q": {"x": rfq0[0], "y": rfq0[1], "z": rfq0[2], "w": rfq0[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}

            tree["m_MuscleClip"] = mc

            obj.save_typetree(tree)
            patched = True
            print(f"[+] Successfully patched Slipstream Frontend_Tactical_idle with {frame_count} frames (PID={TARGET_CLIP_PID})")
            break

    if not patched:
        raise RuntimeError("Target clip not found!")

    OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    out_bytes = env.file.save(packer="lz4")
    OUT_BUNDLE.write_bytes(out_bytes)
    print(f"[SUCCESS] Saved {OUT_BUNDLE} ({len(out_bytes)} bytes, LZ4 packed)")

if __name__ == "__main__":
    main()
