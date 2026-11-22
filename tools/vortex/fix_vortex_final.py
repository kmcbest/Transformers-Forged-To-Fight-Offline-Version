import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import copy
import json
import subprocess
import UnityPy
from UnityPy.enums import TextureFormat
import numpy as np
from PIL import Image

HEAD_BUNDLE = r"e:\Agent\TFTF-blender\tools\vortex\vortex_gs_head.assetbundle"
OUT_BUNDLE  = r"e:\Agent\TFTF-blender\assets_redeco\vortex_gs.assetbundle"
SPLIT_JSON  = r"e:\Agent\TFTF-blender\tools\vortex\diag\vh_submesh_split.json"

# 0. Extract clean HEAD:assets_redeco/vortex_gs.assetbundle
print("[*] Extracting clean HEAD:assets_redeco/vortex_gs.assetbundle...")
raw_head = subprocess.check_output(
    ["git", "show", "HEAD:assets_redeco/vortex_gs.assetbundle"],
    cwd=r"e:\Agent\TFTF-blender"
)
with open(HEAD_BUNDLE, "wb") as f:
    f.write(raw_head)
print(f"[✓] Loaded clean HEAD bundle ({len(raw_head):,} bytes)")

with open(SPLIT_JSON, "r", encoding="utf-8") as f:
    split_data = json.load(f)
logo_tris_set     = set(split_data["logo_tris"])
interior_tris_set = set(split_data["interior_tris"])
assert len(logo_tris_set) == 4 and len(interior_tris_set) == 443
assert not (logo_tris_set & interior_tris_set)

env = UnityPy.load(HEAD_BUNDLE)
obj_map = {obj.path_id: obj for obj in env.objects}

def align16(n):
    return (n + 15) & ~15

def bilinear_sample(img_arr, u, v):
    h, w = img_arr.shape[:2]
    x = (u % 1.0) * (w - 1)
    y = (1.0 - (v % 1.0)) * (h - 1)
    x0 = np.floor(x).astype(int)
    y0 = np.floor(y).astype(int)
    x1 = np.clip(x0 + 1, 0, w - 1)
    y1 = np.clip(y0 + 1, 0, h - 1)
    dx = (x - x0)[..., None]
    dy = (y - y0)[..., None]
    c00 = img_arr[y0, x0].astype(np.float32)
    c10 = img_arr[y0, x1].astype(np.float32)
    c01 = img_arr[y1, x0].astype(np.float32)
    c11 = img_arr[y1, x1].astype(np.float32)
    return (c00 * (1 - dx) * (1 - dy) + c10 * dx * (1 - dy) + c01 * (1 - dx) * dy + c11 * dx * dy)

