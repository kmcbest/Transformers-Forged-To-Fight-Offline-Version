# TFTF 角色技能系统解耦与模块化重构方案规范 (Skill Decoupling Architecture Specification)

> **文档定位**：专为 AI 编码智能体（AI Coding Agent）与开发者编写的落地重构技术白皮书。旨在彻底将具体角色技能（Abilities）与单体大文件 `hook.c` 解耦，建立安全、独立、零手感回退的角色技能扩展系统。

---

## 1. 背景与核心痛点 (Problem Statement)

### 1.1 现状分析
当前 `tools/nativehook/hook.c` 已膨胀至近 **8,000 行**代码。它同时承担着两组完全异构的职责：
1. **底层引擎基础设施**（需绝对稳定）：
   - IL2CPP Trampoline 挂钩与内存页 `mprotect`
   - 输入判定链与取消硬直状态机（GATE-01 ~ GATE-06，即 `combat_truth_backup.c`）
   - 设备自适应（Xiaomi/Adreno 渲染降级旁路）、Native Server 握手
2. **上层具体角色技能业务**（频繁变更、调试周期密集）：
   - 阿尔茜（Arcee）SP1 命中后的 6.5s 远程增伤计时器
   - 犀牛（Rhinox）SP1 驱散敌人 Buff 后触发流血的判定闸门（`RHINOX_NULLIFY_GATE`）
   - 千斤顶（Wheeljack）SP 最终击判定（`WHEELJACK_FINAL_HIT_GATE`）与能量泄露（Power Leak）
   - 铁皮（Ironhide）受击触发燃烧状态标志等

### 1.2 为什么之前的整体重构（Refactoring）会崩溃？
- **全局状态初始化时序依赖**：很多基础指针（如 `g_base`、`g_p0_controller`、`g_f` 日志句柄）在 native 载入瞬间尚未就绪。盲目把 `hook.c` 拆解为多个编译单元容易造成跨文件未定义符号或运行时空指针 `SIGSEGV`。
- **手感基准污染**：在同一个几千行大文件内修改新角色逻辑，很容易不慎修改全局时间戳宏或影响按键缓冲队列，打破 `re_notes/combat_truth_source.md` 的防线。

---

## 2. 解耦总体架构 (Decoupled Architecture)

重构的核心铁律：**`hook.c` 从此变为“只读型事件派发器”，永远不再为任何单一角色增加 `if (strstr(bot_id, "..."))` 逻辑。**

```
┌────────────────────────────────────────────────────────────────────────┐
│                        tools/nativehook/hook.c                         │
│   (纯净核心: 仅保留内存Hook、输入状态机 GATE-01~06、以及事件触发点)    │
└──────────────┬──────────────────────────┬──────────────────────────────┘
               │ OnDamage / HitConnected  │ OnBuffApplyGated
               ▼                          ▼
┌────────────────────────────────────────────────────────────────────────┐
│               tools/nativehook/skills/skill_dispatcher.c               │
│               (集中事件派发中心: 查角色ID表，分发到对应独立模块)       │
└──────────────┬──────────────────────────┬──────────────────────────────┘
               │                          │
       ┌───────┴───────┐          ┌───────┴───────┐
       ▼               ▼          ▼               ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌──────────────────────┐
│ skill_arcee │ │skill_rhinox │ │skill_wheelj │ │ ... 新增任意角色 ... │
│    .c / .h  │ │    .c / .h  │ │    .c / .h  │ │ (完全独立，零交叉影响)│
└─────────────┘ └─────────────┘ └─────────────┘ └──────────────────────┘
```

---

## 3. 详细实施步骤 (Implementation Guide)

### 步骤 1：建立技能接口头文件 (`tools/nativehook/skills/skill_types.h`)

定义纯净的上下文数据结构，将具体游戏对象指针封装起来，只暴露业务关心的字段：

