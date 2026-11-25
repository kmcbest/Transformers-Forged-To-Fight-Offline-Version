# TFTF 战斗实时调试悬浮窗 (Combat Trigger Overlay) 实现方案与技术规范

> **目标**：在游戏启动菜单的隐藏调试弹窗中新增开关，开启后在战斗中实时于屏幕上显示技能掷骰（Dice Roll）、暴击判定与 Buff/Debuff 触发战报，便于玩家通过手机录屏截图直接向开发团队/AI Agent 反馈技能机制与 Bug。

---

## 1. 架构与端到端数据流向

```
┌────────────────────────────────────────────────────────────────────────┐
│ 1. 启动菜单 Launcher Menu (tools/launcher_menu.html)                  │
│    在 #debug-modal 弹窗中提供开关: 战斗判定悬浮战报 (Combat Overlay)    │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ 写入持久化配置
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 2. 本地设置存储 (user_settings.json)                                    │
│    "enable_combat_debug_overlay": true                                 │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ 游戏启动时解析
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 3. 原生服务端配置加载 (tools/nativehook/inapk_server.c & .h)            │
│    - UserSettings 结构体新增 int enable_combat_debug_overlay            │
│    - 导出接口: int tftf_get_combat_debug_overlay(void);                │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ Native 状态读取
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 4. 战斗 Native Hook (tools/nativehook/hook.c)                          │
│    - 拦截 Ability 触发、暴击判定与 Buff 施加                            │
│    - 格式化推入环形队列: g_combat_lines (最近 5 条)                     │
│    - 在屏渲染: Unity OnGUI / 战斗 HUD Label / 战斗飘字组件             │
└──────────────────────────────────┬─────────────────────────────────────┘
                                   │ 实时绘制于画面上方
                                   ▼
┌────────────────────────────────────────────────────────────────────────┐
│ 5. 最终效果 (游戏录屏可见)                                              │
│    [12.4s] Arcee -> Bleed | Dice: 32% Roll: 18% (PASS) | OnCrit        │
│    [13.1s] Ironhide -> Evade Failed | P: 15% Roll: 72%                 │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. 详细实施步骤 (Implementation Steps)

### 步骤 1：前端启动菜单修改 (`tools/launcher_menu.html`)

在隐藏特权调试弹窗 `#debug-modal`（即“敌人不动”所在面板）增加控制开关：

1. **HTML 节点追加**（在 `#chk-full-power` 下方追加）：
   ```html
   <label class="toggle-row" style="cursor: pointer; display: flex; align-items: center; justify-content: space-between; background: rgba(255,255,255,0.03); padding: 10px 12px; border-radius: 8px; border: 1px solid rgba(255,255,255,0.08);">
     <div style="padding-right: 12px;">
       <div style="font-size: 13.5px; font-weight: bold; color: #f8fafc;" data-i18n="combat_overlay_title">战斗判定悬浮战报 (Combat Overlay)</div>
       <div style="font-size: 11px; color: #94a3b8; margin-top: 2px;" data-i18n="combat_overlay_desc">屏幕实时显示技能掷骰概率、暴击/闪避判定与Buff施加，便于录屏分析</div>
     </div>
     <input type="checkbox" id="chk-combat-overlay" onchange="toggleCombatOverlay(this.checked)" style="transform: scale(1.25); accent-color: #f59e0b; cursor: pointer;">
   </label>
   ```

2. **多语言词条 (`i18n`)**：
   - 中文：
     - `combat_overlay_title`: `"战斗判定悬浮战报 (Combat Overlay)"`
     - `combat_overlay_desc`: `"屏幕实时显示技能掷骰概率、暴击/闪避判定与Buff施加，便于录屏分析"`
   - 英文：
     - `combat_overlay_title`: `"Combat Trigger Overlay"`
     - `combat_overlay_desc`: `"Display real-time ability dice rolls, crit/evade procs, and buff events on-screen for video debugging"`

3. **JS 逻辑绑定**：
   - 默认配置：`config.enable_combat_debug_overlay = false;`
   - 开关回调：
     ```javascript
     function toggleCombatOverlay(enabled) {
       config.enable_combat_debug_overlay = !!enabled;
       saveSettings();
     }
     ```
   - 页面初始化解析：
     ```javascript
     if (parsed.enable_combat_debug_overlay !== undefined) {
       var chkOverlay = document.getElementById("chk-combat-overlay");
       if (chkOverlay) chkOverlay.checked = !!parsed.enable_combat_debug_overlay;
       config.enable_combat_debug_overlay = !!parsed.enable_combat_debug_overlay;
     }
     ```

---

### 步骤 2：Native 配置解析层修改 (`tools/nativehook/inapk_server.c` & `.h`)

1. **结构体扩充 (`tools/nativehook/inapk_server.c`)**：
   ```c
   typedef struct {
       char commander_name[64];
       float challenge_hp_multiplier;
       float enemy_mana_gain;
       int enable_custom_bots;
       int arena_randomization;
       int skip_launcher_next_time;
       int target_fps;
       int enable_swipe_specials;
       int freeze_enemy_ai;
       int start_full_power;
       int enable_combat_debug_overlay; // 新增字段
   } UserSettings;

   static UserSettings g_user_settings = {
       // ... 既有字段 ...
       .freeze_enemy_ai = 0,
       .start_full_power = 0,
       .enable_combat_debug_overlay = 0 // 默认关闭
   };
   ```

