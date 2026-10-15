# TFTF 高刷解耦架构与 120 帧自适应实施方案 (Framerate Decoupling Proposal)

> **设计背景**  
> 经实测验证，某外部补丁将 `Time.fixedDeltaTime` 强行设为 `1/144` 虽然提升了渲染帧率，但导致物理模拟与状态机每秒膨胀至 144 次，触发 Unity 时间保护截断，造成游戏内部时钟变慢、重击蓄力（`0.2s`）时间变长、吞键以及手感严重黏滞的问题。  
> 本方案通过**渲染刷新率与物理时钟解耦**，兼顾高刷流畅度与原生格斗手感（真理源保护）。

---

## 一、 核心解耦设计原则

1. **渲染高刷（视觉享受）**：
   - 允许将 `Application.targetFrameRate` 提升至 **120 FPS**（或 144 FPS）。
   - 让 UI 界面、滑动列表、抽卡动画与 3D 角色检视达到旗舰高刷屏的丝滑体验。

2. **物理时钟与判定严格锚定 60Hz（手感真理源）**：
   - 战斗中的物理步长 `UnityEngine.Time.fixedDeltaTime` **严禁随渲染帧率随意压缩**，必须严格保持在 **`1/60s = 0.016667s`**（或原厂 `1/30s` 整数对齐）。
   - 确保 `Simulation.Instance.Time` 与现实物理时间严格 1:1 同步，重击（Heavy Attack）0.2 秒蓄力判定分毫不差，肌肉记忆 100% 还原。

3. **双重演进方案**：
   - **方案 A（全局解耦渲染与物理）**：全局渲染锁 120 FPS，无论大厅还是战斗，渲染都是 120 帧，但战斗物理步长锁定 60Hz（`fixedDeltaTime = 1/60`）。
   - **方案 B（场景自适应高刷，推荐）**：大厅/菜单跑 120 FPS，进入格斗（`BattleArbiter.InitFighters`）后自动切回 60 FPS，战斗结束回大厅恢复 120 FPS。省电且无任何抖动。

---

## 二、 详细落地步骤与代码改动

### 1. 启动器前端 (`assets/launcher_menu.html`)
增加 120 帧选项胶囊：
```html
<div class="pill-btn" id="btn-fps-120" onclick="setFps(120, this)">
  <span class="pill-name c-purple" data-i18n="fps_120">120 帧</span>
  <span class="pill-badge bg-purple game-font">120 FPS</span>
</div>
```
并在本地配置中写入 `config.target_fps = 120`。

### 2. 离线服务器配置解析 (`tools/nativehook/inapk_server.c`)
放开 `target_fps` 的数值白名单限制：
```c
char *fps = strstr(buf, "\"target_fps\"");
if (fps) {
    char *c = strchr(fps, ':');
    if (c) {
        int v = (int)strtol(c + 1, NULL, 10);
        // 放行 30, 60, 120
        if (v == 30 || v == 60 || v == 120) g_user_settings.target_fps = v;
    }
}
```

### 3. 原生钩子与物理时钟解耦 (`tools/nativehook/hook.c`)
在 `installer()` 中 Hook `UnityEngine.Time.set_fixedDeltaTime`（`0x16b6d0c`）：
```c
static fn8 orig_set_fixedDeltaTime = NULL;
static void* hooked_set_fixedDeltaTime(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    // 无论外部如何设置，强制将物理步长锚定在 60Hz 步长（或 timeScale / 60.0f）
    float current_time_scale = 1.0f;
    typedef float (*fn_get_timeScale)(void);
    fn_get_timeScale get_scale = (fn_get_timeScale)(g_base + 0x16b6db8);
    if (get_scale) {
        current_time_scale = get_scale();
        if (current_time_scale <= 0.0f) current_time_scale = 1.0f;
    }
    
    // 物理步长严格基于 60Hz 计算：保证整除 30fps 动作资产，蓄力时间分毫不差
    float physics_step = current_time_scale / 60.0f; 
    
    // 传入底层
    union { float f; void* p; } u;
    u.f = physics_step;
    if (orig_set_fixedDeltaTime) {
        return orig_set_fixedDeltaTime(u.p, a1, a2, a3, a4, a5, a6, a7);
    }
    return NULL;
}
```

### 4. 战斗入口重置防护 (`hook_56` / `BattleArbiter.InitFighters`)
在战斗初始化时，若采用场景自适应方案，调用 `Application.set_targetFrameRate(60)`，退出战斗时切回 `120`。

---

## 三、 验证与质量门禁 (Quality Gate)

1. **TC-GATE-HEAVY (重击蓄力门禁)**：
   - 验证连续 10 次“四连轻击接重击”（L1-L2-L3-L4-Heavy），肌肉记忆松手必须 100% 稳定出重击，绝不吞键。
2. **TC-GATE-TIMESTEP (时钟同步门禁)**：
   - Logcat 中检查战斗内 `Simulation.Instance.Time` 的 1 秒流逝严格对应现实 1000ms（误差 $\le 2\%$）。
3. **TC-GATE-FPS (高刷门禁)**：
   - 在大厅菜单中，通过 Android 系统 GPU 呈现分析或 PerfDog 确认渲染帧率为 120 FPS。
