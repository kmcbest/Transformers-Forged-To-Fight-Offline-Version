#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
validate_port_gates.py
Machine-enforced quality & self-correction gate validator for TFTF 3D character porting.
Run after each pipeline stage so axis flips, missing UV remaps, broken RAOE channels,
dropped weights, or Unity 5.6 bundle corruption fail fast with exact remediation hints.
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import argparse
import os
import struct
import subprocess
import tempfile
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image
import UnityPy

ROOT = Path(r"E:\Agent\TFTF-blender")
BLENDER_EXE = ROOT / "toolchain" / "blender" / "blender.exe"


def fail(code: str, msg: str, fix: str):
    print(f"\n[FAIL:{code}] {msg}")
    print(f"  [SELF-FIX] {fix}\n")
    sys.exit(1)


def parse_unity_mesh_streams(mesh_tt: dict):
    vd = mesh_tt["m_VertexData"]
    vc = int(vd["m_VertexCount"])
    buf = bytes(vd["m_DataSize"])
    chans = vd["m_Channels"]

    def elem_bytes(fmt: int) -> int:
        return {0: 4, 1: 2, 2: 1, 3: 1, 6: 1, 10: 2, 11: 4}.get(fmt, 4)

    streams = sorted(set(c["stream"] for c in chans if c["dimension"] > 0))
    stream_info = {}
    cursor = 0
    for st in streams:
        st_ch = [c for c in chans if c["dimension"] > 0 and c["stream"] == st]
        min_stride = max(c["offset"] + c["dimension"] * elem_bytes(c["format"]) for c in st_ch)
        # Unity 2020/5.6 Stream 2 with skin weights + indices uses 32 bytes (4f + 4u32/padded) or min_stride
        if st == streams[-1] and vc > 0:
            rem = len(buf) - cursor
            actual_stride = rem // vc
            stride = actual_stride if actual_stride >= min_stride else min_stride
        else:
            stride = min_stride
        stream_info[st] = (cursor, stride)
        cursor += ((vc * stride + 15) & ~15)

    # Extract Positions (ch 0), UVs (ch 4), Weights (ch 12), BoneIndices (ch 13)
    off0, st0 = stream_info[0]
    pts = np.zeros((vc, 3), dtype=np.float32)
    for i in range(vc):
        pts[i] = struct.unpack_from("<3f", buf, off0 + i * st0)

    uvs = None
    if len(chans) > 4 and chans[4]["dimension"] >= 2 and chans[4]["stream"] in stream_info:
        c4 = chans[4]
        off4, st4 = stream_info[c4["stream"]]
        uvs = np.zeros((vc, 2), dtype=np.float32)
        for i in range(vc):
            uvs[i] = struct.unpack_from("<2f", buf, off4 + i * st4 + c4["offset"])

    ws = None
    bi = None
    if len(chans) > 13 and chans[13]["dimension"] > 0 and chans[13]["stream"] in stream_info:
        c13 = chans[13]
        off_s, st_s = stream_info[c13["stream"]]
        bi = np.zeros((vc, 4), dtype=np.int32)
        if chans[12]["dimension"] == 4:
            ws = np.zeros((vc, 4), dtype=np.float32)
            for i in range(vc):
                ws[i] = struct.unpack_from("<4f", buf, off_s + i * st_s + chans[12]["offset"])
                raw_b = struct.unpack_from("<4H" if c13["format"] == 10 else "<4I", buf, off_s + i * st_s + c13["offset"])
                bi[i] = raw_b
        else:
            # Rigid single-bone mesh (e.g. megatron _01)
            ws = np.zeros((vc, 4), dtype=np.float32)
            ws[:, 0] = 1.0
            for i in range(vc):
                b0 = struct.unpack_from("<H" if c13["format"] == 10 else "<I", buf, off_s + i * st_s + c13["offset"])[0]
                bi[i, 0] = b0

    return pts, uvs, ws, bi


