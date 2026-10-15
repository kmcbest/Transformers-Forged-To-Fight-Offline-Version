# 现代逆向工具链安装配置与逐步替换老工具实操指南
*(Modern Reverse Engineering Toolchain Setup & Migration Guide)*

> **文档定位**：本文档为开发者换机或新机器环境搭建时的一站式安装指南与工具演进标准。记录了如何从过去“纯 Capstone 裸汇编”的刀耕火种时代，平滑过渡并升级到“Ghidra 反编译 + REA (Reverse Engineer Anything) MCP 智能体驱动”的现代逆向分析工作流，同时明确界定了“分析期现代工具链”与“真机运行时 NativeHook”的严格边界。
> 
> **物理磁盘规范**：所有重型工具链一律装在 `E:\Agent\TFTF\toolchain\`，绝不污染或占用 C 盘空间；在 `C:\Tools` 建立轻量目录联接（Directory Junctions），实现透明跨盘访问。

---

## 目录
1. [核心原则与技术分工界限](#一核心原则与技术分工界限)
2. [E 盘专属工具链物理布局与目录联接](#二e-盘专属工具链物理布局与目录联接)
3. [一键全自动安装与验证脚本](#三一键全自动安装与验证脚本)
4. [核心工具链清单与详细说明](#四核心工具链清单与详细说明)
   - [1. 基础开发与编译环境](#1-基础开发与编译环境)
   - [2. 现代逆向分析与反编译工具链](#2-现代逆向分析与反编译工具链)
   - [3. REA (Reverse Engineer Anything) 智能体配置与 MCP 接入](#3-rea-reverse-engineer-anything-智能体配置与-mcp-接入)
5. [新旧工具平滑过渡与替换实操规范](#五新旧工具平滑过渡与替换实操规范)
   - [1. 淘汰与弃用工具清单 (Deprecated List)](#1-淘汰与弃用工具清单-deprecated-list)
   - [2. 典型实战场景替换对照表](#2-典型实战场景替换对照表)
   - [3. 绝对严禁替换的真理源底线](#3-绝对严禁替换的真理源底线)
6. [冒烟测试清单 (Smoke Test)](#六冒烟测试清单-smoke-test)

---

## 一、核心原则与技术分工界限

在引入最新逆向工具链之前，必须在架构层确立一条铁律：

| 阶段 | 使用工具 | 核心职责 | 替换策略 |
| :--- | :--- | :--- | :--- |
| **逻辑分析与逆向阶段**<br>*(Investigation Phase)* | **Ghidra / JADX / REA / UnityPy** | 分析 ARM64 算法、还原 C 伪代码、提取 APK 内部沉睡资产（关卡/数值表/AssetBundle） | **【立即升级替换】**<br>坚决淘汰 Capstone 裸汇编脚本，全面改用反编译与智能体驱动 |
| **真机运行时拦截阶段**<br>*(Runtime Patching)* | **NativeHook (`hook.c` + NDK)** | 注入 Android 内存、微秒级函数跳板（Trampoline）、保证 100% 官方打击手感 | **【严禁替换，保持极简】**<br>真机端绝不引入任何重型工具，保持轻量高效 C 语言 Hook |

---

## 二、E 盘专属工具链物理布局与目录联接

为避免 C 盘空间膨胀，本项目所有逆向工具实体均位于 `E:\Agent\TFTF\toolchain\`，并通过 NTFS Junction 映射到 `C:\Tools`：

```text
E:\Agent\TFTF\toolchain\
├── ghidra\            <=== [实体] Ghidra 12.1.4 (反编译器核心)
├── jdk-21\            <=== [实体] Adoptium OpenJDK 21 (Ghidra 12+ 强依赖)
├── jadx\              <=== [实体] JADX 1.5.6 (DEX/Java 反编译)
├── Il2CppDumper\      <=== [实体] Il2CppDumper 6.7.46 (符号与结构体导出)
├── rea\               <=== [实体] REA 6.4.0 (Model Context Protocol 逆向智能体服务)
├── rea.bat            <=== REA CLI 快速启动批处理
└── install_modern_re_tools.py <=== 一键自动安装与软链同步脚本

