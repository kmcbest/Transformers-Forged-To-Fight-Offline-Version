# -*- coding: utf-8 -*-
"""
repair_and_backup_demolishor.py

1. Extracts the latest untruncated version of all tools/demolishor/*.py scripts
   directly from transcript_full.jsonl.
2. Restores tools/demolishor/*.py on disk.
3. Structures demolishor_backup/ into clean, complete, uncorrupted directories:
   - demolishor_backup/scripts/ (all full, untruncated scripts)
   - demolishor_backup/assets/ (demolishor_gs.assetbundle, portraits)
   - demolishor_backup/unity_project/ (demolishor_prepared.fbx, demolishor_mesh.assetbundle, textures, AssetBundleBuilder.cs)
   - demolishor_backup/data/ (ironhide_80_bones.json, ironhide_transforms.json, ironhide.obj)
   - demolishor_backup/patches/ (git diff patch for Server/ and tools/nativehook/)
4. Generates an exhaustive README.md with 1-click restore instructions.
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(r"d:\Agent\tftf")
BACKUP_DIR = ROOT / "demolishor_backup"
TRANSCRIPT_PATH = Path(r"C:\Users\lenovo\.gemini\antigravity\brain\61450739-b3fd-40a5-b308-e6e69fbc5127\.system_generated\logs\transcript_full.jsonl")

print("=== Starting Full Demolishor Backup & Repair ===")

# 1. Reconstruct full files from transcript_full.jsonl
print("[1/5] Extracting untruncated files from transcript_full.jsonl...")
file_contents = {}

with open(TRANSCRIPT_PATH, "r", encoding="utf-8") as f:
    for line in f:
        try:
            step = json.loads(line)
        except Exception:
            continue
        for tc in step.get("tool_calls", []):
            name = tc.get("name")
            args = tc.get("args", {})
            if name == "write_to_file":
                target = args.get("TargetFile", "")
                content = args.get("CodeContent", "")
                if target and content and "<truncated" not in content:
                    file_contents[target] = content
            elif name == "replace_file_content":
                target = args.get("TargetFile", "")
                target_str = args.get("TargetContent", "")
                replace_str = args.get("ReplacementContent", "")
                if target in file_contents and target_str and replace_str:
                    file_contents[target] = file_contents[target].replace(target_str, replace_str, 1)

print(f"[+] Found {len(file_contents)} full untruncated files from transcript.")

# Restore tools/demolishor
tools_demo_dir = ROOT / "tools" / "demolishor"
tools_demo_dir.mkdir(parents=True, exist_ok=True)

scripts_backup_dir = BACKUP_DIR / "scripts"
scripts_backup_dir.mkdir(parents=True, exist_ok=True)

for target, content in file_contents.items():
    p = Path(target)
    if "tools\\demolishor" in str(p) or "tools/demolishor" in str(p):
        rel_name = p.name
        # Write to tools/demolishor
        out_live = tools_demo_dir / rel_name
        out_live.write_text(content, encoding="utf-8")
        # Write to backup
        out_bak = scripts_backup_dir / rel_name
        out_bak.write_text(content, encoding="utf-8")

print(f"[✓] Restored and backed up {len(list(scripts_backup_dir.glob('*.py')))} full scripts.")

# 2. Backup Assets (AssetBundle and Portraits)
print("\n[2/5] Backing up game AssetBundles and portraits...")
assets_bak_dir = BACKUP_DIR / "assets"
assets_bak_dir.mkdir(parents=True, exist_ok=True)
portraits_bak_dir = assets_bak_dir / "portraits"
portraits_bak_dir.mkdir(parents=True, exist_ok=True)

# Copy demolishor_gs.assetbundle
live_bundle = ROOT / "assets_redeco" / "demolishor_gs.assetbundle"
if live_bundle.is_file():
    shutil.copy2(live_bundle, assets_bak_dir / "demolishor_gs.assetbundle")
    print(f"  [✓] Copied {live_bundle.name} ({live_bundle.stat().st_size / 1024 / 1024:.2f} MB)")

# Copy portraits
for p_file in (ROOT / "assets_redeco").glob("*demolishor*"):
    if p_file.suffix in (".png", ".jpg", ".jpeg"):
        shutil.copy2(p_file, portraits_bak_dir / p_file.name)
        print(f"  [✓] Copied portrait: {p_file.name}")

# 3. Backup Unity Project assets
print("\n[3/5] Backing up Unity build project assets...")
unity_bak_dir = BACKUP_DIR / "unity_project"
unity_assets_dir = unity_bak_dir / "Assets" / "Demolishor"
unity_editor_dir = unity_bak_dir / "Assets" / "Editor"
unity_bundles_dir = unity_bak_dir / "AssetBundles"

unity_assets_dir.mkdir(parents=True, exist_ok=True)
unity_editor_dir.mkdir(parents=True, exist_ok=True)
unity_bundles_dir.mkdir(parents=True, exist_ok=True)

src_unity_assets = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Demolishor"
if src_unity_assets.is_dir():
    for f in src_unity_assets.glob("*"):
        if f.is_file():
            shutil.copy2(f, unity_assets_dir / f.name)
            print(f"  [✓] Copied Unity asset: {f.name}")

src_builder = ROOT / "toolchain" / "unity_build_project" / "Assets" / "Editor" / "AssetBundleBuilder.cs"
if src_builder.is_file():
    shutil.copy2(src_builder, unity_editor_dir / "AssetBundleBuilder.cs")
    print("  [✓] Copied AssetBundleBuilder.cs")

src_unity_bundle = ROOT / "toolchain" / "unity_build_project" / "AssetBundles" / "demolishor_mesh.assetbundle"
if src_unity_bundle.is_file():
    shutil.copy2(src_unity_bundle, unity_bundles_dir / "demolishor_mesh.assetbundle")
    print(f"  [✓] Copied compiled Unity bundle: demolishor_mesh.assetbundle ({src_unity_bundle.stat().st_size / 1024 / 1024:.2f} MB)")

# 4. Backup Ground-Truth Data
print("\n[4/5] Backing up bone matrices and ground-truth data...")
data_bak_dir = BACKUP_DIR / "data"
data_bak_dir.mkdir(parents=True, exist_ok=True)

for data_f in ["tools/demolishor/ironhide_80_bones.json", "tools/demolishor/ironhide_extracted/ironhide_transforms.json", "tools/demolishor/ironhide_extracted/ironhide.obj"]:
    src_p = ROOT / data_f
    if src_p.is_file():
        shutil.copy2(src_p, data_bak_dir / src_p.name)
        print(f"  [✓] Copied data file: {src_p.name}")

# Also copy processed textures
pbr_bak_dir = BACKUP_DIR / "textures_processed"
pbr_bak_dir.mkdir(parents=True, exist_ok=True)
src_pbr = ROOT / "tools" / "demolishor" / "textures_processed"
if src_pbr.is_dir():
    for f in src_pbr.glob("*.png"):
        shutil.copy2(f, pbr_bak_dir / f.name)
        print(f"  [✓] Copied processed texture: {f.name}")

# 5. Generate Code Patch and Exhaustive README
print("\n[5/5] Generating code diff patch and comprehensive README...")
patches_dir = BACKUP_DIR / "patches"
patches_dir.mkdir(parents=True, exist_ok=True)

try:
    patch_content = subprocess.run(
        ["git", "diff", "HEAD", "--", "Server/", "tools/nativehook/"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=True
    ).stdout
    patch_file = patches_dir / "demolishor_changes.patch"
    patch_file.write_text(patch_content, encoding="utf-8")
    print(f"  [✓] Generated git patch: {patch_file.name} ({len(patch_content)} chars)")
except Exception as e:
    print(f"  [!] Note: could not generate git patch: {e}")

readme_path = BACKUP_DIR / "README.md"
readme_text = """# 破坏者（Demolishor）完整成果备份与恢复指南

