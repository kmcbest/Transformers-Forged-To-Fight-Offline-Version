---
name: tftf_revival
description: Comprehensive knowledge base and pitfall avoidance guide for Transformers: Forged to Fight (TFTF) offline revival development, including Unity assetbundle modifications, IL2CPP native hooking, 3D character/mod/relic scaling and camera alignment, gamedata payload generation, and APK packaging.
---

# Transformers: Forged to Fight (TFTF) Revival Development & Pitfall Guide

This skill documents critical domain knowledge, reverse-engineered architecture, and common pitfalls to avoid when working on the TFTF offline revival project.

---

## 0. 项目核心架构与核心文件导航地图 (Project Architecture & Core File Navigation Map)

本项目是一个基于逆向工程的完全离线单机复活重构工程。为避免在多模块排查时迷失方向，必须清晰掌握以下 5 大核心功能层及其对应的核心文件权责划分：

```
[客户端 APK] (Unity 2017 + IL2CPP arm64)
  │
  ├── 1. 运行时底层 NativeHook 层 (tools/nativehook/)
  │      └── 拦截 C# 虚表与通信 -> libdothook.so (内存级离线微服务器)
  │
  ├── 2. 服务端数据与载荷生成层 (Server/)
  │      └── gamedata.py (单一真理源) -> export_payload.py -> tftf_offline_payload.bin
  │
  ├── 3. 资产与过场动作层 (assets_netflix/ & assets_redeco/)
  │      └── moves.assetbundle (945 招式大包) + character_fx*.assetbundle (物理火花与过场材质)
  │
  ├── 4. 角色定义与本地化字典 (bot_names_zh.json & special_attacks_zh.h)
  │      └── 全角色中英文名、必杀技描述哈希表
  │
  └── 5. 顶层打包与真机部署层 (build_apk.py & INSTALL-ADB.py)
```

### 0.1 核心业务逻辑与数据流 (Game Data & Server Layer)