def build_helicopter_emblem_textures(vh_m, vh_diff_np):
    """Raycast cabin door surface behind Tri 59..62 using TRUE 16-byte aligned Stream 1 UV offset."""
    vd = vh_m.m_VertexData
    vc = vd.m_VertexCount
    raw = bytes(vd.m_DataSize)
    s1_off = align16(vc * 40)
    pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
    uv  = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4),  offset=s1_off)
    ib  = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

    n_right = np.cross(pos[ib[59][1]] - pos[ib[59][0]], pos[ib[59][2]] - pos[ib[59][0]]).astype(np.float64)
    if n_right[0] < 0:
        n_right = -n_right
    n_right /= np.linalg.norm(n_right)

    n_left = np.cross(pos[ib[61][1]] - pos[ib[61][0]], pos[ib[61][2]] - pos[ib[61][0]]).astype(np.float64)
    if n_left[0] > 0:
        n_left = -n_left
    n_left /= np.linalg.norm(n_left)

    quads = {
        "left":  {"TL": pos[178], "TR": pos[175], "BL": pos[176], "BR": pos[177], "ray_dir": -n_left},
        "right": {"TL": pos[173], "TR": pos[171], "BL": pos[172], "BR": pos[174], "ray_dir": -n_right},
    }

    tri_centroids = pos[ib].mean(axis=1)
    cand_idx = [
        i for i in range(len(ib))
        if i not in logo_tris_set and i not in interior_tris_set
        and abs(tri_centroids[i, 0]) > 0.4
        and 2.0 < tri_centroids[i, 1] < 4.0
        and -0.2 < tri_centroids[i, 2] < 1.8
    ]
    body_tris = ib[cand_idx]
    v0 = pos[body_tris[:, 0]].astype(np.float64)
    v1 = pos[body_tris[:, 1]].astype(np.float64)
    v2 = pos[body_tris[:, 2]].astype(np.float64)
    e1 = v1 - v0
    e2 = v2 - v0

    def raycast_side(q, res=512):
        us = np.linspace(0.0, 1.0, res)
        vs = np.linspace(1.0, 0.0, res)
        uu, vv = np.meshgrid(us, vs)
        pts = (
            (1 - uu)[..., None] * vv[..., None] * q["TL"] +
            uu[..., None] * vv[..., None] * q["TR"] +
            (1 - uu)[..., None] * (1 - vv)[..., None] * q["BL"] +
            uu[..., None] * (1 - vv)[..., None] * q["BR"]
        ).reshape(-1, 3)
        d = q["ray_dir"] / np.linalg.norm(q["ray_dir"])
        origins = pts - d * 0.05
        h_vec = np.cross(d, e2)
        a_det = np.einsum("ij,ij->i", e1, h_vec)
        valid_a = np.abs(a_det) > 1e-6
        inv_a = np.where(valid_a, 1.0 / np.where(valid_a, a_det, 1.0), 0.0)

        hit_u = np.zeros(len(origins), dtype=np.float32)
        hit_v = np.zeros(len(origins), dtype=np.float32)
        hit_ok = np.zeros(len(origins), dtype=bool)

        for start in range(0, len(origins), 1024):
            oc = origins[start:start+1024]
            s = oc[:, None, :] - v0[None, :, :]
            ub = inv_a[None, :] * np.einsum("cti,ti->ct", s, h_vec)
            qv = np.cross(s, e1[None, :, :])
            vb = inv_a[None, :] * np.einsum("cti,i->ct", qv, d)
            t = inv_a[None, :] * np.einsum("ti,cti->ct", e2, qv)

            hit = valid_a[None, :] & (ub >= -1e-3) & (vb >= -1e-3) & (ub + vb <= 1.002) & (t > -0.2) & (t < 0.35)
            abs_t = np.where(hit, np.abs(t), 1e9)
            best_ti = np.argmin(abs_t, axis=1)
            best_dt = abs_t[np.arange(len(oc)), best_ti]
            ok = best_dt < 1.0

            u_sel = np.clip(ub[np.arange(len(oc)), best_ti], 0.0, 1.0)
            v_sel = np.clip(vb[np.arange(len(oc)), best_ti], 0.0, 1.0)
            w_sel = 1.0 - u_sel - v_sel
            tri_vi = body_tris[best_ti]
            uv_hit = (
                w_sel[:, None] * uv[tri_vi[:, 0]] +
                u_sel[:, None] * uv[tri_vi[:, 1]] +
                v_sel[:, None] * uv[tri_vi[:, 2]]
            )
            hit_u[start:start+1024] = uv_hit[:, 0]
            hit_v[start:start+1024] = uv_hit[:, 1]
            hit_ok[start:start+1024] = ok

        rgb = np.zeros((len(origins), 3), dtype=np.float32)
        rgb[:] = [182.0, 164.0, 74.0]
        if np.any(hit_ok):
            rgb[hit_ok] = bilinear_sample(vh_diff_np, hit_u[hit_ok], hit_v[hit_ok])
        return rgb.reshape(res, res, 3)

    diff_atlas = np.zeros((512, 1024, 3), dtype=np.uint8)
    raoe_atlas = np.zeros((512, 1024, 3), dtype=np.uint8)
    raoe_atlas[:, :, 0] = 125
    raoe_atlas[:, :, 1] = 220

    logo_raw = Image.open(r"e:\Agent\TFTF-blender\tools\vortex\DecepticonLogo.png").convert("RGBA")
    logo_sz = 380
    pad = (512 - logo_sz) // 2
    logo_resized = np.array(logo_raw.resize((logo_sz, logo_sz), Image.Resampling.LANCZOS))
    raw_alpha = logo_resized[:, :, 3] / 255.0
    sharp_alpha = np.clip((raw_alpha - 0.14) / 0.72, 0.0, 1.0)

    alpha_full = np.zeros((512, 512), dtype=np.float32)
    alpha_full[pad:pad+logo_sz, pad:pad+logo_sz] = sharp_alpha

    logo_rgb = np.zeros((512, 512, 3), dtype=np.float32)
    logo_rgb[:, :, 0] = 105.0
    logo_rgb[:, :, 1] = 32.0
    logo_rgb[:, :, 2] = 180.0

    for side_name, x_off in [("left", 0), ("right", 512)]:
        print(f"  [*] Smooth raycasting {side_name} door panel (s1_off={s1_off})...")
        bg = raycast_side(quads[side_name], res=512)
        a = alpha_full[:, :, None]
        comp = bg * (1.0 - a) + logo_rgb * a
        diff_atlas[:, x_off:x_off+512] = np.clip(comp, 0, 255).astype(np.uint8)
        raoe_atlas[:, x_off:x_off+512, 2] = np.clip(alpha_full * 85.0, 0, 255).astype(np.uint8)

    nm_64 = np.zeros((64, 64, 3), dtype=np.uint8)
    nm_64[:, :] = [128, 128, 255]
    return (
        Image.fromarray(diff_atlas),
        Image.fromarray(raoe_atlas),
        Image.fromarray(nm_64),
        n_left,
        n_right,
    )

