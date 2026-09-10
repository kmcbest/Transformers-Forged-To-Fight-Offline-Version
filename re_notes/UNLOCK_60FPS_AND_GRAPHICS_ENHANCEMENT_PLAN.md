# 《百炼为战》安卓离线版：60帧高刷与高精特效（火花/战损冒烟）解锁方案

## 一、方案背景与现状诊断

### 1.1 帧率现状
- **现象**：大部分安卓设备在运行当前离线编译版时，默认稳定在 **30 FPS**，仅在少数配备 120Hz 屏幕的现代设备上或特定过场瞬间，由于垂直同步分频机制偶尔能观察到 60 帧画面。
- **原因**：2017 年原厂（Kabam）出于对当年移动设备能耗与发热的考量，在游戏底层画质引擎 `PerformanceManager` 的初始化代码中，硬编码了 `Application.targetFrameRate = 30` 以及 `QualitySettings.vSyncCount = 2`。在 60Hz 屏幕下，60 / 2 = 30 FPS。

### 1.2 画质与视觉特效现状
- **现象**：对比原厂 iOS（苹果）版本，安卓版在战斗中缺少大量的打击飞溅火星（Sparks），且角色在残血受损时，身上不会出现受损贴图剥落和冒烟带电的视觉反馈。
- **资源实测**：经由 `UnityPy` 对安卓 APK 内的 `character_fx_procedural.assetbundle` 及角色专属包解包核对，苹果版所拥有的火花粒子贴图（如 `fx_t_grind_sparks.png`、`fx_t_laser_sparks.png` 等）、受损冒烟序列帧（`fx_t_smoke_steam_anim.png`）以及动态破损贴图渲染管线（`CharacterDamageManager`）**100% 完整保留在安卓安装包中，未被做任何资源层面的剔除**。
- **限制原因**：原厂在 2017 年针对当年安卓平台分裂严重的 OpenGL ES 驱动和较弱的 GPU 算力，在代码中设置了保守的硬件门禁——默认禁止安卓运行 GPU 粒子模拟（GPUParticles），并跳过了战损贴图与粒子挂件管理器（`CharacterDamageManager`）的初始化。

---

## 二、底层逆向证据与核心函数定位（ARM64）

### 2.1 帧率控制关键点

1. **`PerformanceManager` 默认硬锁 30 帧**：
   - **函数位置**：`0xda5168`（`PerformanceManager..ctor / Awake`）
   - **关键指令**：
     ```assembly
     0xda52e0: mov  w0, #0x1e             ; 30 FPS
     0xda52f0: bl   #0x1b46108            ; UnityEngine.Application.set_targetFrameRate(30)
     0xda52f8: mov  w0, #2                ; vSyncCount = 2 (2次VBlank刷1帧)
     0xda5304: b    #0x16a71c0            ; UnityEngine.QualitySettings.set_vSyncCount(2)
     ```

2. **场景/画质配置驱动的分支跳转**：
   - **函数位置**：`0xda65dc`（`PerformanceManager.ApplyOnce`）
   - **分支判断**：`0xda6700` 读取 `EnvironmentInfo.targetFramerate`（偏移 `0xa0`）：
     - `eTARGET_FRAMERATE.Capped (0)`：`vSyncCount = 2`, `targetFrameRate = 30`
     - `eTARGET_FRAMERATE.Uncapped (1)`：不加限制，按系统默认刷新
     - `eTARGET_FRAMERATE._30NoVSync (2)`：`vSyncCount = 0`, `targetFrameRate = 30`
     - `eTARGET_FRAMERATE._60NoVSync (3)`（跳转至 `0xda6724`）：
       ```assembly
       0xda6724: mov  w0, wzr              ; vSyncCount = 0
       0xda672c: bl   #0x16a71c0           ; set_vSyncCount(0)
       0xda6730: mov  w0, #0x3c            ; targetFrameRate = 60
       0xda6764: bl   #0x1b46108           ; set_targetFrameRate(60)
       ```