C:\Tools\ (仅占符号链接，0 字节物理占用)
├── ghidra        <junction> ==> E:\Agent\TFTF\toolchain\ghidra
├── jdk-21        <junction> ==> E:\Agent\TFTF\toolchain\jdk-21
├── jadx          <junction> ==> E:\Agent\TFTF\toolchain\jadx
├── Il2CppDumper  <junction> ==> E:\Agent\TFTF\toolchain\Il2CppDumper
├── rea           <junction> ==> E:\Agent\TFTF\toolchain\rea
└── rea.bat       <shim>     ==> 调用 E:\Agent\TFTF\toolchain\rea.bat
```

---

## 三、一键全自动安装与验证脚本

在新机器上克隆仓库后，仅需运行一行命令，脚本会自动下载各工具 Release Zip、解压至 E 盘、配置独立便携式 JDK 21 并建立 `C:\Tools` 联接：

```powershell
python "tools/install_modern_re_tools.py"
```

---

## 四、核心工具链清单与详细说明

### 1. 基础开发与编译环境

1. **Python 3.10+** (推荐 3.10.x 或 3.11.x)
   - 依赖项：`pip install UnityPy capstone colorama requests flask`
2. **Android NDK** (本项目现成位于 `E:\Agent\TFTF\toolchain\android-ndk-r26b`)
3. **Android SDK Platform-Tools (ADB)** (现成位于 `E:\Agent\TFTF\toolchain\android-sdk\platform-tools`)

---

### 2. 现代逆向分析与反编译工具链

1. **Adoptium OpenJDK 21** (`E:\Agent\TFTF\toolchain\jdk-21`)
   - **注意**：Ghidra 12+ **强依赖 JDK 21+**（系统自带的 JDK 17 会报错）。
   - 本方案采用便携式独立部署，并在 `ghidra/support/launch.properties` 中指定了 `JAVA_HOME_OVERRIDE=E:/Agent/TFTF/toolchain/jdk-21`，**完全不污染系统默认 Java 环境**。
2. **Ghidra (v12.x+)** (`E:\Agent\TFTF\toolchain\ghidra`)
   - **无头分析程序**：`support\analyzeHeadless.bat`。
   - **功能定位**：ARM64 机器码分析引擎，直接输出人类可读的 C 伪代码。
3. **JADX (v1.5.x+)** (`E:\Agent\TFTF\toolchain\jadx`)
   - CLI 执行入口：`bin\jadx.bat`；GUI 界面入口：`bin\jadx-gui.bat`。
4. **Il2CppDumper (v6.7.x+)** (`E:\Agent\TFTF\toolchain\Il2CppDumper`)
   - **配合 Ghidra**：运行后生成的 `script.json` 与 `ghidra_with_struct.py` 可直接导入 Ghidra，一键为 9.2.0 所有方法恢复官方命名。

---

### 3. REA (Reverse Engineer Anything) 智能体配置与 MCP 接入

REA 是连接 AI 智能体（Cursor / Claude Code / Antigravity / Codex）与底层逆向工具链（Ghidra、JADX）的 MCP 协议桥梁。

1. **本地运行方式**：
   在任意终端输入以下命令均可直接调用 REA：
   ```powershell
   & "E:\Agent\TFTF\toolchain\rea.bat" --version
   # 或通过 C:\Tools 联接调用
   & "C:\Tools\rea.bat" --version
   ```
2. **MCP 配置文件设置**（以 Cursor / Claude Desktop / Antigravity 的 `mcp_config.json` 为例）：
   ```json
   {
     "mcpServers": {
       "rea": {
         "command": "cmd",
         "args": ["/c", "E:\\Agent\\TFTF\\toolchain\\rea.bat", "--mcp"],
         "env": {
           "GHIDRA_PATH": "E:\\Agent\\TFTF\\toolchain\\ghidra",
           "JADX_PATH": "E:\\Agent\\TFTF\\toolchain\\jadx\\bin\\jadx.bat"
         }
       }
     }
   }
   ```

---

## 五、新旧工具平滑过渡与替换实操规范

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

## 六、冒烟测试清单 (Smoke Test)

在终端中执行以下验证命令，全部通过即代表整套工具链安装完备：

```powershell
# 1. 验证基础编译底座
python --version
node --version

# 2. 验证 Ghidra、JDK21 与 JADX
& "E:\Agent\TFTF\toolchain\jdk-21\bin\java.exe" -version
& "E:\Agent\TFTF\toolchain\jadx\bin\jadx.bat" --version
Test-Path "E:\Agent\TFTF\toolchain\ghidra\support\analyzeHeadless.bat"

# 3. 验证 REA
& "E:\Agent\TFTF\toolchain\rea.bat" --version

# 4. 验证 C:\Tools 联接可用性
Get-ChildItem "C:\Tools"

# 5. 验证 NativeHook 编译
cd E:\Agent\TFTF\tools\nativehook
ndk-build
```
