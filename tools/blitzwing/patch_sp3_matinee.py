import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

"""
Phase 3C: Inject compiled SP3 AnimationClips + 7.40s (222f) Triple-Changer MatineeData
curves, mutually-exclusive 3-mesh visibility, hit events, and prop animators into
assets_redeco/blitzwing_gs.assetbundle.
"""

import copy
import json
from pathlib import Path

import UnityPy

TOOLS_BW = Path(r"E:\Agent\TFTF-blender\tools\blitzwing")
if str(TOOLS_BW) not in sys.path:
    sys.path.insert(0, str(TOOLS_BW))

import sp3_timeline as TL

SP3_CLIPS_BUNDLE = Path(r"E:\Agent\TFTF-blender\toolchain\unity_build_project\AssetBundles\bw_sp3_clips.assetbundle")
BW_BUNDLE = Path(r"E:\Agent\TFTF-blender\assets_redeco\blitzwing_gs.assetbundle")

# Native AnimationClip PathIDs inside blitzwing_gs.assetbundle
PID_CLIP_ROBOT_SP3 = -5010428262070673342        # megatron_gs_attackSpecial_03
PID_CLIP_HIT_REACTION = 4518631348663971232      # megatron_gs_attackSpecial_03_hitReaction
PID_CLIP_TANK_SP3 = -1675687069155817089         # megatron_gs_attackSpecial_03_transformed
PID_CLIP_JET_SP3_SLOT = 2172489900769684748      # repurposed unused megatron_gs_attackSpecial_03_mace

JET_AOC_PID = -4914847298671604126               # override_Blitzwing_GS_jet
ORIG_PROP_SP3_CLIP_PID = 5620803938405291589     # animator_prop_gameplay Base.SpecialAttack03

MATINEE_DATA_PID = -6557821159884267804
TR_ACTOR0_LOC_PID = 7312104377675287820
TR_ACTOR1_LOC_PID = -5961626380605623685
TR_IMPACT_CRACK_PID = -846213694164580830
TR_GROUND_CRACK_PID = 5839659373495804302


def _make_key(time_s: float, val: float, in_s: float = 0.0, out_s: float = 0.0) -> dict:
    return {
        "time": float(time_s),
        "value": float(val),
        "inSlope": float(in_s),
        "outSlope": float(out_s),
        "weightedMode": 0,
        "inWeight": 0.3333333432674408,
        "outWeight": 0.3333333432674408,
    }


def _build_smooth_keys(times: list, values: list) -> list:
    n = len(times)
    keys = []
    for i in range(n):
        if n == 1:
            slope = 0.0
        elif i == 0:
            dt = max(1e-5, times[1] - times[0])
            slope = (values[1] - values[0]) / dt
        elif i == n - 1:
            dt = max(1e-5, times[-1] - times[-2])
            slope = (values[-1] - values[-2]) / dt
        else:
            dt = max(1e-5, times[i + 1] - times[i - 1])
            slope = (values[i + 1] - values[i - 1]) / dt
        keys.append(_make_key(times[i], values[i], slope, slope))
    return keys


def _wrap_curve(keys: list, pre_inf: int = 2, post_inf: int = 2, rot_order: int = 4) -> dict:
    return {
        "serializedVersion": 2,
        "m_Curve": keys,
        "m_PreInfinity": pre_inf,
        "m_PostInfinity": post_inf,
        "m_RotationOrder": rot_order,
    }


def _make_step_keys(pairs: list) -> list:
    return [_make_key(t, v, 0.0, 0.0) for (t, v) in pairs]


def _clear_track_events(tracks: dict, idx: int):
    tracks[f"track_{idx}_econtainer_count"] = 0
    for k in [k for k in tracks if k.startswith(f"track_{idx}_econtainer_") and k != f"track_{idx}_econtainer_count"]:
        del tracks[k]