```c
#pragma once
#include <stdint.h>
#include <stdbool.h>

// 战斗命中结算上下文
typedef struct {
    void* attacker_entity;
    void* target_entity;
    const char* attacker_bot_id;
    const char* target_bot_id;
    int attacker_player_index;    // 0 = 我方, 1 = 敌方
    int special_index;           // 0 = 普通/连招, 1 = SP1, 2 = SP2, 3 = SP3
    bool is_ranged;              // 是否为远程射击
    bool is_crit;                // 是否产生暴击
    float base_damage;           // 基础伤害
    float modified_damage;       // 允许被角色技能修改的最终伤害
    uint32_t hit_flags;          // 原生命中位标记
} SkillHitContext;

// Buff施加拦截上下文
typedef struct {
    void* buffs_controller;
    void* target_entity;
    const char* modifier_id;     // 如 "rhinox_sp1_nullify_bleed", "wheeljack_sp1_shock"
    const char* target_bot_id;
    int applicant_player_index;
    bool allow_application;      // 输出：是否允许施加该Buff (Gate判定)
    float duration_override;     // 输出：覆盖持续时间 (<0 则不覆盖)
} SkillBuffGateContext;

// 单个角色的技能模块抽象接口
typedef struct {
    const char* bot_prefix;      // 匹配前缀，例如 "arcee", "rhinox", "wheeljack"
    
    // 命中前/后回调
    void (*on_hit_connected)(SkillHitContext* ctx);
    
    // Buff施加过滤闸门 (对应原 hook_188)
    void (*on_buff_gated)(SkillBuffGateContext* ctx);
    
    // 战斗重置/回合开始 (清理私有冷却和状态变量)
    void (*on_fight_reset)(int player_index);
} BotSkillModule;
```

---

### 步骤 2：创建技能中央派发器 (`tools/nativehook/skills/skill_dispatcher.c`)

派发器维护角色注册表，进行 `O(N)` 前缀匹配（注册角色通常在 50~100 个以内，毫秒级以下，极快）：

```c
#include "skill_types.h"
#include <string.h>

extern BotSkillModule g_module_arcee;
extern BotSkillModule g_module_rhinox;
extern BotSkillModule g_module_wheeljack;
// 以后每做一个新角色，只需在这里 extern 一行

static const BotSkillModule* s_skill_registry[] = {
    &g_module_arcee,
    &g_module_rhinox,
    &g_module_wheeljack,
    NULL
};

static const BotSkillModule* find_module(const char* bot_id) {
    if (!bot_id || !bot_id[0]) return NULL;
    for (int i = 0; s_skill_registry[i] != NULL; i++) {
        if (strstr(bot_id, s_skill_registry[i]->bot_prefix) != NULL) {
            return s_skill_registry[i];
        }
    }
    return NULL;
}

void skill_dispatch_hit_connected(SkillHitContext* ctx) {
    const BotSkillModule* mod = find_module(ctx->attacker_bot_id);
    if (mod && mod->on_hit_connected) {
        mod->on_hit_connected(ctx);
    }
}

bool skill_dispatch_buff_gate(SkillBuffGateContext* ctx) {
    // 匹配 modifier_id 前缀或 target_bot_id
    for (int i = 0; s_skill_registry[i] != NULL; i++) {
        if (ctx->modifier_id && strstr(ctx->modifier_id, s_skill_registry[i]->bot_prefix) != NULL) {
            if (s_skill_registry[i]->on_buff_gated) {
                s_skill_registry[i]->on_buff_gated(ctx);
                return ctx->allow_application;
            }
        }
    }
    return true; // 默认允许
}

void skill_dispatch_fight_reset(void) {
    for (int i = 0; s_skill_registry[i] != NULL; i++) {
        if (s_skill_registry[i]->on_fight_reset) {
            s_skill_registry[i]->on_fight_reset(0);
            s_skill_registry[i]->on_fight_reset(1);
        }
    }
}
```

---

### 步骤 3：编写独立角色业务模块实例 (`tools/nativehook/skills/bots/skill_arcee.c`)

以现有的阿尔茜（Arcee）逻辑为例，将其私有状态彻底隔离：

