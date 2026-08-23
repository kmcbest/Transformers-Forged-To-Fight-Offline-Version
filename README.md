# Transformers: Forged to Fight - Offline Revival Edition
## 《变形金刚：百炼为战》离线完全重制版

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Platform](https://img.shields.io/badge/Platform-Android%20(arm64--v8a%20%7C%20armeabi--v7a)-green.svg)](README.md)
[![Unity Version](https://img.shields.io/badge/Unity-2020.3.31f1%20(LTS)-orange.svg)](README.md)
[![Bots Roster](https://img.shields.io/badge/Roster-63%20Bots%20(All%205--Star%20Maxed)-red.svg)](Server/gamedata.py)

> [English](#english) | [中文说明](#中文说明)

---

<a name="english"></a>
# English

### 💖 Acknowledgments & Upstream Attribution

This project is built upon the open-source reverse engineering and offline revival framework created by **[Gummygamer / Transformers-Forged-To-Fight-Offline-Version](https://github.com/Gummygamer/Transformers-Forged-To-Fight-Offline-Version)**.
We express our deepest gratitude to the original author for establishing the foundational IL2CPP binary patches, Sparx server simulation layer, runtime inline hook (`libdothook.so`), and standalone in-APK server architecture.

This fork extends the project with massive gameplay enhancements, full data reconstruction, complete Chinese localization, full combat engine and hitbox fixes, and pioneering **cross-version Unity asset transcoding for Netflix exclusive characters (Chromia & Dead End) ported to native 9.2.0**.

---

## 🌟 Core Enhancements & Major Features

### 1. 🤖 Complete 63-Bot Roster (All 5-Star Maxed)
* **Full Roster Unlocked**: Combines all 61 official Kabam 9.2.0 characters + 2 Netflix exclusive characters = **63 Bots Total**!
* **Maxed 5-Star Stats**: Every bot is configured with authentic 5-Star Rank 5 (Level 50) maxed stat profiles (PI, Health, Attack, Critical Rate, Critical Damage, and Armor).
* **Instant Special Meter**: All three special attack meter segments (S1 / S2 / S3) are immediately available upon entering combat.
* **Accurate Faction & Class Mapping**:
  * Corrected all 6 classes: **Warrior**, **Scout**, **Tech**, **Demolitions**, **Tactician**, **Brawler**.
  * Calibrated faction allegiances: Autobots, Decepticons, Maximals, Predacons.

### 2. 🎬 Netflix Exclusive Characters Integration (Chromia & Dead End)
* **Chromia (克劳莉娅)**: Autobot / **Warrior** class, equipped with her signature energy battleaxes and left-hand blaster pistol!
* **Dead End (封锁)**: Decepticon / **Demolitions** class, wielding heavy shotgun blasts and destructive barrage firepower!
* **Cross-Version UnityFS Asset Transcoding Engine**:
  * Netflix edition runs on **Unity 2021.3.39f1 (UnityFS v8)**, whereas official Kabam 9.2.0 runs on **Unity 2020.3.31f1 (UnityFS v7)**;
  * Automated transcoding engine reconstructs BlockInfo/DirectoryInfo tables and LZ4 compressed blocks, solving infinite loading hangs and format incompatibility.
* **Full ODR Registration & Manifest Injection**:
  * Auto-patches `packs.txt` and generates verified `.manifest` files so both characters render their authentic 3D models in base showcase, roster select, and combat arenas (no Sharkticon fallback).

### 3. ⚔️ Combat System, Hitbox & Visual FX Fixes
* **Hitbox & Moves Timeline Fixes**:
  * Transcodes and injects full `moves.assetbundle` and procedural animation libraries;
  * Fixed Dead End's melee combo chain where intermediate hits whiffed;
  * Fixed the softlock freeze where both fighters froze in place after executing S1/S2/S3 special attacks.
* **Chromia Pistol & Ranged Combat Loop Fix**:
  * Restored `projectile_chromia_bullet` entity with proper 9.2.0 aqua projectile energy beam bindings (`fx_p_aqua_projectile` & `fx_p_aqua_projectile_impact`);
  * Replaced muzzle flash with instantaneous self-destroying particle (`fx_p_aqua_muzzle_flash`), eliminating persistent green flame sticking to her hand;
  * Fixed combat state machine to enable infinite repeated dash-back ranged shooting cycles.
* **S3 Cinematic Battleaxe Material & Purple Shader Fix**:
  * Re-pointed S3 thrown battleaxe mesh material to valid weapon metal material (`1952278396157663915`);
  * Eliminated Unity 2021 error shader (magenta/purple texture), restoring true metallic textures and specular highlights.
* **Native High-Definition Shader Preservation**:
  * Retained clean Kabam 9.2.0 `character_fx.assetbundle` to prevent global battle particle and shader corruption.

### 4. 📱 Standalone In-APK Offline Architecture
* **Embedded Loopback Server**: Runs a lightweight Python HTTP server on port 8080 inside the APK, serving compressed `tftf_offline_payload.bin` (9,600+ routes).
* **Zero Configuration Needed**: Network calls automatically redirected to `127.0.0.1:8080` via `libdothook.so` + patched `libil2cpp.so`.
* **No PC, no Wi-Fi, no external server, no root required** — install and play offline anywhere!

### 5. 🇨🇳 Full Chinese Localization
* Built-in official Simplified Chinese bot name translation table ([`bot_names_zh.json`](bot_names_zh.json)).
* Localized class names, faction badges, update notes, and compliance statement screens.

---

## 🛠️ Automated Extraction & Transcoding Tool

To maintain full compliance and copyright safety, this repository **does not distribute proprietary game assets**. Instead, an automated tool [`tools/extract_netflix_assets.py`](tools/extract_netflix_assets.py) is provided.

Users provide their own Netflix edition APK/XAPK to transcode the exclusive assets:

```bash
# Extract and transcode Netflix exclusive assets in one command
python tools/extract_netflix_assets.py --input "path/to/default.apk"
```

---

## 📦 Build & Packaging Guide

### Requirements
* **Python 3.10+** (`pip install UnityPy`)
* **Java JDK 17+** (for `apksigner`)
* **Android SDK Build-Tools** (`zipalign` and `apksigner`)
* **Base Kabam 9.2.0 APK** (`com.kabam.bigrobot` v9.2.0)
* **Netflix Edition APK** (for extracting exclusive bots)

### One-Click Build Steps

```powershell
# 1. Extract and transcode Netflix exclusive assets
python tools/extract_netflix_assets.py --input "path/to/default.apk"

# 2. Build offline APK with embedded server and hook
python Server/build_phone_apk.py `
  "path/to/com.kabam.bigrobot_9.2.0.apk" `
  "build/phone-unsigned.apk" `
  --scheme http `
  --server-host 127.0.0.1 `
  --server-port 8080 `
  --bundle-server `
  --patched-il2cpp "build/libil2cpp-arm64-patched.so"

# 3. 4-byte page alignment
zipalign -f -p 4 build/phone-unsigned.apk build/phone-aligned.apk

# 4. Digital signature
apksigner sign --ks build/debug.keystore --ks-pass pass:android --out build/Transformers-9.2-offline-netflix-edition.apk build/phone-aligned.apk

# 5. Install to device or emulator
adb install -r --no-incremental build/Transformers-9.2-offline-netflix-edition.apk
```

---

<a name="中文说明"></a>
# 中文说明

### 💖 致谢与上游项目声明 (Upstream Acknowledgment)

本项目基于原作者 **[Gummygamer / Transformers-Forged-To-Fight-Offline-Version](https://github.com/Gummygamer/Transformers-Forged-To-Fight-Offline-Version)** 的开源逆向工程与离线复活框架构建。
感谢原作者在 ARM64/ARMv7 IL2CPP 核心八大补丁、Sparx 模拟协议栈、运行时 Inline Hook（`libdothook.so`）以及单 APK 内置伪服务器架构上奠定的坚实基础！

本仓库在此基础上进行了深度的游戏性扩展、数据重构、全中文本地化、战斗引擎与招式判定修复，并开创性地完成了 **Netflix 独占角色与跨版本 Unity 资源向官方 9.2.0 原生架构的完美降级移植**。

---

## 🌟 本版本核心重制与增强特性 (Core Enhancements)

### 1. 🤖 全角色 63 位全满阶五星图鉴解锁 (Complete 63-Bot Roster)
* **全图鉴解锁**：集成官方 9.2.0 的全部 61 位角色 + 2 位 Netflix 独占角色，总计 **63 位金刚全员登场**！
* **全五星满阶满级**：全员配置顶级五星 5/50 满级属性面板（战力 PI、生命值、基础攻击力、暴击率、暴击伤害与护甲等）。
* **全技能条开放**：进入战斗即刻解锁全部三段特殊能量槽（S1 / S2 / S3 必杀特写大招）。
* **职业与阵营精确校正**：
  * 纠正了全员职业分类与克制关系：**勇士 (Warrior)**、**侦察 (Scout)**、**科技 (Tech)**、**爆破 (Demolitions)**、**战术 (Tactician)**、**格斗 (Brawler)**；
  * 校准阵营归属：汽车人 (Autobots)、霸天虎 (Decepticons)、巨无霸 (Maximals)、原始兽 (Predacons)。

### 2. 🇨🇳 全中文本地化支持 (Full Chinese Localization)
* **官方中文角色名对照**：内置全 63 位角色官方简体中文译名表（[`bot_names_zh.json`](bot_names_zh.json) / [`Server/bot_names_zh.json`](Server/bot_names_zh.json)）。
* **本地化界面适配**：修复职业名称、阵营标签、更新公告以及合规声明的中文本地化图文呈现。

### 3. 🎬 Netflix 独占角色深度集成 (Netflix Exclusive Bots: Chromia & Dead End)
* **克劳莉娅（Chromia）**：汽车人阵营 / 勇士系（Warrior），手持标志性能量战斧与专属小手枪！
* **封锁（Dead End）**：霸天虎阵营 / 爆破系（Demolitions），配备专属近战霰弹与重火力轰炸！
* **跨版本 UnityFS 格式降级引擎**：
  * Netflix 独占版采用 **Unity 2021.3.39f1 (UnityFS v8)**，而官方 9.2.0 运行在 **Unity 2020.3.31f1 (UnityFS v7)**；
  * 本项目开发了自动化跨版本 AssetBundle 降级转码引擎，重构 BlockInfo/DirectoryInfo 寻址表与 LZ4 压缩块，完美解决高版本资源在 9.2.0 下无限加载死循环与无法识别的底层兼容难题。
* **完整 ODR 资源挂载与动态注册**：
  * 自动补丁 `packs.txt` 注册表与 `.manifest` 校验文件，让两名全新角色在基地展台、战斗选人与实机对抗中完美加载 3D 专属模型，彻底告别鲨鱼精（Sharkticon）替身兜底。

### 4. ⚔️ 战斗系统、招式判定与渲染全修复 (Combat & Visual Fixes)
* **招式碰撞盒与时间轴（Hitbox & Moves Timeline）修复**：
  * 转码并注入完整 `moves.assetbundle` 与程序化动作库；
  * 彻底修复**封锁（Dead End）**近战多段连击中途挥空、打不到敌人的碰撞判定问题；
  * 彻底解决两名新角色释放完 S1/S2/S3 特殊必杀技后双方原地僵直发呆、战斗无法继续的状态机卡死缺陷。
* **克劳莉娅小手枪与连续射击修复**：
  * 修复专属子弹实体 `projectile_chromia_bullet` 与 `PrefabList` 弹道关联，精准映射至 9.2.0 原生水蓝色能量光束（`fx_p_aqua_projectile` 与 `fx_p_aqua_projectile_impact`）；
  * 替换枪口火花为瞬时自毁特效（`fx_p_aqua_muzzle_flash`），彻底解决开火后手上粘滞一大团持续喷射绿光的 BUG；
  * 修复射击生命周期与状态机复位，支持开局、近战交手后再后撤的**无限轮次持续开火与后撤射击连招**。
* **S3 大招战斧材质与紫模（Error Shader）修复**：
  * 修正克劳莉娅 S3 大招特写中投掷插地战斧的材质引用（重定向至正常武器金属材质 `1952278396157663915`）；
  * 彻底清除 Unity 2021 残留 Shader Blob 导致的粉紫色报错 Shader，呈现真实细腻的金属反射与贴图光影。
* **原生高清 Shader 保护机制**：
  * 保持官方 9.2.0 原生 `character_fx.assetbundle` 的纯净性，彻底杜绝所有标准角色战斗时光效与子弹变成粉紫色色块的问题。

### 5. 📱 纯单机单 APK 内置免联网架构 (Standalone In-APK Server)
* **内置回环服务器**：单 APK 内部集成完整离线 Python HTTP 伪服务器（Port 8080），内置压缩后的 `tftf_offline_payload.bin` 响应载荷。
* **零配置即装即玩**：通过 `libdothook.so` + `libil2cpp-arm64-patched.so` 自动将游戏内全部 API 请求重定向至 `127.0.0.1:8080`；
* **无需电脑、无需外挂 Python、无需 Wi-Fi、无需 Root**，安装后随时随地开机秒进游戏！

---

## 📂 项目结构概览 (Repository Structure)

```
├── Server/
│   ├── gamedata.py             # 核心数据库：定义 63 位角色面板、阵营属性与 1.1.1 关卡
│   ├── build_phone_apk.py      # 独立单机版 APK 打包器（支持 ODR 注入、TOC 生成与内置服务器）
│   ├── bot_names_zh.json       # 全角色中文官方译名与阵营对照
│   └── responses/              # 各网络端点离线响应 JSON（共 9,600+ 路由）
├── tools/
│   ├── extract_netflix_assets.py # Netflix 独占角色一键提取、转码与招式修补工具
│   └── nativehook/
│       ├── hook.c              # 运行时 Inline Hook 源码（数据追踪与网络流量劫持）
│       └── inapk_server.c      # 单机内置极简 C-HTTP 服务器源码
├── patches/
│   └── patch_il2cpp.lbl        # IL2CPP 核心函数补丁脚本（跳过认证、证书锁定与离线登录）
├── bot_names_zh.json           # 根目录全角色中文名映射表
├── COMPLIANCE.md               # 项目合规与版权安全规范
└── TECHNICAL_NOTES.md          # 深度逆向工程笔记与数据协议参考
```

---

## ⚖️ 合规与免责声明 (Compliance & Legal)

1. 本项目为粉丝开源逆向工程研究成果与离线保存沙盒，仅供计算机技术学习与交流使用。
2. 本仓库不分发任何受版权保护的游戏客户端安装包（APK）、原始游戏二进制文件或专有音画素材。
3. 所有角色与游戏资产商标、版权均归属于 **Hasbro**、**Kabam** 及 **Netflix** 原版权所有方。
4. 详见 [`COMPLIANCE.md`](COMPLIANCE.md)。
