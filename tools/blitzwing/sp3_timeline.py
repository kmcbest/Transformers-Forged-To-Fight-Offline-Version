import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

"""
Synthesizes the complete 222-frame (7.40s @ 30fps) Blitzwing Triple-Changer SP3
timeline in Unity world coordinates, combining:
  - Interval I  (0..107f):   Windblade Robot(0..34) -> Jet(35..107)
  - Interval II (108..125f): Smooth cubic-Hermite climb, Jet->Tank swap(f=123),
                             Actor1 knockdown, smooth camera sky chase
  - Interval III(126..222f): Anchored Motormaster Truck sky-slam(mm 134..185) ->
                             Robot landing hero finish(mm 186..230)
"""

import json
from pathlib import Path
from typing import Dict, List, Tuple

import sp3_curves as M


SAMPLES_DIR = Path(r"C:\Users\Xiangli496\.gemini\antigravity\brain\cd1292c4-7b4c-4fe9-9d42-14635924d9d4\scratch\sp3_samples")


def _extract_bone_map(frame_dict: dict, offset=(0.0, 0.0, 0.0)) -> Dict[str, dict]:
    """Build bone-name -> {pos, rot, path} dict; preserves first exact path match or non-prop character_model bones."""
    out = {}
    for b in frame_dict["bones"]:
        name = b["name"]
        path = b["path"]
        # Skip sub-props' nested 'Reference'/'COG' collisions when keying primary skeleton;
        # store vehicle 'transformed/Reference/COG' under explicit keys as well.
        p = M.v_add(M.v3(b["worldPos"]), offset)
        q = M.q4_xyzw(b["worldRot"])
        if path.startswith("character_model/Reference/Hips/transformed"):
            out[f"__tform_{name}"] = {"pos": p, "rot": q, "path": path}
        if name not in out or (not path.endswith("/Reference/COG") and "mace" not in path and "cannon" not in path):
            out[name] = {"pos": p, "rot": q, "path": path}
    return out


def _blend_bone_maps(bm0: Dict[str, dict], bm1: Dict[str, dict], u: float, pos_arc_z_y_drop: float = 0.0) -> Dict[str, dict]:
    out = {}
    s = M.smoothstep(u)
    for k, v0 in bm0.items():
        if k.startswith("__"):
            continue
        v1 = bm1.get(k, v0)
        p = (
            v0["pos"][0] + s * (v1["pos"][0] - v0["pos"][0]),
            v0["pos"][1] + s * (v1["pos"][1] - v0["pos"][1]),
            v0["pos"][2] + s * (v1["pos"][2] - v0["pos"][2]),
        )
        q = M.q_slerp(v0["rot"], v1["rot"], s)
        out[k] = {"pos": p, "rot": q, "path": v0["path"]}
    return out


def _wb_jet_pose(wb0_frame: dict) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    """Extract canonical Unity (pos, rot_xyzw) for Windblade Jet COG: Right=-Z, Up=+X, Fwd=-Y."""
    cog = None
    for b in wb0_frame["bones"]:
        if b["name"] == "COG" and "transformed" in b["path"]:
            cog = b
            break
    p = M.v3(cog["worldPos"])
    q = M.q4_xyzw(cog["worldRot"])
    right = M.v_scale(M.q_rot_vec(q, (0.0, 0.0, 1.0)), -1.0)
    up = M.q_rot_vec(q, (1.0, 0.0, 0.0))
    fwd = M.v_scale(M.q_rot_vec(q, (0.0, 1.0, 0.0)), -1.0)
    rot_can = M.basis_to_q_xyzw(right, up, fwd)
    return p, rot_can


def _mm_truck_pose(mm0_frame: dict, offset=M.MM_ANCHOR_OFFSET_U) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    """Extract canonical Unity (pos, rot_xyzw) for Motormaster BodyBase: Right=+X, Up=+Z, Fwd=-Y."""
    bb = None
    for b in mm0_frame["bones"]:
        if b["name"] == "BodyBase" and "transformed" in b["path"]:
            bb = b
            break
    p = M.v_add(M.v3(bb["worldPos"]), offset)
    q = M.q4_xyzw(bb["worldRot"])
    right = M.q_rot_vec(q, (1.0, 0.0, 0.0))
    up = M.q_rot_vec(q, (0.0, 0.0, 1.0))
    fwd = M.v_scale(M.q_rot_vec(q, (0.0, 1.0, 0.0)), -1.0)
    rot_can = M.basis_to_q_xyzw(right, up, fwd)
    # Offset BB height slightly so Blitzwing Tank treads (local z=0 at mesh base) touch y=0 cleanly at slam (mm f=165..185)
    return p, rot_can


