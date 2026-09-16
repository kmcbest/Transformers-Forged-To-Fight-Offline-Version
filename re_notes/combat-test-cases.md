# 战斗连击规则与质量门禁测试用例 (Combat Quality Gates)

本文档基于 combo-rules.md 制定，作为战斗手感、连击状态机及 tools/nativehook/hook.c 的核心质量门禁。任何关于输入、连击或状态机代码的修改，均必须严格通过以下 7 个质量门禁场景。

---

## 门禁用例列表

### TC-GATE-01: 终结技重置门禁 (Combo Ender Reset)
- **前置条件**：战斗处于近战攻击距离。
- **测试动作**：
  1. 执行标准五连击（如 M1 -> L1 -> L2 -> L3 -> M2）或者以四连击轻击终结（L1 -> L2 -> L3 -> L4）。
  2. 观察角色完成击飞/击退收招。
  3. **不后撤**，直接在原地点击屏幕右侧 Tap（轻击）。
- **预期结果**：
  - 角色必须从 **L1** 重新起手发起新一套连击。
  - 严禁直接打出 L4 或旧索引动作。
- **代码质量断言 (Invariant)**：
  \COMBAT_ASSERT(current_light_index == 0, "GATE-01", "After combo ender (M2/L4), next attack must start from L1!");\
- **实测记录（2026-09-16 真机）**：
  - 修复前：4 下轻击里的**第 4 下会被 hook 提前清链而变成 L1**，L4 永远打不出来（所有会话里 `l` 的上限恒为 3）。根因是 arm 判定写在"逐帧重发"上——`action==1 && pre_l>=3` 对同一记 L3 攻击的每一次重发都成立，标志在 L3 飞行帧里就被消费掉了。
  - 修复后：`post_l < pre_l` 才是有效判据（原生在 L4 打出时把 `l` 从 **3 直接清成 0**，所以 `post_l >= 4` 永远不成立）。实测 `点 4 下` → **L1, L2, L3, L4**（`l 0→1→2→3→0` + `combo ender CONFIRMED`），第 5 下回到 **L1**；`M1,L1,L2,L3,M2` 之后点 1 下同样回到 **L1**。

---

### TC-GATE-02: 重击强制重置门禁 (Heavy Attack Reset)
- **前置条件**：战斗处于近战攻击距离。
- **测试动作**：
  1. 点击两次 Tap，打出 L1 -> L2。
  2. 紧接着长按右侧屏幕，释放重击（Heavy Attack）。
  3. 重击命中对手并完成收招后，再次点击右侧 Tap。
- **预期结果**：
  - 角色必须从 **L1** 重新起手。
  - 严禁从 L3 或未重置的索引续接。
- **代码质量断言 (Invariant)**：
  \COMBAT_ASSERT(current_light_index == 0, "GATE-02", "After heavy attack, next attack must start from L1!");\
- **实测记录（2026-09-16 真机）**：
  - 真重击派发的动作码是 **`0x100`（256）**（一次按压 5~7 次重发，且从不改动 `l/m/r`），**不是 `8`**；`8` 实测是后划/闪避（同一调用内会进入 `PlayerDodgeState`）。
  - 修复前 `hook_154` 只认 `action == 8`，所以真重击**既不清链也不 arm**：`L1,L2,L3,M1 → 重击 → 前滑` 接成了 **M2**（已复现并留证）。
  - 修复后实测：`PLAYER_ACTION heavy/ender (action=256)` ×5 + 计数 `l 3→0、m 1→0` + 变形与命中判定，随后的前滑必然从 **M1** 起手（此时 `m` 已为 0，M2 不可能出现）。

---

### TC-GATE-03: 受击打断强制重置门禁 (Hit Reaction Reset)
- **前置条件**：双方角色处于近战交锋。
- **测试动作**：
  1. 玩家打出 L1 -> L2 连击中途。
  2. 敌方出手击中玩家，玩家受到伤害并进入受击硬直（Hit Stun / Hit React）。
  3. 玩家受击硬直解除后，立即点击右侧 Tap 反击。
- **预期结果**：
  - 连击序列已被敌方攻击完全打断。
  - 玩家反击的第一招必须是 **L1**（或 Swipe 出 **M1**），严禁续接被打断前的 L3。
- **代码质量断言 (Invariant)**：
  \COMBAT_ASSERT(current_light_index == 0 && current_medium_index == 0, "GATE-03", "After hit reaction, combo chain must be completely reset to 0!");\
- **实测状态（2026-09-16）**：**尚未真机验证**。实现走的是 `hook_145`（Simulation.FixedUpdate）里轮询 P0 血量：一旦下降 >0.01 就清双索引。注意它"过宽"——格挡吃到的削减伤害同样会清链，届时要注意手感反馈。本轮所有测试都把敌人冻结了（`freeze_enemy_ai` 标记文件），因此这条路径一次都没跑到。

---

### TC-GATE-04: 起手合法性门禁 (Initiator Legitimacy)
- **前置条件**：角色处于待机、移动结束、后撤闪避或翻滚起身后的静止状态。
- **测试动作**：
  1. 点击右侧 Tap。
  2. 或者向前 Swipe 右划。
