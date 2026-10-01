# 破坏者（Demolishor）完整成果备份与恢复指南

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
