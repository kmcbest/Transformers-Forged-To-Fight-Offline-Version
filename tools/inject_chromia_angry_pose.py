import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import json
import math
import struct
from pathlib import Path
import numpy as np
import UnityPy

ORIG_BUNDLE = Path("backup/chromia_gs_kabam.assetbundle.orig")
POSE_JSON = Path("build/chromia_pose_angry_export.json")
OUT_BUNDLE = Path("assets_redeco/chromia_gs_kabam.assetbundle")

TARGET_CLIP_PID = 807675994726628539  # TeamSelect_Female_idle

def build_attr_map(data: dict) -> dict[int, float]:
    m = {}
    for i, v in enumerate(data["rootT"]):
        m[7 + i] = float(v)
    for i, v in enumerate(data["rootQ"]):
        m[10 + i] = float(v)
    for i, v in enumerate(data["leftFootT"]):
        m[14 + i] = float(v)
    for i, v in enumerate(data["leftFootQ"]):
        m[17 + i] = float(v)
    for i, v in enumerate(data["rightFootT"]):
        m[21 + i] = float(v)
    for i, v in enumerate(data["rightFootQ"]):
        m[24 + i] = float(v)
    for i, v in enumerate(data["leftHandT"]):
        m[28 + i] = float(v)
    for i, v in enumerate(data["leftHandQ"]):
        m[31 + i] = float(v)
    for i, v in enumerate(data["rightHandT"]):
        m[35 + i] = float(v)
    for i, v in enumerate(data["rightHandQ"]):
        m[38 + i] = float(v)
    for i, v in enumerate(data["muscles"]):
        m[42 + i] = float(v)
    return m

# Silky-smooth chest and shoulder breathing (seamless 2.5s loop)
BREATH_AMP = {
    42: -0.004,  # Spine Front-Back (Dense, 77 frames)
    45: +0.020,  # Chest Front-Back (Streamed, exact cubic Hermite)
    79: +0.006,  # Left Shoulder Down-Up (Dense, 77 frames)
    88: +0.014,  # Right Shoulder Down-Up (Dense, 77 frames)
}

def eval_val(base_val: float, attr: int, t: float, duration: float) -> float:
    amp = BREATH_AMP.get(attr, 0.0)
    if amp == 0.0 or not (0.0 <= t <= duration):
        return base_val
    phase = 0.5 * (1.0 - math.cos(2.0 * math.pi * t / duration))
    return base_val + amp * phase

def eval_deriv(attr: int, t: float, duration: float) -> float:
    amp = BREATH_AMP.get(attr, 0.0)
    if amp == 0.0 or duration <= 0.0 or not (0.0 <= t <= duration):
        return 0.0
    omega = 2.0 * math.pi / duration
    return amp * 0.5 * omega * math.sin(omega * t)

def f32_to_u32(v: float) -> int:
    return struct.unpack("<I", struct.pack("<f", float(v)))[0]