| 核心文件 | 核心职能与记录的内容 | 关键符号 / 函数 / 结构 |
| :--- | :--- | :--- |
| [`Server/gamedata.py`](file:///d:/Agent/tftf/Server/gamedata.py) | **全项目游戏数值与阵容的单一真理源 (Single Source of Truth)**。<br>1. **角色总阵容**：定义全 77+ 名角色的阵营（`autobot`/`decepticon`）、职业（`braw`/`tact`/`scou`/`demo`/`warr`/`tech`）与初始星级。<br>2. **数值曲线**：HP/ATK 基础成长模型与战斗力（Rating / PI）公式。特化角色的弱化约束（如水货饿鲨）。<br>3. **大招段数**：必杀技段数（SP1~SP3）解锁规则与必杀伤害倍率。<br>4. **离线响应生成**：生成客户端启动与漫游所需的全部标准 JSON。 | `ROSTER`: 角色阵容字典<br>`base_stats()`: 属性计算函数<br>`_STAR_BASE`: 星级基础数值表<br>`_CLASS_MOD`: 职业系数表<br>`max_special_attacks()`: 必杀槽位控制<br>`build_user_data()`: 玩家背包/战队/进度数据<br>`build_blueprints()`: 角色/模块/遗物蓝图映射 |
| [`Server/export_payload.py`](file:///d:/Agent/tftf/Server/export_payload.py) | **离线二进制数据库烘焙工具**。<br>将 `gamedata.py` 生成的全部动静态 HTTP 响应路由与 `Server/sp3_timings.json` 烘焙为单一内存对齐的紧凑二进制文件：`build/tftf_offline_payload.bin`（约 23 MB，33000+ 条路由条目）。打包进 APK 的 `assets/` 供 C 语言内嵌微服务器直接 mmap 检索。 | `build_payload()`<br>`PAYLOAD_MAGIC`: `TFTFPAY\0`<br>`add("@sp3_timings")` |
| [`Server/sp3_timings.json`](file:///d:/Agent/tftf/Server/sp3_timings.json) | **全角色三气大招变身时间轴配置表**。<br>记录每个角色施放 SP3（超必杀）期间，人形（`character_model`）与载具变形车态（`transformed`）在时间轴上的切换毫秒区间。支持手机目录热重载调试。 | `intervals: [{"on_ms": ..., "off_ms": ...}]`<br>`notes`: 中文角色标注与形态说明 |
| [`Server/fakeserver.py`](file:///d:/Agent/tftf/Server/fakeserver.py) | **离线路由调度参考原型**。<br>记录副本移动路线校验（`build_quest_movedir`）、副本开始（`build_quest_begin`）、基地展台（`build_base_active`）等动态交互逻辑。 | `_quest_positions`<br>`get_saved_team()` |
| [`Server/responses/`](file:///d:/Agent/tftf/Server/responses/) | **预烘焙的基础 Canned JSON 响应目录**。<br>存放 `GET__bcg_getUserData.json`（玩家全角色背包）、`GET__bcg_getLoginData.json`（全角色蓝图与基础定义）等预导出文件。 | 绝不可手工随意编辑，由 `python Server/gamedata.py` 自动导出覆写。 |

---

### 0.2 角色定义、技能与本地化字典 (Character Definitions, Skills & Localization)

| 核心文件 | 核心职能与记录的内容 | 关键符号 / 结构 |
| :--- | :--- | :--- |
| [`bot_names_zh.json`](file:///d:/Agent/tftf/bot_names_zh.json) /<br>[`Server/bot_names_zh.json`](file:///d:/Agent/tftf/Server/bot_names_zh.json) | **全角色官方中英文对照字典**。<br>包含全 77+ 名角色 ID、英文原名、官方简体中文名及所属派系。用于蓝图注册（`display_name`）与基地/选人界面名称显示。 | 键为 `bot_id`，如 `"chromia_gs_kabam": {"en": "Chromia", "zh": "克劳莉娅", "faction": "汽车人 (Autobots)"}` |
| [`tools/nativehook/special_attacks_zh.h`](file:///d:/Agent/tftf/tools/nativehook/special_attacks_zh.h) | **必杀技中英文文本与技能描述哈希表**。<br>记录所有角色的 SP1、SP2、SP3 技能名称与技能招式中文详细说明。NativeHook 层拦截字符串查找时提供中文替换。 | `ID_SPECIAL_ATTACK_MOVE_*`<br>`ID_SPECIAL_ATTACK_DESCRIPTION_MOVE_*` |
| [`tools/nativehook/bot_names_zh.h`](file:///d:/Agent/tftf/tools/nativehook/bot_names_zh.h) | **C 语言底层角色名与别名映射表**。<br>提供 `bot_id` 与中文展示名的即时查询，用于战斗结算与 HUD 显示。 | `BotNameEntry g_bot_names_zh[]` |

---

### 0.3 底层逆向 Hook 与原生运行时 (IL2CPP Native Hook & Reverse Engineering)

| 核心文件 | 核心职能与记录的内容 | 关键符号 / 函数 / 槽位 |
| :--- | :--- | :--- |
| [`tools/nativehook/hook.c`](file:///d:/Agent/tftf/tools/nativehook/hook.c) | **整套项目的逆向工程核心枢纽 (The Core Engine)**。<br>1. **槽位映射表 (`H[]`)**：170+ 个 IL2CPP 函数拦截。<br>2. **内嵌微服务器 (`inapk_server.c`)**：在游戏内部拦截 Localhost 8080，直接查询 `tftf_offline_payload.bin`。<br>3. **SP3 变身动力学引擎**：通过 `hook_138` (PropData.SetActive)、`hook_139` (SP3MOVE)、`hook_142/143` (CinematicState)、`hook_145` (FixedUpdate pump) 驱动大招车形态与武器显隐。<br>4. **手感与连击状态机**：`hook_154` (Action 2 滑屏拦截) + `hook_165` (PlayerDodgeState) 双重保障后撤立即清空连击段数。 | `hook_138`: 武器/变形部件渲染显隐 (`PROPGOACT`)<br>`hook_139`: SP3 动作未配置兜底解析 (`SP3MOVE`)<br>`hook_142 / hook_143`: SP3 进出状态机 (`SP3XIN` / `SP3XOUT`)<br>`hook_145`: SP3 变身泵驱动 (`SP3BEAT`)<br>`hook_154`: 滑屏与轻重击输入拦截 (`COMBAT_ACTION`)<br>`hook_165`: 闪避后撤状态机 (`DODGE_ENTER`)<br>`reset_player_attack_chain()`: 连击槽重置 |
| [`tools/nativehook/compile_hook.py`](file:///d:/Agent/tftf/tools/nativehook/compile_hook.py) | **NativeHook 自动化交叉编译脚本**。<br>使用 NDK Clang 将 `hook.c`、`inapk_server.c`、`arena.c` 编译为 `libdothook.so` (arm64-v8a)。 | 自动检测项目内置 `toolchain/android-ndk-r26d`。 |
| [`TECHNICAL_NOTES.md`](file:///d:/Agent/tftf/TECHNICAL_NOTES.md) | **深层底层技术细节文档**。<br>记录内存布局、虚表偏移、Hook 槽位号详细对照表、Protobuf/JSON 解析细节、Matinee 电影级切镜阶段工作原理。 | 遇到未知虚表崩溃或调用链异常时首要参考文档。 |

---

### 0.4 资产包、动作库与特效层 (AssetBundles, Movesets & VFX)

| 目录 / 文件 | 核心职能与记录的内容 | 铁律与关键规范 |
| :--- | :--- | :--- |
| [`assets_netflix/`](file:///d:/Agent/tftf/assets_netflix/) | **官方权威资产底包目录 (Netflix Exclusives Source)**。<br>原版 Kabam 9.2.0 APK 缺失克劳莉娅（Chromia）和封锁（Dead End）。全部动作与过程特效**必须以此目录为基底**！<br>- `moves.assetbundle` (943 官方动作)<br>- `character_fx_procedural.assetbundle` (含 Chromia 大招挥斧光弧 `fx_m_Chromia_SP3_trail 1` 等独占材质)<br>- `character_anim_procedural.assetbundle` (含饿鲨等角色全套 SP3 剪辑) | **铁律**：严禁使用 Kabam 原版 APK 覆写此目录或以此目录外的包作为动作底包！ |
| [`assets_redeco/`](file:///d:/Agent/tftf/assets_redeco/) | **自定义魔改与调校包产物目录 (Redeco & Overrides)**。<br>打包时由 `build_phone_apk.py` 优先覆盖进 APK：<br>- `moves.assetbundle`：945 条完整动作库（943 Netflix + 2 回春手 Lifeline 专属缝合动作 + 火花事件注入）。<br>- `character_fx.assetbundle`：物理近战火花粒子系统。<br>- `character_fx_procedural.assetbundle`：保留 Netflix 特效材质的前提下调校自发光火花颜色。<br>- `towers.assetbundle` / `relics.assetbundle`：防御模块与真实遗物 3D 展台模型。 | 必须通过断言守护招式总数 `>= 945`，Chromia 材质存在。 |
| [`tools/apply_spark_tuning.py`](file:///d:/Agent/tftf/tools/apply_spark_tuning.py) | **打击火花物理参数与动作包生成器**。<br>负责解包、参数调校、缝合 Lifeline 动作库并重新以 LZ4 压缩打包 `character_fx.assetbundle`、`character_fx_procedural.assetbundle` 和 `moves.assetbundle`。 | 包含完整的 Fail-Fast 断言校验。 |
| [`tools/spark_tuner.html`](file:///d:/Agent/tftf/tools/spark_tuner.html) &<br>[`打开火花物理调校器.bat`](file:///d:/Agent/tftf/打开火花物理调校器.bat) | **Web 交互式火花物理调校套件**。<br>在浏览器 Canvas 中实时模拟速度、重力加速度、发射角度、拉伸比与色泽，支持一键导出参数命令。 | 双击 `.bat` 即可在默认浏览器启动。 |

---

### 0.5 顶层打包与真机部署 (Build & Deployment Pipeline)

| 核心文件 | 核心职能与命令 |
| :--- | :--- |
| [`build_apk.py`](file:///d:/Agent/tftf/build_apk.py) | **全自动顶层构建脚本**。<br>一键完成：`compile_hook.py` -> `export_payload.py` -> `Server/build_phone_apk.py`，输出 `build/Transformers-9.2-offline-redeco-edition.apk`。 |
| [`Server/build_phone_apk.py`](file:///d:/Agent/tftf/Server/build_phone_apk.py) | **底包重构与重打包核心**。<br>负责：DEX 补丁注入、libil2cpp 修补、AssetBundle 覆盖注入、域名重定向劫持、zipalign 对齐与签名。 |
| [`INSTALL-ADB.py`](file:///d:/Agent/tftf/INSTALL-ADB.py) | **真机自动化部署与测试工具**：<br>- `python INSTALL-ADB.py --auto`：免点击自动查找最新 APK 推送安装。<br>- `python INSTALL-ADB.py --screenshot [--name xxx]`：截取真机当前屏幕回传到本地 `screenshots/` 目录。<br>- 直接运行启动图形界面。 |

---

## 1. Unity AssetBundle & 3D Transform Pitfalls

### 1.1 Compounded Hierarchy Scaling (连乘缩放陷阱)
* **Pitfall**: When scaling a prefab tree recursively, child transforms multiply their parents' local scales (`scale_world = scale_root * scale_child * scale_grandchild...`). A factor like `0.08` applied recursively shrinks deep mesh nodes to `0.08^3 = 0.0005` (microscopic), causing the model to completely disappear ("看不见 / 全都空了").
* **Rule**:
  * **Only modify the direct Level-1 children of the root prefab** (e.g., `s = 0.12 ~ 0.22`).
  * Keep all deeper descendant transforms (grandchildren, meshes) at local scale `Vector3(1.0, 1.0, 1.0)`.

### 1.2 Deep Subtree Y-Position Offsets (高空悬浮坐标陷阱)
* **Pitfall**: Quest map relics and tower models were originally designed to float on top of 25-meter pillar structures. In the prefab assets, the actual mesh gameobjects (`rlc_jazz_01`, `rlc_megatron_w_gs`, `rlc_blaster_gs_wire`, `disc`, etc.) have local `m_LocalPosition.y` hardcoded to **`23.0 ~ 26.5`** inside deep grandchild nodes. Even if the root or level-1 parent is at `Y = 0.0`, the mesh still floats 25 units up in the sky, far above the camera viewport.
* **Rule**:
  * Traverse all transforms in the prefab and reset any deep `m_LocalPosition.y > 15.0` to `0.0`.
  * Position the Level-1 direct child at eye-level (`Y = 0.8 ~ 1.0`) so the 3D model sits directly in front of the showroom camera.

### 1.3 World Terrain & Pillar Occlusion (遮挡视口与巨型地块)
* **Pitfall**: Many relic prefabs contain a 20x20 meter base terrain tile (`base_terrain_metalpanel_01`) and tall pillar structures (`rlc_one_shot_01..04`, `rlc_raid_t1..4`). In the Hero Detail showroom, the horizontal camera at Y=1.0 gets blocked by the giant terrain block or the pillar base.
* **Rule**:
  * Explicitly set `m_IsActive = False` on:
    * `base_terrain_metalpanel_01`
    * `proxy` collider nodes
    * `rlc_one_shot_01`, `rlc_one_shot_02`, `rlc_one_shot_03`, `rlc_one_shot_04`
    * `rlc_raid_t1..4`, `rlc_alliance_t1..4`

---

## 2. Blueprint & Gamedata Architecture

### 2.1 `s1, s2, s3` are NOT Visual Scales
* **Pitfall**: In `GET__bcg_getLoginData.json` / `Server/gamedata.py` blueprints, the fields `s1`, `s2`, `s3` are parsed into `BCGBlueprintBase.Special1Damage / Special2Damage / Special3Damage`. They are combat damage multipliers for Special Attacks 1, 2, and 3 (`special_damage_ratios`). Modifying them does NOT change 3D model scale.
* **Rule**: Keep `s1, s2, s3` at `1.0, 1.0, 1.0` for non-bot items (modules/relics) and `(1.75, 2.50, 3.50)` for playable bots.

### 2.2 Relic vs Defense Module (MODS) 3D Model Mapping
* **Immobilizer vs Paralyzer**:
  * **Paralyzer (机能阻断器)**: Defense Module in `towers.assetbundle` (`mods_immobilizer` prefab) -> Uses portrait `portrait_paralyzer_large.png`.
  * **Immobilizer (禁锢定身器)**: Authentic Relic in `relics.assetbundle` (`rlc3` prefab with `rlc_immobilizer` mesh) -> Uses portrait `portrait_immobilizer_large.png`.
* **Matrix of Leadership (领导模块)**:
  * Authentic 3D Mesh `rlc_the_matrix_of_leadership` resides in prefab **`rlc14`**.
* **Origin Matrix (原初矩阵)**:
  * Authentic 3D Mesh `rlc_the_origin_matrix` resides in prefab **`rlc8`**.
* **Attack & Health Modules**:
  * `mods_attack` (加攻模块 - 红色利刃能量盾) -> Uses `portrait_attack_large.png`.
  * `mods_health` (加血模块 - 蓝色绿十字盾) -> Uses `portrait_health_large.png`.

---

## 3. IL2CPP Native Hooking & UI Interaction

### 3.1 `HeroesScreen` Tab Interaction & Click Binding
* **Pitfall**: If `_screenType` is set to `"building"` when opening the RELICS tab, `HeroesScreen.OnGridItemInitialized` (`0xC5BC3C`) treats items as building plots and fails to bind `HeroPortrait.onClick` / `OnHeroClicked`, resulting in non-clickable tiles that cannot open the 3D Details screen.
* **Rule**:
  * When opening the Relics tab in `hook_42` (`HeroesScreen.SetScreenType`), set `this->_screenType = "relic"`.
  * Ensure `heroesGridContainer` is active and `buildingsGridContainer` is deactivated.

---

## 4. 2D Portraits & Asset Packaging

### 4.1 Portrait Asset Trio & Naming Conventions
Every character, mod, and relic requires 3 portrait formats:
1. `portrait_<stem>_large.png` (512x512 with alpha) -> Injected into `assets/assetpack/portraits_odr/portraits/` (used in Hero Detail screen and full cards).
2. `portrait_<stem>_quest.png` (512x512 / transparent) -> Injected into `assets/assetpack/questboard_odr/questboard/` (used in Quest boards & nodes).
3. `portrait_<stem>_small.jpg` (256x256 RGB JPEG) -> Injected into `assets/assetpack/portraits_odr/portraits/` (used in Team Select, Roster Grid, and mini-portraits).

### 4.2 Custom Redeco Override Priority
* Hand-drawn or custom assets in `assets_redeco/` are automatically prioritized over stock templates by `Server/build_phone_apk.py`.
* Always generate `portrait_*_small.jpg` using high-quality Lanczos resampling from the new `large.png` to keep visual consistency.

---

## 5. Development Workflow & Git Rules

1. **Never Commit Without Explicit Instruction**: Only commit and push when the user explicitly requests it.
2. **Canonical Git Remotes**:
   * Upstream canonical: `Gummygamer/Transformers-Forged-To-Fight-Offline-Version`.
   * User fork: `kmcbest/Transformers-Forged-To-Fight-Offline-Version`.
   * Forbidden fork: Never create PRs or pushes to `geamztheangrybirds727`.
3. **Ignore Media**: Never commit screenshots, recordings, or temporary files from `media/` or `scratch/`.
4. **Standard Build Pipeline**:
   ```powershell
   # 1. Regenerate server JSON payloads
   python Server/gamedata.py

   # 2. Package unsigned APK
   python Server/build_phone_apk.py "c:\Users\Administrator\Desktop\Personal\TFTFRevival\com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk" "build/phone-unsigned-redeco.apk" --scheme http --server-host 127.0.0.1 --server-port 8080 --bundle-server --patched-il2cpp "build/libil2cpp-arm64-patched.so"

   # 3. Zipalign and sign
   .\toolchain\android-13\zipalign.exe -f -p 4 build\phone-unsigned-redeco.apk build\phone-aligned-redeco.apk
   cmd /c ".\toolchain\android-13\apksigner.bat sign --ks build\debug.keystore --ks-pass pass:android --out build\Transformers-9.2-offline-redeco-edition.apk build\phone-aligned-redeco.apk"
   Remove-Item -Force build\phone-unsigned-redeco.apk, build\phone-aligned-redeco.apk
   ```

---

## 6. 特殊着色器特效与“鬼魂/自发光”机制 (Ghost / Hologram Emissive Technique)

### 6.1 PBR Composite (RAOE) 贴图通道解密
在 TFTF 使用的 `EB/Character/PBR` 及 `EB/Character/PBR/Uber` 高级角色着色器中，贴图 `_pbr_composite_tex`（通常命名为 `*_RAOE` 或 `*_RMEA`）采用 4 通道紧凑打包：
* **R 通道 (Red)**：Roughness（粗糙度，控制高光弥散）
* **G 通道 (Green)**：Ambient Occlusion / Metallic（环境遮挡 / 金属度）
* **B 通道 (Blue)**：Cavity / Detail Mask（凹陷与微观细节）
* **A 通道 (Alpha)**：**Emissive Mask（自发光 / 能量辉光蒙版）**
  * `Alpha = 0`（纯黑）：完全不发光，正常接受场景实时光照与阴影投射；
  * `Alpha = 255`（纯白）：满额 $100\%$ 自发光（Self-Illuminating），无视外部阴影遮挡，与战斗相机的 Bloom / HDR 后处理产生剧烈光学反应，泛出耀眼辉光；
  * `Alpha = 50 ~ 150`（灰度）：呈现内敛柔和的微光或幽暗荧光质感。

### 6.2 局部/任意部位精准发光定位 (Localized Part Emissive Control)
发光效果**完全不局限于全身**，可精准控制到角色的**任意指定部位**甚至单个像素：
* **原理**：角色 3D 模型的各个身体部件（眼睛、面罩、整个头部、胸口车灯、阵营标志、剑刃刀锋、引擎喷气口等）在 2D 贴图上均有严格对应的 UV 坐标区间。
* **做法**：通过 3D 几何或 UV 选区提取（例如使用 3D Mesh 顶点高度 $Y$ 与深度 $Z$ 进行空间定位，或直接在 2D 贴图遮罩上选区），将指定区域在 RAOE 的 Alpha 通道涂白（255），其他身体部位的 Alpha 保持为 0，即可实现**仅眼睛发亮、仅头部发光、或仅武器刀刃幽幽发光，而机体其余金属部位保持正常磨砂或高光质感**。

### 6.3 发光色彩与辉光强度调控 (Color & Intensity Customization)
发光绝不仅限于史达的“幽幽青蓝色”，其最终光芒色彩与质感由三大要素共同决定：
1. **底层漫反射色彩 (`_base_tex` Albedo)**：
   * 自发光直接叠加在底色之上。底色为亮红则透出猩红光，底色为亮金则透出炽烈金光，底色为翠绿则透出医疗/能量晶体绿光。
2. **材质级发光调色向量 (`_emissive_intensity_col`)**：
   * 原生 Material 内部暴露了专属发光调色向量（RGBA 浮点），直接控制发光色调：
     * **霸天虎暗能量紫光 (Dark Energon)**：`{r: 0.85, g: 0.15, b: 1.0, a: 0.0}`
     * **狂怒/狂暴猩红光 (Fury / Berserk)**：`{r: 1.0, g: 0.05, b: 0.05, a: 0.0}`
     * **领袖矩阵神圣炽金光 (Matrix Gold)**：`{r: 1.0, g: 0.85, b: 0.2, a: 0.0}`
     * **赛博坦能量晶体绿光 (Energon Green)**：`{r: 0.1, g: 1.0, b: 0.4, a: 0.0}`
     * **纯白超载耀斑强光 (Overcharge White)**：`{r: 1.0, g: 1.0, b: 1.0, a: 0.0}`
     * **史达青蓝能量光 (Saber Cyan)**：`{r: 0.0, g: 0.14, b: 0.66, a: 0.0}`
3. **超亮泛光倍率 (`_emissive_overbright_range`)**：
   * 材质浮点参数，默认可达 `120.0`。数值设定在 `10.0 ~ 40.0` 时表现为柔和幽光；拉高到 `100.0 ~ 150.0` 时将产生极强烈的眩目泛光（Bloom 光晕溢出），极具视觉冲击力。

### 6.4 原生着色器进阶高级特效拓展 (Advanced Shader Effects)
基于 `EB/Character/PBR` 的原生暴露属性，还可进一步调出以下高阶视觉表现：
1. **能量核心呼吸闪烁 (Pulsing / Breathing Glow)**：
   * 调节材质浮点 `_emissive_pulse_intensity_range`（脉冲波动幅度，如 `0.2 ~ 0.8`）与 `_emissive_pulse_time_range`（呼吸周期时长，如 `1.5s`）。无需任何额外脚本，着色器会自动让发光部位像**机械心脏/能量火种一般有节奏地一明一暗“呼吸”**（极度契合震荡波独眼、死火核心、或领袖胸口能量宝）。
2. **电流回路流动 / 全息扫描线 (UV Scrolling Circuit Flow)**：
   * 调节材质向量 `_emissive_scroll_speed_vector: {r: speed_x, g: speed_y, b: 0, a: 0}`。配合绘制好的能量回路贴图，光效将沿装甲线路不断滚动流动，实现**赛博朋克电路奔涌或全息扫描**动态。
3. **镜面电镀镀铬高反光 (Chrome Metal Finish)**：
   * 在 `_pbr_composite_tex` 中将 G 通道（Metallic）拉满到 255，同时将 R 通道（Roughness）压至接近 0，可使原本塑料质感的哑光外壳瞬间变为**如水银般映射环境的镜面电镀金/电镀银**。
4. **熔岩地狱战损裂纹 (Magma / Molten Armor)**：
   * 在 Diffuse 贴图绘制细密装甲裂痕，而在 Emissive Alpha 通道仅将裂痕线刷白并赋予高饱和红/橙光，呈现**机体裂解熔岩喷薄、过载暴走**的狂战士机甲风范。
5. **能量幽灵 / 全息投影形态 (Ghost / Hologram Avatar)**：
   * 将全身 Alpha 贴图全面提亮，结合材质半透明（Transparency），呈现类似“鬼魂红蜘蛛（Ghost Starscream）”晶莹剔透的全息灵体。

---

## 7. 3D 武器挂点与骨骼绑定标准 (Weapon Socket Rigging)

### 7.1 官方武器标准挂点 `RightProp`
* 在所有 TFTF 金刚手部骨骼树中，`RightHand` 下方均存在官方预设的 **`RightProp`** 节点（例如坐标 `(-0.588, 0.510, 0.047)`），此点恰好为握拳时的**手心中心空洞**。
* **铁律**：
   1. 将武器网格的 `RootBone` 与 `m_Bones[0]` 直接绑定至 **`RightProp`**；
   2. 将网格的 `BindPose[0]` 设为标准单位矩阵（`Matrix4x4.identity`）；
   3. 确保网格的 `Stream 2` 携带完整的 `Channel[12]`（BoneWeight = 1.0）与 `Channel[13]`（BoneIndex = 0），即可实现武器与手心 100% 贴合，彻底避免位移漂移与隐形。

---

## 8. Android 官方 Bionic 动态链接器与 DT_NEEDED 注入陷阱 (Bionic Linker Crash)

### 8.1 现象与报错
* **崩溃现象**：应用启动瞬间闪退（SIGABRT / Signal 6）。
* **Logcat 标志性报错**：
  ```text
  F libc : bionic/linker/linker_phdr.cpp:183: get_string CHECK 'index < strtab_size_' failed
  Abort message: 'bionic/linker/linker_phdr.cpp:183: get_string CHECK 'index < strtab_size_' failed'
  ```
* **根本原因**：
  原版 `--needed byte` 机制将 `"libdothook.so"` 写入了 0x7D3034 的零空洞（Zero Cave），并在 `.dynamic` 的 `DT_NEEDED` 处填入了该偏移 `0x7BFE5C`。在 LDPlayer 等第三方模拟器中链接器较宽松可以启动，但在**所有真实物理机（小米、vivo、华为、三星等）及 Google 官方标准模拟器**中，Bionic 的 `linker64` 严格校验 `d_val < strtab_size_`（原版 `strtab_size_` 仅为 `0x19C8A`），因越界直接导致 SIGABRT 闪退。

### 8.2 解决方案（In-Place 字符串槽位重定向置换）
* **铁律**：绝对不能将 `DT_NEEDED` 指向超出 `.dynstr` 声明大小之外的地址。
* **做法**：
  1. 在 ARM64 的 `.dynstr` 内部寻找完全等价且未被 relocation 引用的导出别名符号（如 `_ZNSt6__ndk17codecvtIDsc9mbstate_tED1Ev` 与 `D2Ev`，槽位空间 39 字节 $\ge$ 14 字节）；
  2. 将 D1Ev 的 `st_name` 重定向至 D2Ev；
  3. 在原 D1Ev 所在的合法内部槽位写入 `"libdothook.so\0"`；
  4. 将 `.dynamic` 的 `DT_NEEDED` 的 `d_val` 指向该内部槽位偏移。
* **效果**：保持 ELF 段布局 0 偏移，在 Windows 纯原生环境下即可完美兼容所有标准 Android Bionic 真实设备。

---

## 9. 独立离线单机打包与“连接网络出现问题”陷阱 (Standalone Offline Bundled Server & Network Error Trap)

### 9.1 现象与报错
* **报错弹窗**：应用启动时黑屏或加载界面弹出系统提示：
  `"连接网络出现问题。\n请检查你的网络连接。"`（游戏资源键 `ID_SERVER_POOR_CONNECTION`）。
* **高发场景**：在进行本地化翻译（xlate）、招式动作（moves）、Redeco 重涂或角色模型移植等开发迭代时，每次重新打包 APK 都极易因忽略打包参数而周期性复发。

### 9.2 根本原因
1. **默认开发模式错位**：`Server/build_phone_apk.py` 最初设计面向 PC 局域网调试（默认连接 `https://127.0.0.1:8443`，默认 `bundle_server = False`）。
2. **缺失单机本地服务端 Payload**：未携带 `--bundle-server` 时，APK 内不会生成 `assets/tftf_offline_payload.bin`（32,000+ 离线路由），导致手机内嵌 HTTP 服务端无法启动。
3. **缺失关键 IL2CPP 原生补丁**：未携带 `--patched-il2cpp build/libil2cpp-arm64-patched.so` 时，APK 会直接使用原始无补丁的 `libil2cpp.so`。原始二进制中：
   - 缺少 Patch 7 & 8（`Application.internetReachability` 与 `EndPoint.HasInternetConnectivity` 绕过检测，防止飞行模式/无外网时报错）；
   - 缺少 `DT_NEEDED` 依赖，导致 `libdothook.so` 根本不会被加载，内嵌本地服务器完全不执行；
   - 缺少 TLS 证书校验绕过（Patch 1 & 2）与登录跳过补丁。
4. **端口错配**：客户端将登录、翻译及数据拉取请求发送到了未开放的 `https://127.0.0.1:8443`，最终触发网络断开提示。

### 9.3 规范与防护
1. **完整打包命令铁律**：
   ```powershell
   python Server/build_phone_apk.py "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk" "build/phone-unsigned-redeco.apk" --scheme http --server-host 127.0.0.1 --server-port 8080 --bundle-server --patched-il2cpp "build/libil2cpp-arm64-patched.so"
   ```
2. **打包脚本底层智能防御**：
   `Server/build_phone_apk.py` 内部已集成智能自适应：当检测到处于离线工程且存在 `build/libil2cpp-arm64-patched.so` 时，即便命令漏传参数，也会自动启用 `--bundle-server`、嵌入全部 3.2 万条路由并打入修补版 IL2CPP，彻底从底层根除该 bug。

---

## 10. UnityPy AssetBundle 压缩机制与安装包体积膨胀陷阱 (UnityPy AssetBundle Compression & APK Bloat)

### 10.1 现象与体积异常暴增
* **现象**：在对角色 AssetBundle（如添加动作控制器、材质或模型补丁）进行全量处理后，编译出的 APK 安装包体积由原本正常的 **~0.9 GB** 剧增至 **~1.35 GB**（额外膨胀了 400MB+）。
* **排查对比**：
  * 单个角色的 AssetBundle 修改前后体积实测：
    * 原版 Bundle（例如 `acidstorm_gs_leader2015.assetbundle`）：**4.46 MB**
    * UnityPy 默认 `env.file.save()` 导出后：**10.21 MB**（体积直接翻倍至 2.3 倍！）
  * 当工程对全游戏 75 个角色 Bundle 进行批量处理并重新打包时：$75 \times \approx 5.5\text{ MB} \approx 410\text{ MB}$，导致 APK 安装包整体剧烈膨胀。

### 10.2 根本原因
1. **UnityFS 内部压缩机制**：Unity 官方导出的 `.assetbundle` 采用 LZ4 块压缩算法存储资源数据。
2. **Android APK 存储规范**：在 Android APK 的 ZIP 结构中，所有 `.assetbundle` 文件必须以 `ZIP_STORED`（仅存储不压缩，`compress_type = 0`）方式放入，以允许 Unity 引擎运行时直接流式加载与内存映射。
3. **UnityPy 的默认保存策略**：
   在 `UnityPy.files.BundleFile.save(self, packer=None)` 中：
   ```python
   def save(self, packer=None):
       # packer 为 None 时，默认采用 "none"（完全无压缩，raw data）
       if not packer or packer == "none":
           self.save_fs(writer, 64, 64)
       elif packer == "lz4":
           self.save_fs(writer, data_flag=194, block_info_flag=2)
       elif packer == "original":
           self.save_fs(writer, data_flag=self.dataflags, block_info_flag=self._block_info_flags)
   ```
   **调用 `env.file.save()` 若不显式指定 `packer`，将默认导出完全未压缩的裸数据**。APK 打包时由于不进行二次 zip 压缩，裸数据直接进包，最终导致整体体积严重失控。

### 10.3 规范与铁律
* **铁律**：凡使用 `UnityPy` 保存任何 UnityFS AssetBundle，**严禁使用无参 `save()`**！必须显式传入 `packer="lz4"` 或 `packer="original"`：
  ```python
  # 推荐写法（保留原 Bundle 压缩方式或使用标准 LZ4）
  patched_bytes = env.file.save(packer="lz4")       # 标准 LZ4 块压缩
  # 或
  patched_bytes = env.file.save(packer="original")  # 沿用原文件头压缩标志位
  ```
* **效果**：体积完美与原版保持 $100\%$ 一致（4.46 MB），APK 安装包稳定维持在 0.9 GB 黄金区间。

---

## 11. ADB 手机端 APK 快捷安装图形工具 (`INSTALL-ADB.py`)

为解决开发者与用户通过命令行手动输入 `adb install` 命令易遗漏关键参数的问题，项目根目录下提供了专属图形化安装工具 `INSTALL-ADB.py`。

### 11.1 工具核心功能
* **设备自动识别**：自动调用 `adb devices` 探测并列出当前连接的物理真机与模拟器。
* **默认标准安装参数**：预设 `-r --no-incremental`，彻底避免增量安装失败或签名不匹配问题。
* **文件拖选与实时日志**：支持图形化文件浏览弹窗，多线程异步执行安装，实时回显终端控制台日志与结果弹窗提示。

### 11.2 使用方式
```powershell
python INSTALL-ADB.py
```

---

## 12. Netflix 独占金刚招式库继承与覆盖陷阱 (Chromia & Dead End MoveSet Inheritance Trap)

### 12.1 现象与隐蔽 Bug
* **现象**：新构建的 APK 中，克劳莉娅（Chromia）和封锁（Dead End）的普攻/重击/必杀动作失效或动作姿态异常，部分专属招式打不出判定或丢失特效。
* **排查发现**：打包进 APK 的 `moves.assetbundle` 招式总数由正常的 **945 条** 异常缩水为 **923 条**。

### 12.2 根本原因
1. **历史版本差异**：原版 Kabam 9.2.0 基础 APK 中尚未实装克劳莉娅（12 条招式）和封锁（8 条招式）。这 20 条官方动作资产仅存在于后续 Netflix 版本中，通过 `tools/extract_netflix_assets.py` 转码提取到了 `assets_netflix/moves.assetbundle`（共 943 条招式）。
2. **复合新角色依赖**：自制金刚回春手（Lifeline）的专属 S1/S2 必杀招式（`move_lifeline_special_01` 与 `02`）亦需缝合注入该动作库（合计 945 条）。
3. **重涂工具覆盖陷阱**：
   在编写打击火花物理调校（`apply_spark_tuning.py`）或动作事件修复脚本时，若直接从 Kabam 基础 APK (`APK_PATH`) 中提取并重新覆写 `assets_redeco/moves.assetbundle`，由于 `Server/build_phone_apk.py` 会优先采纳 `assets_redeco/` 下的同名 Bundle，该缩水后的 923 条文件将无情覆盖 APK 打包流，导致克劳莉娅、封锁与回春手的动作库被全量清空剔除。

### 12.3 规范与铁律
* **铁律 1（底包锁定）**：所有对 `moves.assetbundle` 的解包、修改或保存工具，**底包数据源必须且只能使用 `assets_netflix/moves.assetbundle`**，严禁以 Kabam 原始 APK 作为底包！
* **铁律 2（动作全量保留与断言）**：凡导出 `assets_redeco/moves.assetbundle`，必须包含以下基准校验，数量不足直接中断抛错：
  ```python
  assert len(chromia_moves) >= 12, "Chromia moves missing!"
  assert len(deadend_moves) >= 8,   "DeadEnd moves missing!"
  assert len(lifeline_moves) >= 2,  "Lifeline moves missing!"
  assert total_moves >= 945,        "moves.assetbundle truncated!"
  ```

---

## 13. 战斗连击状态机重置与后撤输入防御 (Combat Combo Attack Chain & Dodge Reset Trap)

### 13.1 现象与手感退化
* **现象**：打完一套连击或突进后，玩家向后滑屏后撤（Dodge），再点击屏幕（Tap）攻击时，未能从 L1 起手，而是直接打出 L4 或非法动作；连击槽计数未被正确重置。
* **排查复现**：在 commit `5c5bc2c` 中，为了解决 `hook_166` 重置导致封锁（Dead End）等角色 S2 必杀手雷状态机中断的问题，清理代码时误将 `hook_165`（`PlayerDodgeState.OnEnter`）中的 `else if (obj_ok(g_p0_controller)) reset_player_attack_chain(g_p0_controller);` 一并删去。

### 13.2 根本原因
1. **状态对象指针延迟**：在 `PlayerDodgeState.OnEnter`（`0x117E4AC`）执行起始，传入的 `a0` 对象的 `[a0, 0x18]` 指针在部分机型和状态转换瞬间可能未完成初始化或无法通过严格的指针校验。若移除了 `g_p0_controller` 兜底保护，将导致重置逻辑直接被跳过。
2. **底层动作与状态机对应关系**：
   在 `PlayerController.Action`（`0x1179AF4` / `hook_154`）的底层跳转表中：
   * `action == 2`：底层精确对应滑屏后撤（`StateMachine.ChangeState(typeof(PlayerDodgeState))`）；
   * `action == 4`：轻击输入（Tap）；
   * `action == 8`：中击突进（Swipe Forward）。

### 13.3 规范与双保险防御机制
1. **输入层即时重置（Action 2 拦截）**：
   在 `hook_154`（`PlayerController.Action`）中，一旦检测到本地玩家执行 `action == 2`（后撤动作），立即直接重置攻击链：
   ```c
   if (action == 2) {
       reset_player_attack_chain(self);
   }
   ```
2. **状态层兜底重置（DodgeEnter 拦截）**：
   在 `hook_165`（`PlayerDodgeState.OnEnter`）中，保留 `g_p0_controller` 兜底检查，确保无论从哪个路径触发后撤，本地玩家的普攻索引（`_lightAttackIndex`、`_mediumAttackIndex`、`_rangedAttackIndex`）均被 100% 重置为 0。

---

## 14. 独占角色过场光效与过程材质包跨版本继承陷阱 (Character FX Procedural & Matinee VFX Trap)

### 14.1 现象与隐蔽丢失
* **现象**：克劳莉娅（Chromia）在施放三气超必杀大招（SP3 / Special Attack 3）时，开场挥舞斧头的动作缺少原版划过屏幕的明亮弧光光效（刀光拖尾），动画表现单薄。
* **排查深层根因**：
  1. **Matinee 镜头舞台挂载**：Chromia 的大招属于 Unity Matinee 电影级切镜舞台（`TFormStage_chromia_gs_special03`）。开场挥斧光弧由 `Trails/fx_p_Chromia_SP3_trail_first` 粒子节点发射。
  2. **双重依赖缺失（材质 + 3D 切割网格）**：
     - **材质依赖**：粒子渲染器引用的外部材质为 `fx_m_Chromia_SP3_trail 1`（PathID `1790633657150229957`）。
     - **网格依赖（关键陷阱）**：该粒子系统的渲染模式为网格渲染（`m_RenderMode: 4`），其刀光几何体引用了外部网格 `SlashMesh5`（PathID `4547667473076947885`）。**若仅注入材质而漏掉网格，Unity 粒子系统因缺少网格模型无法绘制任何多边形，光弧完全隐形！**
  3. **版本跨度（Unity 2021 vs Unity 2020）与 .resS 崩溃陷阱**：
     - 若直接将 Netflix 的 `character_fx_procedural.assetbundle` 替换进 APK，由于 Netflix 资产包出自 Unity 2021，其 Material 使用了 `m_ValidKeywords` 列表字段，且 17MB 的 `.resS` 纹理流数据偏移与 2020 引擎不匹配，会导致 `Loading.Preload` 预加载阶段报 `Position out of bounds!` 严重损毁并直接触发 `SIGTRAP` 闪退。

### 14.2 解决方案与规范 (Transcoding & Inlining Solution)
1. **以 2020 原包为底座**：
   以 9.2.0 原版 `character_fx_procedural.assetbundle` 为主体基底，保护原有全部纹理和 `.resS` 外部流。
2. **材质 Schema 跨版本转码**：
   从 Netflix 提取 Chromia 独占材质（`fx_m_Chromia_SP3_trail 1` 等），克隆 2020 Material 模板，将 `m_ValidKeywords` 列表合并为空格分隔的 `m_ShaderKeywords` 字符串，按原 PathID 注入并注册入容器。
3. **网格内联技术（Self-Contained Inline Mesh）**：
   从 Netflix 的 `.resS` 提取 `SlashMesh5` 的 15,680 字节顶点数据，直接写入 `m_VertexData['m_DataSize']`，并将 `m_StreamData` 设为 `{offset: 0, size: 0, path: ""}`。这样无需扩充或修改原版 `.resS`，即可在 2020 引擎中稳定自包含渲染 3D 刀光网格。
4. **全自动断言守护**：
   在 [`tools/apply_spark_tuning.py`](file:///d:/Agent/tftf/tools/apply_spark_tuning.py) 的重载验证阶段，必须同时对材质与网格进行存在性断言：
   ```python
   assert any(m.name == "fx_m_Chromia_SP3_trail 1" for m in materials)
   assert any(m.name == "SlashMesh5" for m in meshes)
   ```

---

## 15. 副本卡片专属图标定制与 ODR 路径解析规范 (Quest Card Custom Icons & ODR Path Resolution)

### 15.1 业务场景与需求
* **场景**：对于随机敌人路线（如 1.1.1 宿命降临 / Arrival）或多职业高难轮盘战（如 1.1.2 六道轮回 / Karma Six），不应显示默认随机变动的关底 Boss 头像，而需要注入专属的固化方形图标（如专属能量魔方或六芒星轮盘徽标）。
* **多语言支持**：关卡标题与描述在服务端数据中需支持中英文双语适配（如中文「宿命降临」「六道轮回」，英文「Arrival」「Karma Six」）。

### 15.2 逆向架构与调用链路
1. **关卡卡片刷新**：
   关卡选择界面通过 `SelectQuestTile.RefreshDisplay`（`0x11CF018`）计算 Boss 信息后，调用 `SelectQuestTile.SetTexturePath(this, path, addSuffix)`（`0x11CFCAC`）。
2. **底层贴图设置**：
   * `a0`：`SelectQuestTile*` 对象指针。
   * `a1`：贴图相对路径字符串（`Il2CppString*`）。
   * `a2`：`bool addSuffix`。若为 `true`，底层将自动在字符串后追加 `this->PortraitSuffix`（即 `_quest`）。
   * `SetTexturePath` 激活 `this->_bossPortrait`（位于偏移 `0x118` 的 `UITextureRef` 组件），并调用 `UITextureRef.set_baseTexturePath`（`0x1991FD0`）。
3. **ODR 资源调度与加载**：
   `UITextureRef.LoadTexture` 收集候选路径列表后，最终调用 `EB.Assets.LoadTexture` 在按需资源（ODR）体系中异步加载贴图。

### 15.3 核心陷阱：ODR 资源子目录前缀缺失 (The ODR Subfolder Prefix Trap)
* **致命陷阱**：
  在 Unity 及 `EB.Assets` 资源体系中，所有 ODR 资产包内部的文件索引全部带有各包专属的子目录前缀，例如：
  - 对话框头像：`dialogue_odr` -> `dialogue/bumbl_gs.png`
  - 场景宣传图：`fightlanding_odr` -> `fightlanding/FightStoryImgLrg.jpg`
  - 角色头像：`portraits_odr` -> `portraits/portrait_optimus_c_tf_small.jpg`
  - 关卡看板：`questboard_odr` -> **`questboard/portrait_xxx_quest.png`**
* **失败表现**：
  若在 Hook 中重定向至 `portrait_arrival_quest`，由于缺少 `questboard/` 前缀，`EB.Assets` 在读取 `assets/questboard_odr/toc.txt` 时将无法匹配到任何条目，Unity 不会发起资源请求，导致关卡卡片方框内贴图**完全空白且无任何报错提示**。
* **铁律与规范**：
  在 `tools/nativehook/hook.c` 的 Hook 170 中进行路径重定向时，**必须显式包含 `questboard/` 子目录前缀，并将 `addSuffix` 置为 0 (`false`)**：
  ```c
  if (strcmp(qid, "1.1.1") == 0) {
      a1 = g_strnew("questboard/portrait_arrival_quest");
      a2 = (void*)0; // 禁用自动追加 _quest
  } else if (strcmp(qid, "1.1.2") == 0) {
      a1 = g_strnew("questboard/portrait_karmasix_quest");
      a2 = (void*)0;
  }
  ```

### 15.4 资源标准与自动化打包流
1. **图标尺寸与格式**：
   * 尺寸：**128×128**（无需使用原版 256×256，既保证在卡片方框内的视觉精细度，又能节省 APK 打包体积）。
   * 格式：RGBA PNG 或高质量 JPEG（推荐转为 RGBA PNG）。
2. **存放目录与打包自动注入**：
   * 资源存放在 `assets_redeco/portrait_<name>_quest.png`。
   * [`Server/build_phone_apk.py`](file:///d:/Agent/tftf/Server/build_phone_apk.py) 已实现全自动识别与装配：
     1. 自动注入文件至 `assets/assetpack/questboard_odr/questboard/portrait_<name>_quest.png`；
     2. 自动在 `assets/questboard_odr/toc.txt` 的 `files` 列表中注册 `"questboard/portrait_<name>_quest.png"`。
3. **验证判定标准**：
   通过 `adb logcat` 观察必须出现如下资源加载确认行：
   ```log
   I Unity : Calling get asset location, assetPackName: default, path: assetpack/questboard_odr/questboard/portrait_arrival_quest.png
   ```
   并通过 `python INSTALL-ADB.py --screenshot` 直观复核卡片方框内的图案渲染效果。

---

## 16. 阵营徽章 PUA 字形与"静默空白"陷阱 (Faction Badge PUA Glyph & Silent Blank Trap)

### 16.1 现象
* **主现象**：机器人列表（BOTS）卡片的 RatingWidget 上，稀有度外框、星级、战力数字全部正常，**唯独阵营徽章位置空白**——不崩溃、不报错、`logcat` 里也没有任何异常。
* **连带现象**：接入野兽之战（Beast Wars）角色后，黄豹 / 恐龙勇士 / 猩猩队长 / 犀牛显示成**汽车人**徽章，黄蜂勇士 / 巨蝎勇士显示成**霸天虎**徽章。

### 16.2 逆向架构：徽章是字形，不是 Sprite
阵营徽章**不存在于任何图集**，它是 **UI 字体的私用区（PUA）字形**；客户端把"一个字符"写进 RatingWidget 的阵营 UILabel（`widget+0x30`，用 `GameObject.SetActive` 激活）来绘制：

| 字形 | 阵营 | `ROSTER.faction` 取值 |
| :--- | :--- | :--- |
| `U+E134` | Autobot 汽车人 | `"autobot"` |
| `U+E135` | Decepticon 霸天虎 | `"decepticon"` |
| `U+E160` | Maximal 巨无霸 | `"maximal"` |
| `U+E161` | Predacon 原始兽 | `"predacon"` |

数据链路（单一真理源 → 客户端字段 → hook 读回）：

```
Server/gamedata.py ROSTER.faction
  └─ blueprint `a` (AttributeBaseType @0x70) ──┐
  └─ characters `gen` / `hc` / `hero_colour`   ├─ hook 从 blueprint @0x70 读回字符串
  └─ userData `faction`  (@0x48 的 blueprint) ─┘
```

### 16.3 根本原因：为什么会"静默空白"
1. 早期实现把"取阵营 → 翻译成字形"整件事**外包给客户端的图标查询函数**（`0xC2197C`）与 `HeroData.get_Faction`（`0xE8D8A0`）。这两个符号在本工程内没有任何名字注释（`re_notes/dump.cs` 已不在仓库里），签名与 key 契约**无从验证**。
2. 该查询函数遇到不认识的 key **返回 NULL**，而调用点写成 `if (icon_str) { set_text(...) }`——判空后**直接跳过写入**。于是既不崩、也不打日志，徽章就是空白：故障被"静默吞掉"。
3. 更隐蔽的是：**客户端自己的 `RatingWidget.SetData` 走的是同一个 getter**。hook 只是"用同一条坏链路再画一遍"，无论怎么调参都不可能画出来——必须把映射表拿回自己手里。
4. `int faction = get_Faction(...)` 这种把未知返回类型一律当 `int` 接的写法同样是隐患：若该 getter 返回 `Il2CppString*`，指针会被截断成低 32 位再喂给查表函数，永远查不到。

### 16.4 规范与铁律
1. **铁律 1（映射表自己写）**：阵营 → PUA 字形必须由 `tools/nativehook/hook.c` 的 `faction_icon_code()` / `faction_icon_glyph()` 用 `if/switch` 本地实现，**禁止**委托客户端的图标查询函数（`0xC2197C`）与 `0xE8D94C`。字形用 `g_strnew()`（UTF-8）构造后写入阵营 label。
2. **铁律 2（读我们自己的字段）**：阵营字符串优先读 blueprint 的 `AttributeBaseType`（`@0x70` == login-data 的 `a`），`HeroData.get_Faction`（`0xE8D8A0`）只保留为兜底，避免客户端字段一挪就再次静默空白。
3. **铁律 3（取值小写 + 四处同步）**：`ROSTER.faction` 一律小写；新增 / 修改角色时，`Server/gamedata.py`、`Server/bot_names_zh.json`、`bot_names_zh.json`、`Server/gamedata.lbl` 四处同名定义必须同步。野兽之战角色归属以客户端自带官方 bio 为准（`assets/xlate/snapshots/zh-CN/character_bios_zh-CN.json`）。
4. **铁律 4（不许静默）**：任何"取值 → 查表 → 写入"的链路都要带日志。现行 hook 会打印 `RATEWGT <bid> faction='...' glyph=U+.... label=...(<类名>) written`；取不到时打印 `-> NO glyph, badge blank`（`label=(非 Label 类名)` 就意味着 `widget+0x30` 的偏移判断也错了）。
5. **判定标准**：真机 `logcat` 或 `/sdcard/Documents/tftf_*.log` 必须出现 `RATEWGT ... written`；BOTS 列表中黄豹 / 恐龙勇士 / 猩猩队长 / 犀牛为 `U+E160`（巨无霸），黄蜂勇士 / 巨蝎勇士为 `U+E161`（原始兽）。

> 关联记录：[`re_notes/ROSTER_PORTRAIT_RARITY_FRAME_AND_STARS.md`](file:///e:/Agent/TFTF/re_notes/ROSTER_PORTRAIT_RARITY_FRAME_AND_STARS.md) 第六节。
