#pragma once
#include <stdint.h>
#include <stdbool.h>
#include <stddef.h>

// 官方职业枚举位掩码 (源自 CharacterMetaData.Class)
#define BOT_CLASS_NONE     0
#define BOT_CLASS_BRAW     1
#define BOT_CLASS_TACT     2
#define BOT_CLASS_SCOU     4
#define BOT_CLASS_DEMO     8
#define BOT_CLASS_WARR     16
#define BOT_CLASS_TECH     32

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
    bool is_melee;               // 是否为近战攻击 (DamageType 含 melee，或普攻非远程)
    bool is_heavy;               // 是否为重击 (Heavy Attack)
    bool is_crit;                // 是否暴击
    bool is_blocked;             // 是否被格挡
    float base_damage;           // 原始计算伤害
    float modified_damage;       // 技能修改后的伤害输出
    float armor_penetration;     // 护甲穿透倍率 (0.0..1.0+)
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
    bool is_heavy;
    float* p_roll;               // 传入的骰子点数指针
    float* p_chance;             // 传入的判定概率指针
    void* trigger_params;
    void* method;
} SkillTestRollContext;

// 官方 HitResultFlags 位掩码 (源自 HitResultFlags.cs)
#define HIT_FLAG_HIT            0x0001u
#define HIT_FLAG_MISSED         0x0002u
#define HIT_FLAG_BLOCKED        0x0004u
#define HIT_FLAG_IGNORE_DMG     0x0008u
#define HIT_FLAG_IGNORE_REACT   0x0010u
#define HIT_FLAG_INVULNERABLE   0x0018u
#define HIT_FLAG_CRIT           0x0020u
#define HIT_FLAG_PERFECT_BLOCK  0x0040u
#define HIT_FLAG_LAST_HIT       0x0080u
#define HIT_FLAG_PROJECTILE     0x0100u
#define HIT_FLAG_AVOIDED        0x0200u
#define HIT_FLAG_EVADED         0x0400u
#define HIT_FLAG_CANCELLED      0x0800u
#define HIT_FLAG_REFLECTED      0x1000u

// 单次打击事件终态结算上下文 (ResolveHitResult + ResolveAttackEvent / Projectile.OnDisable)
typedef struct {
    int attacker_player_index;   // 0 = P0, 1 = P1
    int target_player_index;     // 0 = P0, 1 = P1
    const char* attacker_bot_id;
    const char* target_bot_id;
    int event_id;                // HitResultData.Id
    int attack_level;            // 1=L, 2=M, 4=Heavy, 8=Ranged, 16=SP1, 32=SP2, 64=SP3
    int hit_index;               // HitResultData.HitIndex
    int attack_count;            // HitResultData.AttackCount
    uint32_t flags;              // 最终结算 HitResultFlags
    bool is_last_hit;            // (flags & HIT_FLAG_LAST_HIT) != 0
    bool is_missed;              // 统一落空判定：非 Hit/Blocked/Cancelled/Reflected 且带 Missed/Evaded/Avoided/Invulnerable
    float damage;                // 最终伤害
} SkillAttackEndContext;