def _sample_cam_at(cam_entry: dict, t: float) -> Tuple[Tuple[float, float, float], Tuple[float, float, float], float]:
    cam_pos = (0.0, 2.0, -10.0)
    int_pos = (0.0, 2.0, 0.0)
    fov = 45.0
    for tr in cam_entry["tracks"]:
        en = tr.get("en", "")
        for pr in tr.get("props", []):
            iname = pr.get("infoName", "")
            curves = pr.get("curves", [])
            if en == "StageCamera" and iname == "localPosition" and len(curves) == 3:
                cam_pos = tuple(M.eval_unity_anim_curve(curves[k], t) for k in range(3))
            elif en == "StageCamera" and "field of view" in iname.lower() and curves:
                fov = M.eval_unity_anim_curve(curves[0], t)
            elif en == "StageCameraInterest" and iname == "localPosition" and len(curves) == 3:
                int_pos = tuple(M.eval_unity_anim_curve(curves[k], t) for k in range(3))
    return cam_pos, int_pos, fov


def synthesize_timeline(samples_dir: Path = SAMPLES_DIR) -> dict:
    wb0 = json.loads((samples_dir / "wb_actor0.json").read_text(encoding="utf-8"))
    wb0_bw = json.loads((samples_dir / "wb_actor0_bw.json").read_text(encoding="utf-8"))
    wb1_bw = json.loads((samples_dir / "wb_actor1_bw.json").read_text(encoding="utf-8"))
    mm0 = json.loads((samples_dir / "mm_actor0.json").read_text(encoding="utf-8"))
    mm0_bw = json.loads((samples_dir / "mm_actor0_bw.json").read_text(encoding="utf-8"))
    mm1_bw = json.loads((samples_dir / "mm_actor1_bw.json").read_text(encoding="utf-8"))
    cams = json.loads((samples_dir / "matinee_cameras.json").read_text(encoding="utf-8"))

    D = M.MM_ANCHOR_OFFSET_U

    # Precompute tightened Jet orbit + C1 bridge anchors
    ORBIT_CENTER = (1.5, 16.5, 0.0)
    ORBIT_SCALE = 0.65

    def _jet_frame_pose(fi: int):
        raw_p, raw_q = _wb_jet_pose(wb0["frames"][fi])
        # Compute Actor1 target Hips for aiming
        bm1 = _extract_bone_map(wb1_bw["frames"][min(fi, wb1_bw["frameCount"])])
        a1_p = bm1["Hips"]["pos"]
        if fi <= 35:
            p = raw_p
        elif fi <= 55:
            # Smooth Hermite/cosine from f=35 takeoff (-12.1,21.6,6.8) -> (-18.5,20.5,-2.5) -> tightened f=55
            p55_raw, _ = _wb_jet_pose(wb0["frames"][55])
            p55 = tuple(ORBIT_CENTER[k] + ORBIT_SCALE * (p55_raw[k] - ORBIT_CENTER[k]) for k in range(3))
            p35_raw, _ = _wb_jet_pose(wb0["frames"][35])
            u = (fi - 35) / 20.0
            s = M.smoothstep(u)
            # Midpoint pulls left-back gently without leaving screen
            mid = (-21.0, 21.5, -3.5)
            o = 1.0 - u
            p = tuple((o*o)*p35_raw[k] + (2*o*u)*mid[k] + (u*u)*p55[k] for k in range(3))
        else:
            p = tuple(ORBIT_CENTER[k] + ORBIT_SCALE * (raw_p[k] - ORBIT_CENTER[k]) for k in range(3))

        if 48 <= fi <= 102:
            # Aim jet nose (+Z) toward enemy while preserving Windblade's banked up vector
            aim = (a1_p[0], max(a1_p[1] - 0.8, 3.0), a1_p[2])
            fwd_aim = M.v_norm(M.v_sub(aim, p))
            fwd_raw = M.q_rot_vec(raw_q, (0.0, 0.0, 1.0))
            up_raw = M.q_rot_vec(raw_q, (0.0, 1.0, 0.0))
            w_aim = 1.0
            if fi < 54:
                w_aim = M.smoothstep((fi - 48) / 6.0)
            elif fi > 96:
                w_aim = 1.0 - M.smoothstep((fi - 96) / 6.0)
            fwd = M.v_norm(tuple(fwd_raw[k] * (1.0 - w_aim) + fwd_aim[k] * w_aim for k in range(3)))
            right = M.v_norm(M.v_cross(up_raw, fwd))
            up = M.v_cross(fwd, right)
            q = M.basis_to_q_xyzw(right, up, fwd)
        else:
            q = raw_q
        return p, q

    # Precompute boundary anchors for Interval II smooth Hermite bridges
    # Exit from Windblade Jet at f=104 (before Windblade's mid-robot tumble at 106..107!)
    p_j103, q_j103 = _jet_frame_pose(103)
    p_j104, q_j104 = _jet_frame_pose(104)
    # Entry into Motormaster sky flip at mm f=134 -> combined f=126
    p_m134, q_m134 = _mm_truck_pose(mm0["frames"][134], D)
    p_m135, q_m135 = _mm_truck_pose(mm0["frames"][135], D)

    N_JET_BRIDGE = (M.II_END + 1) - 104  # frames 104..126 (22 intervals)
    v_j_exit = M.v_scale(M.v_sub(p_j104, p_j103), float(N_JET_BRIDGE))
    v_m_entry = M.v_scale(M.v_sub(p_m135, p_m134), float(N_JET_BRIDGE))

    # Seamless Robot->Jet position anchor at f=35 (Blitzwing humanScale Hips -> Windblade Jet COG over 35..46)
    bm_bw35 = _extract_bone_map(wb0_bw["frames"][35])
    hips_bw35 = bm_bw35["Hips"]["pos"]
    p_j35, _ = _wb_jet_pose(wb0["frames"][35])
    delta_j35 = M.v_sub(hips_bw35, p_j35)

    # Seamless Tank->Robot anchor at mm=186 (combined f=178)
    bm_m186_bw = _extract_bone_map(mm0_bw["frames"][186], D)
    hips_m186_bw = bm_m186_bw["Hips"]["pos"]
    p_m186_bb, _ = _mm_truck_pose(mm0["frames"][186], D)
    delta_m186 = M.v_sub(hips_m186_bw, p_m186_bb)

    # Camera anchors at f=107 and mm f=134 (combined f=126)
    cam_wb106, int_wb106, _ = _sample_cam_at(cams["windblade"], 106 / M.FPS)
    cam_wb107, int_wb107, fov_wb = _sample_cam_at(cams["windblade"], 107 / M.FPS)
    cam_mm134_raw, int_mm134_raw, fov_mm = _sample_cam_at(cams["motormaster"], 134 / M.FPS)
    cam_mm135_raw, int_mm135_raw, _ = _sample_cam_at(cams["motormaster"], 135 / M.FPS)
    cam_mm134 = M.v_add(cam_mm134_raw, D)
    int_mm134 = M.v_add(int_mm134_raw, D)
    cam_mm135 = M.v_add(cam_mm135_raw, D)
    int_mm135 = M.v_add(int_mm135_raw, D)

    N_CAM_BRIDGE = (M.II_END + 1) - M.I_END  # 107..126 -> 19 intervals
    v_cam0 = M.v_scale(M.v_sub(cam_wb107, cam_wb106), float(N_CAM_BRIDGE))
    v_cam1 = M.v_scale(M.v_sub(cam_mm135, cam_mm134), float(N_CAM_BRIDGE))
    v_int0 = M.v_scale(M.v_sub(int_wb107, int_wb106), float(N_CAM_BRIDGE))
    v_int1 = M.v_scale(M.v_sub(int_mm135, int_mm134), float(N_CAM_BRIDGE))

    # Actor1 bridge endpoints
    bm_a1_107 = _extract_bone_map(wb1_bw["frames"][M.I_END])
    bm_a1_134 = _extract_bone_map(mm1_bw["frames"][M.MM_START], D)

    frames_out: List[dict] = []

    for f in range(M.TOTAL_FRAMES + 1):
        # 1. Visibility Mode
        if f < M.F_ROBOT_TO_JET:
            mode = "robot"
        elif f < M.F_JET_TO_TANK:
            mode = "jet"
        elif f < M.F_TANK_TO_ROBOT:
            mode = "tank"
        else:
            mode = "robot"

        # 2. Actor0 Robot Bones (when active or for root Hips anchor)
        if f <= M.I_END:
            f_wb = min(f, wb0_bw["frameCount"])
            a0_robot_bones = _extract_bone_map(wb0_bw["frames"][f_wb])
            a0_root_rm = M.v3(wb0_bw["frames"][f_wb]["rootPos_AnimatorStep"])
        elif f <= M.II_END:
            a0_robot_bones = None
            a0_root_rm = None
        else:
            mm_f = min(int(round(M.combined_to_mm_frame(f))), mm0_bw["frameCount"])
            a0_robot_bones = _extract_bone_map(mm0_bw["frames"][mm_f], D)
            a0_root_rm = M.v_add(M.v3(mm0_bw["frames"][mm_f]["rootPos_AnimatorStep"]), D)

        # 3. Actor0 Vehicle Pose (Jet / Tank canonical Unity (pos, rot_xyzw))
        if f < M.F_ROBOT_TO_JET:
            veh_pos, veh_rot = _jet_frame_pose(M.F_ROBOT_TO_JET)
        elif f < 104:
            veh_pos, veh_rot = _jet_frame_pose(f)
            # Smoothly blend away Blitzwing-vs-Windblade leap offset delta_j35 over f=35..46
            if f <= 46:
                blend = 1.0 - M.smoothstep((f - 35) / 11.0)
                veh_pos = M.v_add(veh_pos, M.v_scale(delta_j35, blend))
        elif f <= M.II_END:
            u = (f - 104) / float(N_JET_BRIDGE)
            veh_pos = M.hermite_vec3(p_j104, v_j_exit, p_m134, v_m_entry, u)
            # Slight dynamic aerodynamic arc boost on climb
            veh_pos = (veh_pos[0], veh_pos[1] + 2.0 * math.sin(math.pi * u), veh_pos[2]) if "math" in globals() else veh_pos
            veh_rot = M.q_slerp(q_j104, q_m134, M.smoothstep(u))
        else:
            mm_f = min(int(round(M.combined_to_mm_frame(f))), mm0["frameCount"])
            veh_pos, veh_rot = _mm_truck_pose(mm0["frames"][mm_f], D)
            # Over combined f=170..178 (mm 178..186), blend onto mm0_bw Hips(186) for seamless Tank->Robot swap
            if 170 <= f <= M.F_TANK_TO_ROBOT:
                blend = M.smoothstep((f - 170) / float(M.F_TANK_TO_ROBOT - 170))
                veh_pos = M.v_add(veh_pos, M.v_scale(delta_m186, blend))

        # 4. Actor1 Bones & Root RM
        if f <= M.I_END:
            f_wb1 = min(f, wb1_bw["frameCount"])
            a1_bones = _extract_bone_map(wb1_bw["frames"][f_wb1])
            a1_root_rm = M.v3(wb1_bw["frames"][f_wb1]["rootPos_AnimatorStep"])
        elif f <= M.II_END:
            u = (f - M.I_END) / float(M.II_END + 1 - M.I_END)
            a1_bones = _blend_bone_maps(bm_a1_107, bm_a1_134, u)
            r0 = M.v3(wb1_bw["frames"][M.I_END]["rootPos_AnimatorStep"])
            r1 = M.v_add(M.v3(mm1_bw["frames"][M.MM_START]["rootPos_AnimatorStep"]), D)
            s = M.smoothstep(u)
            a1_root_rm = tuple(r0[k] + s * (r1[k] - r0[k]) for k in range(3))
        else:
            mm_f_raw = min(int(round(M.combined_to_mm_frame(f))), mm1_bw["frameCount"])
            # Crushed visibly under Tank on impact (f=155..159 at ground y=-0.15), then drop underground
            # (f>=161 at y=-14.0, matching Motormaster SP3 mm_f=169) so opponent vanishes post-squash!
            if f < 155:
                mm_f_pose = mm_f_raw
            elif f < 157:
                mm_f_pose = 163
            else:
                mm_f_pose = 172
            a1_bones = _extract_bone_map(mm1_bw["frames"][mm_f_pose], D)
            a1_root_rm = M.v_add(M.v3(mm1_bw["frames"][mm_f_pose]["rootPos_AnimatorStep"]), D)
            if f >= 155:
                if f <= 159:
                    target_a1_y = -0.15
                elif f == 160:
                    target_a1_y = -4.5
                else:
                    target_a1_y = -14.0
                lift_y = target_a1_y - a1_root_rm[1]
                a1_root_rm = (a1_root_rm[0], target_a1_y, a1_root_rm[2])
                for b in a1_bones.values():
                    p = b["pos"]
                    b["pos"] = (p[0], p[1] + lift_y, p[2])

        # 5. StageCamera, Interest, FOV — Ref-matched framing with smooth C1 bridges
        a0_focus = a0_robot_bones["Hips"]["pos"] if (mode == "robot" and a0_robot_bones is not None) else veh_pos
        a1_focus = a1_bones["Hips"]["pos"]

        def _shot1_cam(fi: int):
            # Opening kicks (Ref Shot 1): A0 top-left (~0.35..0.44), A1 center-right (~0.56..0.64)
            u = min(1.0, max(0.0, fi / 34.0))
            s = M.smoothstep(u)
            mx = 0.40 * a0_focus[0] + 0.60 * a1_focus[0]
            if fi < 10:
                blend = M.smoothstep(fi / 10.0)
                ix = -17.0 * (1.0 - blend) + mx * blend
                iy = 4.2 * (1.0 - blend) + 5.6 * blend
            else:
                ix = mx - 0.8
                iy = 5.6 + 3.2 * M.smoothstep((fi - 10) / 24.0)
            cx = -16.0 * (1.0 - s) + (ix + 1.5) * s
            cy = 2.8 + 1.1 * s
            cz = -21.0 - 6.0 * s
            return (cx, cy, cz), (ix, iy, 0.8), 44.0

        def _shot2_cam(fi: int):
            # Bird's-eye circling (Ref Shot 2): cam high overhead looking steeply at A1 center
            u = min(1.0, max(0.0, (fi - 55) / 45.0))
            cx = -11.0 - 3.5 * u
            cy = 52.0
            cz = -30.0 + 2.5 * u
            ix = 1.5 + 0.45 * (a1_focus[0] - 1.5)
            iy = 4.5
            iz = 0.5 + 0.45 * a1_focus[2]
            return (cx, cy, cz), (ix, iy, iz), 45.0

        def _shot3_cam(fi: int):
            # Tank overhead slam (Ref Shot 3): track Tank height directly so it never clips bottom!
            cx, cy, cz = 2.5, 1.7, -14.2
            if fi <= 145:
                ix = a0_focus[0] * 0.85 + a1_focus[0] * 0.15
                iy = max(12.0, a0_focus[1] - 1.5)
                iz = a0_focus[2] * 0.85 + a1_focus[2] * 0.15
            elif fi <= 157:
                # Mirror Tank's actual drop curve cleanly down to slam impact (-5.2, 2.6, 0.3)
                u = M.smoothstep((fi - 145) / 12.0)
                w_tank = 1.0 - u
                ix = (-6.8) * w_tank + (-5.2) * u
                iy = max(2.6, a0_focus[1] * 0.75 + 1.2)
                iz = 2.2 * w_tank + 0.3 * u
            else:
                u = M.smoothstep(min(1.0, (fi - 157) / 30.0))
                cx = 2.5 + 0.6 * u
                cy = 1.7 + 0.6 * u
                cz = -14.2 - 0.8 * u
                ix, iy, iz = -5.2, 2.6 + 1.0 * u, 0.3 + 0.1 * u
            return (cx, cy, cz), (ix, iy, iz), 48.0

        if f <= 34:
            cam_p, int_p, fov = _shot1_cam(f)
        elif f < 55:
            # Smooth ascent from Shot 1 (f=34) to Bird's-Eye Shot 2 (f=55)
            u = (f - 34) / 21.0
            s = M.smoothstep(u)
            c0, i0, f0 = _shot1_cam(34)
            c1, i1, f1 = _shot2_cam(55)
            cam_p = tuple(c0[k] + s * (c1[k] - c0[k]) for k in range(3))
            # Steer interest gently through jet/a1 blend mid-ascent so Jet never leaves frame
            i_lin = tuple(i0[k] + s * (i1[k] - i0[k]) for k in range(3))
            w_jet = 0.72 * math.sin(math.pi * u)
            i_track = (0.52 * a0_focus[0] + 0.48 * a1_focus[0], 0.62 * a0_focus[1] + 0.38 * a1_focus[1], 0.5 * (a0_focus[2] + a1_focus[2]))
            int_p = tuple(i_lin[k] * (1.0 - w_jet) + i_track[k] * w_jet for k in range(3))
            fov = f0 + s * (f1 - f0) + 8.0 * math.sin(math.pi * u)
        elif f <= 100:
            cam_p, int_p, fov = _shot2_cam(f)
        elif f <= 125:
            # Smooth swoop from Bird's-Eye Shot 2 (f=100) to Tank Sky Shot 3 (f=126)
            u = (f - 100) / 26.0
            s = M.smoothstep(u)
            c0, i0, f0 = _shot2_cam(100)
            c1, i1, f1 = (-6.8, 24.0, 2.2)
            # Wait: _shot3_cam(126) targets Tank sky
            cam1, int1, fov1 = _shot3_cam(126)
            cam_p = tuple(c0[k] + s * (cam1[k] - c0[k]) for k in range(3))
            i_lin = tuple(i0[k] + s * (int1[k] - i0[k]) for k in range(3))
            w_climb = 0.6 * math.sin(math.pi * u)
            int_p = tuple(i_lin[k] * (1.0 - w_climb) + a0_focus[k] * w_climb for k in range(3))
            fov = f0 + s * (fov1 - f0)
        else:
            cam_p, int_p, fov = _shot3_cam(f)

        frames_out.append({
            "frame": f,
            "time": f / M.FPS,
            "mode": mode,
            "a0_robot_bones": a0_robot_bones,
            "a0_root_rm": a0_root_rm,
            "veh_pos": veh_pos,
            "veh_rot": veh_rot,
            "a1_bones": a1_bones,
            "a1_root_rm": a1_root_rm,
            "cam_pos": cam_p,
            "int_pos": int_p,
            "fov": fov,
        })

    return {
        "fps": M.FPS,
        "total_frames": M.TOTAL_FRAMES,
        "wb_a0_locator": M.v3(wb0_bw["locatorPos"]),
        "wb_a1_locator": M.v3(wb1_bw["locatorPos"]),
        "frames": frames_out,
    }


import math

if __name__ == "__main__":
    tl = synthesize_timeline()
    print(f"Synthesized {len(tl['frames'])} frames ({tl['total_frames']/tl['fps']:.2f}s @ {tl['fps']}fps)")
    for check_f in [0, 34, 35, 53, 54, 104, 107, 115, 123, 126, 138, 157, 177, 178, 222]:
        fr = tl["frames"][check_f]
        vp = fr["veh_pos"]
        cp = fr["cam_pos"]
        ip = fr["int_pos"]
        a1h = fr["a1_bones"]["Hips"]["pos"]
        print(f"  f={check_f:3d} [{fr['mode']:5s}] veh=({vp[0]:6.2f},{vp[1]:5.2f},{vp[2]:6.2f}) A1_Hips=({a1h[0]:6.2f},{a1h[1]:5.2f},{a1h[2]:6.2f}) cam=({cp[0]:6.2f},{cp[1]:5.2f},{cp[2]:6.2f}) int=({ip[0]:6.2f},{ip[1]:5.2f},{ip[2]:6.2f}) fov={fr['fov']:.1f}")
