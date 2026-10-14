# 现代逆向工具链安装配置与逐步替换老工具实操指南
*(Modern Reverse Engineering Toolchain Setup & Migration Guide)*

> **文档定位**：本文档为开发者换机或新机器环境搭建时的一站式安装指南与工具演进标准。记录了如何从过去“纯 Capstone 裸汇编”的刀耕火种时代，平滑过渡并升级到“Ghidra 反编译 + REA (Reverse Engineer Anything) MCP 智能体驱动”的现代逆向分析工作流，同时明确界定了“分析期现代工具链”与“真机运行时 NativeHook”的严格边界。

---

## 目录
1. [核心原则与技术分工界限](#一核心原则与技术分工界限)
2. [新机器完整工具链安装清单](#二新机器完整工具链安装清单)
   - [1. 基础开发与编译环境](#1-基础开发与编译环境)
   - [2. 现代逆向分析与反编译工具链](#2-现代逆向分析与反编译工具链)
   - [3. REA (Reverse Engineer Anything) 与 MCP 智能体配置](#3-rea-reverse-engineer-anything-与-mcp-智能体配置)
3. [新旧工具平滑过渡与替换实操规范](#三新旧工具平滑过渡与替换实操规范)
   - [1. 淘汰与弃用工具清单 (Deprecated List)](#1-淘汰与弃用工具清单-deprecated-list)
   - [2. 典型实战场景替换对照表](#2-典型实战场景替换对照表)
   - [3. 绝对严禁替换的真理源底线](#3-绝对严禁替换的真理源底线)
4. [新机环境冒烟测试清单 (Smoke Test)](#四新机环境冒烟测试清单-smoke-test)

---

## 一、核心原则与技术分工界限

在引入最新逆向工具链之前，必须在架构层确立一条铁律：

| 阶段 | 使用工具 | 核心职责 | 替换策略 |
| :--- | :--- | :--- | :--- |
| **逻辑分析与逆向阶段**<br>*(Investigation Phase)* | **Ghidra / JADX / REA / UnityPy** | 分析 ARM64 算法、还原 C 伪代码、提取 APK 内部沉睡资产（关卡/数值表/AssetBundle） | **【立即升级替换】**<br>坚决淘汰 Capstone 裸汇编脚本，全面改用反编译与智能体驱动 |
| **真机运行时拦截阶段**<br>*(Runtime Patching)* | **NativeHook (`hook.c` + NDK)** | 注入 Android 内存、微秒级函数跳板（Trampoline）、保证 100% 官方打击手感 | **【严禁替换，保持极简】**<br>真机端绝不引入任何重型工具，保持轻量高效 C 语言 Hook |

---

## 二、新机器完整工具链安装清单

在新机器上按以下分类顺序完成安装与环境变量配置：

### 1. 基础开发与编译环境

1. **Git**
   - 官方下载并安装，配置用户名与邮箱。
2. **Python 3.10+** (推荐 3.10.x 或 3.11.x)
   - 安装时勾选 `Add Python to PATH`。
   - 常用依赖库安装（克隆仓库后在终端执行）：
     ```powershell
     pip install UnityPy capstone colorama requests flask
     ```
3. **Android NDK** (推荐 `r25c` 或 `r23c`)
   - 解压至推荐路径：`C:\Tools\android-ndk-r25c`
   - 将 NDK 目录添加到系统环境变量 `PATH`，并在系统变量中设置 `ANDROID_NDK_HOME`。
4. **Android SDK Platform-Tools (ADB)**
   - 确保 `adb` 命令在 PowerShell 中可直接运行。

---

### 2. 现代逆向分析与反编译工具链

1. **Java JDK (17 或 21 LTS)**
   - Ghidra 强依赖 Java 17+。推荐安装 OpenJDK 17 或 21（如 Microsoft OpenJDK 或 Temurin）。
   - 配置系统环境变量 `JAVA_HOME` 指向 JDK 安装目录（如 `C:\Program Files\Eclipse Adoptium\jdk-17...`），并将 `%JAVA_HOME%\bin` 添加到 `PATH`。
2. **Ghidra (v11.x+)**
   - **下载与解压**：从 GitHub 官方发布页下载最新 release，解压至推荐路径 `C:\Tools\ghidra`。
   - **验证无头模式**：检查 `C:\Tools\ghidra\support\analyzeHeadless.bat` 是否存在。
   - **功能定位**：ARM64 机器码的终极分析引擎，负责生成清晰可读的 C 语言伪代码（Decompiled C Pseudocode）、函数交叉引用（XRefs）与结构体对齐恢复。
3. **JADX (v1.5.x+)**
   - 从 GitHub 下载 `jadx-gui` 与 CLI 压缩包，解压至 `C:\Tools\jadx`。
   - 将 `C:\Tools\jadx\bin` 添加到系统 `PATH`。
   - **功能定位**：Android APK 的 Java/DEX 层一键反编译利器。
4. **Il2CppDumper (v6.7.x+)**
   - 下载并放置在 `C:\Tools\Il2CppDumper`。
   - **功能定位**：针对 Unity IL2CPP，读取 `libil2cpp.so` 和 `global-metadata.dat`，输出 `dump.cs`、`script.json` 和符号映射。
   - **Ghidra 符号联动**：使用 Il2CppDumper 目录下的 `ghidra_with_struct.py` 脚本直接导入 Ghidra，秒级将 9.2.0 所有无名函数恢复出官方类名与方法名！

---

### 3. REA (Reverse Engineer Anything) 与 MCP 智能体配置

REA 是连接 AI 智能体（Cursor / Claude Code / Antigravity / Codex）与底层逆向工具链（Ghidra、JADX）的桥梁。

1. **Node.js (LTS v18 或更高)**
   - 官方下载安装，确保 `node` 和 `npm` 可用。
2. **安装 REA 代理服务**：
   在 PowerShell 中运行全局安装或直接使用 npx：
   ```powershell
   npm install --global rea-agents
   ```
3. **初始化与 MCP 配置**：
   运行官方交互式设置向导：
   ```powershell
   rea setup
   ```
   或者在支持 MCP 的客户端（例如 Cursor / Claude Desktop / Antigravity）配置文件中手动声明 REA MCP Server：
   ```json
   {
     "mcpServers": {
       "rea": {
         "command": "npx",
         "args": ["-y", "rea-agents@latest"],
         "env": {
           "GHIDRA_PATH": "C:\\Tools\\ghidra",
           "JADX_PATH": "C:\\Tools\\jadx\\bin\\jadx.bat"
         }
       }
     }
   }
   ```

---

## 三、新旧工具平滑过渡与替换实操规范

### 1. 淘汰与弃用工具清单 (Deprecated List)

| 既有老工具 / 老脚本 | 现状与痛点 | 现代替换工具 | 替换理由 |
| :--- | :--- | :--- | :--- |
| `tools/disas_*.py`<br>*(上百个临时 Capstone 脚本)* | **全面弃用**<br>打印裸汇编指令，无控制流、无变量类型，依赖人眼脑补寄存器 | **Ghidra / REA (MCP)** | 直接输出清晰的 C 伪代码；大模型自动解析调用意图，效率提升 10 倍以上 |
| 人工比对 Hex 猜测协议 | 效率极低，易漏字段，多次引发 UI 显示 0 属性 bug | **UnityPy 批量解包** | 批量 Dump APK 内部的 `level_*.asset` 与 TextAsset，直接获得真实 JSON 数据 |
| 盲目猜测 AssetBundle 资源格式 | 只能看原始十六进制，解密算法靠猜 | **REA 交叉引用追踪 (XRefs)** | 让 REA 顺着文件加载函数直接提取解密密钥与算法 |

---

### 2. 典型实战场景替换对照表

#### 场景 A：探查某个看不懂的 ARM64 函数逻辑（如 SP3 触发、暴击算法、状态机迁移）
* **【过去的老做法】**：
  编写 `tools/disas_sp3.py`，调用 Capstone 反汇编 200 行指令，人眼或 AI 一行行追踪 `ldr w0, [x1, #0x28]`。
* **【现代的新做法】**：
  1. 使用 Il2CppDumper 导出的 `script.json` 在 Ghidra 中恢复符号。
  2. 直接定位到目标函数 RVA（例如 `0x71a4f0`）。
  3. 通过 REA 命令或 Ghidra 反编译器，直接读取 C 伪代码：
     ```c
     if (is_special_unlocked(bot) && current_sp >= 3) {
         TriggerMatineeSequence("sp3_motormaster");
     }
     ```
  4. 开发者在 5 秒钟内获知真实业务条件，立即对照去编写服务端返回包或 Hook 拦截。

#### 场景 B：挖掘战役关卡树、突袭节点与新角色属性数据
* **【过去的老做法】**：
  等待网络抓包，或者手写模拟数据构造器，导致缺少必要字段。
* **【现代的新做法（借鉴 PrimeDEV 的成功经验）】**：
  1. 不依赖外部网络抓包，利用 `UnityPy` 写一个自动化脚本：
     `python tools/extract_offline_assets.py --apk app-netflix-release.apk`
  2. 批量扫描并提取 `level_*.asset`、`tuning_*.json`、`roster_*.asset`。
  3. 将导出的静态字典直接整合进本地服务端数据库（`tftf_database.db`），瞬间点亮所有新角色属性、全关卡与突袭地图。

---

### 3. 绝对严禁替换的真理源底线

1. **真机运行时 NativeHook (`hook.c`) 绝不替换**：
   * 运行时必须保持轻量、极简的 C 语言注入架构。
   * 绝不在 APK 中运行任何解释型或臃肿的逆向框架。
2. **战斗真理源与手感基线绝不弱化**：
   * `re_notes/combat_truth_source.md` 与 `tools/nativehook/combat_truth_backup.c` 是神圣基线。
   * 工具链升级仅服务于“看懂逻辑”和“提取数据”，任何 Hook 修改必须 100% 跑通 `combat-test-cases.md` 的 6 大测试门禁（GATE-01 ~ GATE-06）。

---

## 四、新机环境冒烟测试清单 (Smoke Test)

换机后，在新环境的终端中按序执行以下命令，全绿即代表现代逆向工具链就绪：

```powershell
# 1. 验证基础编译底座
git --version
python --version
ndk-build --version
adb version

# 2. 验证 Java 与 Ghidra
java -version
Test-Path "C:\Tools\ghidra\support\analyzeHeadless.bat"

# 3. 验证 REA 工具与 Node
node -version
npx rea-agents --version

# 4. 验证既有 NativeHook 能正常编译出动态库
cd e:\Agent\TFTF\tools\nativehook
ndk-build clean
ndk-build
# 检查 libs/arm64-v8a/libnativehook.so 是否成功生成！
```