---

### 2.2 画质与特效门禁关键点

1. **GPU 粒子模拟门禁（`CanDeviceRunGPUParticles`）**：
   - **函数位置**：`0xda7e68`
   - **逻辑分析**：
     ```assembly
     0xda7ea8: ldr  w19, [x8, #0x24]      ; 读取 EnvironmentInfo.gpuParticles (偏移 0x24)
     ...
     0xda7ec4: cmp  w19, #2               ; 判断是否等于 2 (eDEFAULT.ForceOn)
     0xda7ec8: cset w0, eq                ; 仅当配置显式等于 ForceOn 时返回 true (1)，否则全部返回 false (0)
     0xda7edc: ret
     ```
   - **影响**：安卓的默认配置文件中 `gpuParticles` 为 `Default (0)` 或 `ForceOff (1)`，导致该函数永远返回 `0`，打击产生的大量 GPU 火花粒子被整体屏蔽。

2. **角色受损/残血冒烟管理器初始化门禁（`CharacterDamageManager`）**：
   - **函数位置**：`0xda65dc`（`PerformanceManager.ApplyOnce` 内 `0xda663c`）
   - **逻辑分析**：
     ```assembly
     0xda663c: ldr  w9, [x8, #0x5c]       ; 读取 EnvironmentInfo.damageQuality (偏移 0x5c)
     0xda6640: cbnz w9, #0xda66c8         ; 若未配置或关闭，直接跳过初始化！
     ...
     0xda66bc: bl   #0xd19da4             ; CharacterDamageManager.Init (实例化战损渲染器)
     ```
   - **影响**：当 `CharacterDamageManager` 被跳过初始化后，战斗内所有机器人的受击破损贴图计算停止，角色身上挂载的残血低血量烟雾/蒸汽粒子预制体（`fx_t_smoke_steam_anim.png` / `fx_p_burst_smoke.prefab`）因无法接收到血量阶段阈值信号而无法触发。

3. **环境物理破坏门禁（`CanDeviceRunDestruction`）**：
   - **函数位置**：`0xda7df0`
   - **逻辑分析**：同样仅当 `destruction == 2`（`ForceOn`）时返回 1。

---

## 三、解锁实施方案

我们可以采用两种互补的工程实现路径：
- **方案 A（首选/最优雅）：Native Hook 运行时拦截注入**
  直接在仓库现有的 `tools/nativehook/hook.c`（`libdothook.so`）中挂钩或初始化时修改，具备极佳的兼容性，不用频繁改动 `patch_il2cpp.py`。
- **方案 B：静态二进制补丁（Static Binary Patching）**
  直接把补丁写入 `patches/patch_il2cpp.py`，永久性修改 `libil2cpp.so` 机器码。

---

### 方案 A：通过 `libdothook.so` 运行时注入（推荐）

现有的 `libdothook.so` 会在 `libil2cpp.so` 加载后由动态链接器优先初始化。我们可以在 `hook.c` 的构造函数中通过内联 Hook 拦截相关 API。

#### 1. 帧率控制 Hook（强制 60 帧或满帧）
在 `tools/nativehook/hook.c` 中：
```c
// 拦截 Application.set_targetFrameRate (arm64: 0x1B46108)
// 无论游戏内部试图将帧率切为 30 还是其他值，一律强制重写为 60 (或 120)
static void hooked_set_targetFrameRate(int fps, void* methodInfo) {
    // 强制锁 60 帧 (若支持高刷屏幕可设为 120 或 -1 不限帧)
    orig_set_targetFrameRate(60, methodInfo);
}

// 拦截 QualitySettings.set_vSyncCount (arm64: 0x16A71C0)
// 将垂直同步设为 1（60Hz屏->60帧，120Hz屏->120帧）或设为 0（关垂直同步，由 targetFrameRate 决定）
static void hooked_set_vSyncCount(int count, void* methodInfo) {
    orig_set_vSyncCount(1, methodInfo);
}
```