def validate_tex_stage(args):
    tex_dir = Path(args.tex_dir)
    if not tex_dir.is_dir():
        fail("TEX_DIR", f"Texture directory missing: {tex_dir}", "Run texture atlas generator first.")

    for prefix in args.prefixes:
        print(f"=== [Gate 1: TEX] Validating '{prefix}' in {tex_dir} ===")
        req_files = [
            f"{prefix}_Diffuse.png",
            f"{prefix}_Normal.png",
            f"{prefix}_Normal_unity.png",
            f"{prefix}_RAOE.png",
            f"{prefix}_Emission.png",
        ]
        for rf in req_files:
            p = tex_dir / rf
            if not p.is_file():
                fail("TEX_MISSING", f"Missing required texture: {p}", "See Pipeline §4.4 & §8.5: output Diffuse, _Normal (NM.B metallic), _Normal_unity, RGB RAOE, and _Emission.")

        im_d = Image.open(tex_dir / f"{prefix}_Diffuse.png")
        im_r = Image.open(tex_dir / f"{prefix}_RAOE.png")
        im_n_kabam = Image.open(tex_dir / f"{prefix}_Normal.png")
        im_n_unity = Image.open(tex_dir / f"{prefix}_Normal_unity.png")

        if im_r.mode != "RGB":
            fail("RAOE_NOT_RGB", f"{prefix}_RAOE.png has mode='{im_r.mode}', MUST be strict 3-channel 'RGB'!", "See Pipeline §11.9: Never save RAOE as RGBA (Alpha gets dropped in .convert('RGB'), erasing all Emissive!). Pack R=Roughness, G=AO, B=Emissive directly.")

        raoe = np.array(im_r, dtype=np.float32)
        r_mean = raoe[:, :, 0].mean()
        em_pct = (raoe[:, :, 2] > 20).mean() * 100.0
        if not (130.0 <= r_mean <= 235.0):
            fail("RAOE_ROUGH_RANGE", f"{prefix}_RAOE Roughness (R) mean={r_mean:.1f} out of [130, 235].", "Set painted armor roughness to ~185-210 to avoid greasy mirror shine (§8.5).")
        if not (0.05 <= em_pct <= 20.0):
            fail("RAOE_EM_PCT", f"{prefix}_RAOE Emissive (B>20) pixels={em_pct:.2f}% (must be 0.05%..20%).", "Ensure B channel holds eye/light emissive mask ONLY and non-emissive armor is strictly 0 (§11.9).")

        nk = np.array(im_n_kabam.convert("RGB"), dtype=np.float32)
        nu = np.array(im_n_unity.convert("RGB"), dtype=np.float32)
        if nk[:, :, 2].mean() > 195.0:
            fail("NM_BLUE_MISSING", f"{prefix}_Normal.png Blue mean={nk[:,:,2].mean():.1f} > 195 (looks like raw Nz=255 instead of Kabam Metallic Mask!).", "See Pipeline §8.5: Kabam _METALLIC_TEX reads NM.B as metallic! Painted armor should be 0..40, dark metal 95..140.")
        if nu[:, :, 2].mean() < 200.0:
            fail("NM_UNITY_BAD", f"{prefix}_Normal_unity.png Blue mean={nu[:,:,2].mean():.1f} < 200 (Unity Standard needs Nz~255).", "Keep standard OpenGL (Nx, Ny, Nz) in *_Normal_unity.png for Unity Editor previews.")

        print(f"  [PASS] {prefix}: size={im_d.size}, RAOE=RGB (RoughMean={r_mean:.1f}, Em={em_pct:.2f}%), NM.B Mean={nk[:,:,2].mean():.1f}")


