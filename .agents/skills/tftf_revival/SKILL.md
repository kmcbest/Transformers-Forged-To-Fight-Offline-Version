---
name: tftf_revival
description: Comprehensive knowledge base and pitfall avoidance guide for Transformers: Forged to Fight (TFTF) offline revival development, including Unity assetbundle modifications, IL2CPP native hooking, 3D character/mod/relic scaling and camera alignment, gamedata payload generation, and APK packaging.
---

# Transformers: Forged to Fight (TFTF) Revival Development & Pitfall Guide

This skill documents critical domain knowledge, reverse-engineered architecture, and common pitfalls to avoid when working on the TFTF offline revival project.

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
* **R 通道 (Red)**：Roughness（粗糙度）
* **G 通道 (Green)**：Ambient Occlusion / Metallic（环境遮挡 / 金属度）
* **B 通道 (Blue)**：Cavity / Detail Mask（凹陷与细节）
* **A 通道 (Alpha)**：**Emissive Mask（自发光 / 能量辉光蒙版）**

### 6.2 幽灵/能量过载/全息发光实战技巧 (Ghost Starscream / Hologram)
* **原理**：当向角色的 `_pbr_composite_tex` 注入具有高亮度 Alpha 甚至全彩亮度的贴图时，着色器会将这些区域视作 $100\%$ 自发光材质（Self-Illuminating），并与战斗场景的 Bloom 泛光及后处理（Post-Processing）产生剧烈光学反应，呈现出通体晶莹剔透、幽幽发光的“能量幽灵”视觉效果。
* **应用场景**：
  * 鬼魂红蜘蛛（Ghost Starscream）
  * 黑暗能量超载形态（Dark Energon Overload）
  * 领袖能量矩阵爆发 / 赛博坦全息分身投影

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