def clone_material_base(src_mat_obj, dst_mat_obj, texs=None, colors=None, floats=None):
    src_tt = src_mat_obj.read_typetree()
    dst_tt = dst_mat_obj.read_typetree()
    cloned = copy.deepcopy(src_tt)
    cloned["m_Name"] = dst_tt["m_Name"]

    if colors:
        cloned["m_SavedProperties"]["m_Colors"] = [
            (k, colors[k]) if k in colors else (k, v)
            for k, v in cloned["m_SavedProperties"]["m_Colors"]
        ]
    if floats:
        cloned["m_SavedProperties"]["m_Floats"] = [
            (k, floats[k]) if k in floats else (k, v)
            for k, v in cloned["m_SavedProperties"]["m_Floats"]
        ]
    if texs:
        new_texs = []
        for k, v in cloned["m_SavedProperties"]["m_TexEnvs"]:
            nv = dict(v)
            if k in texs:
                nv["m_Texture"] = {"m_FileID": 0, "m_PathID": texs[k]}
            new_texs.append((k, nv))
        cloned["m_SavedProperties"]["m_TexEnvs"] = new_texs

    dst_mat_obj.save_typetree(cloned)

def set_tex_and_wrap(tex_obj, pil_img, wrap_mode):
    """Clear external .resS m_StreamData, embed RGB24 mip=1 image cleanly, and set WrapU/WrapV."""
    img = pil_img.convert("RGB")
    t = tex_obj.read()
    t.m_StreamData.offset = 0
    t.m_StreamData.size = 0
    t.m_StreamData.path = ""
    t.m_TextureSettings.m_WrapU = wrap_mode
    t.m_TextureSettings.m_WrapV = wrap_mode
    t.set_image(img, target_format=TextureFormat.RGB24, mipmap_count=1)
    t.save()