def validate_fbx_stage(args):
    print(f"=== [Gate 2: FBX] Validating {args.fbx} ===")
    assert BLENDER_EXE.is_file(), f"Missing Blender: {BLENDER_EXE}"
    fbx_paths = [Path(args.fbx)]
    if args.tank_fbx:
        fbx_paths.append(Path(args.tank_fbx))

    helper = """
import sys, math
import bpy
fbx_path = sys.argv[-1]
is_tank = ("tank" in fbx_path.lower() or "vh" in fbx_path.lower())
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx_path)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']
arms = [o for o in bpy.data.objects if o.type == 'ARMATURE']
assert meshes, f"NO MESH in {fbx_path}"
m = meshes[0]
uvl = m.data.uv_layers.active
assert uvl, "Missing UV layer!"
us = [d.uv.x for d in uvl.data]
vs = [d.uv.y for d in uvl.data]
assert all(math.isfinite(x) for x in us + vs), "NaN/Inf in UVs!"
if min(us) < -0.05 or max(us) > 1.05 or min(vs) < -0.05 or max(vs) > 1.05:
    raise RuntimeError(f"FAIL_UV_RANGE: U=[{min(us):.3f},{max(us):.3f}] V=[{min(vs):.3f},{max(vs):.3f}] -> UVs were NOT cleanly remapped into [0,1] atlas!")
torn = 0
for p in m.data.polygons:
    pu = [uvl.data[li].uv.x for li in p.loop_indices]
    pv = [uvl.data[li].uv.y for li in p.loop_indices]
    if max(pu) - min(pu) > 0.70 or max(pv) - min(pv) > 0.70:
        torn += 1
if torn > 0:
    raise RuntimeError(f"FAIL_UV_TEAR: {torn} polygons span >0.70 UV (caused by naive uv % 1.0 wrapping across seam)!")
zero_w = sum(1 for v in m.data.vertices if sum(g.weight for g in v.groups) < 1e-4)
if zero_w > 0:
    raise RuntimeError(f"FAIL_ZERO_WEIGHT: {zero_w} vertices have zero bone weights!")
zs = [(m.matrix_world @ v.co).z for v in m.data.vertices]
if min(zs) < -0.25:
    raise RuntimeError(f"FAIL_GROUND: min Z={min(zs):.3f} < -0.25 (not grounded at Z=0!)")
if not is_tank and arms:
    arm = arms[0]
    vg_map = {vg.name: vg.index for vg in m.vertex_groups}
    for bname, want_pos_x in (("LeftArm", True), ("RightArm", False), ("LeftHand", True)):
        if bname in vg_map:
            idx = vg_map[bname]
            pts = [m.matrix_world @ v.co for v in m.data.vertices if any(g.group == idx and g.weight > 0.4 for g in v.groups)]
            if pts:
                mx = sum(p.x for p in pts) / len(pts)
                if (want_pos_x and mx <= 0.5) or (not want_pos_x and mx >= -0.5):
                    raise RuntimeError(f"FAIL_BLENDER_AXIS: {bname} verts mean X={mx:.2f} (In Blender Z-up, Left MUST be +X, Right MUST be -X!)")
print(f"[PASS] FBX verified: {m.name} verts={len(m.data.vertices)} U=[{min(us):.3f},{max(us):.3f}] V=[{min(vs):.3f},{max(vs):.3f}] Z=[{min(zs):.3f},{max(zs):.3f}] tornUV={torn} zeroW={zero_w}")
"""
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(helper)
        tf_path = tf.name
    try:
        for fp in fbx_paths:
            res = subprocess.run([str(BLENDER_EXE), "-b", "-P", tf_path, "--", str(fp)], capture_output=True, text=True, encoding="utf-8", errors="replace")
            if res.returncode != 0 or "Error:" in res.stdout or "FAIL_" in res.stdout:
                fail("FBX_CHECK", f"FBX gate failed for {fp}:\n{res.stdout}\n{res.stderr}", "Check R_z(-90) axis orientation, clean polygon UV shift+clamp (NO % 1.0), and zero-weight audit (§4.3, §4.4, §11.3).")
            for line in res.stdout.splitlines():
                if "[PASS]" in line:
                    print(" ", line)
    finally:
        os.unlink(tf_path)