// ---------------------------------------------------------------------------
// 2. 独立角色技能模块抽象接口 (Bot Module Interface)
// ---------------------------------------------------------------------------
typedef struct {
    const char* bot_prefix;      // 角色前缀匹配 (如 "arcee", "rhinox", "wheeljack", "prowl")
    const char* display_name_zh; // 可选中文显示名 (用于通用 HUD 播报，避免在总线硬编码英雄名)

    // 命中前/后回调
    void (*on_hit_connected)(SkillHitContext* ctx);

    // 新一轮打击命中解析开始 (用于重置单次打击局部状态)
    void (*on_hit_begin)(void);

    // Buff 施加过滤门禁 (返回 1 表示已处理并输出 ctx->allow_application, 返回 0 表示非本模块管辖)
    int (*on_buff_gated)(SkillBuffGateContext* ctx);

    // Buff 施加成功后回调 (激活计时器、增益、特效等)
    void (*on_buff_applied)(SkillBuffAppliedContext* ctx);
    void (*on_opponent_buff_applied)(SkillBuffAppliedContext* ctx);

    // 闪避几率检定 (返回 1 表示已处理，*out_evade 为 0 或 1; 返回 0 表示非本模块管辖)
    int (*on_evade_check)(SkillEvadeContext* ctx, int* out_evade);

    // 闪避真实触发成功后的协同回调 (evader_player_index 为触发闪避的一方)
    void (*on_evade_triggered)(int evader_player_index, int is_ranged);

    // TestRoll 触发判定 (返回 1 表示已接管判定并输出 *out_res; 返回 0 表示非本模块管辖，继续原生流程)
    int (*on_test_roll)(SkillTestRollContext* ctx, int* out_res);

    // 原生 TestRoll 完成后的后置回调 (roll_result 为原版返回的 0 或 1)
    void (*on_test_roll_post)(SkillTestRollContext* ctx, int roll_result);

    // 能量获取率倍率修正 (返回 1 表示已处理并输出 *out_mult, 返回 0 表示非本模块管辖)
    int (*on_power_gain_rate)(int player_index, float* out_mult);

    // 远程子弹反射检定 (返回 1 表示已接管并输出 *out_reflect_mod; 返回 0 表示非本模块管辖)
    int (*on_reflect_proj)(int player_index, float* out_reflect_mod);

    // 弹丸飞行速度倍率修正 (返回 1 表示已接管并输出 *out_speed_mult; 返回 0 表示非本模块管辖)
    int (*on_projectile_speed)(int player_index, int is_heavy, float* out_speed_mult);

    // 战斗重置/回合开始 (清理私有冷却和状态变量)
    void (*on_fight_reset)(int player_index);

    // 每帧物理模拟时钟驱动
    void (*on_simulation_tick)(uint64_t now_ms);

    // 动作状态进入与退出回调 (格挡、闪避、受击等)
    void (*on_block_state)(int player_index, int entered); // entered=1 进入格挡, entered=0 退出格挡
    void (*on_dodge_enter)(int player_index);
    void (*on_opponent_block_state)(int opponent_index, int entered); // 对手进入/退出格挡
    void (*on_opponent_dodge_enter)(int opponent_index);             // 对手进入闪避
    void (*on_hitreact_enter)(int player_index);
    void (*on_attack_start)(int player_index, int action_type);

    // 单次打击事件终态结算回调 (精确落空状态机与打击完成通知)
    void (*on_attack_ended)(SkillAttackEndContext* ctx);
    // 必杀技状态机进出回调 (sp_level: 1=SP1, 2=SP2, 3=SP3; entered: 1=进入, 0=退出)
    void (*on_special_state)(int player_index, int sp_level, int entered);
    void (*on_opponent_special_state)(int opponent_player_index, int sp_level, int entered);

    // 攻击方反规避判定 (返回 1 表示阻止防守方触发任何规避; 返回 0 表示不干涉)
    int (*on_anti_evade_check)(int attacker_player_index, const SkillEvadeContext* ctx);
    // 动态被动暴击率加权回调 (返回 1 并累加到 *out_bonus; 返回 0 表示无加成)
    int (*on_crit_chance_mod)(int player_index, int atk_level, float* out_bonus);
    // 暴击判定结果出炉回调 (在计算暴击伤害倍率前同步派发，用于暴击专属觉醒技如抹杀)
    void (*on_crit_rolled)(int player_index, int atk_level, int is_last_hit, int is_crit);
    // 远程穿透判定回调 (前冲/重击期间穿透敌方远程，返回 1 表示穿透无视碰撞与伤害)
    int (*on_ranged_pierce_check)(int player_index, int atk_level);
    // 攻击方动态不可防御判定回调 (返回 1 并输出 *out_unblockable = 1 表示本次攻击无视格挡且不挂战斗图标)
    int (*on_unblockable_check)(int attacker_player_index, int* out_unblockable);
} BotSkillModule;
