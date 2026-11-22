import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(r"E:\Agent\TFTF-blender")
SRC_TEX_DIR = Path(r"O:\agent\transformers-fall-of-cybertron-combaticons\textures")
OUT_DIR = ROOT / "3rd-party-models" / "BlastOff" / "02_textures"
OUT_DIR.mkdir(parents=True, exist_ok=True)
UNITY_TEX_DIR = ROOT / "toolchain" / "unity_build_project" / "Assets" / "BlastOff" / "Textures"
UNITY_TEX_DIR.mkdir(parents=True, exist_ok=True)


def find_tex(name: str):
    if not name:
        return None
    p = SRC_TEX_DIR / name
    if p.exists():
        return p
    low = name.lower()
    for f in SRC_TEX_DIR.iterdir():
        if f.name.lower() == low:
            return f
    return None


def load_rgb(name: str, size, default_rgb=(88, 72, 52)) -> np.ndarray:
    fp = find_tex(name)
    if fp:
        im = Image.open(fp).convert("RGB")
        if im.size != size:
            im = im.resize(size, Image.Resampling.LANCZOS)
        return np.array(im, dtype=np.uint8)
    arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
    arr[:, :] = default_rgb
    return arr


def load_normal_gl(name: str, size) -> np.ndarray:
    """Load DirectX normal map and flip G channel (G = 255 - G) to Unity OpenGL standard."""
    fp = find_tex(name)
    if not fp:
        arr = np.zeros((size[1], size[0], 3), dtype=np.uint8)
        arr[:, :] = (128, 128, 255)
        return arr
    im = Image.open(fp).convert("RGB")
    if im.size != size:
        im = im.resize(size, Image.Resampling.LANCZOS)
    arr = np.array(im, dtype=np.uint8)
    arr[:, :, 1] = 255 - arr[:, :, 1]
    return arr


def extract_purple_em_in_boxes(diff: np.ndarray, boxes_and_strengths: list, min_bg=6, min_b=30) -> tuple[np.ndarray, np.ndarray]:
    """Extract glowing purple/violet conduits & vents directly from Blast Off's own diffuse UV regions.

    NOTE: The generic *_e.jpg files in the FOC pack (chest_e.jpg, head_e.jpg, armup_e.jpg, legs_e.jpg,
    armlo_e.jpg, vh.jpg) belong to other Combaticons and miss Blast Off's shoulders, chest grille,
    lower chest crescents, and shin strips. Extracting from Blast Off's verified UV island regions
    while excluding matte purple armor (pelvis/collar) produces 100% anatomically accurate emission.
    """
    h, w, _ = diff.shape
    df = diff.astype(np.float32)
    r, g, b = df[:, :, 0], df[:, :, 1], df[:, :, 2]

    # Purple/violet signal: Blue clearly exceeds Green AND Blue is at least 84% of Red (excludes tan/brown/grey)
    purple_delta = np.maximum(0.0, b - g)
    is_purple = (purple_delta >= min_bg) & (b >= r * 0.84) & (b >= min_b)
    # Soft ramp from purple strength
    raw_strength = np.clip((purple_delta - min_bg + 4.0) / 38.0, 0.0, 1.0)
    raw_strength = np.where(is_purple, np.maximum(raw_strength, 0.55), 0.0)

    em_mask = np.zeros((h, w), dtype=np.uint8)
    for (x0, y0, x1, y1), target_val in boxes_and_strengths:
        x0c, x1c = max(0, x0), min(w, x1)
        y0c, y1c = max(0, y0), min(h, y1)
        sub_str = raw_strength[y0c:y1c, x0c:x1c]
        vals = np.clip(sub_str * target_val, 0.0, 255.0).astype(np.uint8)
        em_mask[y0c:y1c, x0c:x1c] = np.maximum(em_mask[y0c:y1c, x0c:x1c], vals)

    # Boost diffuse on active emissive pixels into rich saturated purple (avoid high G so HDR doesn't wash to white)
    m = (em_mask.astype(np.float32) / 145.0).clip(0.0, 1.0)[..., None]
    vivid_purple = np.array([155.0, 25.0, 245.0], dtype=np.float32)
    out_diff = np.clip(df * (1.0 - m * 0.90) + vivid_purple * (m * 0.90), 0, 255).astype(np.uint8)
    return out_diff, em_mask