def validate_mesh_bundle(mesh_bundle_path: Path, donor_bundle_path: Path, robot_name: str, veh_name: str = None):
    print(f"=== [Gate 3: UNITY MESH] Validating {mesh_bundle_path.name} vs {donor_bundle_path.name} ===")
    env_m = UnityPy.load(str(mesh_bundle_path))
    env_d = UnityPy.load(str(donor_bundle_path))

    grafted = {}
    for o in env_m.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            grafted[tt["m_Name"]] = tt

    if robot_name not in grafted:
        fail("MESH_MISSING", f"Robot mesh '{robot_name}' not in {mesh_bundle_path}", "Rebuild brawl_mesh.assetbundle.")

    # Find donor robot SMR + Avatar TOS for bone coordinates
    donor_meshes = {}
    donor_avatars = {}
    for o in env_d.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            donor_meshes[tt["m_Name"]] = tt
        elif o.type.name == "Avatar":
            tt = o.read_typetree()
            donor_avatars[tt["m_Name"]] = dict(tt.get("m_TOS", []))

    # Match donor robot mesh (ends with _00)
    d_r_name = next((k for k in donor_meshes if k.endswith("_00") and "wpns" not in k.lower()), None)
    d_r_tt = donor_meshes[d_r_name]
    av_tos = next(iter(donor_avatars.values()), {})
    bone_names = [av_tos.get(h, f"h_{h}").split("/")[-1] for h in d_r_tt["m_BoneNameHashes"]]

    r_tt = grafted[robot_name]
    pts, uvs, ws, bi = parse_unity_mesh_streams(r_tt)
    if len(r_tt["m_BindPose"]) != len(d_r_tt["m_BindPose"]):
        fail("BONE_COUNT", f"{robot_name} bindposes={len(r_tt['m_BindPose'])} != donor={len(d_r_tt['m_BindPose'])}", "Must copy donor bindposes cleanly.")
    if pts[:, 1].max() < 8.5 or pts[:, 1].min() < -0.35 or pts[:, 1].min() > 0.35:
        fail("ROBOT_HEIGHT", f"Robot Unity Y=[{pts[:,1].min():.2f}, {pts[:,1].max():.2f}] abnormal!", "Ensure Y is Up [0, ~11..12.5m].")
    if uvs is not None and (uvs.min() < -0.05 or uvs.max() > 1.05):
        fail("ROBOT_UV_RANGE", f"Robot UV out of [0,1]: U=[{uvs[:,0].min():.3f},{uvs[:,0].max():.3f}] V=[{uvs[:,1].min():.3f},{uvs[:,1].max():.3f}]", "Atlas UV remapping missing in FBX export!")
    if ws is not None:
        wsum = ws.sum(axis=1)
        bad_w = int(((wsum < 0.98) | (wsum > 1.02)).sum())
        if bad_w > 0:
            fail("ROBOT_WEIGHTS", f"{bad_w} vertices have weight sum != 1.0!", "Normalize all vertex weights before exporting.")

    # CRITICAL §11.3 SIGN CHECK: Left/Right limbs must NEVER cross X=0!
    for check_b in ("LeftArm", "RightArm", "LeftForeArm", "RightForeArm", "LeftUpLeg", "RightUpLeg"):
        if check_b not in bone_names:
            continue
        bidx = bone_names.index(check_b)
        bp = d_r_tt["m_BindPose"][bidx]
        inv = np.linalg.inv(np.array([
            [bp["e00"], bp["e01"], bp["e02"], bp["e03"]],
            [bp["e10"], bp["e11"], bp["e12"], bp["e13"]],
            [bp["e20"], bp["e21"], bp["e22"], bp["e23"]],
            [bp["e30"], bp["e31"], bp["e32"], bp["e33"]],
        ]))
        donor_bx = float(inv[0, 3])
        mask = (bi[:, 0] == bidx) & (ws[:, 0] > 0.4)
        if mask.sum() > 5 and abs(donor_bx) > 0.4:
            vx = float(pts[mask, 0].mean())
            if vx * donor_bx < 0:
                fail("X_AXIS_INVERTED", f"CROSS-BODY MIRROR DETECTED on {check_b}: mesh verts mean X={vx:+.2f} while donor bone X={donor_bx:+.2f}!", "See Pipeline §11.3! You flipped X an odd number of times between Blender and Unity. Use BuildTarnInspectionScene's DetectAxisSpec!")
            if abs(vx - donor_bx) > 1.5:
                fail("LIMB_OFFSET_TOO_LARGE", f"{check_b} verts X={vx:+.2f} deviate >1.5m from donor bone X={donor_bx:+.2f}!", "Pose arms/legs cleanly via pose_segment_world to donor m_BindPose before baking!")
    print(f"  [PASS] Robot Mesh '{robot_name}': verts={len(pts)}, Y=[{pts[:,1].min():.2f},{pts[:,1].max():.2f}], Left/Right X-parity & UVs 100% aligned!")

    if veh_name and veh_name in grafted:
        v_tt = grafted[veh_name]
        vp, vuv, vws, vbi = parse_unity_mesh_streams(v_tt)
        vx_span = float(np.ptp(vp[:, 0]))
        vy_span = float(np.ptp(vp[:, 1]))
        vz_span = float(np.ptp(vp[:, 2]))
        if vz_span <= vy_span * 1.1:
            fail("TANK_VERTICAL", f"Vehicle mesh '{veh_name}' is standing VERTICAL! size=({vx_span:.2f}, {vy_span:.2f}, {vz_span:.2f})", "Unity Y MUST be height (~3-4m) and Z MUST be length (~8-10m)! Fix zIsHeight in C#.")
        if vuv is not None and (vuv.min() < -0.05 or vuv.max() > 1.05):
            fail("VEH_UV_RANGE", f"Vehicle UV out of [0,1]: [{vuv.min():.3f}, {vuv.max():.3f}]", "Remap & clamp vehicle UVs in Blender.")
        if vws is not None:
            bad_vw = int((vws.sum(axis=1) < 0.98).sum())
            if bad_vw > 0:
                fail("VEH_WEIGHTS", f"{bad_vw} vehicle vertices have weight sum < 0.98!", "Bind 100% of vehicle vertices to steady root bone (e.g. COG) cleanly.")
        print(f"  [PASS] Vehicle Mesh '{veh_name}': verts={len(vp)}, size=({vx_span:.2f}, {vy_span:.2f}, {vz_span:.2f}) horizontal & UVs clean!")


