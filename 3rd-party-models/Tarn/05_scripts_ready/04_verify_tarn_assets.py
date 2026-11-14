#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
04_verify_tarn_assets.py
Tarn 资产门禁自检脚本 (检查贴图规范、Mesh 顶点 16-bit 限额及 AssetBundle 合规性):
  python 05_scripts_ready/04_verify_tarn_assets.py [--bundle path/to/tarn_gs.assetbundle]
"""
import argparse
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

TARN_ROOT = Path(__file__).resolve().parent.parent
TEX_DIR = TARN_ROOT / "06_working" / "unified_textures"
DONOR_DIR = TARN_ROOT / "04_donor_reference" / "ultramagnus_gs_leader"


def check_texture_pair(prefix: str):
    nm_p = TEX_DIR / f"{prefix}_NM_kabam.png"
    raoe_p = TEX_DIR / f"{prefix}_RAOE.png"
    base_p = TEX_DIR / (f"{prefix}_a.png" if "main" in prefix else f"{prefix}_A.png")
    ok = True
    for p in (nm_p, raoe_p, base_p):
        if not p.is_file():
            print(f"  [!] 跳过缺失贴图: {p.name}")
            return False
    nm = np.array(Image.open(nm_p).convert("RGBA"))
    raoe = np.array(Image.open(raoe_p).convert("RGBA"))
    base = np.array(Image.open(base_p).convert("RGBA"))
    dielectric_ratio = float((nm[:, :, 2] < 20).mean())
    b_a_diff = int(np.abs(raoe[:, :, 2].astype(int) - raoe[:, :, 3].astype(int)).max())
    r_p10, r_p90 = np.percentile(raoe[:, :, 0], [10, 90])
    g_min = int(raoe[:, :, 1].min())
    glow_px = int((raoe[:, :, 2] > 200).sum())
    base_a_min = int(base[:, :, 3].min())

    print(f"\n[检查贴图] {prefix}: size={nm.shape[1]}x{nm.shape[0]}")
    print(f"  Diffuse Alpha 最小值     : {base_a_min} (须为 255 全不透明)")
    print(f"  NM.B 电介质(紫漆<20)占比: {dielectric_ratio*100:.1f}% (正常应 >50%)")
    print(f"  RAOE.R 粗糙度 p10..p90   : {r_p10:.0f}..{r_p90:.0f}")
    print(f"  RAOE.G AO 最小值         : {g_min}")
    print(f"  RAOE.B 发光像素数 (>200) : {glow_px}, max|B-A|={b_a_diff}")
    if base_a_min < 255:
        print("  [FAIL] Diffuse 存在透明像素，可能导致角色半透/穿帮！")
        ok = False
    if b_a_diff > 2:
        print("  [FAIL] RAOE.B 与 RAOE.A 未保持同步！")
        ok = False
    if dielectric_ratio < 0.45:
        print("  [FAIL] NM.B 电介质占比偏低，紫漆装甲可能在游戏中被渲染成黑斑镜面金属！")
        ok = False
    return ok


def check_bundle(bundle_path: Path):
    import UnityPy
    print(f"\n[检查 AssetBundle] {bundle_path}")
    size_mb = bundle_path.stat().st_size / (1024 * 1024)
    print(f"  压缩后大小: {size_mb:.2f} MB (packer='lz4')")
    env = UnityPy.load(str(bundle_path))

    robo_spec = json.loads((DONOR_DIR / "cha_ultramagnus_gs_leader_00_bones.json").read_text(encoding='utf-8'))
    veh_spec = json.loads((DONOR_DIR / "cha_ultramagnus_gs_leader_01_bones.json").read_text(encoding='utf-8'))
    ok = True
    stale_um_cab = "1701bf1e2efc86b7f16eaab30f47c200"

    for fname in env.file.files.keys():
        if stale_um_cab in fname.lower():
            print(f"  [FAIL] 发现残留旧通天晓 CAB 文件名: {fname}")
            ok = False

    checked_meshes = set()
    for o in env.objects:
        if o.type.name == 'AssetBundle':
            ab = o.read_typetree()
            c_keys = [k for k, _ in ab.get('m_Container', [])]
            print(f"  BundleName='{ab.get('m_AssetBundleName')}', Container={c_keys}")
            if not any('tarn_gs.prefab' in k for k in c_keys):
                print("  [FAIL] m_Container 缺少 tarn_gs.prefab！")
                ok = False
        elif o.type.name == 'Mesh':
            m = o.read_typetree()
            vc = m.get('m_VertexData', {}).get('m_VertexCount', 0)
            idx_fmt = m.get('m_IndexFormat', 0)
            c = m.get('m_LocalAABB', {}).get('m_Center', {})
            e = m.get('m_LocalAABB', {}).get('m_Extent', {})
            name = m.get('m_Name', '')
            if idx_fmt == 0 and vc > 65535:
                print(f"  [FAIL] Mesh '{name}' verts={vc} > 65535 且 m_IndexFormat=0！")
                ok = False
            if name == "cha_tarn_gs_00":
                checked_meshes.add(name)
                print(f"  Robot Mesh '{name}': verts={vc}, AABB center=({c.get('x',0):.2f},{c.get('y',0):.2f},{c.get('z',0):.2f}) ext=({e.get('x',0):.2f},{e.get('y',0):.2f},{e.get('z',0):.2f})")
                if c.get('y', 0) < 3.0 or e.get('y', 0) < 3.0:
                    print("  [FAIL] Robot Mesh 中心/半高低于 3m，疑似未正确旋转导致角色躺平！")
                    ok = False
                if m.get('m_BoneNameHashes') != robo_spec['m_BoneNameHashes']:
                    print("  [FAIL] Robot Mesh m_BoneNameHashes 与通天晓 53 骨母壳不一致！")
                    ok = False
            elif name == "cha_tarn_gs_01":
                checked_meshes.add(name)
                print(f"  Vehicle Mesh '{name}': verts={vc}, AABB center=({c.get('x',0):.2f},{c.get('y',0):.2f},{c.get('z',0):.2f}) ext=({e.get('x',0):.2f},{e.get('y',0):.2f},{e.get('z',0):.2f})")
                if m.get('m_BoneNameHashes') != veh_spec['m_BoneNameHashes']:
                    print("  [FAIL] Vehicle Mesh m_BoneNameHashes 与通天晓 40 骨母壳不一致！")
                    ok = False
        elif o.type.name == 'Texture2D':
            t = o.read()
            if stale_um_cab in (t.m_StreamData.path or '').lower():
                print(f"  [FAIL] Texture2D '{t.m_Name}' 仍指向旧 CAB 流路径: {t.m_StreamData.path}")
                ok = False
            if t.m_Name.startswith('cha_tarn_'):
                print(f"  [Tex] '{t.m_Name}' {t.m_Width}x{t.m_Height} fmt={t.m_TextureFormat}")
                if t.m_Name.endswith('_RAOE') and t.m_TextureFormat != 3:
                    print(f"  [FAIL] RAOE '{t.m_Name}' 应为 RGB24 (fmt=3)，实际 fmt={t.m_TextureFormat}！")
                    ok = False
                elif (t.m_Name.endswith('_a') or t.m_Name.endswith('_A') or t.m_Name.endswith('_NM')) and t.m_TextureFormat != 4:
                    print(f"  [FAIL] Diffuse/NM '{t.m_Name}' 应为 RGBA32 (fmt=4)，实际 fmt={t.m_TextureFormat}！")
                    ok = False
        elif o.type.name == 'AudioClip':
            ac = o.read_typetree()
            src = (ac.get('m_Resource', {}) or {}).get('m_Source', '')
            if stale_um_cab in src.lower():
                print(f"  [FAIL] AudioClip '{ac.get('m_Name')}' 仍指向旧 CAB 资源路径: {src}")
                ok = False
        elif o.type.name == 'SkinnedMeshRenderer' and o.path_id in (
            -6929876573960912518, 8776407398459535180,
            -3806277267122844283, 5537406516109862368,
            -3099658301619870697, 4543470380929569169,
        ):
            s = o.read_typetree()
            if s.get('m_Enabled', False) or s.get('m_Mesh', {}).get('m_PathID', 0) != 0:
                print(f"  [FAIL] 武器 SMR {o.path_id} 未禁用/清零！")
                ok = False
        elif o.type.name == 'Material' and o.path_id in (5520268204611603145, 5691636987978222339):
            m = o.read_typetree()
            fl = dict(m['m_SavedProperties']['m_Floats'])
            if fl.get('_emissive_range', -1.0) != 0.0:
                print(f"  [FAIL] 材质 {o.path_id} _emissive_range={fl.get('_emissive_range')} != 0.0！")
                ok = False

    if checked_meshes != {"cha_tarn_gs_00", "cha_tarn_gs_01"}:
        print(f"  [FAIL] 缺少目标 Mesh，仅找到: {checked_meshes}")
        ok = False
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", type=str, default="", help="可选：待验证的最终 .assetbundle 路径")
    args = ap.parse_args()

    print("=== Tarn 资产质量门禁检查 ===")
    ok1 = check_texture_pair("cha_tarn_tform_misc")
    ok2 = check_texture_pair("cha_tarn_main")
    ok3 = True
    if args.bundle:
        bp = Path(args.bundle)
        if bp.is_file():
            ok3 = check_bundle(bp)
        else:
            print(f"[!] 找不到指定的 Bundle: {bp}")
            ok3 = False
    if not (ok1 and ok2 and ok3):
        sys.exit(1)
    print("\n[✓] Tarn 所有资产与 AssetBundle 门禁检查全部通过！")


if __name__ == "__main__":
    main()
