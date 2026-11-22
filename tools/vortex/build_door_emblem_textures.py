import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

import UnityPy
import numpy as np
from PIL import Image

head_path = r"e:\Agent\TFTF-blender\tools\vortex\vortex_gs_head.assetbundle"
env = UnityPy.load(head_path)
obj_map = {o.path_id: o for o in env.objects}

vh_m = obj_map[-2766188856892899435].read()
vd = vh_m.m_VertexData
vc = vd.m_VertexCount
raw = bytes(vd.m_DataSize)
pos = np.ndarray((vc, 3), dtype=np.float32, buffer=raw, strides=(40, 4), offset=0)
uv = np.ndarray((vc, 2), dtype=np.float32, buffer=raw, strides=(8, 4), offset=vc*40)
ib = np.frombuffer(bytes(vh_m.m_IndexBuffer), dtype=np.uint16).reshape(-1, 3)

vh_diff = np.array(Image.open(r"e:\Agent\TFTF-blender\tools\vortex\diag\head_vh_diff.png").convert("RGB"))
dh, dw = vh_diff.shape[:2]

# For each quad (Right: 59,60; Left: 61,62), define exact corner positions in 3D matching [0..1]x[0..1] UVs:
# From inspect_source_emblem_uvs.py:
# Right: v173 (TL, uv=(0,1)), v171 (TR, uv=(1,1)), v172 (BL, uv=(0,0)), v174 (BR, uv=(1,0))
# Left:  v178 (TL, uv=(0,1)), v175 (TR, uv=(1,1)), v176 (BL, uv=(0,0)), v177 (BR, uv=(1,0))
quads = {
    "right": {
        "TL": pos[173], "TR": pos[171], "BL": pos[172], "BR": pos[174],
        "ray_dir": np.array([-0.8801, 0.0637, -0.4706], dtype=np.float64), # inward into door
    },
    "left": {
        "TL": pos[178], "TR": pos[175], "BL": pos[176], "BR": pos[177],
        "ray_dir": np.array([0.8801, 0.0637, -0.4706], dtype=np.float64), # inward into door
    }
}

