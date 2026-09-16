# 战斗连击规则与质量门禁测试用例 (Combat Quality Gates)

本文档基于 combo-rules.md 制定，作为战斗手感、连击状态机及 tools/nativehook/hook.c 的核心质量门禁。任何关于输入、连击或状态机代码的修改，均必须严格通过以下 6 个质量门禁场景。

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

---

## 门禁执行标准
1. **Logcat 监控**：真机测试期间，运行 \db logcat | Select-String "COMBAT_RULE_VIOLATION"\。
2. **零容忍**：凡出现任何一次 \[COMBAT_RULE_VIOLATION]\，该版本视为未达到发布质量，立即驳回修改。
