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