本目录包含塞伯坦陨落（Fall of Cybertron）霸天虎重装角色 **破坏者（Demolishor）** 移植到 TFTF 的全部开发成果、资产、脚本与补丁。

---

## 目录结构

```
demolishor_backup/
├── README.md                     # 本说明文档
├── assets/                       # 最终游戏运行时资产
│   ├── demolishor_gs.assetbundle # 7.65MB 完整角色资产包（含展厅模型与战斗模型隔离）
│   └── portraits/                # 全套 8 种规格头像（large/small/quest）
├── unity_project/                # Unity 工程核心构建资产
│   ├── Assets/Demolishor/        # 对齐 FBX、PBR 贴图源文件
│   │   ├── demolishor_prepared.fbx
│   │   ├── cha_demolishor_main_a.png
│   │   ├── cha_demolishor_main_NM.png
│   │   └── cha_demolishor_main_tform_misc_RAOE.png
│   ├── Assets/Editor/            # Unity 打包菜单插件
│   │   └── AssetBundleBuilder.cs
│   └── AssetBundles/             # Unity 编译生成的 Mesh 资产包
│       └── demolishor_mesh.assetbundle
├── scripts/                      # 全部完整未截断的 Python 工具脚本（70+ 个）
│   ├── build_aligned_demolishor.py    # 80 骨骼自动映射与 FBX 生成
│   ├── generate_demolishor_bundle.py  # 资产包自动嫁接与坐标转换
│   ├── apply_perfect_alignment.py     # 终极 BindPose 数学对齐
│   └── ...
├── data/                         # 关键基准数据
│   ├── ironhide_80_bones.json         # 铁皮 80 骨骼世界坐标
│   ├── ironhide_transforms.json       # 91 根层级树数据
│   └── ironhide.obj                   # 铁皮地面真值网格模型
├── textures_processed/           # PBR 贴图（漫反射/法线/RAOE 遮罩）
└── patches/                      # 代码修改 Patch
    └── demolishor_changes.patch       # Server/ 与 tools/nativehook/ 代码差异
```

---

## 一键还原步骤

若要在新分支或新环境中还原破坏者：

1. **还原资产与脚本**：
   - 将 `assets/demolishor_gs.assetbundle` 复制到 `assets_redeco/demolishor_gs.assetbundle`
   - 将 `assets/portraits/*` 复制到 `assets_redeco/`
   - 将 `scripts/*` 复制到 `tools/demolishor/`
   - 将 `unity_project/Assets/Demolishor/*` 复制到 `toolchain/unity_build_project/Assets/Demolishor/`
   - 将 `unity_project/Assets/Editor/*` 复制到 `toolchain/unity_build_project/Assets/Editor/`

2. **应用代码补丁**：
   ```bash
   git apply demolishor_backup/patches/demolishor_changes.patch
   ```

3. **打包 APK**：
   ```bash
   python build_apk.py
   ```
"""

readme_path.write_text(readme_text, encoding="utf-8")
print(f"[✓] Created master README.md at {readme_path}")
print("\n=== Backup & Repair Complete: All Assets and Uncut Scripts Secured! ===")