def make_decepticon_tile(size) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Build (diff, norm_gl, em_mask, metallic_mask) for TR_FactionLogo_Mat_INST.001."""
    w, h = size
    diff = np.zeros((h, w, 3), dtype=np.uint8)
    diff[:, :] = (55, 48, 40)  # Dark Blast Off brown-tan backing plate
    fp = find_tex("DecepticonLogo.png")
    em_mask = np.zeros((h, w), dtype=np.uint8)
    if fp:
        logo = Image.open(fp).convert("RGBA").resize(size, Image.Resampling.LANCZOS)
        la = np.array(logo, dtype=np.float32)
        alpha = (la[:, :, 3] / 255.0)[..., None]
        # Rich deep purple badge (keep R/G controlled so badge stays purple instead of pinkish-white)
        badge_purple = np.array([145, 22, 235], dtype=np.float32)
        diff = (diff.astype(np.float32) * (1.0 - alpha) + badge_purple * alpha).astype(np.uint8)
        # Keep RAOE.B ~105 so the badge glows rich purple without blowing out to white
        em_mask = np.clip(la[:, :, 3] * (105.0 / 255.0), 0, 255).astype(np.uint8)
    norm = np.zeros((h, w, 3), dtype=np.uint8)
    norm[:, :] = (128, 128, 255)
    met = np.zeros((h, w), dtype=np.uint8)
    met[:, :] = np.where(em_mask > 20, 0, 120).astype(np.uint8)
    return diff, norm, em_mask, met


def assemble_tile(diff_name: str, norm_name: str, boxes_and_strengths: list, size: tuple[int, int], is_head=False, min_bg=6):
    diff = load_rgb(diff_name, size)
    norm = load_normal_gl(norm_name, size)

    if is_head:
        h, w, _ = diff.shape
        em_mask = np.zeros((h, w), dtype=np.uint8)
        # 1. Eyes ONLY (left eye visor & right eye visor) — keep crown [Y=0..195] strictly matte!
        for box_x, box_y in [((191, 226), (201, 221)), ((288, 323), (201, 221))]:
            x0, x1 = box_x
            y0, y1 = box_y
            for y in range(y0, y1):
                for x in range(x0, x1):
                    r, g, b = [int(v) for v in diff[y, x]]
                    is_frame = (r > 120 and g > 115 and abs(r - g) < 22 and abs(r - b) < 25)
                    is_visor = not is_frame and (b > g + 8 or (r < 110 and g < 110 and b < 125))
                    if is_visor:
                        # Rich saturated purple diffuse & calibrated RAOE.B (150, NOT 255!) so eyes glow VIVID PURPLE instead of white!
                        em_mask[y, x] = 150
                        diff[y, x] = [155, 22, 255]
        # 2. Rear head micro vents
        diff, rear_mask = extract_purple_em_in_boxes(diff, [((204, 460, 286, 476), 120)], min_bg=10, min_b=40)
        em_mask = np.maximum(em_mask, rear_mask)
    else:
        diff, em_mask = extract_purple_em_in_boxes(diff, boxes_and_strengths, min_bg=min_bg)

    # Compute metallic mask for Kabam NM.B:
    # Brown/tan painted armor: ~25, Dark grey mechanical joints: ~110, Glowing parts: 0
    lum = diff.astype(np.float32).mean(axis=2)
    sat = (diff.max(axis=2) - diff.min(axis=2)) / np.maximum(diff.max(axis=2), 1)
    is_metal = (sat < 0.20) & (lum >= 35) & (lum <= 130)
    metallic = np.where(is_metal, 110, 25).astype(np.uint8)
    metallic = np.where(em_mask > 20, 0, metallic).astype(np.uint8)

    return diff, norm, em_mask, metallic


def build_atlas(tiles_spec, base_prefix: str):
    diff_atlas = np.zeros((2048, 2048, 4), dtype=np.uint8)
    diff_atlas[:, :, 3] = 255

    raoe_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    raoe_atlas[:, :, 0] = 195
    raoe_atlas[:, :, 1] = 255

    norm_game_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_game_atlas[:, :] = (128, 128, 25)

    norm_unity_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)
    norm_unity_atlas[:, :] = (128, 128, 255)

    em_atlas = np.zeros((2048, 2048, 3), dtype=np.uint8)

    for (x, y, w, h), (d, n, em, met) in tiles_spec:
        diff_atlas[y:y+h, x:x+w, :3] = d
        r_chan = np.where(met > 80, 160, 200).astype(np.uint8)
        raoe_atlas[y:y+h, x:x+w, 0] = r_chan
        raoe_atlas[y:y+h, x:x+w, 1] = 255
        raoe_atlas[y:y+h, x:x+w, 2] = em

        norm_game_atlas[y:y+h, x:x+w, 0] = n[:, :, 0]
        norm_game_atlas[y:y+h, x:x+w, 1] = n[:, :, 1]
        norm_game_atlas[y:y+h, x:x+w, 2] = met

        norm_unity_atlas[y:y+h, x:x+w, 0] = n[:, :, 0]
        norm_unity_atlas[y:y+h, x:x+w, 1] = n[:, :, 1]
        norm_unity_atlas[y:y+h, x:x+w, 2] = n[:, :, 2]

        # Blender preview Emission texture: pure neon purple proportional to RAOE.B intensity
        ef = em.astype(np.float32) / 155.0
        em_rgb_color = np.zeros((h, w, 3), dtype=np.uint8)
        em_rgb_color[:, :, 0] = np.clip(ef * 175.0, 0, 255).astype(np.uint8)
        em_rgb_color[:, :, 1] = np.clip(ef * 35.0, 0, 255).astype(np.uint8)
        em_rgb_color[:, :, 2] = np.clip(ef * 255.0, 0, 255).astype(np.uint8)
        em_atlas[y:y+h, x:x+w] = em_rgb_color

    p_diff = OUT_DIR / f"{base_prefix}_Diffuse.png"
    p_norm = OUT_DIR / f"{base_prefix}_Normal.png"
    p_norm_u = OUT_DIR / f"{base_prefix}_Normal_unity.png"
    p_raoe = OUT_DIR / f"{base_prefix}_RAOE.png"
    p_em = OUT_DIR / f"{base_prefix}_Emission.png"

    Image.fromarray(diff_atlas, mode="RGBA").save(p_diff)
    Image.fromarray(norm_game_atlas, mode="RGB").save(p_norm)
    Image.fromarray(norm_unity_atlas, mode="RGB").save(p_norm_u)
    Image.fromarray(raoe_atlas, mode="RGB").save(p_raoe)
    Image.fromarray(em_atlas, mode="RGB").save(p_em)

    em_pct = (raoe_atlas[:, :, 2] > 20).mean() * 100.0
    nz = raoe_atlas[:, :, 2][raoe_atlas[:, :, 2] > 20]
    p50 = np.percentile(nz, 50) if len(nz) else 0
    print(f"  [{base_prefix}] Emissive(>20)={em_pct:.2f}%, p50={p50:.0f}, max={raoe_atlas[:,:,2].max()}")

    for p in [p_diff, p_norm, p_norm_u, p_raoe, p_em]:
        dst = UNITY_TEX_DIR / p.name
        Image.open(p).save(dst)


def main():
    print("=== [Blast Off] Building Anatomically Accurate Vivid Purple PBR Texture Atlases ===")

    # Exact UV boxes verified via Blender FBX polygon mapping (excludes matte purple pelvis & collar!)
    CHEST_BOXES = [
        ((0, 350, 375, 495), 145),     # Front Chest Grille vertical slats & brow louver slits (Arrow #2)
        ((340, 415, 488, 535), 150),   # Lower Chest crescent honeycomb vents (Arrow #3)
        ((760, 615, 855, 715), 135),   # Back turbine ring
        ((394, 706, 422, 730), 125),   # Small chest accent diamond 1
        ((498, 750, 522, 770), 125),   # Small chest accent diamond 2
    ]

    LEGS_BOXES = [
        ((705, 10, 975, 62), 145),     # Shin Top-Right glowing honeycomb fin strip (Arrow #4)
        ((965, 232, 1002, 286), 145),  # Shin outer slit (Arrow #4)
        ((720, 144, 742, 174), 135),   # Shin side slit
        ((412, 385, 434, 496), 145),   # Shin center front vertical glowing strip
        ((186, 542, 304, 636), 140),   # Outer calf/ankle circular wheel hub
    ]

    ARMLO_BOXES = [
        ((406, 460, 474, 512), 140),   # Forearm wrist glowing honeycomb vent
    ]

    ARMUP_BOXES = [
        ((92, 240, 200, 348), 150),    # Shoulder Pad circular gear arc / horseshoe (Arrow #1)
        ((360, 96, 490, 224), 145),    # Shoulder drum spoked glowing ring
        ((404, 256, 472, 316), 140),   # Shoulder drum inner hexagon
        ((228, 164, 320, 212), 130),   # Shoulder top/back mesh vent
    ]

    VEH_BOXES = [
        ((344, 44, 744, 164), 145),    # Shuttle cockpit & upper fuselage wing strips
        ((552, 492, 676, 576), 140),   # Shuttle side thruster vents 1
        ((704, 616, 736, 700), 140),   # Shuttle side thruster vents 2
        ((940, 952, 964, 1004), 145),  # Shuttle tail thruster glow
        ((16, 752, 116, 872), 135),    # Shuttle intake/wing accent
    ]

    robot_tiles = [
        ((0, 0, 1024, 1024), assemble_tile("rb_blastoff_chest_cust_matinst.jpg", "rb_blastoff_chest_cust_matinst_n.jpg", CHEST_BOXES, (1024, 1024), min_bg=5)),
        ((0, 1024, 1024, 1024), assemble_tile("rb_blastoff_legs_cust_matinst.jpg", "rb_blastoff_legs_cust_matinst_n.jpg", LEGS_BOXES, (1024, 1024), min_bg=5)),
        ((1024, 0, 512, 512), assemble_tile("rb_blastoff_head_cust_matinst.jpg", "rb_blastoff_head_cust_matinst_n.jpg", [], (512, 512), is_head=True)),
        ((1536, 0, 512, 512), assemble_tile("rb_blastoff_armlo_cust_matinst.jpg", "rb_blastoff_armlo_cust_matinst_n.jpg", ARMLO_BOXES, (512, 512), min_bg=5)),
        ((1024, 512, 512, 512), assemble_tile("rb_blastoff_armup_cust_matinst.jpg", "rb_blastoff_armup_cust_matinst_n.jpg", ARMUP_BOXES, (512, 512), min_bg=5)),
        ((1536, 512, 512, 512), make_decepticon_tile((512, 512))),
        ((1024, 1024, 1024, 1024), assemble_tile("vh_blastoff_cust_matinst.jpg", "vh_blastoff_cust_matinst_n.jpg", VEH_BOXES, (1024, 1024), min_bg=8)),
    ]
    build_atlas(robot_tiles, "cha_blastoff_main")

    veh_tiles = [
        ((0, 0, 1024, 1024), assemble_tile("vh_blastoff_cust_matinst.jpg", "vh_blastoff_cust_matinst_n.jpg", VEH_BOXES, (1024, 1024), min_bg=8)),
        ((1024, 0, 1024, 1024), assemble_tile("vh_blastoff_cust_matinst.jpg", "vh_blastoff_cust_matinst_n.jpg", VEH_BOXES, (1024, 1024), min_bg=8)),
        ((0, 1024, 512, 512), make_decepticon_tile((512, 512))),
        ((512, 1024, 512, 512), assemble_tile("rb_blastoff_head_cust_matinst.jpg", "rb_blastoff_head_cust_matinst_n.jpg", [], (512, 512), is_head=True)),
        ((1024, 1024, 1024, 1024), assemble_tile("vh_blastoff_cust_matinst.jpg", "vh_blastoff_cust_matinst_n.jpg", VEH_BOXES, (1024, 1024), min_bg=8)),
    ]
    build_atlas(veh_tiles, "cha_blastoff_tform_misc")

    print("[✓] All Blast Off PBR texture atlases built cleanly!")


if __name__ == "__main__":
    main()