- **预期结果**：
  - 任何新一轮连击的起手，轻攻击只允许为 **L1**，中攻击只允许为 **M1**。
  - 严禁任何形式的 L2/L3/L4 或 M2 越级起手。
- **代码质量断言 (Invariant)**：
  \COMBAT_ASSERT((is_tap && light_index == 0) || (is_swipe && medium_index == 0), "GATE-04", "New combo initiation must start with L1 or M1!");\
- **实现（2026-09-16）**：`hook.c` 新增 **空等窗口** `COMBO_IDLE_RESET_MS = 900`。任何攻击动作（`action` 1/4/32）都会刷新 `g_p0_last_attack_ms`；`hook_145` 每帧检查，超过 900 ms 没有任何攻击 → 清链并打印 `COMBAT_IDLE: ... ms without an attack (>= 900 ms window)`。之所以要自己实现：原生的连招窗口**不可观测**——实测"点一下 → 等 1 秒 → 点一下 → 等 1 秒 → 点一下"出的是 **L1, L2, L3**（原地空等根本不结束连击）。
- **实测记录（2026-09-16 真机）**：修复后同一序列的日志里出现 4 次 `COMBAT_IDLE`（921 / 940 / 908 / 921 ms），每次清链后紧跟的点按都是 **L1** ✓。

---

### TC-GATE-05: 防无限左右连门禁 (Infinite Loop Prevention)
- **前置条件**：双方处于近战或中近距离。
- **测试动作**：
  1. 极快速度交替点击左侧屏幕（防御）与右侧屏幕（轻击），如“左-右-左-右-左-右”，每次点左侧时间 < 200ms。
- **预期结果**：
  - 点按左侧由于未达到 200ms 防守蓄势阈值，不重置连击槽。
  - 玩家打出的动作按正常的轻击序列推进（L1 -> L2 -> L3 -> L4），无法实现无限重复刷出 L1 或远程第 1 枪。
- **代码质量断言 (Invariant)**：
  \COMBAT_ASSERT(tap_block_time_ms < 200 => chain_not_reset, "GATE-05", "Short block tap (<200ms) must NOT reset combo chain!");\
- **实现修复（2026-09-16）**：格挡入口的 hook 地址被 `0ae8498` 从 `0x1173848` 换成了 `0x0D32A00`，后者**在任何会话里都从未触发**（实测一整场 `BLOCK_ENTER = 0`），于是"按住防御 ≥200ms 清链"彻底失效（实测 `TAP, 防御, TAP, 防御` 出的是 **L1, L2**）。现在**两个地址同时挂**（槽位 160 `0x0D32A00` + 槽位 171 `0x1173848`），并在 `hook_171` 里加了缓存控制器兜底。
- **实测记录（2026-09-16 真机）**：修复后 `BLOCK_ENTER (0x1173848)` 正常触发；**长按**的三次实测 `BLOCK_HELD: 231 / 257 / 226 ms >= 200ms` 每次都清链，紧随的点按都是 **L1** ✓；**快点**（<200ms）只出现 `BLOCK_ENTER`、**无** `BLOCK_HELD`，连击照常推进（`l 1→2→3`，直到 L4 终结）✓ —— 正是本条门禁要的"长按该清、快点不清"。

---

### TC-GATE-06: 远程三枪封顶与取消前冲门禁 (Ranged Cap & Cancel)
- **前置条件**：拉开距离进入远程有效射程。
- **测试动作**：
  1. 连续点击 Tap 射击。
  2. 验证射击最多连续 3 枪，第 3 枪后出现强制收招后摇，无法无限点射。
  3. 在打出第 1 枪或第 2 枪时，立即向前右划 Swipe。
- **预期结果**：
  - 前冲成功取消射击后摇，角色快速突进并打出近战起始中击 **M1**。
- **代码质量断言 (Invariant)**：
  \COMBAT_ASSERT(ranged_index <= 3, "GATE-06", "Ranged shooting capped at 3 rounds!");\
  \COMBAT_ASSERT(gun_cancel_dash => medium_index == 0, "GATE-06", "Gun cancel into forward dash must initiate M1!");\
- **实测状态（2026-09-16）**：**hook 侧仍未实现**（`+0x1c8` 远程计数只被写 0、从不读取，也没有 `ranged_index <= 3` 断言）。但实测到原生行为是有效的：远距离连点时 `r` 递增 `0→1→2`，第 3 枪后**原生自己清零**（无清链日志），即三枪封顶由客户端保证。"开枪取消前冲出 M1"这一步尚未专门验证。

---

### TC-GATE-07: 重击后中击起手门禁 (Heavy → M1 Re-initiation)
- **前置条件**：近身，并先打出一段同时含轻击与中击的连击，例：`L1 -> L2 -> L3 -> M1`。
- **测试动作**：
  1. 在上述连击之后，长按右侧打出**重击**（真机实测其动作码为 `0x100` / `256`）。
  2. 重击收招完毕，立即**向前滑**（Swipe Forward）。
