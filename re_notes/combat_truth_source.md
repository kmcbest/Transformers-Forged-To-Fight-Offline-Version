# TFTF 战斗手感与连招状态机真理源 (Combat Truth Source)

> **重要声明（Golden Reference / 真理源）**  
> 本文档是整个离线版项目战斗手感、触控派发、攻击链推进与中断状态机的**唯一真理源（Single Source of Truth）**。  
> 无论是新增角色能力（Ability）、修改钩子还是重构代码，**绝对禁止**擅自改动或弱化本真理源中定义的任何一条逻辑与时序。  
> 任何后续针对连招或战斗手感的优化，必须在通过全部门禁用例验证后，同步更新本真理源文档及对应代码备份。

---

## 一、 TFTF 原生动作枚举对照表 (Action Enum)

源自 `PlayerController.Action` 反编译规范，所有触控手势派发的动作码如下：

| 枚举常量 | 十进制 | 十六进制 | 对应操作 / 状态 |
| :--- | :---: | :---: | :--- |
| `None` | 0 | `0x0` | 无动作 / 动作未生效 |
| `Attack` | 1 | `0x1` | 屏幕右侧点按 (Tap / 轻击 L1~L4) |
| `Block` | 2 | `0x2` | 屏幕左侧长按 (格挡防御) |
| `ReleaseBlock` | 4 | `0x4` | 松开屏幕左侧 (释放格挡) |
| `Dodge` | 8 | `0x8` | 屏幕左向后划 (后退滑步 / 后闪) |
| `Dash` | 32 | `0x20` | 屏幕右向前划 (前冲冲刺 / 中击 M1~M2) |
| `SidestepLeft` | 64 | `0x40` | 屏幕向上滑动 (向上侧闪) |
| `SidestepRight` | 128 | `0x80` | 屏幕向下滑动 (向下侧闪) |
| `Sidestep` | 192 | `0xC0` | 侧闪掩码 (`SidestepLeft \| SidestepRight`) |
| `HeavyAttack` | 256 | `0x100` | 屏幕右侧长按蓄力 (重击) |
| `SpecialAttack` | 512 | `0x200` | 能量槽 / 必杀技按键点击 (SP 特技) |

> [!WARNING]
> **历史事故教训（牢记）**：
> `0x80`（128）在原生引擎中是 `SidestepRight`（向下滑动侧闪），**绝不是所谓的“轻击松手抬起”**！真正的松开格挡动作码是 `4`（`ReleaseBlock`）。严禁将 `0x80` 误作轻击释放！

---

## 二、 核心状态变量与时序规范

定义于 `tools/nativehook/hook.c`：

```c
static void* g_p0_controller = NULL;                  // 本地玩家 (P0) PlayerController 指针
static volatile uint64_t g_p0_block_enter_ms = 0;     // 格挡按下时间戳（ms）
static volatile int g_p0_block_reset_done = 0;        // 格挡长按（>=200ms）清链完成标记
static volatile int g_p0_after_heavy = 0;             // 重击后等待首击重置连击链的 Latch
static volatile int g_p0_combo_ended = 0;             // 连招打完（Ender 触发）等待下次首击清链的 Latch
static volatile uint64_t g_p0_last_attack_ms = 0;     // 上一次有效攻击动作打出的时间戳（ms）
#define COMBO_IDLE_RESET_MS 900                       // 连击空等超时窗口（900ms，TC-GATE-04）
```

---

## 三、 核心战斗规则与代码实现

### 1. 攻击链重置函数 `reset_player_attack_chain`
用于在合法中断点将本地角色的轻、中、远程计数器归零：
```c
static void reset_player_attack_chain(void* pc) {
    if (!obj_ok(pc)) return;
    int32_t p_idx = *(int32_t*)((uintptr_t)pc + 0xF4);
    if (p_idx != 0) return; // 严格限制仅对本地玩家 P0 生效
    g_p0_controller = pc;
    g_p0_last_attack_ms = 0;                 // 空等计时器在下一次有效攻击时重新计算
    *(uint32_t*)((uintptr_t)pc + 0x1c0) = 0; // _lightAttackIndex = 0 (下次为 L1)
    *(uint32_t*)((uintptr_t)pc + 0x1c4) = 0; // _mediumAttackIndex = 0 (下次为 M1)
    *(uint32_t*)((uintptr_t)pc + 0x1c8) = 0; // _rangedAttackIndex = 0 (下次为远程第1发)
    // 【关键铁律】：严禁清空 _lastHitResult.Flags！
    // 否则会破坏 Arcee 等多段 M2 角色根据首段命中状态触发第二段判定的原生机制！
    flog("RESET_ATTACK_CHAIN on p0 pc=%p (caller=%p)", pc, __builtin_return_address(0));
}
```

