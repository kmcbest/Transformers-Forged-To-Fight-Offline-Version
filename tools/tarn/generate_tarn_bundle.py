#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
generate_tarn_bundle.py
Builds assets_redeco/tarn_gs.assetbundle by grafting Tarn's baked Robot/Vehicle meshes
and 3-map Kabam PBR textures onto Ultra Magnus (ultramagnus_gs_leader) donor bundle:
  - A1: Disables all donor weapon SMRs (axe, gun_right, pistol_left)
  - A2: Keeps chop1_backpack_main_center rigid vehicle rig + UM 40-bone hashes
  - A3: Converts UM FX materials, ParticleSystems, and PerceptualLights to Decepticon purple/magenta
"""
import sys
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

from pathlib import Path
from PIL import Image
import UnityPy
from UnityPy.enums import TextureFormat

ROOT = Path(r"E:\Agent\TFTF-blender")
DONOR_BUNDLE = ROOT / "extracted_apk" / "assets" / "assetpack" / "ultramagnus_gs_leader_odr" / "ultramagnus_gs_leader.assetbundle"
TARN_MESH_BUNDLE = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "tarn_mesh.assetbundle"
TEX_DIR = ROOT / "3rd-party-models" / "Tarn" / "06_working" / "unified_textures"
OUT_BUNDLE = ROOT / "assets_redeco" / "tarn_gs.assetbundle"

NEW_CAB = "CAB-7a4900007a4900007a4900007a490001"  # 32 lowercase hex digits

# Exact donor PIDs verified from ultramagnus_gs_leader.assetbundle
MESH_ROBOT_PID = -3677919709812409737
MESH_VEHICLE_PID = 1965915829973675685

SMR_ROBOT_PIDS = (-4497864873147514607, -5669485655896040359)
SMR_VEHICLE_PIDS = (6374655313817044002, 7769099272486437918)
SMR_WEAPON_PIDS = (
    -6929876573960912518, 8776407398459535180,  # axe_right
    -3806277267122844283, 5537406516109862368,  # gun_right
    -3099658301619870697, 4543470380929569169,  # pistol_left
)

MAT_ROBOT_PID = 5520268204611603145
MAT_VEHICLE_PID = 5691636987978222339

TEX_ROBOT_DIFF_PID = -6970767896792368081
TEX_ROBOT_NM_PID = 5841746967496826142
TEX_ROBOT_RAOE_PID = -7076967624015231670

TEX_VEH_DIFF_PID = -695917625355825749
TEX_VEH_NM_PID = -3742620179713543448
TEX_VEH_RAOE_PID = -8868189788918103369  # repurposed from wpns_RAOE -> vehicle RAOE

FX_MAT_PIDS = (
    -8252988663645228829,  # fx_m_energy_wave_a
    147355351511293498,    # fx_m_energy_shockwave_a
    -5813945392773663879,  # fx_m_tiled_crack_rock_hot
    -487659167540195070,   # fx_m_tiled_crack_rock
    982866352748045095,    # fx_m_axe_glow_ultramagnus_a
)


def is_chromatic(c: dict, threshold: float = 0.12) -> bool:
    r, g, b = float(c.get("r", 1.0)), float(c.get("g", 1.0)), float(c.get("b", 1.0))
    return (max(r, g, b) - min(r, g, b)) > threshold


def to_purple_color(c: dict, lum_floor: float = 0.35) -> dict:
    r, g, b = float(c.get("r", 1.0)), float(c.get("g", 1.0)), float(c.get("b", 1.0))
    lum = max(lum_floor, min(1.0, 0.299 * r + 0.587 * g + 0.114 * b))
    return {
        "r": round(0.92 * lum, 4),
        "g": round(0.14 * lum, 4),
        "b": round(1.00 * lum, 4),
        "a": float(c.get("a", 1.0)),
    }


def remap_gradient(grad: dict) -> int:
    changed = 0
    if not isinstance(grad, dict):
        return 0
    nkeys = int(grad.get("m_NumColorKeys", 0))
    for i in range(max(nkeys, 2)):
        kname = f"key{i}"
        k = grad.get(kname)
        if isinstance(k, dict) and is_chromatic(k):
            nk = to_purple_color(k)
            k["r"], k["g"], k["b"] = nk["r"], nk["g"], nk["b"]
            changed += 1
    return changed


def patch_kabam_character_mat(mat: dict, diff_pid: int, nm_pid: int, raoe_pid: int, metallic: float):
    tex_map = {
        "_base_tex": diff_pid,
        "_normal_tex": nm_pid,
        "_pbr_composite_tex": raoe_pid,
    }
    for name, entry in mat["m_SavedProperties"]["m_TexEnvs"]:
        if name in tex_map:
            entry["m_Texture"] = {"m_FileID": 0, "m_PathID": tex_map[name]}
            entry["m_Scale"] = {"x": 1.0, "y": 1.0}
            entry["m_Offset"] = {"x": 0.0, "y": 0.0}

    float_overrides = {
        "_Mode": 3.0,
        "_ZWrite": 1.0,
        "_metallic_range": metallic,
        "_roughness_range": 0.88,
        "_emissive_range": 0.0,  # CRITICAL: >0 acts as emission cutoff threshold and kills glow
        "_emissive_none": 0.0,
        "_emissive_overbright_range": 36.0,
    }
    floats = mat["m_SavedProperties"]["m_Floats"]
    existing_keys = {k for k, _ in floats}
    new_floats = [(k, float_overrides[k] if k in float_overrides else v) for k, v in floats]
    for k, v in float_overrides.items():
        if k not in existing_keys:
            new_floats.append((k, v))
    mat["m_SavedProperties"]["m_Floats"] = new_floats

    purple_emissive = {"r": 0.90, "g": 0.14, "b": 1.0, "a": 0.0}
    white = {"r": 1.0, "g": 1.0, "b": 1.0, "a": 1.0}
    color_overrides = {
        "_Color": white,
        "_base_col": white,
        "_emissive_intensity_col": purple_emissive,
    }
    colors = mat["m_SavedProperties"]["m_Colors"]
    mat["m_SavedProperties"]["m_Colors"] = [
        (k, dict(color_overrides[k]) if k in color_overrides else v) for k, v in colors
    ]


def set_texture(obj, img_path: Path, name: str, is_raoe: bool = False):
    t = obj.read()
    img = Image.open(img_path)
    if is_raoe:
        img = img.convert("RGB")
        target_fmt = TextureFormat.RGB24
    else:
        img = img.convert("RGBA")
        if img_path.name.endswith("_a.png") or img_path.name.endswith("_A.png"):
            # Guarantee 100% opaque diffuse alpha so cutout/translucency never activates
            r, g, b, _ = img.split()
            img = Image.merge("RGBA", (r, g, b, Image.new("L", img.size, 255)))
        target_fmt = TextureFormat.RGBA32

    t.m_Name = name
    t.m_StreamData.offset = 0
    t.m_StreamData.size = 0
    t.m_StreamData.path = ""
    t.set_image(img, target_format=target_fmt, mipmap_count=1)
    t.save()
    print(f"  [Tex queued] {obj.path_id}: '{name}' {img.size[0]}x{img.size[1]} target_fmt={int(target_fmt)}")


def main():
    assert DONOR_BUNDLE.is_file(), f"Missing donor bundle: {DONOR_BUNDLE}"
    assert TARN_MESH_BUNDLE.is_file(), f"Missing tarn mesh bundle: {TARN_MESH_BUNDLE}"

    print(f"[*] Loading tarn_mesh bundle: {TARN_MESH_BUNDLE}")
    env_m = UnityPy.load(str(TARN_MESH_BUNDLE))
    tarn_meshes = {}
    for o in env_m.objects:
        if o.type.name == "Mesh":
            tt = o.read_typetree()
            tarn_meshes[tt["m_Name"]] = tt
    assert "cha_tarn_gs_00" in tarn_meshes and "cha_tarn_gs_01" in tarn_meshes, f"Meshes missing: {list(tarn_meshes.keys())}"

    print(f"[*] Loading UM donor bundle: {DONOR_BUNDLE}")
    env = UnityPy.load(str(DONOR_BUNDLE))

    # Detect existing CAB prefix
    cab_files = [k for k in env.file.files.keys() if k.lower().startswith("cab-") and "." not in k]
    assert cab_files, f"Could not detect CAB inside donor bundle: {list(env.file.files.keys())}"
    old_cab = cab_files[0]
    old_cab_low = old_cab.lower()
    new_cab_low = NEW_CAB.lower()
    print(f"[*] Remapping CAB: {old_cab} -> {NEW_CAB}")

    obj_map = {o.path_id: o for o in env.objects}

    # 1. Update AssetBundle container and name
    ab_objs = [o for o in env.objects if o.type.name == "AssetBundle"]
    assert len(ab_objs) == 1
    ab_tt = ab_objs[0].read_typetree()
    ab_tt["m_Name"] = "data/tarn_gs_odr/tarn_gs.assetbundle"
    ab_tt["m_AssetBundleName"] = "data/tarn_gs_odr/tarn_gs.assetbundle"
    new_container = []
    for k, v in ab_tt["m_Container"]:
        nk = k.replace("ultramagnus_gs_leader", "tarn_gs")
        new_container.append([nk, v])
        print(f"  [Container] '{k}' -> '{nk}'")
    ab_tt["m_Container"] = new_container
    ab_objs[0].save_typetree(ab_tt)

    # 2. Remap stream paths containing old_cab across AudioClip/Texture2D/Mesh (skip replaced PIDs)
    replaced_pids = {
        MESH_ROBOT_PID, MESH_VEHICLE_PID,
        TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID,
        TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID,
    }
    remapped_streams = 0
    for o in env.objects:
        if o.path_id in replaced_pids:
            continue
        if o.type.name in ("AudioClip", "Texture2D", "Mesh"):
            tt = o.read_typetree()
            dirty = False
            sd = tt.get("m_StreamData")
            if isinstance(sd, dict) and isinstance(sd.get("path"), str) and old_cab_low in sd["path"].lower():
                sd["path"] = sd["path"].replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
                dirty = True
            res = tt.get("m_Resource")
            if isinstance(res, dict) and isinstance(res.get("m_Source"), str) and old_cab_low in res["m_Source"].lower():
                res["m_Source"] = res["m_Source"].replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
                dirty = True
            if dirty:
                o.save_typetree(tt)
                remapped_streams += 1
    print(f"[*] Remapped external stream paths on {remapped_streams} objects")

    # 3. Graft Robot & Vehicle Meshes while keeping UM donor m_BoneNameHashes & m_RootBoneNameHash
    for dst_pid, src_name in ((MESH_ROBOT_PID, "cha_tarn_gs_00"), (MESH_VEHICLE_PID, "cha_tarn_gs_01")):
        src_tt = tarn_meshes[src_name]
        dst_obj = obj_map[dst_pid]
        dst_tt = dst_obj.read_typetree()
        keep_hashes = list(dst_tt["m_BoneNameHashes"])
        keep_root_hash = int(dst_tt["m_RootBoneNameHash"])
        assert len(keep_hashes) == len(src_tt["m_BindPose"]), (
            f"{src_name} bindPose len={len(src_tt['m_BindPose'])} != donor bone hashes len={len(keep_hashes)}"
        )

        dst_tt["m_Name"] = src_name
        for field in (
            "m_SubMeshes",
            "m_Shapes",
            "m_BindPose",
            "m_BonesAABB",
            "m_VariableBoneCountWeights",
            "m_MeshCompression",
            "m_IndexFormat",
            "m_IndexBuffer",
            "m_VertexData",
            "m_CompressedMesh",
            "m_LocalAABB",
            "m_StreamData",
        ):
            dst_tt[field] = src_tt[field]
        dst_tt["m_BoneNameHashes"] = keep_hashes
        dst_tt["m_RootBoneNameHash"] = keep_root_hash
        dst_tt["m_IsReadable"] = True
        dst_tt["m_KeepVertices"] = True
        dst_tt["m_KeepIndices"] = True
        dst_tt["m_MeshUsageFlags"] = 1
        dst_obj.save_typetree(dst_tt)
        print(f"  [Mesh] {dst_pid} -> '{src_name}' verts={src_tt['m_VertexData']['m_VertexCount']} bones={len(keep_hashes)} submeshes={len(src_tt['m_SubMeshes'])}")

    # 4. Update SMRs (Robot=53, Vehicle=40, Weapons=disabled)
    generous_aabb = {
        "m_Center": {"x": 0.0, "y": 0.0, "z": 0.0},
        "m_Extent": {"x": 10.0, "y": 10.0, "z": 10.0},
    }
    for pid in SMR_ROBOT_PIDS:
        smr = obj_map[pid].read_typetree()
        assert len(smr["m_Bones"]) == 53
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_ROBOT_PID}]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)
        print(f"  [SMR Robot] {pid}: mat={MAT_ROBOT_PID}, bones=53")

    for pid in SMR_VEHICLE_PIDS:
        smr = obj_map[pid].read_typetree()
        assert len(smr["m_Bones"]) == 40
        smr["m_Materials"] = [{"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID}]
        smr["m_AABB"] = generous_aabb
        smr["m_UpdateWhenOffscreen"] = True
        obj_map[pid].save_typetree(smr)
        print(f"  [SMR Vehicle] {pid}: mat={MAT_VEHICLE_PID}, bones=40")

    for pid in SMR_WEAPON_PIDS:
        smr = obj_map[pid].read_typetree()
        smr["m_Enabled"] = False
        smr["m_Mesh"] = {"m_FileID": 0, "m_PathID": 0}
        obj_map[pid].save_typetree(smr)
        go_pid = smr["m_GameObject"]["m_PathID"]
        if go_pid in obj_map:
            go = obj_map[go_pid].read_typetree()
            go["m_IsActive"] = False
            obj_map[go_pid].save_typetree(go)
    print(f"  [SMR Weapons] Disabled {len(SMR_WEAPON_PIDS)} weapon SMRs + leaf GameObjects (A1)")

    # 5. Replace Textures (Diffuse opaque RGBA, NM RGBA, RAOE 3-channel RGB)
    print("[*] Replacing character textures...")
    set_texture(obj_map[TEX_ROBOT_DIFF_PID], TEX_DIR / "cha_tarn_main_a.png", "cha_tarn_main_a", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_NM_PID], TEX_DIR / "cha_tarn_main_NM_kabam.png", "cha_tarn_main_NM", is_raoe=False)
    set_texture(obj_map[TEX_ROBOT_RAOE_PID], TEX_DIR / "cha_tarn_main_RAOE.png", "cha_tarn_main_RAOE", is_raoe=True)

    set_texture(obj_map[TEX_VEH_DIFF_PID], TEX_DIR / "cha_tarn_tform_misc_A.png", "cha_tarn_tform_misc_A", is_raoe=False)
    set_texture(obj_map[TEX_VEH_NM_PID], TEX_DIR / "cha_tarn_tform_misc_NM_kabam.png", "cha_tarn_tform_misc_NM", is_raoe=False)
    set_texture(obj_map[TEX_VEH_RAOE_PID], TEX_DIR / "cha_tarn_tform_misc_RAOE.png", "cha_tarn_tform_misc_RAOE", is_raoe=True)

    # 6. Configure Kabam PBR Character Materials
    mat_r = obj_map[MAT_ROBOT_PID].read_typetree()
    patch_kabam_character_mat(mat_r, TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID, metallic=0.25)
    obj_map[MAT_ROBOT_PID].save_typetree(mat_r)

    mat_v = obj_map[MAT_VEHICLE_PID].read_typetree()
    patch_kabam_character_mat(mat_v, TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID, metallic=0.22)
    obj_map[MAT_VEHICLE_PID].save_typetree(mat_v)
    print("[*] Patched Robot & Vehicle Kabam PBR materials (_emissive_range=0.0)")

    # 7. A3 Purple / Magenta FX recoloring (FX Materials, ParticleSystems, PerceptualLights)
    for pid in FX_MAT_PIDS:
        m = obj_map[pid].read_typetree()
        m["m_SavedProperties"]["m_Colors"] = [
            (k, {"r": 0.95, "g": 0.14, "b": 1.0, "a": 1.0} if k == "_emissive_intensity_col" else v)
            for k, v in m["m_SavedProperties"]["m_Colors"]
        ]
        obj_map[pid].save_typetree(m)

    ps_patched = 0
    light_patched = 0
    for o in env.objects:
        if o.type.name == "ParticleSystem":
            d = o.read_typetree()
            changes = 0
            sc = d.get("InitialModule", {}).get("startColor", {})
            for cname in ("minColor", "maxColor"):
                c = sc.get(cname)
                if isinstance(c, dict) and is_chromatic(c):
                    nk = to_purple_color(c)
                    c.update(nk)
                    changes += 1
            for gname in ("minGradient", "maxGradient"):
                changes += remap_gradient(sc.get(gname))
            for mod_name in ("ColorModule", "ColorBySpeedModule"):
                mod = d.get(mod_name, {})
                g = mod.get("gradient", {})
                changes += remap_gradient(g.get("minGradient"))
                changes += remap_gradient(g.get("maxGradient"))
            if changes > 0:
                o.save_typetree(d)
                ps_patched += 1
        elif o.type.name == "MonoBehaviour":
            try:
                d = o.read_typetree()
            except Exception:
                continue
            if "_Color" in d and "ColorGradient" in d:
                c = d["_Color"]
                if isinstance(c, dict):
                    d["_Color"] = {"r": 0.90, "g": 0.15, "b": 1.0, "a": float(c.get("a", 1.0))}
                remap_gradient(d.get("ColorGradient"))
                o.save_typetree(d)
                light_patched += 1
    print(f"[*] A3 FX recolor complete: {len(FX_MAT_PIDS)} FX mats, {ps_patched} ParticleSystems, {light_patched} PerceptualLights")

    # 8. Rename CAB file entries right before saving
    new_files = {}
    for k, v in env.file.files.items():
        if old_cab in k:
            nk = k.replace(old_cab, NEW_CAB)
        elif old_cab_low in k:
            nk = k.replace(old_cab_low, new_cab_low)
        else:
            nk = k
        if hasattr(v, "name") and isinstance(v.name, str):
            v.name = v.name.replace(old_cab, NEW_CAB).replace(old_cab_low, new_cab_low)
        new_files[nk] = v
    env.file.files = new_files

    OUT_BUNDLE.parent.mkdir(parents=True, exist_ok=True)
    OUT_BUNDLE.write_bytes(env.file.save(packer="lz4"))
    size_mb = OUT_BUNDLE.stat().st_size / (1024 * 1024)
    print(f"[✓] Saved {OUT_BUNDLE} ({size_mb:.2f} MB, packer='lz4', CAB={NEW_CAB})")

    # Verify reloaded persisted textures & meshes
    verify_env = UnityPy.load(str(OUT_BUNDLE))
    v_map = {o.path_id: o for o in verify_env.objects}
    print(f"[*] Verified reloaded CAB files: {list(verify_env.file.files.keys())}")
    for pid in (TEX_ROBOT_DIFF_PID, TEX_ROBOT_NM_PID, TEX_ROBOT_RAOE_PID, TEX_VEH_DIFF_PID, TEX_VEH_NM_PID, TEX_VEH_RAOE_PID):
        vt = v_map[pid].read()
        print(f"    [Persisted Tex] {pid}: '{vt.m_Name}' {vt.m_Width}x{vt.m_Height} fmt={vt.m_TextureFormat} streamSize={vt.m_StreamData.size}")
    for pid in (MESH_ROBOT_PID, MESH_VEHICLE_PID):
        vm = v_map[pid].read_typetree()
        print(f"    [Persisted Mesh] {pid}: '{vm['m_Name']}' verts={vm['m_VertexData']['m_VertexCount']} bones={len(vm['m_BoneNameHashes'])} submeshes={len(vm['m_SubMeshes'])}")


if __name__ == "__main__":
    main()