# ==============================================================================
# PART A: HELICOPTER 3-SUBMESH RESTORATION (Base + Seamless Emblem + Dark Interior)
# ==============================================================================
print("\n=== PART A: Helicopter 3-SubMesh Restoration & Seamless Door Emblem ===")
vh_mesh_obj = obj_map[-2766188856892899435]
vh_m = vh_mesh_obj.read()
vh_diff_np = np.array(obj_map[-7643335609835079515].read().image.convert("RGB"))

emb_diff_img, emb_raoe_img, emb_nm_img, n_left, n_right = build_helicopter_emblem_textures(vh_m, vh_diff_np)
emb_diff_img.save(r"e:\Agent\TFTF-blender\tools\vortex\diag\final_emblem_diff.png")
emb_raoe_img.save(r"e:\Agent\TFTF-blender\tools\vortex\diag\final_emblem_raoe.png")

# Unused weapon textures for Emblem (Clamp=1)
TEX_EMB_DIFF_PID = 6239694728433603131   # cha_grindor_cin_rotf_wpns_a
TEX_EMB_RAOE_PID = -8672171104083879485  # cha_grindor_cin_rotf_wpns_e
TEX_EMB_NM_PID   = -8753204007397435811  # cha_grindor_cin_rotf_wpns_n

set_tex_and_wrap(obj_map[TEX_EMB_DIFF_PID], emb_diff_img, wrap_mode=1)
set_tex_and_wrap(obj_map[TEX_EMB_RAOE_PID], emb_raoe_img, wrap_mode=1)
set_tex_and_wrap(obj_map[TEX_EMB_NM_PID],   emb_nm_img,   wrap_mode=1)
print("  [✓] Saved Emblem textures (Clamp=1) into unused slots")

# Unused weapon textures for Interior Mechanical Pipes TR_Test_Mat_INST (Repeat=0!)
TEX_INT_DIFF_PID = 5741437468734501436   # cha_grindor_cin_rotf_wpns_m
TEX_INT_NM_PID   = -3179261496129805109  # cha_grindor_cin_rotf_wpns_r
TEX_INT_RAOE_PID = 696671028566742258    # cha_grindor_cin_rotf_wpns_ao

int_diff_img = Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\orig_vh_interior_mat.jpg").convert("RGB")
int_nm_img   = Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\orig_vh_interior_n.jpg").convert("RGB")
int_raoe_np  = np.zeros((256, 256, 3), dtype=np.uint8)
int_raoe_np[:, :] = [145, 220, 0] # Roughness=145, AO=220, Emissive=0
int_raoe_img = Image.fromarray(int_raoe_np)

set_tex_and_wrap(obj_map[TEX_INT_DIFF_PID], int_diff_img, wrap_mode=0)
set_tex_and_wrap(obj_map[TEX_INT_NM_PID],   int_nm_img,   wrap_mode=0)
set_tex_and_wrap(obj_map[TEX_INT_RAOE_PID], int_raoe_img, wrap_mode=0)
print("  [✓] Saved Interior Mechanical Pipes textures (vh_interior_mat/n, Repeat=0!) into unused slots")

# Update cha_grindor_cin_rotf_01 vertex buffer AT TRUE ALIGNED s1_off = align16(vc_vh * 40)!
vh_tt = vh_mesh_obj.read_typetree()
vd_vh = vh_tt["m_VertexData"]
vc_vh = vd_vh["m_VertexCount"]
s1_off_vh = align16(vc_vh * 40)
raw_vh = bytearray(vd_vh["m_DataSize"])

pos_vh = np.ndarray((vc_vh, 3), dtype=np.float32, buffer=raw_vh, strides=(40, 4), offset=0)
uv_vh  = np.ndarray((vc_vh, 2), dtype=np.float32, buffer=raw_vh, strides=(8, 4),  offset=s1_off_vh)