### 2. 闪避、侧闪与受击状态原生切入 (Dodge, Sidestep & Hit React)
彻底告别过去将 `0x117E4AC`（实际为 `PlayerDashState.OnEnter` 前冲）误当 Dodge 的历史错误。原厂四路状态机切入点严格对应原生 RVA：
- **后退闪避 (`hook_172 @ 0x0117F614`)**：`PlayerDodgeState.OnEnter`，向后滑步立即清链；
- **侧滑翻滚 (`hook_160 @ 0x00E3349C`)**：`PlayerSidestepState.OnEnter`，向上/向下侧闪立即清链；
- **真实受击 (`hook_165 @ 0x0117FEC4`)**：`PlayerHitReactState.OnEnter`，受到非格挡实体伤害进入硬直时立即清链（彻底移除过去在 FixedUpdate 里每帧轮询血量下降的粗暴 hack，避免格挡削减伤害误清链）；
- **前冲冲刺 (`0x117E4AC`)**：保持原生 `PlayerDashState` 完整状态机，**严禁挂钩清链**，确保前冲突进、滑步取消及 M1 正常衔接！

```c
// 侧闪入口 (0x00E3349C) 与真实闪避入口 (0x0117F614)
g_p0_block_enter_ms = 0;
g_p0_block_reset_done = 0;
g_p0_combo_ended = 0;
g_p0_after_heavy = 0;
reset_player_attack_chain(pc);
```

### 3. 重击状态与后置衔接 (Heavy Attack & GATE-02 / GATE-07)
长按重击（`action == 0x100`）起手时，强制重置双索引并立起 `g_p0_after_heavy = 1`：
```c
if (action == 0x100) {
    g_p0_block_enter_ms = 0;
    g_p0_block_reset_done = 0;
    g_p0_after_heavy = 1;
    flog("PLAYER_ACTION heavy (action=0x100) on P0: reset attack chain and arm after_heavy flag");
    reset_player_attack_chain(self);
    did_reset = 1;
    COMBAT_ASSERT(*(uint32_t*)((uintptr_t)self + 0x1c4) == 0, "GATE-07",
                  "Medium index must be 0 after heavy attack so the next swipe is M1, got %u",
                  *(uint32_t*)((uintptr_t)self + 0x1c4));
}
```
* 当重击击飞对手后，玩家按下 Tap 或前划（`action == 1 || action == 32`）时，消费 `g_p0_after_heavy`，首击严格归零：
  - 点击必打出 **L1**（TC-GATE-02）
  - 前划必打出 **前冲 M1**（TC-GATE-07，严禁出后段 M2）
  - （注：修正了将 `action == 4` 误作前冲的历史笔误，动作码 4 严格为松开格挡 `ReleaseBlock`）

### 4. 必杀技三路清链保障 (Special Attack Enter & Exit)
彻底解决 SP 特技施放后右滑误出 M2 的问题：
- **入口层 (`hook_153`)**：`PlayerController.SpecialAttack` 调用时，执行 `reset_player_attack_chain(self)`；
- **输入层 (`hook_154 action 0x200`)**：玩家点击必杀技按键瞬间，执行 `reset_player_attack_chain(self)`；
- **退出层 (`hook_155`)**：`PlayerSpecialAttackState.OnExit` 状态退出时，通过 `g_p0_controller` 兜底强行清链。

### 5. 原生 TuningGameplay 调优与 900ms 超时保护机制 (TC-GATE-04)
- **Server 数据配置层（根本解）**：
  在 `Server/gamedata.py` 的 `bcg-combat` 中下发 `attackChainResetTime = 0.8` 以及完整战斗调优参数，激活客户端原厂 `TuningGameplay` 内置的连招空等重置机制。
- **POST 阶段更新时间戳**：
  必须在原生引擎真正接受并执行了攻击动作时（`int action_ok = ((uintptr_t)r != 0);` 且 `action == 1 || action == 32 || action == 0x100`），才记录 `g_p0_last_attack_ms = propgo_now_ms()`。
  - **关键保护**：当角色处于受创硬直或倒地期间，玩家盲目狂点屏幕右侧 Tap 时，底层由于 `CanAttack == false` 会返回 `action_ok == 0`，**绝不刷新时间戳**！
- **FixedUpdate 轮询兜底 (`hook_145`)**：
  当角色倒地、受击无法攻击、或者站立停顿超过 `COMBO_IDLE_RESET_MS`（900ms）后，`hook_145` 兜底执行 `reset_player_attack_chain(g_p0_controller)`。

### 6. 格挡长短按区分机制 (TC-GATE-05)
- **短按格挡（< 200ms）**：松开或接反击（`action == 4 || action == 1 || action == 32 || action == 0x100`）时立即 abort block timer，连招进度完整保留；
- **长按格挡（>= 200ms）**：进入稳定防御架势后，`hook_145` 触发重置，连招清链。

---

## 四、 黄金源码备份文件

本真理源对应的独立 C 源码快照位于：
[`tools/nativehook/combat_truth_backup.c`](file:///e:/Agent/TFTF/tools/nativehook/combat_truth_backup.c)

未来若发生意外修改导致战斗手感异常，只需对比上述文件即可在 1 分钟内无损恢复。
