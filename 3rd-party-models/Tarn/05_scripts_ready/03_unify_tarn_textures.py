#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
03_unify_tarn_textures.py
通用纯 Python 脚本 (无需 Blender，仅需 Pillow + numpy):
  python 05_scripts_ready/03_unify_tarn_textures.py

功能:
1. 读取 06_working/robot_baked_raw/* 烘焙出的人形贴图 与 03_vehicle_preprocessed_tftf/tarn_palette_target.json 锁定色板；
2. 将人形的深紫装甲、炭黑关节、暗金/银炮管颜色连续调色拉齐到坦克同色区，并叠加统一 45% AO 质感；
3. 按 Kabam EB/Character/PBR 铁律打包人形贴图至 06_working/unified_textures/:
   - cha_tarn_main_a.png       (统一校色 + 粉紫自发光写入 Albedo, RGBA)
   - cha_tarn_main_NM_kabam.png(R=Nx, G=Ny, B=物理金属度: 紫漆/发光=0纯电介质防黑斑, 骨架/炮管=95~155)
   - cha_tarn_main_NM_std.png  (Unity 编辑器预览用标准三轴法线)
   - cha_tarn_main_RAOE.png    (R=缎面陶瓷粗糙度 172..225, G=通透AO >=165, B=A=双通道粉紫发光掩码!)
4. 同步复制 03_vehicle_preprocessed_tftf/ 坦克贴图至 06_working/unified_textures/ 形成全套统一产出。
"""
import json
import shutil
import sys
from pathlib import Path
import numpy as np
from PIL import Image, ImageFilter

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

TARN_ROOT = Path(__file__).resolve().parent.parent
BAKED_DIR = TARN_ROOT / "06_working" / "robot_baked_raw"
VEH_PREP_DIR = TARN_ROOT / "03_vehicle_preprocessed_tftf"
OUT_DIR = TARN_ROOT / "06_working" / "unified_textures"
OUT_DIR.mkdir(parents=True, exist_ok=True)


def unify_robot_textures():
    palette = json.loads((VEH_PREP_DIR / "tarn_palette_target.json").read_text(encoding='utf-8'))["regions"]

    req = [
        "tarn_robot_albedo.png", "tarn_robot_normal_std.png",
        "tarn_robot_roughness.png", "tarn_robot_ao.png",
        "tarn_robot_emission.png", "tarn_robot_metallic.png",
    ]
    for fn in req:
        if not (BAKED_DIR / fn).is_file():
            raise FileNotFoundError(f"缺少人形烘焙图 {BAKED_DIR / fn}，请先运行 Blender 02 脚本！")

    alb = np.array(Image.open(BAKED_DIR / "tarn_robot_albedo.png").convert("RGB"), dtype=np.float32)
    nrm = np.array(Image.open(BAKED_DIR / "tarn_robot_normal_std.png").convert("RGB"))
    ao = np.array(Image.open(BAKED_DIR / "tarn_robot_ao.png").convert("L"), dtype=np.float32)
    emit_rgb = np.array(Image.open(BAKED_DIR / "tarn_robot_emission.png").convert("RGB"), dtype=np.float32)
    metal_raw = np.array(Image.open(BAKED_DIR / "tarn_robot_metallic.png").convert("L"), dtype=np.float32)
    rough_raw = np.array(Image.open(BAKED_DIR / "tarn_robot_roughness.png").convert("L"), dtype=np.float32)
    H, W, _ = alb.shape

    r, g, b = alb[:, :, 0], alb[:, :, 1], alb[:, :, 2]
    max_c = np.maximum(np.maximum(r, g), b)
    min_c = np.minimum(np.minimum(r, g), b)
    lum = 0.299 * r + 0.587 * g + 0.114 * b
    sat = (max_c - min_c) / np.maximum(max_c, 1.0)

    # 1. 自发光区域识别与双通道羽化掩码
    emit_lum = emit_rgb.max(axis=-1)
    glow_mask_raw = Image.fromarray(np.where(emit_lum > 24.0, 255, 0).astype(np.uint8), "L")
    glow_feathered = np.maximum(
        np.array(glow_mask_raw, dtype=np.float32),
        np.array(glow_mask_raw.filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float32)
    )
    w_glow = np.clip(glow_feathered / 255.0, 0.0, 1.0)

    # 2. 材质分区连续权重 (用于跨模型颜色对齐)
    w_purple = np.clip((b - g) / 22.0, 0.0, 1.0) * np.clip((sat - 0.18) / 0.14, 0.0, 1.0) * (1.0 - w_glow)
    w_gold = np.clip((r - b - 24.0) / 24.0, 0.0, 1.0) * np.clip((g - b - 8.0) / 18.0, 0.0, 1.0) * (1.0 - w_glow)
    w_silver = np.clip((0.26 - sat) / 0.10, 0.0, 1.0) * np.clip((lum - 85.0) / 28.0, 0.0, 1.0) * (1.0 - w_glow)
    w_dark = np.clip(1.0 - w_glow - w_purple - w_gold - w_silver, 0.0, 1.0)

    # 3. 连续色调拉齐到 Tarn 坦克目标色板
    p_tgt = np.array(palette["purple_armor"]["median_rgb"], dtype=np.float32)
    if (w_purple > 0.6).any():
        p_cur = np.median(alb[w_purple > 0.6], axis=0)
        p_scale = np.clip(p_tgt / np.maximum(p_cur, 8.0), 0.55, 1.75)
    else:
        p_scale = np.array([1.0, 1.0, 1.0], dtype=np.float32)
    purple_graded = np.clip(alb * p_scale[None, None, :], 0, 255)

    dark_graded = np.stack([
        np.clip(17.0 + r * 0.65, 14, 70),
        np.clip(16.0 + g * 0.65, 14, 70),
        np.clip(22.0 + b * 0.65, 18, 82),
    ], axis=-1)

    glow_tgt = np.array(palette["neon_magenta_emissive"]["base_rgb"], dtype=np.float32)
    glow_graded = glow_tgt[None, None, :] * (0.80 + 0.20 * (ao[:, :, None] / 255.0))

    alb_unified = (
        purple_graded * w_purple[:, :, None]
        + dark_graded * w_dark[:, :, None]
        + alb * (w_silver[:, :, None] + w_gold[:, :, None])
        + glow_graded * w_glow[:, :, None]
    )

    # 叠加与坦克一致的 ~45% AO 阴影对比，并防止紫/炭黑死黑
    ao_mult = 0.58 + 0.42 * (ao[:, :, None] / 255.0)
    alb_unified = np.clip(alb_unified * ao_mult, 0, 255)
    alb_unified = np.where(w_glow[:, :, None] > 0.5, glow_graded, alb_unified)
    Image.fromarray(np.dstack([alb_unified.astype(np.uint8), np.full((H, W), 255, dtype=np.uint8)]), "RGBA").save(
        OUT_DIR / "cha_tarn_main_a.png"
    )

    # 4. 重建 Kabam NM.B 物理金属度（紫色涂装严格清零=0，防止环境反光变黑！）
    metal_b = (
        w_purple * 0.0
        + w_glow * 0.0
        + w_dark * np.clip(metal_raw * 0.25, 18.0, 40.0)
        + w_silver * np.clip(metal_raw * 0.65 + 45.0, 110.0, 165.0)
        + w_gold * 155.0
    )
    metal_u8 = np.clip(metal_b, 0, 255).astype(np.uint8)
    Image.fromarray(np.stack([nrm[:, :, 0], nrm[:, :, 1], metal_u8, np.full((H, W), 255, dtype=np.uint8)], axis=-1), "RGBA").save(
        OUT_DIR / "cha_tarn_main_NM_kabam.png"
    )
    Image.fromarray(np.stack([nrm[:, :, 0], nrm[:, :, 1], nrm[:, :, 2], np.full((H, W), 255, dtype=np.uint8)], axis=-1), "RGBA").save(
        OUT_DIR / "cha_tarn_main_NM_std.png"
    )

    # 5. 统一陶瓷缎面粗糙度 + 通透 AO + 双通道自发光 RAOE
    rough_r = (
        w_purple * np.clip(182.0 + (rough_raw / 255.0) * 28.0, 180, 214)
        + w_silver * np.clip(145.0 + (rough_raw / 255.0) * 25.0, 142, 175)
        + w_gold * 156.0
        + w_dark * np.clip(218.0 + (rough_raw / 255.0) * 22.0, 215, 242)
        + w_glow * 165.0
    ).astype(np.uint8)
    ao_airy = np.clip(165.0 + ((ao / 255.0) ** 0.72) * 90.0, 165, 255).astype(np.uint8)
    em_u8 = np.clip(glow_feathered, 0, 255).astype(np.uint8)
    Image.fromarray(np.stack([rough_r, ao_airy, em_u8, em_u8], axis=-1), "RGBA").save(
        OUT_DIR / "cha_tarn_main_RAOE.png"
    )
    print("[✓] 已输出校色对齐后的 Tarn 人形贴图 -> 06_working/unified_textures/")


def sync_vehicle_textures():
    mapping = {
        "tarn_veh_base_graded.png": "cha_tarn_tform_misc_A.png",
        "tarn_veh_normal_kabam.png": "cha_tarn_tform_misc_NM_kabam.png",
        "tarn_veh_normal_std.png": "cha_tarn_tform_misc_NM_std.png",
        "tarn_veh_raoe.png": "cha_tarn_tform_misc_RAOE.png",
    }
    for src, dst in mapping.items():
        sp = VEH_PREP_DIR / src
        if sp.is_file():
            shutil.copy2(sp, OUT_DIR / dst)
    print("[✓] 已同步载具预处理贴图至 06_working/unified_textures/")


if __name__ == "__main__":
    sync_vehicle_textures()
    if (BAKED_DIR / "tarn_robot_albedo.png").is_file():
        unify_robot_textures()
    else:
        print("[i] 尚未检测到 06_working/robot_baked_raw/ 人形烘焙图，仅同步了坦克贴图。")