def main():
    if not ORIG_BUNDLE.exists():
        raise FileNotFoundError(f"Missing backup bundle: {ORIG_BUNDLE}")
    if not POSE_JSON.exists():
        raise FileNotFoundError(f"Missing exported pose JSON: {POSE_JSON}")

    data = json.loads(POSE_JSON.read_text(encoding="utf-8-sig"))
    attr_map = build_attr_map(data)
    assert len(attr_map) == 130, f"Expected 130 attrs, got {len(attr_map)}"

    env = UnityPy.load(str(ORIG_BUNDLE))
    patched = False
    for obj in env.objects:
        if obj.type.name == "AnimationClip" and obj.path_id == TARGET_CLIP_PID:
            tree = obj.read_typetree()
            assert tree.get("m_Name") == "TeamSelect_Female_idle"

            bind = tree["m_ClipBindingConstant"]["genericBindings"]
            mc = tree["m_MuscleClip"]
            duration = float(mc.get("m_StopTime", 2.5))
            clip_data = mc["m_Clip"]["data"]
            streamed = clip_data["m_StreamedClip"]
            dense = clip_data["m_DenseClip"]
            constant = clip_data["m_ConstantClip"]

            num_s = streamed["curveCount"]
            num_d = dense["m_CurveCount"]
            frames_d = dense["m_FrameCount"]

            s_data = list(streamed["data"])
            c_data = list(constant["data"])
            d_samples = np.array(dense["m_SampleArray"], dtype=np.float32).reshape((frames_d, num_d))

            deltas = mc["m_ValueArrayDelta"]

            # Verify all 130 bindings mapped
            missing = [b["attribute"] for b in bind if b["attribute"] not in attr_map]
            if missing:
                raise RuntimeError(f"Unmapped attributes: {missing}")

            # 1. Update m_ValueArrayDelta, DenseClip, ConstantClip
            for b_idx, b in enumerate(bind):
                attr = b["attribute"]
                base_val = attr_map[attr]
                if b_idx < len(deltas):
                    deltas[b_idx]["m_Start"] = base_val
                    deltas[b_idx]["m_Stop"] = base_val

                if num_s <= b_idx < num_s + num_d:
                    d_idx = b_idx - num_s
                    for f in range(frames_d):
                        t = (f / max(frames_d - 1, 1)) * duration
                        d_samples[f, d_idx] = eval_val(base_val, attr, t, duration)
                elif b_idx >= num_s + num_d:
                    c_idx = b_idx - num_s - num_d
                    if c_idx < len(c_data):
                        c_data[c_idx] = base_val

            # 2. Update StreamedClip (Group by curve, zero kp+1..3 for static, exact Hermite for breathing)
            if num_s > 0 and len(s_data) > 0:
                curve_keys: dict[int, list[tuple[float, int]]] = {}
                pos = 0
                while pos < len(s_data):
                    t_raw = struct.unpack("<f", struct.pack("<I", s_data[pos]))[0]
                    t_clamped = t_raw if (not math.isnan(t_raw) and abs(t_raw) < 1e6) else -1.0
                    num_keys = s_data[pos + 1]
                    for k in range(num_keys):
                        kp = pos + 2 + k * 5
                        c_idx = s_data[kp]
                        if c_idx < len(bind):
                            curve_keys.setdefault(c_idx, []).append((t_clamped, kp))
                    pos += 2 + num_keys * 5

                for c_idx, entries in curve_keys.items():
                    attr = bind[c_idx]["attribute"]
                    base_val = attr_map[attr]
                    amp = BREATH_AMP.get(attr, 0.0)
                    if amp == 0.0:
                        val_u32 = f32_to_u32(base_val)
                        for _, kp in entries:
                            s_data[kp + 1] = 0
                            s_data[kp + 2] = 0
                            s_data[kp + 3] = 0
                            s_data[kp + 4] = val_u32
                    else:
                        valid = [(t, kp) for (t, kp) in entries if 0.0 <= t <= duration]
                        for t, kp in entries:
                            if not (0.0 <= t <= duration):
                                s_data[kp + 1] = 0
                                s_data[kp + 2] = 0
                                s_data[kp + 3] = 0
                                s_data[kp + 4] = f32_to_u32(base_val)
                        for i, (t0, kp0) in enumerate(valid):
                            v0 = eval_val(base_val, attr, t0, duration)
                            if i + 1 < len(valid):
                                t1, _ = valid[i + 1]
                                dx = t1 - t0
                                if dx > 1e-6:
                                    v1 = eval_val(base_val, attr, t1, duration)
                                    m0 = eval_deriv(attr, t0, duration)
                                    m1 = eval_deriv(attr, t1, duration)
                                    c3 = v0
                                    c2 = m0
                                    c1 = (3.0 * (v1 - v0) - (2.0 * m0 + m1) * dx) / (dx * dx)
                                    c0 = (2.0 * (v0 - v1) + (m0 + m1) * dx) / (dx * dx * dx)
                                    s_data[kp0 + 1] = f32_to_u32(c0)
                                    s_data[kp0 + 2] = f32_to_u32(c1)
                                    s_data[kp0 + 3] = f32_to_u32(c2)
                                    s_data[kp0 + 4] = f32_to_u32(c3)
                                    continue
                            s_data[kp0 + 1] = 0
                            s_data[kp0 + 2] = 0
                            s_data[kp0 + 3] = 0
                            s_data[kp0 + 4] = f32_to_u32(v0)

            streamed["data"] = s_data
            constant["data"] = c_data
            dense["m_SampleArray"] = d_samples.flatten().tolist()
            mc["m_ValueArrayDelta"] = deltas

            # 3. Update m_StartX, m_StopX, m_LeftFootStartX, m_RightFootStartX
            rt = data["rootT"]
            rq = data["rootQ"]
            mc["m_StartX"] = {"t": {"x": rt[0], "y": rt[1], "z": rt[2]}, "q": {"x": rq[0], "y": rq[1], "z": rq[2], "w": rq[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}
            mc["m_StopX"]  = {"t": {"x": rt[0], "y": rt[1], "z": rt[2]}, "q": {"x": rq[0], "y": rq[1], "z": rq[2], "w": rq[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}

            lft = data["leftFootT"]
            lfq = data["leftFootQ"]
            rft = data["rightFootT"]
            rfq = data["rightFootQ"]
            mc["m_LeftFootStartX"]  = {"t": {"x": lft[0], "y": lft[1], "z": lft[2]}, "q": {"x": lfq[0], "y": lfq[1], "z": lfq[2], "w": lfq[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}
            mc["m_RightFootStartX"] = {"t": {"x": rft[0], "y": rft[1], "z": rft[2]}, "q": {"x": rfq[0], "y": rfq[1], "z": rfq[2], "w": rfq[3]}, "s": {"x": 1.0, "y": 1.0, "z": 1.0}}

            obj.save_typetree(tree)
            patched = True
            print(f"[+] Patched ALL 130 native customType=8 channels in Chromia TeamSelect_Female_idle (PID={TARGET_CLIP_PID})")
            print(f"    RootT={rt}, LeftFootT={lft}, RightFootT={rft}")
            break

    if not patched:
        raise RuntimeError("Target clip not found!")

    OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    out_bytes = env.file.save(packer="lz4")
    OUT_BUNDLE.write_bytes(out_bytes)
    print(f"[SUCCESS] Saved {OUT_BUNDLE} ({len(out_bytes)} bytes, LZ4 packed)")

if __name__ == "__main__":
    main()
