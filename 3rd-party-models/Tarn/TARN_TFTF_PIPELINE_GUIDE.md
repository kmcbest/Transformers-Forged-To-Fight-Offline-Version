# Tarn（塔恩）引入《变形金刚：百炼为战》预处理资产包与全流程作业指南

> **适用对象**：家用电脑上的 **Antigravity Agent** 与开发者  
> **目标游戏**：*Transformers: Forged to Fight (TFTF)*（Unity 5.5/5.6 IL2CPP Runtime + Unity 2020.3.31f1 Build Tooling）  
> **参考母体管线**：仓库 `origin/blender` 分支 [THIRD_PARTY_3D_MODEL_PIPELINE.md](https://github.com/kmcbest/Transformers-Forged-To-Fight-Offline-Version/blob/blender/re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md) 及 `.agents/skills/hard_surface_character_grafting/SKILL.md`

---

## 一、本压缩包已完成的预处理与目录分类清单

本目录已按**源文件 / 预处理成果 / 官方母壳基准 / 即用脚本**完成物理分类，所有可在无 Blender 环境下提前算好的贴图、色板、母壳骨架与缺图兜底均已生成完毕；解压到家用机（例如 `TFTF-blender` 仓库的 `3rd-party-models/tarn/`）即可直接跑 Blender 步骤。

```text
Tarn/
├── TARN_TFTF_PIPELINE_GUIDE.md              <-- 本文档（总控流程与排坑铁律）
│
├── 01_robot_source/                         <-- [人形源资产：Blender 2.79 网友高精度渲染稿]
│   ├── source/last comp3.blend              <-- 原始 105MB Cycles 工程（裸模 48.1万顶点 / 101.8万面；含Subsurf/Mirror达343万+面）
│   ├── textures/MetalGrime013_NRM_3K.jpeg   <-- 原始附带的唯一外部法线图
│   ├── fallback_textures/                   <-- [已预处理] 11张缺失外部贴图的中性兜底图（含 .jpg 副本、关联脏迹、DECAL透明图），防止 Cycles 烘焙出紫红块！
│   ├── packed_masks_preview/                <-- 从 .blend 内包解出的典型磨损遮罩 512 预览图
│   └── blend_audit_report.json              <-- [已预处理] 116个Mesh/曲线/负缩放物体/64个无UV物体精确体检报告
│
├── 02_vehicle_source/                       <-- [载具源资产：Tactical Arena 提取坦克]
│   ├── Tarn_Vehicle.glb                     <-- 带 127 节点完整骨架与刚性蒙皮的 glTF 2.0 坦克（82,970 顶点 / 57,454 面）
│   ├── obj/                                 <-- 原始拆件 OBJ（TarnTank_Mesh + TreadL + TreadR）
│   ├── textures/                            <-- Tactical Arena 烘焙图（注意 Emissive 全黑，Glow 在第二材质）
│   ├── raw_textures/                        <-- 原始 64x64 图集与 AO 源图
│   └── renders/                             <-- 6 视角官宣形态与配色参考图
│
├── 03_vehicle_preprocessed_tftf/            <-- [已完成预处理！可直接进 Unity/Bundle]
│   ├── tarn_veh_base_graded.png             <-- 1024 RGBA：已从 GLB `TarnTank_Glow_MAT` 2526个面精准烘入粉紫灯带，并提亮死黑履带底色
│   ├── tarn_veh_emissive_mask.png           <-- 1024 L：从 GLB 光栅化+轻度羽化提取的 12,543 像素灯带掩码
│   ├── tarn_veh_normal_kabam.png            <-- 1024 RGBA：Sobel 硬表面接缝法线 + Blue通道重建精确金属度（紫漆=0，银炮管/金排气=145~155）
│   ├── tarn_veh_normal_std.png              <-- 1024 RGBA：Unity/Blender 预览用标准三轴切线法线
│   ├── tarn_veh_raoe.png                    <-- 1024 RGBA：R=陶瓷统一粗糙度(177~234)，G=通透AO(>=165)，B=A=双通道同步发光掩码
│   ├── tarn_palette_target.json             <-- [核心] 锁定好的 Tarn 紫/黑/银/金/粉紫发光目标色板，用于后续把 Blender 人形拉成同一画风！
│   └── preview_tarn_veh_tftf.png            <-- 4 象限视觉验收总览图
│
├── 04_donor_reference/                      <-- [已从官方 APK 预提取权威母壳！家用机无需重新解包]
│   ├── megatron_gs_leader2015/              <-- ★ 首选推荐母壳（G1 威震天：坦克+右臂融合炮+30手指+现成紫色光束/紫火特效）
│   │   ├── cha_megatron_gs_leader2015_00_robot.obj
│   │   ├── cha_megatron_gs_leader2015_01_tank.obj
│   │   ├── cha_megatron_gs_leader2015_wpns_cannon_right.obj
│   │   ├── robot_51_bones_and_bindposes.json    <-- 51 骨精确顺序、BindPose、BoneNameHashes & Avatar TOS
│   │   ├── tank_21_bones_and_bindposes.json     <-- 21 骨坦克精确顺序、BindPose、BoneNameHashes
│   │   ├── cannon_3_bones_and_bindposes.json    <-- 右臂炮 FX / COG / mount 三骨基准
│   │   ├── skeleton_hierarchy.json              <-- Showcase/LW 双 Prefab SMR 清单与重要坑点警告
│   │   ├── material_and_fx_params.json          <-- 官方材质参数 & SP3 区间 [[2800, 5566], [2233, 8666]]
│   │   └── donor_textures/                      <-- 官方原版贴图对照
│   └── megatron_cin_rotf/                   <-- 备选赛星坦克形状参考（但右手无五指，不建议作主壳）
│
├── 05_scripts_ready/                        <-- [已写好的跨平台工作流脚本（直接运行/微调）]
│   ├── 01_blender_prepare_scene_and_clean_robot.py
│   ├── 02_blender_bake_robot_pbr.py
│   ├── 03_unify_tarn_textures.py            <-- 本机实测通过！
│   └── 04_verify_tarn_assets.py             <-- 本机实测通过！
│
└── 06_working/                              <-- 中间产物输出目录
    ├── robot_baked_raw/                     <-- 02脚本输出的人形原始烘焙通道
    ├── unified_textures/                    <-- 03脚本输出的人形+载具统一校色终极贴图（已预同步坦克组）
    └── fbx_exports/                         <-- 最终导出的待入 Unity 低模 FBX 存放处
```

---

## 二、母壳选型与双模型底子关键结论（给家里 Agent 的背景对齐）

1. **首选母壳：`megatron_gs_leader2015`（G1 威震天）**
   - 人形 `51` 骨带**完整 30 根手指骨** + 独立右臂融合炮槽位（可保留 Tarn 右臂双联融合炮与左手完整手势），坦克 `_01` 为标准双履带 `21` 骨，SP3 变形区间 `[[2800, 5566], [2233, 8666]]`。
   - 原生携带紫色系 FX（`fx_m_megatron_gs_beam_a`、`fx_m_purple_fire_plume_a`、`tform_misc` 紫光参数），换血程度最低。
2. **两大模型现状与必须处理的硬伤**：
   - **人形 `.blend`**：造型好、近似 A-Pose 且已含紫/黑/银/粉光配色意图，但它是 **343万+面渲染工程**，缺少 `11` 张外部链接纹理、只有两套孤立手骨、`64/116` 零件无 UV、存在 `Cylinder.001` 与 `Plane.020` **负行列式缩放（法线朝内）**、整体偏向 `-X/-Z` 且高度约 `82.3` 单位。
   - **坦克 `.glb`**：干净手游低模，**正对方向已与官方一致（无需 180° 旋转！）**，唯一需注意 **双履带共占 `36,224` 面**（需减面控制整车顶点 `< 65,535`）以及**地面基准差异**：官方坦克 `_01` 网格履带底面处于本地 `Y = -1.549m`，而非 `0.0`！

---

## 三、家用机实操流程（Phase 1 → Phase 5）

### Phase 1：Blender 清理工程、减面、对位与搭建权威母壳骨架

> 环境要求：**Blender 3.6 LTS**（在 `TFTF-blender` 仓库一般位于 `toolchain/blender/blender.exe`）。

1. **执行自动清理与对齐脚本**：
   ```powershell
   & "<path_to_blender>\blender.exe" -b -P "05_scripts_ready/01_blender_prepare_scene_and_clean_robot.py"
   ```
2. **脚本已完成的工作**：
   - 使用 `01_robot_source/fallback_textures/` 一键重连全部缺失贴图并填充空图，彻底杜绝 Cycles 烘焙出现紫红色；
   - 清理纯悬浮 DECALmachine 卡片，转 `BezierCurve` 为 Mesh，移除高倍率 `Subsurf`，应用 `Mirror`，**自动修复 `Cylinder.001` / `Plane.020` 负缩放法线并统一朝外**；
   - 在合并压面至 `~3.8万` 三角面之前，保留每个零件的 `part__<原名称>` 顶点组标记（便于 Phase 3 按硬表面零件批量分配刚性权重！）；
   - 将人形整体缩放到 `11.45m` 高、脚踩 `Z=0`、面向 `-Y`，并载入 `megatron_gs_leader2015` 人形/坦克/右炮参考白模及 `51 骨 / 21 骨` 权威骨架；
   - 导入 `Tarn_Vehicle.glb`，将左右高模履带各减面 `75%`（降到各 ~4,500 面，整车约 ~3万面 < `65,535` 顶点限额），按 `0.78×` 缩放并下移至 `Z = -1.549` 对齐官方坦克底盘。
3. **人工/Agent 精细复检要点（打开 `06_working/tarn_workspace_cleaned.blend` 查看）**：
   - 检查合并减面后**面具眼部、胸口能源线、右臂双联融合炮**细节是否被过度 Decimate（若局部太糊，可从原 `.blend` 对面部/头盔/炮管单独放宽 `Decimate ratio = 0.25~0.5`）。
   - **决策右臂融合炮方案**：
     - *方案 A（稳妥省事）*：将右臂双联融合炮保留在人形网格并随 `RightForeArm` 刚性运动，同时在后续 Unity 注入时**隐藏/置空母体 `wpns_cannon_right` 与 `wpns_mace_left`**（需在模型中删净不要重叠两个炮！）。
     - *方案 B（进阶更还原）*：把双联融合炮独立拆成 `Tarn_Cannon_Right`（归零到右手臂外侧并与 `cha_megatron_gs_leader2015_wpns_cannon_right.obj` 对齐），绑定 3 骨 `FX / COG / mount` 后替换母体的 `wpns_cannon_right`，可继承 G1 威“发射/变形时炮管微调与 `FX` 炮口精确出弹”机制。

---

### Phase 2：Cycles PBR 烘焙与跨来源双形态统一校色

1. **Blender 烘焙人形原始通道**：
   ```powershell
   & "<path_to_blender>\blender.exe" -b "06_working/tarn_workspace_cleaned.blend" -P "05_scripts_ready/02_blender_bake_robot_pbr.py"
   ```
   - 该脚本为低模建立不重叠 `UV_TFTF_Main`，关闭重脏迹 Mix 干扰，一口气烘焙输出至 `06_working/robot_baked_raw/`：
     `albedo` / `normal_std` / `roughness` / `ao` / `emission` / `metallic`（已通过节点临时接驳 `Emission` 精确烘出物理金属遮罩）。
   - *画质进阶建议*：若希望低模边缘保留原高模的锐利倒角法线，可在不减面保留高模副本的前提下将本脚本改为 `use_selected_to_active = True`（高模向低模烘焙法线与 AO），效果更惊艳。

2. **统一校色与 Kabam PBR 通道打包**：
   ```powershell
   python "05_scripts_ready/03_unify_tarn_textures.py"
   ```
   - 读取 `03_vehicle_preprocessed_tftf/tarn_palette_target.json` 作为统一度量衡，自动把人形烘焙出的 **深紫主甲、炭黑骨架、金/银炮管、粉紫自发光** 连续拉齐到与坦克完全一致的色阶与 ~45% AO 质感。
   - 严格按 `EB/Character/PBR` 契约输出到 `06_working/unified_textures/`：
     - **紫色涂装与发光区 `NM.B = 0`（纯电介质）**：防止进游戏变成反光黑铁；
     - **裸露金属件/枪灰炮管 `NM.B = 110~165`**；
     - **陶瓷 Satin 粗糙度 `RAOE.R ≈ 175~215`**，消灭一亮一哑的割裂感；
     - **双通道自发光 `RAOE.B = RAOE.A = 255`（带 0.6px 羽化）**。

---

### Phase 3：人形 51 骨 / 坦克 21 骨刚体蒙皮、SBS 验招与 FBX 导出

> 参考标准流程：`THIRD_PARTY_3D_MODEL_PIPELINE.md` 第 4~5 章 与 `tools/elita_one/` 脚本范式。

1. **人形 51 骨绑定（基于 `ARM_MegatronGS_Robot51`）**：
   - 在绑定前，建议按 `part__*` 顶点组批量执行 **100% 硬表面刚体权重分配**（每个装甲零件整块赋予 1 根骨骼，严禁“自动平滑权重”导致装甲弯折如橡胶！）：
     - 头部面具/头雕 → `Head`
     - 胸腹/双肩背塔架/履带翼 → `Spine1` / `Spine`
     - 大臂/小臂/手掌 → 对齐 `LeftArm`/`LeftForeArm`/`LeftHand` 与 `RightArm`/`RightForeArm`/`RightHand`（或微调骨骼所在关节旋转角度与肩宽，确保跟 `REF_cha_megatron_gs_leader2015_00_robot` 重合，**切忌改变母壳骨骼命名与最终导出时的 `BindPose` 顺序**！）
     - 手指 30 根骨（`LeftHandThumb/Index/Middle/Ring/Pinky 1..3` 及右侧）→ 利用距离/关节最近邻指派，或参考 Elita One 管线按每节指骨分段硬切。
     - 大腿/小腿/脚掌 → `Left/RightUpLeg`、`Left/RightLeg`、`Left/RightFoot`、`ToeBase`（务必确保 A-Pose 站姿腿间距与 `REF_00` 对齐，防止待机交叉撞腿）。
   - **Side-by-Side (SBS) 动作验收**：务必比照 G1 威待机/重击/挥拳动作渲染 3~5 个极端帧检查穿模（尤其肩部履带架与头部、右臂融合炮与胯部是否干涉）。

2. **坦克 21 骨绑定（基于 `ARM_MegatronGS_Tank21`）**：
   - 将 `TarnTank_Mesh`、`TarnTankTreadL_Mesh`、`TarnTankTreadR_Mesh` 合并为统一单材质网格（或保留单一 `tform_misc` 材质，因为 `tarn_veh_base_graded.png` 与 `tarn_veh_raoe.png` 已经将 `TarnTank_Glow_MAT` 灯带烘进来了！）。
   - 依据原有 GLB `127` 骨顶点组快捷重映射到母体 `21` 骨：
     - `TarnTank_GunUpper*`（主双联炮塔）→ `chop1_cannon_right` / `chop1_forearm_armor_right`
     - `TarnTank_Body_Jnt` / `Main_Jnt` / `TarnTank_GunLower*`（车身主壳）→ `chop2_torso_main_center`
     - 前/后左右侧翼及履带（`TreadL/R`, `AxelFL/FR/BL/BR`）→ 对应 `chop1_shoulder_left/right`、`chop1_calf_left/right`、`chop1_foot_left/right`、`chop2_thigh_left/right`。

3. **FBX 导出铁律**：
   - 应用全对象位移/旋转/缩放（`Location=0, Rotation=0, Scale=1`），无任何负缩放（`det > 0`）。
   - 导出设定：`Forward = -Z Forward`, `Up = Y Up`, `Apply Scalings = FBX All`, `Add Leaf Bones = False`, `Use Armature Deform Only`。
   - 分别输出至 `06_working/fbx_exports/tarn_robot_prepared.fbx` 与 `tarn_tank_prepared.fbx`（如选用方案 B 另导出 `tarn_cannon_prepared.fbx`）。

---

### Phase 4：Unity 2020.3.31f1 编译与 AssetBundle 注入（核心防踩坑铁律）

参考 `tools/elita_one/prepare_elita_unity_assets.py`、`generate_elita_one_bundle.py` 与 `patch_textures_and_materials_only.py`：

1. **Unity 导入设置**：
   - `ModelImporter`: `animationType = Generic`, `useFileScale = false`, `bakeAxisConversion = false`, `globalScale = 1.0f`，确认 Import Normals 无异常开孔、单 Mesh 顶点 `< 65,535`（`m_IndexFormat = 0`）。
   - 构建中间包 `tarn_mesh.assetbundle`（Target: Android）。

2. **用 UnityPy 注入母壳 `megatron_gs_leader2015.assetbundle` 时必须遵守的 6 条铁律**：
   - **铁律 1 — 骨骼与哈希原样锁死**：目标 Mesh 的 `m_BindPose`、`m_BoneNameHashes`、`m_RootBoneNameHash` **必须 100% 沿用 `04_donor_reference/megatron_gs_leader2015/` JSON 里的官方权威数值**！绝对不要混入 Blender 自动生成的新骨骼哈希，否则角色在动画帧里会散架或消失。
   - **铁律 2 — 双 Prefab SMR 物理隔离**：母壳内含 `Megatron_GS_Leader2015` (Showcase) 与 `Megatron_GS_Leader2015_lw` (Combat LW) 两棵独立骨骼树！两边的 `_00`、`_01` 及武器 SMR 必须**严格各自指向自己 Prefab 树内的 Transform `PathID`**，绝不允许 Showcase 指向 LW 骨架。
   - **铁律 3 — 处理 G1 威多余武器 (`skeleton_hierarchy.json` 特有警告)**：
     - `megatron_gs_leader2015` 每个 Prefab 中都有 **两处** `wpns_cannon_right` SMR（`Reference/cannon/` 与 `RightForeArm/staticCannon/`），还有 **一处** `LeftHand/mace/wpns_mace_left` 链锤 SMR！
     - **如不用链锤**：将 `_wpns_mace_left` 网格清空为最小 dummy 退化三角面（勿直接删除 GameObject 以免动画曲线引用报错），或在 SMR `m_Enabled = False`；
     - **如方案 A（炮已随手）**：同样将 `_wpns_cannon_right` 置空/禁用；**如方案 B（换炮）**：同步替换两处 `wpns_cannon_right` 或按需激活。
   - **铁律 4 — 避免 `main_tform_misc_RAOE` UV 上下半区踩踏**：
     - 官方母壳中人形 `main` 与坦克 `tform_misc` 共用同一张 `main_tform_misc_RAOE`（上半区给人形，下半区给坦克）。
     - **推荐最干净写法**：在 Bundle 里把人形材料的 `_pbr_composite_tex` 设为 `cha_tarn_main_RAOE`，再**克隆/新建独立 `Texture2D` PathID 给坦克材料 `_pbr_composite_tex` 使用 `cha_tarn_tform_misc_RAOE`**（两张图均保持完整 `0..1` UV，彻底免去 UV 缩放拼半区的麻烦与串色！）。
   - **铁律 5 — `RAOE` 格式与自发光 Shader 参数**：
     - 注入 `RAOE` 贴图后务必确认 UnityPy 写入为 **Format 4 (`RGBA32`)**（不能是无 Alpha 的 `RGB24` / `ETC2_RGB4`）。
     - 材质属性同步写入：`_Mode = 3.0`、`_clearcoat_reflectance_range = 0.1`、`_emissive_range = 0.0`（切记不是 1.0！）、`_emissive_overbright_range = 120.0`、`_emissive_intensity_col = (0.95, 0.16, 0.78, 0.0)`。
   - **铁律 6 — 独立命名隔离与 LZ4 压缩**：
     - 将资产包中 `CAB-` 字符串及 `m_Container` 内路径前缀彻底隔离重命名为 `tarn_gs`（`ModelID = "tarn_gs"`），防止覆盖原版 G1 威震天！
     - 保存必须使用 `bf.save(packer="lz4")`！

3. **门禁脚本一键验收**：
   ```powershell
   python "05_scripts_ready/04_verify_tarn_assets.py" --bundle "assets_redeco/tarn_gs.assetbundle"
   ```

---

### Phase 5：服务端注册、三规格立绘与 NativeHook 本地化

1. **三规格头像准备**：沿用规范准备 `portrait_tarn_gs_large.png` (512×512 RGBA)、`portrait_tarn_gs_small.jpg` (256×256 RGB)、`portrait_tarn_gs_quest.png` (512×512 RGBA)（可直接用本目录 `02_vehicle_source/renders/` 与 Blender 渲染人形全身照合成精修）。
2. **服务端注册**：
   - `Server/gamedata.py` 注册角色 `BotID` 与 `ModelID: "tarn_gs"`（参照威震天属性与动作原型，或结合项目 `ABILITY_AUTHORING.md` 挂载技能）；
   - `Server/sp3_timings.json` 添加 `"tarn_gs": [[2800, 5566], [2233, 8666]]`（实机若需微调变身时间点再细校准）。
3. **本地化与招式表**：
   - `assets/xlate/custom_special_attacks.json` 配置塔恩中文 SP1/SP2/SP3（例如死亡之音/双重融合炮齐射/终极审判）并运行 `tools/generate_special_attacks.py`；
   - `tools/nativehook/hook.c` 的 `hook_162` 增加 `tarn` / `TARN` 的中文名称“塔恩”与传记拦截；
   - 核对 `moves.assetbundle >= 945` 门禁，运行 `build_apk.py` 打包实机验收！

---

## 四、给家里 Antigravity 的“一键开工指令模板”

解压本文件夹放到家用工程对应位置后，直接对 Antigravity 说：

> “这是准备接入《百炼为战》的 **Tarn（塔恩）** 预处理资产包，请先阅读包内的 `TARN_TFTF_PIPELINE_GUIDE.md`、参考仓库的 `re_notes/THIRD_PARTY_3D_MODEL_PIPELINE.md` 与 `hard_surface_character_grafting/SKILL.md`，然后直接从 `05_scripts_ready/01_blender_prepare_scene_and_clean_robot.py` 开始跑通 Blender 清理与 Cycles 烘焙、完成 51骨人形/21骨坦克绑定并导出注入 `tarn_gs.assetbundle`。”