def validate_final_bundle(args):
    bundle_path = Path(args.bundle)
    donor_path = Path(args.donor)
    bot_id = args.bot
    print(f"=== [Gate 4: FINAL BUNDLE] Validating {bundle_path} for '{bot_id}' ===")
    env = UnityPy.load(str(bundle_path))
    sf = list(env.assets)[0]

    # 1. Container & Preload Closure
    ab = next(o for o in sf.objects.values() if o.type.name == "AssetBundle").read_typetree()
    if bot_id not in ab.get("m_AssetBundleName", "").lower():
        fail("AB_NAME", f"m_AssetBundleName '{ab.get('m_AssetBundleName')}' does not contain '{bot_id}'", "Rename AssetBundle name per §4.7 Rule 1.")
    for cname, cinfo in ab.get("m_Container", []):
        if bot_id not in cname.lower():
            fail("CONTAINER_KEY", f"Unrenamed m_Container entry '{cname}'!", "Replace donor bot id with new bot_id per §4.7 Rule 1.")

    # 2. Check Stream 2 & weights on ALL Meshes inside final bundle
    env_d = UnityPy.load(str(donor_path))
    d_mesh_bps = {}
    for o in env_d.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            d_mesh_bps[tt["m_Name"]] = len(tt["m_BindPose"])

    # Collect active character materials referenced by SMRs (ignore unused donor weapon materials)
    active_mat_pids = set()
    for o in env.objects:
        if o.type.name == "SkinnedMeshRenderer":
            smr_tt = o.read_typetree()
            for mp in smr_tt.get("m_Materials", []):
                if mp.get("m_PathID"):
                    active_mat_pids.add(int(mp["m_PathID"]))

    for o in env.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            mn = tt["m_Name"]
            if bot_id.split("_")[0] in mn.lower():
                pts, uvs, ws, bi = parse_unity_mesh_streams(tt)
                if ws is not None:
                    bad = int((ws.sum(axis=1) < 0.98).sum())
                    if bad > 0:
                        fail("FINAL_MESH_WEIGHTS", f"In final bundle, mesh '{mn}' has {bad} vertices with weight sum < 0.98! (Did you overwrite Stream 2 with zeros?!)", "NEVER zero Stream 2 bytes manually! Copy m_VertexData intact from Unity 2020 mesh bundle like generate_tarn_bundle.py.")
                if len(tt["m_BindPose"]) != len(tt["m_BoneNameHashes"]):
                    fail("FINAL_BONE_HASH", f"Mesh '{mn}' m_BindPose len ({len(tt['m_BindPose'])}) != m_BoneNameHashes len ({len(tt['m_BoneNameHashes'])})!", "Keep matching bone count between m_BindPose, m_BoneNameHashes, and SMR.m_Bones.")
                print(f"  [PASS] Final Mesh '{mn}': verts={len(pts)}, bones={len(tt['m_BindPose'])}, weights 100% valid.")

        elif o.type.name == "Texture2D":
            t = o.read()
            if getattr(t.m_StreamData, "size", 0) == 0 and int(t.m_TextureFormat) in (3, 4):
                bpp = 4 if int(t.m_TextureFormat) == 4 else 3
                exp = t.m_Width * t.m_Height * bpp
                act = len(getattr(t, "image_data", b""))
                if act != exp:
                    fail("TEX_DATA_LEN", f"Texture '{t.m_Name}' data len {act} != expected {exp}", "Use set_image(img, target_format=..., mipmap_count=1) and clear m_StreamData.")

        elif o.type.name == "Material" and o.path_id in active_mat_pids:
            tt = o.read_typetree()
            if "fx_" in tt.get("m_Name", "").lower():
                continue
            envs = tt.get("m_SavedProperties", {}).get("m_TexEnvs", [])
            tex_dict = {k: v for k, v in envs}
            if "_base_tex" in tex_dict and "_pbr_composite_tex" in tex_dict:
                for ch_k in ("_base_tex", "_normal_tex", "_pbr_composite_tex"):
                    sc = tex_dict[ch_k].get("m_Scale", {})
                    of = tex_dict[ch_k].get("m_Offset", {})
                    if sc.get("x") != 1.0 or sc.get("y") != 1.0 or of.get("x") != 0.0 or of.get("y") != 0.0:
                        fail("MAT_UV_SCALE", f"Material '{tt['m_Name']}' {ch_k} still has half-atlas Scale={sc}, Offset={of}!", "Reset m_Scale=(1,1), m_Offset=(0,0) on all 3 PBR texture slots per §4.7 Rule 6.")
                cols = {k: v for k, v in tt["m_SavedProperties"].get("m_Colors", [])}
                if "_Color" in cols and min(cols["_Color"]["r"], cols["_Color"]["g"], cols["_Color"]["b"]) < 0.65:
                    fail("MAT_DARK_COLOR", f"Material '{tt['m_Name']}' _Color={cols['_Color']} is darkened (<0.65)!", "Set _Color=(0.92,0.92,0.92,1) & _emissive_intensity_col=(1,1,1,0) so diffuse albedo & eyes don't inherit donor tint.")

    print(f"[PASS] Gate 4 Bundle Verification PASSED cleanly for '{bot_id}'!")