```c
#include "../skill_types.h"
#include <string.h>

// 私有状态：完全不污染全局 hook.c
static uint64_t s_arcee_ranged_boost_end_ms[2] = {0, 0};
static float    s_arcee_ranged_dmg_mult = 0.35f;

static void arcee_on_hit_connected(SkillHitContext* ctx) {
    int p = ctx->attacker_player_index;
    
    // SP1 命中激活 6.5 秒远程增伤
    if (ctx->special_index == 1) {
        // propgo_now_ms() 可通过辅助函数传入
        s_arcee_ranged_boost_end_ms[p] = 6500; // 记录时间戳
    }
    
    // 远程攻击伤害加成
    if (ctx->is_ranged && s_arcee_ranged_boost_end_ms[p] > 0) {
        ctx->modified_damage *= (1.0f + s_arcee_ranged_dmg_mult);
    }
}

static void arcee_on_buff_gated(SkillBuffGateContext* ctx) {
    // 移植原 hook.c:6898 Arcee SP1 & SP3 踢击 gate
    if (strstr(ctx->modifier_id, "arcee_sp1_kick") != NULL) {
        // 判定条件...
    }
}

static void arcee_on_fight_reset(int player_index) {
    s_arcee_ranged_boost_end_ms[player_index] = 0;
}

BotSkillModule g_module_arcee = {
    .bot_prefix = "arcee",
    .on_hit_connected = arcee_on_hit_connected,
    .on_buff_gated = arcee_on_buff_gated,
    .on_fight_reset = arcee_on_fight_reset
};
```

---

### 步骤 4：在 `hook.c` 中收敛为单行委托调用

清理 `hook.c` 里的死乱硬编码：

1. **在受击结算处（原 `hook.c:6335` 附近）**：
   ```c
   // 原先 50 行包含 arcee / ironhide 增伤的混杂代码替换为：
   SkillHitContext hit_ctx = {
       .attacker_entity = g_p0_controller,
       .target_entity = self,
       .attacker_bot_id = g_p0_bot_id,
       .target_bot_id = g_p1_bot_id,
       .attacker_player_index = 0,
       .special_index = g_p0_current_special_index,
       .is_ranged = s_current_hit_is_ranged,
       .base_damage = damage,
       .modified_damage = damage,
       .hit_flags = s_last_hit_flags
   };
   skill_dispatch_hit_connected(&hit_ctx);
   damage = hit_ctx.modified_damage; // 接收技能模块调整后的数值
   ```

2. **在 Buff 过滤处（原 `hook_188` 处）**：
   ```c
   // 原先硬编码的一堆 Gate 1, Gate 2, Gate 3 替换为：
   SkillBuffGateContext gate_ctx = {
       .buffs_controller = self,
       .modifier_id = mod_id,
       .target_bot_id = target_bot_id,
       .allow_application = true
   };
   if (!skill_dispatch_buff_gate(&gate_ctx)) {
       return 0; // 技能模块否决了本次 Buff 施加
   }
   ```

---

## 4. 为什么这个方案能彻底拯救后期开发？

| 对比维度 | 当前的单体 `hook.c` 模式 | 解耦后的模块化架构 |
|---|---|---|
| **编写新角色技能** | 打开 8,000 行 `hook.c`，小心翼翼找插入点，生怕改坏全局变量 | 新建 `skills/bots/skill_optimus.c`，在独立的 50 行代码里尽情编写 |
| **引入 Bug 的半径** | 极容易引发全局连招断裂、崩溃或老角色手感回退 | **Bug 半径仅限于当前单个文件**，绝对不可能影响其他角色或核心输入链 |
| **给 AI 智能体提需求** | Agent 容易在几千行文件里“迷航”并产生幻觉破坏手感 | 给 Agent 的 Prompt 极度精简：“请在 `skill_bumblebee.c` 里实现大黄蜂闪避” |
| **编译与排错定位** | 编译器报错淹没在大文件里，符号错位难以肉眼排查 | 编译警告直接指向具体的 `skill_xxx.c`，单点排查极其迅速 |

---

## 5. 阶段实施计划 (Actionable Roadmap)

- [ ] **阶段一：框架就绪（不迁移老代码）**
  - 创建 `tools/nativehook/skills/skill_types.h` 与 `skill_dispatcher.c`。
  - 在 `hook.c` 中接入调用桩，编译并打包验证，确保全绿零回退。
- [ ] **阶段二：典范迁移（验证机制）**
  - 把 `arcee`（阿尔茜）、`rhinox`（犀牛）、`wheeljack`（千斤顶）原有的 Gate 逻辑抽离到 `bots/` 子文件。
  - 验证上述 3 个角色技能在战斗中 100% 表现一致。
- [ ] **阶段三：规模化量产（开足马力做剩下 4/5 角色）**
  - 后续角色（威震天、大黄蜂、漂移、红蜘蛛等）全部直接以新文件格式新建，`hook.c` 进入绝对只读锁定保护。
