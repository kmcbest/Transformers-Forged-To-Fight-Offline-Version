import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

"""Exports Unity-space target transforms per frame for CompileSp3Clips.cs."""

import json
from pathlib import Path

TOOLS_BW = Path(r"E:\Agent\TFTF-blender\tools\blitzwing")
if str(TOOLS_BW) not in sys.path:
    sys.path.insert(0, str(TOOLS_BW))

import sp3_curves as M
import sp3_timeline as TL

OUT = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\cd1292c4-7b4c-4fe9-9d42-14635924d9d4\scratch\sp3_vehicle_targets.json")


def v3d(t):
    return {"x": float(t[0]), "y": float(t[1]), "z": float(t[2])}


def q4d(q):
    return {"x": float(q[0]), "y": float(q[1]), "z": float(q[2]), "w": float(q[3])}


def main():
    tl = TL.synthesize_timeline()
    frames = tl["frames"]
    out_frames = []
    for fr in frames:
        vp = fr["veh_pos"]
        vq = fr["veh_rot"]
        up = M.q_rot_vec(vq, (0.0, 1.0, 0.0))
        fwd = M.q_rot_vec(vq, (0.0, 0.0, 1.0))

        # Tank mesh treads already sit at local Y=0.00 in COG space (Motormaster BodyBase is near y=0 at slam),
        # so only apply a tiny +0.06m Up bias (removing stale +1.199m lift that left Tank floating above ground).
        tank_pos = M.v_add(vp, M.v_scale(up, 0.06))
        jet_pos = M.v_add(M.v_add(vp, M.v_scale(up, -1.65)), M.v_scale(fwd, -1.0))

        a0_hips = fr["a0_robot_bones"]["Hips"]["pos"] if fr["a0_robot_bones"] is not None else vp
        a1_hips = fr["a1_bones"]["Hips"]["pos"]
        out_frames.append({
            "frame": fr["frame"],
            "time": fr["time"],
            "tankPos": v3d(tank_pos),
            "jetPos": v3d(jet_pos),
            "vehRot": q4d(vq),
            "a0Hips": v3d(a0_hips),
            "a1Hips": v3d(a1_hips),
        })

    payload = {
        "fps": tl["fps"],
        "totalFrames": tl["total_frames"],
        "a0LocatorPos": v3d(tl["wb_a0_locator"]),
        "a1LocatorPos": v3d(tl["wb_a1_locator"]),
        "frames": out_frames,
    }
    OUT.write_text(json.dumps(payload), encoding="utf-8")
    print(f"Wrote {OUT} ({len(out_frames)} frames)")


if __name__ == "__main__":
    main()
