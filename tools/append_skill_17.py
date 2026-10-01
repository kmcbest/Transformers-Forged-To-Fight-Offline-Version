# -*- coding: utf-8 -*-
section_17 = '''

---

## 17. 跨分支切换编译卡 LOGO / ODR 虚假包体死锁坑 (Branch Switching Boot Freeze & ODR Phantom Pack Deadlock)

### 17.1 现象 (Symptom)
* **主现象**：在切换 Git 分支（例如从 `main`/`redeco` 切换到 `whitebox`、`blender` 等其他分支或新克隆工作区）后，运行 `build_apk.py` 编译并安装 APK，游戏启动后停留在 **KABAM** 启动屏 LOGO 界面，无法进入游戏，Unity 音频播放静音帧空转。
* **日志特征**：
  - `adb logcat` 显示 `HTTP: POST /auth/init` 与 `HTTP: POST /auth/enumerate` 之后再无任何后续 HTTP 请求（无法到达 `/auth/login` 与 `/bcg/getLoginData`）。
  - 主进程并未崩溃（PID 存活，主线程 `main` 与 `UnityGfxDeviceW` 持续占用 10%~20% CPU 循环刷新空白帧）。
  - Native Hook 内部日志在读取 FastDot `bundles` 与 `assetpack` 处戛然而止（通常停在 210KB 左右）。
* **误区警示**：容易误判为 Native Hook 地址漂移、Google Play / Token 认证失败、网络请求死锁或深层 il2cpp 汇编指令崩溃，导致开发者或 Agent 陷入数小时无意义的逆向死循环。

### 17.2 根本原因 (Root Cause)
1. **`.gitignore` 导致的跨分支资产断代 (Git-Ignored Asset Bundles Disconnected)**：
   - 核心资产目录 `assets_netflix/` 在 `.gitignore` 中被全局忽略；`assets_redeco/` 下的 `.assetbundle` 同样受忽略规则影响。
   - 当从主开发分支切换到其它分支或新建工作区目录时，Git **不会携带这些未跟踪的二进制资产**，导致新工作区的 `assets_netflix/` 为空，`assets_redeco/` 缺失大量角色包（如 Seekers 极速流派包等）。
2. **打包脚本硬编码注册引发的 ODR 虚假包体死锁 (ODR Phantom Pack Deadlock)**：
   - `Server/build_phone_apk.py` 在向 `assets/packs.txt` 注册包体列表时，曾包含硬编码的全量角色包名单（如 `chromia_gs_kabam_odr`、`deadend_gs_deluxe2015_odr`、`acidstorm_gs_leader2015_odr` 等）。
   - 如果本地 `assets_netflix/` 或 `assets_redeco/` 缺失对应 bundle，打包脚本无法向 APK 注入其实际的 `.assetbundle` 和 `toc.txt` 文件。
   - **致命后果**：`packs.txt` 声明了这些包存在，但 APK 内部却完全没有这些文件（虚假包体）。Unity 的按需资源加载系统（`ODRManager` / `AssetPackService`）在启动阶段遍历 `packs.txt` 时，认为这些包尚未下载，便激活 `ODRManager.DownloadAllCoroutine` 发起 CDN 网络下载。在离线环境下该下载永远不会返回，导致整个游戏初始化流程**死锁在开屏 LOGO 阶段**！
3. **SDCard 残余热重载 Payload 混淆 (Stale SDCard Hot-Reload Payload Override)**：
   - 手机端 `/sdcard/Android/media/com.kabam.bigrobot/tftf_offline_payload.bin` 若残留了旧分支推送的旧数据，`inapk_server.c` 会优先使用热重载 payload 覆盖 APK 内置 payload，造成蓝图数据与 APK 实际打包资产版本不匹配。

### 17.3 规范与铁律 (Standard & Rules)
1. **铁律 1（动态注册原则）**：`Server/build_phone_apk.py` 严禁盲目硬编码向 `assets/packs.txt` 添加不存在的 pack；只能向 `packs.txt` 注册在 `assets_netflix/` 或 `assets_redeco/` 中**真实存在且被成功注入 APK** 的包体。
2. **铁律 2（换分支资产对齐检查）**：切换分支后编译 APK 前，必须执行资产对齐检查，确保 `assets_netflix/`（含 `chromia_gs_kabam.assetbundle`、`deadend_gs_deluxe2015.assetbundle`、`moves.assetbundle`、procedural 动画/音效/特效包）和 `assets_redeco/` 所需资源已到位。
3. **铁律 3（防卡 LOGO 质检工具）**：在安装 APK 前，运行质检脚本扫描 APK 内的 `packs.txt`：
   ```python
   # 遍历 APK 的 assets/packs.txt 中的所有 pack 名称
   # 验证 APK 中是否至少包含该 pack 对应的一个有效文件（bundle 或 toc.txt）
   # 若 Missing packs > 0，禁止安装！必须立即补齐资产后重新打包！
   ```
4. **铁律 4（清理手机残留文件）**：切换分支或遇到 LOGO 卡顿时，执行标准清理命令：
   ```bash
   adb shell rm -f /sdcard/Android/media/com.kabam.bigrobot/tftf_offline_payload.bin
   adb shell rm -rf /sdcard/Android/data/com.kabam.bigrobot/files/UnityCache
   ```
'''

with open(r'e:\Agent\TFTF-blender\.agents\skills\tftf_revival\SKILL.md', 'a', encoding='utf-8') as f:
    f.write(section_17)

print("Successfully appended Section 17 to SKILL.md in TFTF-blender!")