def main():
    p = argparse.ArgumentParser(description="TFTF 3D Character Porting Gate Validator")
    sub = p.add_subparsers(dest="stage", required=True)

    p1 = sub.add_parser("tex")
    p1.add_argument("--tex-dir", required=True)
    p1.add_argument("--prefixes", nargs="+", required=True)

    p2 = sub.add_parser("fbx")
    p2.add_argument("--fbx", required=True)
    p2.add_argument("--tank-fbx", default=None)

    p3 = sub.add_parser("mesh")
    p3.add_argument("--mesh-bundle", required=True)
    p3.add_argument("--donor", required=True)
    p3.add_argument("--robot-mesh", required=True)
    p3.add_argument("--veh-mesh", default=None)

    p4 = sub.add_parser("bundle")
    p4.add_argument("--bundle", required=True)
    p4.add_argument("--donor", required=True)
    p4.add_argument("--bot", required=True)

    args = p.parse_args()
    if args.stage == "tex":
        validate_tex_stage(args)
    elif args.stage == "fbx":
        validate_fbx_stage(args)
    elif args.stage == "mesh":
        validate_mesh_bundle(Path(args.mesh_bundle), Path(args.donor), args.robot_mesh, args.veh_mesh)
    elif args.stage == "bundle":
        validate_final_bundle(args)


if __name__ == "__main__":
    main()