# Lift 8mm outward along Unity normal (leaves all other 6449 verts untouched!)
for vi in [171, 172, 173, 174]:
    pos_vh[vi] += (n_right * 0.008).astype(np.float32)
for vi in [175, 176, 177, 178]:
    pos_vh[vi] += (n_left * 0.008).astype(np.float32)

# Cleanly write emblem UVs at TRUE Stream 1 aligned offset!
uv_vh[178] = [0.002, 0.998]  # Left TL
uv_vh[175] = [0.498, 0.998]  # Left TR
uv_vh[176] = [0.002, 0.002]  # Left BL
uv_vh[177] = [0.498, 0.002]  # Left BR

uv_vh[173] = [0.502, 0.998]  # Right TL
uv_vh[171] = [0.998, 0.998]  # Right TR
uv_vh[172] = [0.502, 0.002]  # Right BL
uv_vh[174] = [0.998, 0.002]  # Right BR

vd_vh["m_DataSize"] = bytes(raw_vh)

# Partition cha_grindor_cin_rotf_01 into 3 SubMeshes:
# SubMesh 0: 5756 base fuselage tris
# SubMesh 1: 4 emblem tris (59..62)
# SubMesh 2: 443 mechanical interior/thruster tris (TR_Test_Mat_INST)
ib_vh = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)
sub0_ib = np.array([ib_vh[i] for i in range(len(ib_vh)) if i not in logo_tris_set and i not in interior_tris_set], dtype=np.uint16).flatten()
sub1_ib = np.array([ib_vh[i] for i in range(len(ib_vh)) if i in logo_tris_set], dtype=np.uint16).flatten()
sub2_ib = np.array([ib_vh[i] for i in range(len(ib_vh)) if i in interior_tris_set], dtype=np.uint16).flatten()
new_vh_ib = np.concatenate([sub0_ib, sub1_ib, sub2_ib])

vh_tt["m_IndexBuffer"] = list(new_vh_ib.tobytes())
orig_vh_sm0 = vh_tt["m_SubMeshes"][0]

sm0_vh = dict(orig_vh_sm0)
sm0_vh["firstByte"] = 0
sm0_vh["indexCount"] = len(sub0_ib)

sm1_vh = dict(orig_vh_sm0)
sm1_vh["firstByte"] = len(sub0_ib) * 2
sm1_vh["indexCount"] = len(sub1_ib)

sm2_vh = dict(orig_vh_sm0)
sm2_vh["firstByte"] = (len(sub0_ib) + len(sub1_ib)) * 2
sm2_vh["indexCount"] = len(sub2_ib)

vh_tt["m_SubMeshes"] = [sm0_vh, sm1_vh, sm2_vh]
vh_mesh_obj.save_typetree(vh_tt)
print(f"  [✓] Partitioned Helicopter Mesh into 3 SubMeshes: Base={len(sub0_ib)//3}, Emblem={len(sub1_ib)//3}, Interior={len(sub2_ib)//3}")

MAT_VEHICLE_PID     = -3423934603996225370
MAT_EMBLEM_PID      = -7619844944224089758
MAT_VH_INTERIOR_PID = 6154045054253613272