#### 2. 特效能力函数 Hook（强制开启 GPU 粒子与破坏效果）
直接将 `PerformanceManager` 的能力检测函数短接为 `return true`：
```c
// arm64 RVA: 0xda7e68 (CanDeviceRunGPUParticles)
// 机器码直接替换为: mov w0, #1; ret (bytes: 20008052 c0035fd6)
// arm64 RVA: 0xda7df0 (CanDeviceRunDestruction)
// 机器码直接替换为: mov w0, #1; ret (bytes: 20008052 c0035fd6)
```

---

### 方案 B：静态 IL2CPP 字节补丁

在 `patches/patch_il2cpp.py` 中追加静态补丁规则：

#### 1. 启动帧率由 30 提升至 60 帧并设置垂直同步为 1
- **目标地址**：`0xda52e0`
- **原始机器码**：
  ```assembly
  0xda52e0: mov w0, #0x1e             ; 20038052
  ...
  0xda52f8: mov w0, #2                ; 40008052
  ```
- **补丁机器码**：
  ```assembly
  0xda52e0: mov w0, #0x3c             ; 80078052 (目标帧率 60)
  ...
  0xda52f8: mov w0, #1                ; 20008052 (vSyncCount = 1)
  ```

#### 2. 强制开启 GPU 粒子与环境破坏
- **`PerformanceManager.CanDeviceRunGPUParticles` (0xda7e68)**:
  - 替换为 `mov w0, #1; ret` (`20008052 c0035fd6`)
  - **效果**：无论设备配置如何，强制向引擎报告支持并渲染 GPU 粒子（火星四溅）。
- **`PerformanceManager.CanDeviceRunDestruction` (0xda7df0)**:
  - 替换为 `mov w0, #1; ret` (`20008052 c0035fd6`)
  - **效果**：解锁战斗场景破坏特效。

#### 3. 强制开启战损贴图与残血冒烟初始化
- **目标地址**：`0xda6640`
- **原始机器码**：
  ```assembly
  0xda6640: cbnz w9, #0xda66c8        ; 49040035 (若未配置则跳转跳过初始化)
  ```
- **补丁机器码**：
  ```assembly
  0xda6640: nop                       ; 1f2003d5 (取消跳转，强制穿透执行 CharacterDamageManager.Init)
  ```
  - **效果**：角色受损渲染器（`DamageRenderer`）与战损管理器被强行初始化，战斗中当机器人血量下降至阈值阶段时，残血冒烟粒子与破损贴图正常渲染。

---

## 四、验证与测试计划

1. **帧率测试**：
   - 使用 Android Studio / 快手 Perfdog / 小米或华为手机内置的游戏帧率监视悬浮窗。
   - 观察在战斗常规状态、过场动画（Matinee）、以及菜单界面的实时渲染帧率是否稳定在 60 FPS，无 30 FPS 掉帧回落。
2. **火花粒子（Sparks）测试**：
   - 选用重击型角色（如巨齿鲨、钢锁、威震天）进行重击蓄力或被重击格挡。
   - 观察兵刃相交或金属碰撞瞬间是否有密集的明亮火星散射（原版安卓仅有微弱的光圈，开启后应有大量拉丝状火星粒子）。
3. **残血冒烟（Damage & Smoke）测试**：
   - 进入单挑对战，将己方或敌方机器人的生命值打至 30% 以下。
   - 观察机器人关节、胸口或受损骨骼处是否开始持续向外喷出黑烟或带有电弧的蒸汽动画（`fx_t_smoke_steam_anim`）。
4. **性能与稳定性监控**：
   - 连续进行 3-5 场战斗，通过 `logcat -s TFTFHOOK` 观察是否有 GPU 内存泄漏或 Shader 编译异常，监测机身温控状态。