def apply_sp3_matinee(env: UnityPy.Environment, sp3_clips_path: Path = SP3_CLIPS_BUNDLE, timeline: dict = None):
    if timeline is None:
        timeline = TL.synthesize_timeline()

    obj_map = {o.path_id: o for o in env.objects}

    # 1. Load compiled clips from bw_sp3_clips.assetbundle
    src_env = UnityPy.load(str(sp3_clips_path))
    src_clips = {}
    for o in src_env.objects:
        if o.type.name == "AnimationClip":
            tt = o.read_typetree()
            src_clips[tt["m_Name"]] = tt

    clip_injections = [
        (PID_CLIP_ROBOT_SP3, "blitzwing_gs_attackSpecial_03", "megatron_gs_attackSpecial_03"),
        (PID_CLIP_HIT_REACTION, "blitzwing_gs_attackSpecial_03_hitReaction", "megatron_gs_attackSpecial_03_hitReaction"),
        (PID_CLIP_TANK_SP3, "blitzwing_gs_attackSpecial_03_transformed", "megatron_gs_attackSpecial_03_transformed"),
        (PID_CLIP_JET_SP3_SLOT, "blitzwing_gs_attackSpecial_03_jet", "blitzwing_gs_attackSpecial_03_jet"),
    ]
    for dst_pid, src_name, dst_name in clip_injections:
        if src_name not in src_clips:
            raise RuntimeError(f"Missing '{src_name}' in {sp3_clips_path}")
        if dst_pid not in obj_map:
            raise RuntimeError(f"Missing target AnimationClip PID {dst_pid} in blitzwing bundle")
        tt = copy.deepcopy(src_clips[src_name])
        tt["m_Name"] = dst_name
        obj_map[dst_pid].save_typetree(tt)
        print(f"  [SP3 Clip] Injected '{src_name}' -> PID {dst_pid} ('{dst_name}', len={tt['m_MuscleClip']['m_StopTime']:.3f}s)")

    # 2. Wire JET_AOC_PID Base.SpecialAttack03 override to PID_CLIP_JET_SP3_SLOT
    jet_aoc = obj_map[JET_AOC_PID].read_typetree()
    wired = False
    for pair in jet_aoc["m_Clips"]:
        if pair["m_OriginalClip"]["m_PathID"] == ORIG_PROP_SP3_CLIP_PID:
            pair["m_OverrideClip"] = {"m_FileID": 0, "m_PathID": PID_CLIP_JET_SP3_SLOT}
            wired = True
    if not wired:
        jet_aoc["m_Clips"].append({
            "m_OriginalClip": {"m_FileID": 5, "m_PathID": ORIG_PROP_SP3_CLIP_PID},
            "m_OverrideClip": {"m_FileID": 0, "m_PathID": PID_CLIP_JET_SP3_SLOT},
        })
    obj_map[JET_AOC_PID].save_typetree(jet_aoc)
    print(f"  [SP3 Jet AOC] Bound {ORIG_PROP_SP3_CLIP_PID} -> {PID_CLIP_JET_SP3_SLOT} on {JET_AOC_PID}")

    # 3. Align Actor0_locator, Actor1_locator & Tank Slam ground crack world positions
    a0_loc = timeline["wb_a0_locator"]
    a1_loc = timeline["wb_a1_locator"]
    for tr_pid, new_xyz, label in [
        (TR_ACTOR0_LOC_PID, a0_loc, "Actor0_locator"),
        (TR_ACTOR1_LOC_PID, a1_loc, "Actor1_locator"),
        (TR_IMPACT_CRACK_PID, (-5.2, -0.79, 0.2), "Impact_crack"),
        (TR_GROUND_CRACK_PID, (-5.2, 0.21, 0.2), "ground_crack_quad_01"),
    ]:
        if tr_pid in obj_map:
            tr = obj_map[tr_pid].read_typetree()
            tr["m_LocalPosition"] = {"x": float(new_xyz[0]), "y": float(new_xyz[1]), "z": float(new_xyz[2])}
            obj_map[tr_pid].save_typetree(tr)
            print(f"  [SP3 Locator] {label} ({tr_pid}) pos -> ({new_xyz[0]:.3f}, {new_xyz[1]:.3f}, {new_xyz[2]:.3f})")

    # 4. Patch MatineeData (PID=-6557821159884267804)
    md = obj_map[MATINEE_DATA_PID].read_typetree()
    jd = json.loads(md["jSONData"])
    tracks = jd["TRACKS"]
    tlist = md["trackList"]

    duration_s = 7.4
    fc = 222
    jd["MC"] = {"duration": duration_s, "lo": False, "fc": fc}

    frames = timeline["frames"]
    times = [fr["frame"] / 30.0 for fr in frames]
    cam_xs = [fr["cam_pos"][0] for fr in frames]
    cam_ys = [fr["cam_pos"][1] for fr in frames]
    cam_zs = [fr["cam_pos"][2] for fr in frames]
    cam_fovs = [fr["fov"] for fr in frames]
    int_xs = [fr["int_pos"][0] for fr in frames]
    int_ys = [fr["int_pos"][1] for fr in frames]
    int_zs = [fr["int_pos"][2] for fr in frames]

    # 4a. StageCamera localPosition + FOV (trackList[1])
    for prop in tlist[1]["propertyList"]:
        iname = prop["propInfo"]["infoName"]
        if iname == "localPosition":
            prop["curves"] = [
                _wrap_curve(_build_smooth_keys(times, cam_xs)),
                _wrap_curve(_build_smooth_keys(times, cam_ys)),
                _wrap_curve(_build_smooth_keys(times, cam_zs)),
            ]
        elif iname == "field of view":
            prop["curves"] = [_wrap_curve(_build_smooth_keys(times, cam_fovs))]

    # 4b. StageCameraInterest localPosition (trackList[2])
    for prop in tlist[2]["propertyList"]:
        if prop["propInfo"]["infoName"] == "localPosition":
            prop["curves"] = [
                _wrap_curve(_build_smooth_keys(times, int_xs)),
                _wrap_curve(_build_smooth_keys(times, int_ys)),
                _wrap_curve(_build_smooth_keys(times, int_zs)),
            ]

    # 4c. Actor0 / Actor1 / Tank / Mace / Jet Prop Animation Events
    tracks["track_3_econtainer_0"]["e_0"]["ed"] = duration_s
    tracks["track_3_econtainer_0"]["e_0"]["ad"]["dur"] = duration_s
    tracks["track_3_econtainer_0"]["e_0"]["ad"]["teoacn"] = "megatron_gs_attackSpecial_03"
    tracks["track_3_econtainer_0"]["e_0"]["avs"] = 7.1961

    tracks["track_4_econtainer_0"]["e_0"]["ed"] = duration_s
    tracks["track_4_econtainer_0"]["e_0"]["ad"]["dur"] = duration_s
    tracks["track_4_econtainer_0"]["e_0"]["ad"]["teoacn"] = "megatron_gs_attackSpecial_03_hitReaction"
    tracks["track_4_econtainer_0"]["e_0"]["srm"] = True
    tracks["track_4_econtainer_0"]["e_0"]["avs"] = 7.1961

    tracks["track_5_econtainer_0"]["e_0"]["ed"] = duration_s
    tracks["track_5_econtainer_0"]["e_0"]["ad"]["dur"] = duration_s
    tracks["track_5_econtainer_0"]["e_0"]["ad"]["teoacn"] = "megatron_gs_attackSpecial_03_transformed"

    # Disable unused mace animator (track 7)
    _clear_track_events(tracks, 7)

    # Add/update track_44 for Jet prop ('cannon') PlayMecanimAnimationEvent
    jet_ev = copy.deepcopy(tracks["track_5_econtainer_0"])
    jet_ev["e_0"]["ad"]["teoacn"] = "blitzwing_gs_attackSpecial_03_jet"
    tracks["track_44"] = {
        "enp": "Hips",
        "si": 44,
        "ty": "EB.Animation.Matinee.MatineeActorTrack",
        "ere": "",
        "mt": 0,
        "en": "cannon",
        "ver": 1,
        "ftr": "",
        "eid": "cannon|Hips|Reference|character_model|Megatron_GS_Leader2015|Actor0_locator",
    }
    tracks["track_44_econtainer_count"] = 1
    tracks["track_44_econtainer_0"] = jet_ev
    if len(tlist) == 44:
        tlist.append({"propertyList": []})
    else:
        tlist[44] = {"propertyList": []}
    tracks["track_count"] = len(tlist)

    # 4d. Retarget track_9 to Jet SMR ('cannon' parent) and set mutually exclusive m_Enabled schedules
    t35 = 35.0 / 30.0
    t123 = 123.0 / 30.0
    t178 = 178.0 / 30.0
    eps = 0.001
    tEnd = duration_s

    # Track 10: Robot _00 (f=0..34, 178..222)
    tlist[10]["propertyList"][0]["curves"] = [_wrap_curve(_make_step_keys([
        (0.0, 1.0), (t35 - eps, 1.0), (t35, 0.0), (t178 - eps, 0.0), (t178, 1.0), (tEnd, 1.0),
    ]))]

    # Track 9: Jet SMR under Hips/cannon (f=35..122)
    tracks["track_9"]["en"] = "cha_megatron_gs_leader2015_wpns_cannon_right"
    tracks["track_9"]["enp"] = "cannon"
    tracks["track_9"]["eid"] = "cha_megatron_gs_leader2015_wpns_cannon_right|cannon|Hips|Reference|character_model|Megatron_GS_Leader2015|Actor0_locator"
    tlist[9]["propertyList"][0]["curves"] = [_wrap_curve(_make_step_keys([
        (0.0, 0.0), (t35 - eps, 0.0), (t35, 1.0), (t123 - eps, 1.0), (t123, 0.0), (tEnd, 0.0),
    ]))]

    # Track 6: Tank _01 (f=123..177)
    tlist[6]["propertyList"][0]["curves"] = [_wrap_curve(_make_step_keys([
        (0.0, 0.0), (t123 - eps, 0.0), (t123, 1.0), (t178 - eps, 1.0), (t178, 0.0), (tEnd, 0.0),
    ]))]

    # Track 8: Mace weapon SMR -> always OFF
    tlist[8]["propertyList"][0]["curves"] = [_wrap_curve(_make_step_keys([
        (0.0, 0.0), (tEnd, 0.0),
    ]))]

    # 4e. Hit events (track_0_econtainer_2): 2 slashes + 10 Jet strafe hits + Tank Slam finisher @ 5.2333s (f=157)
    hit_spec = [
        (0.50, 0.10, False),   # f=15 Windblade slash 1
        (0.90, 0.10, False),   # f=27 Windblade slash 2
        (1.90, 0.025, False),  # Jet strafe bursts while nose aimed <=2deg at Actor1 (f=57..96)
        (2.04, 0.025, False),
        (2.18, 0.025, False),
        (2.32, 0.025, False),
        (2.46, 0.025, False),
        (2.60, 0.025, False),
        (2.74, 0.025, False),
        (2.88, 0.025, False),
        (3.02, 0.025, False),
        (3.16, 0.025, False),
        (157.0 / 30.0, 0.55, True),  # f=157 Tank Slam Knockdown Finisher
    ]
    ec_hits = {
        "eventCount": 1 + len(hit_spec),
        "e_0": {"et": 0, "tt": "MatineePlayFabricLvl3Event", "ord": False, "ed": -1},
    }
    for hi, (het, hdp, hdb) in enumerate(hit_spec, 1):
        ec_hits[f"e_{hi}"] = {"dp": hdp, "et": het, "tt": "MatineeHitEvent", "ord": False, "db": hdb, "ed": 0}
    tracks["track_0_econtainer_2"] = ec_hits

    # 4f. Clear unused mace/galvatron FX, tune Jet gunfire PS, and wire VFX tracks
    for old_fx_idx in (13, 14, 15, 16, 17, 18, 19, 20, 23, 24, 27, 29, 30, 31, 32, 33, 39, 40, 41, 42, 43):
        _clear_track_events(tracks, old_fx_idx)
        if old_fx_idx < len(tlist):
            tlist[old_fx_idx]["propertyList"] = []

    def _make_attach_ev(et: float, pn: str, tn: str, offset: tuple, rot: tuple) -> dict:
        return {
            "ord": False,
            "localAttachRotation": {"x": float(rot[0]), "y": float(rot[1]), "z": float(rot[2])},
            "ed": -1,
            "localAttachOffset": {"x": float(offset[0]), "y": float(offset[1]), "z": float(offset[2])},
            "mtn": "",
            "os": False,
            "mirrorPlane": 2,
            "at": True,
            "et": float(et),
            "reflectionNormal": {"x": 0, "y": 0, "z": 1},
            "tt": "EB.Animation.Matinee.AttachToTransformEvent",
            "tn": tn,
            "inheritParentRotation": True,
            "pn": pn,
            "ignoreRotation": False,
        }

    def _set_attached_ps(tr_idx: int, t_att: float, pn: str, tn: str, offset: tuple, rot: tuple, t_play: float, t_stop: float, clear: bool = False):
        tracks[f"track_{tr_idx}_econtainer_count"] = 1
        tracks[f"track_{tr_idx}_econtainer_0"] = {
            "eventCount": 3,
            "e_0": _make_attach_ev(t_att, pn, tn, offset, rot),
            "e_1": {"et": float(t_play), "ord": False, "tt": "EB.Animation.Matinee.PlayParticleSystemEvent", "pm": "", "sim": True, "restart": False, "ed": -1},
            "e_2": {"et": float(t_stop), "ord": False, "tt": "EB.Animation.Matinee.StopParticleSystemEvent", "pm": "", "eo": True, "cl": clear, "ed": -1},
        }

    def _set_attached_trail(tr_idx: int, t_att: float, pn: str, tn: str, offset: tuple, rot: tuple, t_play: float, dur: float):
        tracks[f"track_{tr_idx}_econtainer_count"] = 1
        tracks[f"track_{tr_idx}_econtainer_0"] = {
            "eventCount": 2,
            "e_0": _make_attach_ev(t_att, pn, tn, offset, rot),
            "e_1": {"et": float(t_play), "tt": "PlayTrailRenderer", "ord": True, "ebld": True, "ed": float(dur)},
        }

    # Tune fx_p_galvatron_blast_streaks (PS 7196867372041124456) -> crisp glowing World-space tracer bolts
    BLAST_STREAKS_PS_PID = 7196867372041124456
    BLAST_STREAKS_PSR_PID = -6069629422623588848
    if BLAST_STREAKS_PS_PID in obj_map:
        ps = obj_map[BLAST_STREAKS_PS_PID].read_typetree()
        ps["moveWithTransform"] = 1  # World simulation space so fired bullets traverse space cleanly
        ps["ClampVelocityModule"]["enabled"] = False  # Previously capped speed at 1.0 m/s!
        ps["SizeModule"]["enabled"] = False
        ps["ColorModule"]["enabled"] = False
        ps["ShapeModule"]["type"] = 4  # Cone
        ps["ShapeModule"]["angle"] = 3.0
        ps["ShapeModule"]["radius"]["value"] = 0.25
        ps["ShapeModule"]["m_Rotation"] = {"x": 0.0, "y": 0.0, "z": 0.0}
        ps["InitialModule"]["startSpeed"]["minMaxState"] = 0
        ps["InitialModule"]["startSpeed"]["scalar"] = 72.0
        ps["InitialModule"]["startLifetime"]["minMaxState"] = 0
        ps["InitialModule"]["startLifetime"]["scalar"] = 0.28
        ps["InitialModule"]["startSize"]["minMaxState"] = 0
        ps["InitialModule"]["startSize"]["scalar"] = 0.30
        bullet_col = {"r": 1.0, "g": 0.92, "b": 0.45, "a": 1.0}
        sc = ps["InitialModule"]["startColor"]
        sc["minMaxState"] = 0
        sc["minColor"] = dict(bullet_col)
        sc["maxColor"] = dict(bullet_col)
        for gname in ("minGradient", "maxGradient"):
            sc[gname]["key0"] = dict(bullet_col)
            sc[gname]["key1"] = dict(bullet_col)
        ps["EmissionModule"]["rateOverTime"]["minMaxState"] = 0
        ps["EmissionModule"]["rateOverTime"]["scalar"] = 24.0
        obj_map[BLAST_STREAKS_PS_PID].save_typetree(ps)
    if BLAST_STREAKS_PSR_PID in obj_map:
        psr = obj_map[BLAST_STREAKS_PSR_PID].read_typetree()
        psr["m_VelocityScale"] = -0.028
        psr["m_LengthScale"] = -1.5
        obj_map[BLAST_STREAKS_PSR_PID].save_typetree(psr)

    # Jet wingtip contrails (COG -Y is forward, so +Y=2.2 is aft, +/-Z=3.5 are wingtips) + Robot Kick trail
    _set_attached_trail(15, 1.15, "cannon", "COG", (0.0, 2.2, 3.5), (0.0, 0.0, 0.0), 1.17, 2.43)
    _set_attached_trail(17, 1.15, "cannon", "COG", (0.0, 2.2, -3.5), (0.0, 0.0, 0.0), 1.17, 2.43)
    _set_attached_trail(16, 0.15, "Actor0_locator", "LeftFoot", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 0.20, 0.90)

    # Jet nose gunfire tracers (local +Z mapped to COG -Y = Jet forward via Euler X=90)
    # Note: Track[41] fx_p_galvatron_blast_discharge intentionally left cleared (its 4m sphere caused radial purple speed-lines around Jet)
    _set_attached_ps(39, 1.60, "cannon", "COG", (0.0, -3.5, 0.0), (90.0, 0.0, 0.0), 1.83, 3.18)

    # Victim bullet-impact sparks & smoke while Jet strafes (1.88..3.25s)
    _set_attached_ps(32, 1.80, "Actor1_locator", "Hips", (0.0, 0.0, 0.0), (0.0, 0.0, 0.0), 1.88, 3.25)
    _set_attached_ps(33, 1.80, "Actor1_locator", "Hips", (0.3, 0.5, 0.0), (0.0, 180.0, 0.0), 1.88, 3.25)
    _set_attached_ps(23, 1.80, "Actor1_locator", "Reference", (0.0, 0.8, 0.0), (0.0, 0.0, 0.0), 1.88, 3.25)
    _set_attached_ps(31, 1.80, "Actor1_locator", "Reference", (0.0, 0.5, 0.0), (0.0, 0.0, 0.0), 1.88, 3.30)

    # Track 11: fx_p_hit_large_matinee_01 -> hit1 (0.50s) & Tank Slam (5.2333s)
    tracks["track_11_econtainer_count"] = 1
    tracks["track_11_econtainer_0"] = {
        "eventCount": 3,
        "e_0": {"et": 0.48, "ord": False, "tt": "EB.Animation.Matinee.PlayParticleSystemEvent", "pm": "", "sim": True, "restart": False, "ed": -1},
        "e_1": {"et": 1.15, "ord": False, "tt": "EB.Animation.Matinee.StopParticleSystemEvent", "pm": "", "eo": True, "cl": False, "ed": -1},
        "e_2": {"et": 5.23, "ord": False, "tt": "EB.Animation.Matinee.PlayParticleSystemEvent", "pm": "", "sim": True, "restart": False, "ed": -1},
    }
    for prop in tlist[11]["propertyList"]:
        if prop["propInfo"]["infoName"] == "localPosition":
            prop["curves"] = [
                _wrap_curve(_make_step_keys([(0.48, -9.0), (5.20, -4.9)])),
                _wrap_curve(_make_step_keys([(0.48, 6.2), (5.20, 1.2)])),
                _wrap_curve(_make_step_keys([(0.48, 1.2), (5.20, -0.8)])),
            ]
        elif prop["propInfo"]["infoName"] == "localRotation":
            prop["curves"] = [
                _wrap_curve(_make_step_keys([(0.48, 0.0), (5.20, 0.0)])),
                _wrap_curve(_make_step_keys([(0.48, 0.0), (5.20, 0.0)])),
                _wrap_curve(_make_step_keys([(0.48, 0.0), (5.20, 0.0)])),
            ]

    # Track 12: fx_p_hit_large_matinee_02 -> hit2 (0.90s)
    tracks["track_12_econtainer_count"] = 1
    tracks["track_12_econtainer_0"] = {
        "eventCount": 2,
        "e_0": {"et": 0.88, "ord": False, "tt": "EB.Animation.Matinee.PlayParticleSystemEvent", "pm": "", "sim": True, "restart": False, "ed": -1},
        "e_1": {"et": 1.40, "ord": False, "tt": "EB.Animation.Matinee.StopParticleSystemEvent", "pm": "", "eo": True, "cl": False, "ed": -1},
    }
    for prop in tlist[12]["propertyList"]:
        if prop["propInfo"]["infoName"] == "localPosition":
            prop["curves"] = [
                _wrap_curve(_make_step_keys([(0.88, 0.8), (1.40, 0.8)])),
                _wrap_curve(_make_step_keys([(0.88, 5.3), (1.40, 5.3)])),
                _wrap_curve(_make_step_keys([(0.88, 0.2), (1.40, 0.2)])),
            ]
        elif prop["propInfo"]["infoName"] == "localRotation":
            prop["curves"] = [_wrap_curve(_make_step_keys([(0.88, 0.0), (1.40, 0.0)])) for _ in range(3)]

    # Track 21 & 22: Impact_crack & ground_crack_quad_01 on @ Tank Slam f=157 (5.2333s)
    t_slam_pre = 156.0 / 30.0
    t_slam = 157.0 / 30.0
    for tr_idx in (21, 22):
        tlist[tr_idx]["propertyList"][0]["curves"] = [_wrap_curve(_make_step_keys([
            (0.0, 0.0), (t_slam_pre, 0.0), (t_slam, 1.0), (tEnd, 1.0),
        ]))]

    # Track 28: fx_p_jump_dust -> Jet takeoff @ f=35 (1.1667s)
    tracks["track_28_econtainer_0"]["e_0"]["et"] = 1.17

    # Tracks 34, 35, 36: RBD sparks -> f=15 (0.50s), f=27 (0.90s), f=157 (5.23s)
    tracks["track_35_econtainer_0"]["e_0"]["et"] = 0.50
    tracks["track_36_econtainer_0"]["e_0"]["et"] = 0.90
    tracks["track_34_econtainer_0"]["e_0"]["et"] = 5.23

    # Tracks 37, 38: Hit lights -> 0.50s & 5.23s
    tracks["track_37_econtainer_0"]["e_0"]["et"] = 0.48
    tracks["track_38_econtainer_0"]["e_0"]["et"] = 5.20

    # Track 25 & 26: POST_FX & Special_POST_FX bounded cleanly within 0..7.35s
    t_fade_start = 7.10
    t_fade_end = 7.35
    for prop in tlist[25]["propertyList"]:
        iname = prop["propInfo"]["infoName"]
        if iname in ("Vignette_Mix", "Bloom_Mix"):
            prop["curves"] = [_wrap_curve(_make_step_keys([(0.0, 0.0), (0.167, 1.0), (t_fade_start, 1.0), (t_fade_end, 0.0)]))]
        elif iname == "Bloom_Ramp":
            prop["curves"] = [_wrap_curve(_make_step_keys([
                (0.0, 2.0), (0.45, 2.0), (0.50, 1.5), (0.56, 2.0),
                (0.85, 2.0), (0.90, 1.5), (0.96, 2.0),
                (5.18, 2.0), (5.23, 1.3), (5.35, 2.0), (tEnd, 2.0),
            ]))]
        elif iname == "ColorTint_Mix":
            prop["curves"] = [_wrap_curve(_make_step_keys([
                (0.0, 0.0), (0.45, 0.0), (0.50, 1.0), (0.56, 0.0),
                (0.85, 0.0), (0.90, 1.0), (0.96, 0.0),
                (5.18, 0.0), (5.23, 1.0), (5.35, 0.0), (tEnd, 0.0),
            ]))]
    for prop in tlist[26]["propertyList"]:
        if prop["propInfo"]["infoName"] == "ColorTint_Mix":
            prop["curves"] = [_wrap_curve(_make_step_keys([(0.0, 0.0), (0.167, 1.0), (t_fade_start, 1.0), (t_fade_end, 0.0)]))]

    md["jSONData"] = json.dumps(jd, separators=(",", ":"))
    obj_map[MATINEE_DATA_PID].save_typetree(md)
    print(f"  [SP3 MatineeData] Patched {MATINEE_DATA_PID}: duration={duration_s}s ({fc}f), {len(tlist)} tracks, {len(hit_spec)} HitEvents (sum_dp={sum(x[1] for x in hit_spec):.2f})")


def main():
    print(f"[*] Loading {BW_BUNDLE} ...")
    env = UnityPy.load(str(BW_BUNDLE))
    apply_sp3_matinee(env)
    BW_BUNDLE.write_bytes(env.file.save(packer="lz4"))
    size_mb = BW_BUNDLE.stat().st_size / (1024 * 1024)
    print(f"[✓] Saved patched {BW_BUNDLE} ({size_mb:.2f} MB, packer='lz4')")


if __name__ == "__main__":
    main()