clone_material_base(
    obj_map[MAT_VEHICLE_PID],
    obj_map[MAT_EMBLEM_PID],
    texs={
        "_base_tex": TEX_EMB_DIFF_PID,
        "_normal_tex": TEX_EMB_NM_PID,
        "_pbr_composite_tex": TEX_EMB_RAOE_PID,
    },
    colors={"_emissive_intensity_col": {"r": 0.70, "g": 0.05, "b": 1.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 24.0, "_emissive_range": 1.0},
)

clone_material_base(
    obj_map[MAT_VEHICLE_PID],
    obj_map[MAT_VH_INTERIOR_PID],
    texs={
        "_base_tex": TEX_INT_DIFF_PID,
        "_normal_tex": TEX_INT_NM_PID,
        "_pbr_composite_tex": TEX_INT_RAOE_PID,
    },
    colors={"_emissive_intensity_col": {"r": 0.0, "g": 0.0, "b": 0.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 1.0, "_emissive_range": 0.0},
)
print("  [✓] Configured MAT_EMBLEM & MAT_VH_INTERIOR with matching Vehicle PBR shader")

for smr_pid in [-3058981427382277161, 6619623465709811202]:
    smr_obj = obj_map[smr_pid]
    smr_tt = smr_obj.read_typetree()
    smr_tt["m_Materials"] = [
        {"m_FileID": 0, "m_PathID": MAT_VEHICLE_PID},
        {"m_FileID": 0, "m_PathID": MAT_EMBLEM_PID},
        {"m_FileID": 0, "m_PathID": MAT_VH_INTERIOR_PID},
    ]
    smr_obj.save_typetree(smr_tt)
print("  [✓] Bound Helicopter SMRs to [MAT_VEHICLE, MAT_EMBLEM, MAT_VH_INTERIOR]")

# ==============================================================================
# PART B: ROBOT TEXTURE RAOE FIXES + DUAL-SUBMESH VISOR SEPARATION
# ==============================================================================
print("\n=== PART B: Robot Emissive Mask Refinements & Visor Split ===")
ROB_DIFF_PID = -527106191474585865
ROB_NM_PID   = -3094932978529403771
ROB_RAOE_PID = -2574972184015167263

rob_diff_np = np.array(obj_map[ROB_DIFF_PID].read().image.convert("RGB"))
rob_raoe_np = np.array(obj_map[ROB_RAOE_PID].read().image.convert("RGB"))

rob_raoe_np[1840:1940, 1410:1470, 2] = 0
rob_raoe_np[1750:1796, 1080:1108, 2] = 0
print("  [✓] Cleared RAOE.B=0 on vertical nose strip & forehead crest dot")

visor_diff = rob_diff_np[1669:1720, 1360:1461]
visor_yellow = (visor_diff[:, :, 0] > 180) & (visor_diff[:, :, 1] > 180) & (visor_diff[:, :, 2] < 145)
rob_raoe_np[1669:1720, 1360:1461, 2][visor_yellow] = 220
print(f"  [✓] Filled uniform yellow visor RAOE.B=220 ({visor_yellow.sum()} px)")

emb_tile_diff = rob_diff_np[0:512, 1536:2048].astype(int)
emb_purple_face = (emb_tile_diff[:, :, 2] > emb_tile_diff[:, :, 1] + 40) & (emb_tile_diff[:, :, 2] > 130)
rob_raoe_np[0:512, 1536:2048, 2] = np.where(emb_purple_face, 90, 0).astype(np.uint8)
print(f"  [✓] Toned Chest Emblem RAOE.B=90 ({emb_purple_face.sum()} px), 0 on crevices")

honey_sub = rob_diff_np[1490:1700, 60:350].astype(int)
honey_mask = (honey_sub[:, :, 2] > honey_sub[:, :, 1] + 25) & (honey_sub[:, :, 2] > honey_sub[:, :, 0] + 15) & (honey_sub[:, :, 0] >= honey_sub[:, :, 1] - 4) & (honey_sub[:, :, 2] > 65)
honey_b = np.clip((honey_sub[:, :, 2] - 50) * 1.4, 0, 170).astype(np.uint8)
rob_raoe_np[1490:1700, 60:350, 2] = np.where(honey_mask, honey_b, 0)
print(f"  [✓] Lit Chest Diagonal Honeycomb Vents strictly ({honey_mask.sum()} px)")

sword_tile = rob_raoe_np[512:1023, 1024:1535, 2]
rob_raoe_np[512:1023, 1024:1535, 2] = np.where(sword_tile > 10, 155, sword_tile)

rob_raoe_img_new = Image.fromarray(rob_raoe_np)
rob_raoe_img_new.save(r"e:\Agent\TFTF-blender\tools\vortex\diag\final_robot_raoe.png")
rob_raoe_data = obj_map[ROB_RAOE_PID].read()
rob_raoe_data.image = rob_raoe_img_new
rob_raoe_data.save()

rob_mesh_obj = obj_map[5703189533076905359]
rob_m = rob_mesh_obj.read()
rob_tt = rob_mesh_obj.read_typetree()
ib_rob = np.frombuffer(bytes(rob_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

eye_rob_tris_idx = set(range(6098, 6108))
body_rob_ib = np.array([ib_rob[i] for i in range(len(ib_rob)) if i not in eye_rob_tris_idx], dtype=np.uint16).flatten()
eye_rob_ib  = np.array([ib_rob[i] for i in range(len(ib_rob)) if i in eye_rob_tris_idx], dtype=np.uint16).flatten()
new_rob_ib  = np.concatenate([body_rob_ib, eye_rob_ib])

rob_tt["m_IndexBuffer"] = list(new_rob_ib.tobytes())
orig_rob_sm0 = rob_tt["m_SubMeshes"][0]
sm0_rob = dict(orig_rob_sm0)
sm0_rob["firstByte"] = 0
sm0_rob["indexCount"] = len(body_rob_ib)
sm1_rob = dict(orig_rob_sm0)
sm1_rob["firstByte"] = len(body_rob_ib) * 2
sm1_rob["indexCount"] = len(eye_rob_ib)
rob_tt["m_SubMeshes"] = [sm0_rob, sm1_rob]
rob_mesh_obj.save_typetree(rob_tt)

MAT_ROBOT_PID      = 2433515842246304279
MAT_ROBOT_EYES_PID = -4921200029808501144

mat_rob_obj = obj_map[MAT_ROBOT_PID]
clone_material_base(
    mat_rob_obj,
    mat_rob_obj,
    colors={"_emissive_intensity_col": {"r": 0.72, "g": 0.08, "b": 1.0, "a": 0.0}},
    floats={"_emissive_overbright_range": 24.0, "_emissive_range": 1.0},
)

clone_material_base(
    mat_rob_obj,
    obj_map[MAT_ROBOT_EYES_PID],
    texs={
        "_base_tex": ROB_DIFF_PID,
        "_normal_tex": ROB_NM_PID,
        "_pbr_composite_tex": ROB_RAOE_PID,
    },
    colors={"_emissive_intensity_col": {"r": 1.0, "g": 0.85, "b": 0.12, "a": 0.0}},
    floats={"_emissive_overbright_range": 24.0, "_emissive_range": 1.0},
)

for smr_pid in [-3243551817942222242, -2776875793336503958]:
    smr_obj = obj_map[smr_pid]
    smr_tt = smr_obj.read_typetree()
    smr_tt["m_Materials"] = [
        {"m_FileID": 0, "m_PathID": MAT_ROBOT_PID},
        {"m_FileID": 0, "m_PathID": MAT_ROBOT_EYES_PID},
    ]
    smr_obj.save_typetree(smr_tt)
print("  [✓] Updated Robot Mesh, Materials & SMRs cleanly")

# Two-pass save -> reload -> rebuild_container_preload_table -> final LZ4 save
pass1_bytes = env.file.save(packer="lz4")
with open(OUT_BUNDLE, "wb") as f:
    f.write(pass1_bytes)

sys.path.insert(0, r"e:\Agent\TFTF-blender\tools")
from patch_vortex_melee import rebuild_container_preload_table

env2 = UnityPy.load(OUT_BUNDLE)
rebuild_container_preload_table(list(env2.assets)[0])
out_bytes = env2.file.save(packer="lz4")
with open(OUT_BUNDLE, "wb") as f:
    f.write(out_bytes)
print(f"\n[✓] Saved {OUT_BUNDLE} with LZ4 + clean PreloadTable ({len(out_bytes):,} bytes)!")