2. **JSON 反序列化解析 (`load_user_settings`)**：
   ```c
   char *cdo = strstr(buf, "\"enable_combat_debug_overlay\"");
   if (cdo) {
       char *c = strchr(cdo, ':');
       if (c) {
           while (*c && (*c == ':' || isspace((unsigned char)*c))) c++;
           g_user_settings.enable_combat_debug_overlay = !strncmp(c, "true", 4);
       }
   }
   ```

3. **头文件导出 (`tools/nativehook/inapk_server.h`)**：
   ```c
   int tftf_get_combat_debug_overlay(void);
   ```

---

### 步骤 3：Native Hook 战斗判定捕获与环形缓冲区 (`tools/nativehook/hook.c`)

1. **环形战报队列定义**：
   ```c
   #define COMBAT_OVERLAY_MAX_LINES 5
   #define COMBAT_OVERLAY_LINE_LEN  128

   typedef struct {
       char text[COMBAT_OVERLAY_LINE_LEN];
       float timestamp;
       float duration;
       int is_active;
   } CombatOverlayEntry;

   static CombatOverlayEntry g_overlay_lines[COMBAT_OVERLAY_MAX_LINES];
   static int g_overlay_head = 0;
   static pthread_mutex_t g_overlay_lock = PTHREAD_MUTEX_INITIALIZER;

   void combat_overlay_push(const char *fmt, ...) {
       if (!tftf_get_combat_debug_overlay()) return;

       char buf[COMBAT_OVERLAY_LINE_LEN];
       va_list args;
       va_start(args, fmt);
       vsnprintf(buf, sizeof(buf), fmt, args);
       va_end(args);

       pthread_mutex_lock(&g_overlay_lock);
       int idx = g_overlay_head % COMBAT_OVERLAY_MAX_LINES;
       strncpy(g_overlay_lines[idx].text, buf, COMBAT_OVERLAY_LINE_LEN - 1);
       g_overlay_lines[idx].text[COMBAT_OVERLAY_LINE_LEN - 1] = '\0';
       g_overlay_lines[idx].is_active = 1;
       g_overlay_head++;
       pthread_mutex_unlock(&g_overlay_lock);
   }
   ```

2. **核心判定拦截点挂钩**：
   - **暴击与受击点**：在 `CombatEntity.TakeDamage` / 攻击链命中结算处，拦截判定结果：
     ```c
     if (is_crit) {
         combat_overlay_push("[%s] CRIT! Dmg: %d | Move: %s", attacker_name, damage, move_id);
     }
     ```
   - **Ability 技能掷骰与 Buff 施加点**：在能力评估函数（如 `Ability.Evaluate`）或 `BuffSystem.ApplyBuff` 处：
     ```c
     if (proc_success) {
         combat_overlay_push("[%s] -> %s (PASS: %d%% <= Req:%d%%) | %s",
             attacker_name, buff_name, rolled_dice, req_chance, trigger_condition);
     } else {
         combat_overlay_push("[%s] -> %s (FAIL: %d%% > Req:%d%%)",
             attacker_name, buff_name, rolled_dice, req_chance);
     }
     ```

---

### 步骤 4：在屏实时文字渲染机制 (Rendering)

推荐**方案 A（Unity 官方 `OnGUI` 注入）**：
1. 拦截战斗 UI 控制器（如 `FightHUD.OnGUI`），若未实现可直接在 `hook.c` 挂钩已有在战斗主循环中触发的 MonoBehaviour。
2. 调用 Unity 导出 C-API 绘制半透明黑色背景与文字列表：
   ```c
   // 伪代码示例：
   void hook_FightHUD_OnGUI(void *self) {
       orig_FightHUD_OnGUI(self);

       if (!tftf_get_combat_debug_overlay()) return;

       // 绘制屏幕上方顶栏区域 (血条正下方，宽度 600px，高度 120px)
       pthread_mutex_lock(&g_overlay_lock);
       for (int i = 0; i < COMBAT_OVERLAY_MAX_LINES; i++) {
           int idx = (g_overlay_head - 1 - i + COMBAT_OVERLAY_MAX_LINES) % COMBAT_OVERLAY_MAX_LINES;
           if (g_overlay_lines[idx].is_active) {
               // 渲染绿色/高亮文字，逐行向上滚动
               DrawGUI_Label(100, 150 + i * 22, g_overlay_lines[idx].text);
           }
       }
       pthread_mutex_unlock(&g_overlay_lock);
   }
   ```

**备选方案 B（原生战斗跳字系统 Fly-off Text）**：
- 直接调用游戏现成的 `CombatFlyoffManager.SpawnText(target_pos, debug_str, Color.yellow)`。
- **优点**：无需手写 GUI 渲染，跳字随角色移动，画面极具原生打击感。

---

## 3. 验收标准与测试门禁 (Quality Gate Checklist)

1. [ ] **启动设置持久化**：在启动菜单勾选后，检查 `/data/data/com.kabam.bigrobot/files/user_settings.json` 中存在 `"enable_combat_debug_overlay": true`，重启游戏仍保持勾选。
2. [ ] **关闭状态无副作用**：未勾选时，无任何文字显示，Hook 函数直接返回，零性能开销。
3. [ ] **触发时机精准性**：阿尔茜命中触发流血时，屏幕在命中瞬间弹出：
   `Arcee -> Bleed | Dice: 32% Roll: 18% (PASS) | OnCrit`。
4. [ ] **手感与安全红线**：根据 `AGENTS.md`，本次改动不修改 `tools/nativehook/combat_truth_backup.c`，不弱化连招状态机，保证战斗手感基线全绿通过。
