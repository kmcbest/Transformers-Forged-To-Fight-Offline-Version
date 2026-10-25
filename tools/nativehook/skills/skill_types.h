#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// ---------------------------------------------------------------------------
// 1. 上下文结构体定义 (Context Structures)
// ---------------------------------------------------------------------------

// 命中结算上下文 (hook_177 / OnDamage)
typedef struct {
    void* attacker_entity;
    void* target_entity;
    const char* attacker_bot_id;
    const char* target_bot_id;
    int attacker_player_index;    // 0 = P0 (我方), 1 = P1 (敌方)
    int target_player_index;      // 0 = P0, 1 = P1
    int special_index;           // 0 = 普通/连招, 1 = SP1, 2 = SP2, 3 = SP3
    int hit_index;               // 当前段数 (0-indexed)
    bool is_last_hit;            // 是否为当前动作的收招最终击
    bool is_ranged;              // 是否为远程射击
    bool is_heavy;               // 是否为重击 (Heavy Attack)
    bool is_crit;                // 是否暴击
    bool is_blocked;             // 是否被格挡
    float base_damage;           // 原始计算伤害
    float modified_damage;       // 技能修改后的伤害输出
    uint32_t hit_flags;          // 原生命中标志
    int action_type;             // 动作类别 (1=L, 2=M, 4=Heavy, 8=Ranged, 16=SP1, 32=SP2, 64=SP3)
} SkillHitContext;

// Buff 施加过滤闸门上下文 (hook_188 pre-apply gate)
typedef struct {
    void* buffs_controller;
    void* applicant;
    void* stat_modifier;
    const char* modifier_id;     // 技能 Modifier 标识字符串
    const char* target_bot_id;
    int target_player_index;      // 0 = P0, 1 = P1
    int attacker_player_index;    // 0 = P0, 1 = P1
    int current_special_index;   // 正在释放的 SP (0, 1, 2, 3)
    int last_hit_index;          // 当前 hit index
    bool current_hit_is_last;    // 是否为收招最终击
    bool is_heavy;               // 是否为重击 (Heavy Attack)
    uint32_t last_hit_flags;     // 命中标志位
    bool allow_application;      // 输出：是否允许施加 (true=放行, false=阻止)
} SkillBuffGateContext;

// Buff 施加成功后激活上下文 (hook_188 post-apply activation)
typedef struct {
    void* buffs_controller;
    void* applicant;
    void* stat_modifier;
    const char* modifier_id;
    const char* target_bot_id;
    int target_player_index;
    int attacker_player_index;
    float override_duration;
    uint64_t now_ms;
} SkillBuffAppliedContext;


// 闪避概率结算上下文 (hook_190 近战, hook_191 远程)
typedef struct {
    void* entity_attr;
    const char* bot_id;
    int player_index;            // 0 = P0, 1 = P1
    bool is_ranged;              // true = 远程 (hook_191), false = 近战 (hook_190)
    int original_evade_result;   // 游戏原生计算的闪避判定 (0 或 1)
    float base_chance;           // 闪避几率
    float modified_chance;       // 技能修改后的几率
    bool force_guaranteed;       // 是否强制 100% 闪避
} SkillEvadeContext;

// 触发器/概率检定上下文 (hook_192 TestRoll)
typedef struct {
    void* self;
    void* stat_modifier;
    const char* modifier_id;
    const char* owner_bot_id;
    int owner_player_index;      // 0 = P0, 1 = P1
    int target_player_index;
    int current_special_index;
    int last_hit_index;
    bool current_hit_is_last;
    bool is_ranged;
    float* p_roll;               // 传入的骰子点数指针
    float* p_chance;             // 传入的判定概率指针
    void* trigger_params;
    void* method;
} SkillTestRollContext;

// ---------------------------------------------------------------------------
// 2. 独立角色技能模块抽象接口 (Bot Module Interface)
// ---------------------------------------------------------------------------
typedef struct {
    const char* bot_prefix;      // 角色前缀匹配 (如 "arcee", "rhinox", "wheeljack", "prowl")

    // 命中前/后回调
    void (*on_hit_connected)(SkillHitContext* ctx);

    // Buff 施加过滤门禁 (返回 1 表示已处理并输出 ctx->allow_application, 返回 0 表示非本模块管辖)
    int (*on_buff_gated)(SkillBuffGateContext* ctx);

    // Buff 施加成功后回调 (激活计时器、增益、特效等)
    void (*on_buff_applied)(SkillBuffAppliedContext* ctx);

    // 闪避几率检定 (返回 1 表示已处理，*out_evade 为 0 或 1; 返回 0 表示非本模块管辖)
    int (*on_evade_check)(SkillEvadeContext* ctx, int* out_evade);

    // TestRoll 触发判定 (返回 1 表示已接管判定并输出 *out_res; 返回 0 表示非本模块管辖)
    int (*on_test_roll)(SkillTestRollContext* ctx, int* out_res);

    // 能量获取率倍率修正 (返回 1 表示已处理并输出 *out_mult, 返回 0 表示非本模块管辖)
    int (*on_power_gain_rate)(int player_index, float* out_mult);

    // 远程子弹反射检定 (返回 1 表示已接管并输出 *out_reflect_mod; 返回 0 表示非本模块管辖)
    int (*on_reflect_proj)(int player_index, float* out_reflect_mod);

    // 战斗重置/回合开始 (清理私有冷却和状态变量)
    void (*on_fight_reset)(int player_index);

    // 每帧物理模拟时钟驱动
    void (*on_simulation_tick)(uint64_t now_ms);

    // 动作状态进入与退出回调 (格挡、闪避、受击等)
    void (*on_block_state)(int player_index, int entered); // entered=1 进入格挡, entered=0 退出格挡
    void (*on_dodge_enter)(int player_index);
    void (*on_hitreact_enter)(int player_index);
    void (*on_attack_start)(int player_index, int action_type);
} BotSkillModule;