- **预期结果**：
  - 重击终结整段连击，**中击计数必须归零**。
  - 因此接下来的前滑必须从 **M1**（前冲中攻击）起手，**严禁**接续重击之前的中击进度而打出 **M2**。
- **代码质量断言 (Invariant)**：
  \COMBAT_ASSERT(medium_index == 0, "GATE-07", "After heavy attack, the next swipe must initiate M1!");\
- **实测记录（2026-09-16 真机）**：修复前，`L1 -> L2 -> L3 -> M1` → 重击 → 前滑 会打出 **M2**；根因是真重击派发的是 `action == 0x100`，而 `hook_154` 当时只识别 `action == 8`，导致重击既没有清链也没有 arm `after_heavy`，中击计数器仍停留在上一个 M1 的进度上。
- **判定标准**：前滑对应的 `ACTION post` 行中 `m` 必须由 **0 → 1**（= M1），而不是 `1 -> 2`（= M2）；且 `logcat` 中不得出现 `[COMBAT_RULE_VIOLATION][GATE-07]`。
- **修复后实测（2026-09-16 真机）**：`action=256` 被正确识别（一场内 5 次 `PLAYER_ACTION heavy/ender (action=256)`），重击当即把两个计数同时清零（`l 3→0`、`m 1→0`）并打出变形与命中判定，随后前滑从 **M1** 起手（起手时 `m=0`，M2 在数值上不可能出现）✓。

---

## 门禁执行标准
1. **Logcat 监控**：真机测试期间，运行 \db logcat | Select-String "COMBAT_RULE_VIOLATION"\。
2. **零容忍**：凡出现任何一次 \[COMBAT_RULE_VIOLATION]\，该版本视为未达到发布质量，立即驳回修改。
3. **判定用的日志锚点（2026-09-16 起由 `hook.c` 提供，真机 `logcat` 或 `/sdcard/Android/data/com.kabam.bigrobot/files/tftf_*.log`）**：

   | 日志串 | 含义 |
   | :--- | :--- |
   | `COMBAT_START: Simulation.RegisterComponents -> ...` | 每场战斗开始、连击状态清零；用它把一份日志按"场"切开 |
   | `ACTION pre act=%d l=%u m=%u r=%u` / `ACTION post act=%d l=%u m=%u r=%u ended=%d heavy=%d` | 每次 `PlayerController.Action` 调用**前后**的轻/中/远程计数与两个 latch。**攻击会被逐帧重发约 10 次**，所以"出了几招"要看**计数器变化**，不是看行数 |
   | `COMBAT_GATE: combo ender CONFIRMED (action=.., pre l=.. m=.. -> post l=.. m=..)` | 终结被确认（计数达到终结值，或原生自己清链 `post < pre`）。**原生在 L4 打出时把 `l` 由 3 直接清 0**，所以 `post_l >= 4` 永不成立 |
   | `PLAYER_ACTION heavy/ender (action=%d) on P0: ...` | 重击/后划被识别为终结（真重击 = `0x100`，后划 = `8`） |
   | `BLOCK_ENTER (0x1173848)` / `BLOCK_HELD: ... >= 200ms` | 格挡进入 与 "按住 ≥200ms 清链"（`0x0D32A00` 从不触发，`0x1173848` 才是真入口） |
   | `DODGE_ENTER (0x117E4AC) ...` | 后撤进入（`0x0D34E6C` 的 `a0+0x18` 解析为 0，只有它的兜底在跑） |
   | `COMBAT_IDLE: N ms without an attack (>= 900 ms window)` | 空等窗口清链（GATE-04） |
   | `[COMBAT_RULE_VIOLATION][GATE-0x] ...` | 断言失败。注意宏**只打日志不中断**，且断言写在自己触发的分支内部，因此"没有这行"**不等于**门禁通过 |

4. **实测动作码对照（2026-09-16 真机实测，请以日志为准，不要照抄旧文档）**：

   | 动作 | 动作码 |
   | :--- | :--- |
   | 轻击 / 通用攻击请求（近战或远程由距离决定） | `1` |
   | 后划 / 闪避输入（触摸、拖拽事件也会产生） | `2` |
   | 前冲 / 前滑的冲刺边沿 | `4` |
   | 后撤（进入 `PlayerDodgeState`） | `8` |
   | 中击攻击状态（逐帧重发；M1 时 `m 0→1`，M2 时原生把 `m` 清 0） | `32` |
   | **重击** | **`0x100` (256)** |

5. **测试辅助开关（都在 `hook.c` 内，且"无标记文件 = 行为完全不变"）**：
   - **冻结敌方 AI**：`adb shell touch /sdcard/Android/media/com.kabam.bigrobot/freeze_enemy_ai`（`rm -f` 即恢复）。用于安静地测连击，日志出现 `ENEMY_AI_FROZEN` 即已生效。
   - **空等窗口阈值**：`hook.c` 里的 `COMBO_IDLE_RESET_MS`（默认 900 ms）可直接调。
   - **重打包后务必确认设备跑的是新包**：比对设备 `/data/app/.../base.apk` 与你本地构建产物的字节数是否一致；`.so` 是否含新串可用 `Select-String` 在本地 APK 里核对 `lib/arm64-v8a/libdothook.so`。