# Only keep tris near the cabin door region (|X|>0.4, Y in [2.0..4.0], Z in [-0.2..1.8])
tri_centroids = pos[ib].mean(axis=1)
cand_idx = [
    i for i in range(len(ib))
    if i not in (59, 60, 61, 62)
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

def raycast_batch(origins, direction):
    d = direction / np.linalg.norm(direction)
    h = np.cross(d, e2) # (T, 3)
    a = np.einsum("ij,ij->i", e1, h) # (T,)
    valid_a = np.abs(a) > 1e-6
    inv_a = np.where(valid_a, 1.0 / np.where(valid_a, a, 1.0), 0.0)

    out_rgb = np.zeros((len(origins), 3), dtype=np.uint8)
    out_rgb[:] = [182, 164, 74]

    for start in range(0, len(origins), 512):
        o_chunk = origins[start:start+512] # (C, 3)
        s = o_chunk[:, None, :] - v0[None, :, :] # (C, T, 3)
        u_bary = inv_a[None, :] * np.einsum("cti,ti->ct", s, h)
        q = np.cross(s, e1[None, :, :])
        v_bary = inv_a[None, :] * np.einsum("cti,i->ct", q, d)
        t = inv_a[None, :] * np.einsum("ti,cti->ct", e2, q)

        hit = (valid_a[None, :]) & (u_bary >= -1e-3) & (v_bary >= -1e-3) & (u_bary + v_bary <= 1.002) & (t > -0.2) & (t < 0.35)
        # pick smallest |t|
        abs_t = np.where(hit, np.abs(t), 1e9)
        best_tri = np.argmin(abs_t, axis=1)
        best_dist = abs_t[np.arange(len(o_chunk)), best_tri]

        for k in range(len(o_chunk)):
            if best_dist[k] < 1.0:
                ti = best_tri[k]
                ub = np.clip(u_bary[k, ti], 0.0, 1.0)
                vb = np.clip(v_bary[k, ti], 0.0, 1.0)
                wb = 1.0 - ub - vb
                tri_vi = body_tris[ti]
                uv_hit = wb * uv[tri_vi[0]] + ub * uv[tri_vi[1]] + vb * uv[tri_vi[2]]
                px = int(np.clip((uv_hit[0] % 1.0) * dw, 0, dw - 1))
                py = int(np.clip((1.0 - (uv_hit[1] % 1.0)) * dh, 0, dh - 1))
                out_rgb[start + k] = vh_diff[py, px]
    return out_rgb

# Render 512x512 for each side into 1024x512 atlas:
# Left side in texture U=[0.0..0.5] (x=0..512), Right side in U=[0.5..1.0] (x=512..1024)
diff_atlas = np.zeros((512, 1024, 3), dtype=np.uint8)
raoe_atlas = np.zeros((512, 1024, 3), dtype=np.uint8)
raoe_atlas[:, :, 0] = 125 # match head_vh_raoe R=125
raoe_atlas[:, :, 1] = 220 # match head_vh_raoe G=220
raoe_atlas[:, :, 2] = 0

logo_raw = Image.open(r"e:\Agent\TFTF-blender\tools\vortex\DecepticonLogo.png").convert("RGBA")
# Size inside 512x512 panel: ~380x380 centered (matching original FOC logo margin!)
logo_sz = 380
pad = (512 - logo_sz) // 2
logo_resized = np.array(logo_raw.resize((logo_sz, logo_sz), Image.Resampling.LANCZOS))
logo_alpha_full = np.zeros((512, 512), dtype=np.float32)
logo_alpha_full[pad:pad+logo_sz, pad:pad+logo_sz] = logo_resized[:, :, 3] / 255.0
logo_rgb_full = np.zeros((512, 512, 3), dtype=np.float32)
# Crisp Decepticon purple (matching original FOC purple logo on door)
logo_rgb_full[pad:pad+logo_sz, pad:pad+logo_sz, 0] = 105
logo_rgb_full[pad:pad+logo_sz, pad:pad+logo_sz, 1] = 35
logo_rgb_full[pad:pad+logo_sz, pad:pad+logo_sz, 2] = 175

for idx, (side_name, x_offset) in enumerate([("left", 0), ("right", 512)]):
    q = quads[side_name]
    print(f"[*] Raycasting {side_name} door surface (512x512 -> 256x256 down/up or direct 256x256 then upscale 2x for speed)...")
    res = 256
    us = np.linspace(0.0, 1.0, res)
    vs = np.linspace(1.0, 0.0, res) # row 0 is V=1 (top)
    uu, vv = np.meshgrid(us, vs)
    # Bilinear pos on quad
    pts = (
        (1 - uu)[..., None] * vv[..., None] * q["TL"] +
        uu[..., None] * vv[..., None] * q["TR"] +
        (1 - uu)[..., None] * (1 - vv)[..., None] * q["BL"] +
        uu[..., None] * (1 - vv)[..., None] * q["BR"]
    ).reshape(-1, 3)
    # start slightly outside door, cast inward
    origins = pts - q["ray_dir"] * 0.05
    bg_256 = raycast_batch(origins, q["ray_dir"]).reshape(res, res, 3)
    bg_512 = np.array(Image.fromarray(bg_256).resize((512, 512), Image.Resampling.BILINEAR)).astype(np.float32)

    a = logo_alpha_full[:, :, None]
    comp = bg_512 * (1.0 - a) + logo_rgb_full * a
    diff_atlas[:, x_offset:x_offset+512] = np.clip(comp, 0, 255).astype(np.uint8)
    # Soft purple RAOE.B=85 on emblem only (0 on background) so it matches original door badge cleanly
    raoe_atlas[:, x_offset:x_offset+512, 2] = np.clip(logo_alpha_full * 85.0, 0, 255).astype(np.uint8)

Image.fromarray(diff_atlas).save(r"e:\Agent\TFTF-blender\tools\vortex\diag\emblem_diff_1024x512.png")
Image.fromarray(raoe_atlas).save(r"e:\Agent\TFTF-blender\tools\vortex\diag\emblem_raoe_1024x512.png")
nm_64 = np.zeros((64, 64, 3), dtype=np.uint8)
nm_64[:, :] = [128, 128, 255]
Image.fromarray(nm_64).save(r"e:\Agent\TFTF-blender\tools\vortex\diag\emblem_nm_64x64.png")
print("[✓] Saved emblem_diff_1024x512.png, emblem_raoe_1024x512.png, emblem_nm_64x64.png!")
