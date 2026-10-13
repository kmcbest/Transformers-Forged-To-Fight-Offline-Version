#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 威震天 (Megatron Leader 2015) 技能模块
// Bot ID: megatron_gs_leader2015
// ===========================================================================
// 1. [3121] 被动：融合炮充能 (Fusion Cannon Charge)
// 2. [3129] SP2：弱化 (Weakness / Atk Debuff)
// 3. [3130] SP3：震击 (Shock)
// 4. [3137] SP1：破甲 (Armor Break)
// 5. [3138] 特色能力：减益融合 (Debuff Fusion)
//
// 核心机制：减益融合 (把有倒计时的减益变成无倒计时的永久减益)
// 威震天使用重击蓄力击中对手时，将对手身上当前的减益效果彻底固化为永久减益 (duration = -1.0)。
// ===========================================================================

static int      s_fusion_charges[2]          = {0, 0};
static uint64_t s_last_charge_ms[2]          = {0, 0};
static int      s_debuff_frozen_permanent[2] = {0, 0};

static void megatron_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 1. 威震天作为攻击方：
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "megatron") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 周期性融合炮充能 (每 6 秒自动充能 1 层，上限 3 层)
        if (s_last_charge_ms[ap] == 0) s_last_charge_ms[ap] = now_ms;
        if (now_ms - s_last_charge_ms[ap] >= 6000 && s_fusion_charges[ap] < 3) {
            s_fusion_charges[ap]++;
            s_last_charge_ms[ap] = now_ms;
            skill_overlay("[%s] 融合炮充能完成 (%d/3)",
                          ap == 0 ? "威震天" : "敌方威震天", s_fusion_charges[ap]);
        }

        // 重击命中触发减益融合固化
        if (ctx->is_last_hit) {
            s_debuff_frozen_permanent[tp] = 1;
            if (s_fusion_charges[ap] > 0) {
                // 消耗融合炮充能造成额外破甲与增伤
                float boost = 1.0f + (0.35f * s_fusion_charges[ap]);
                ctx->modified_damage *= boost;
                skill_overlay("[%s] 消耗 %d 层融合炮充能！重击轰击增伤 %.0f%%！固化对手全部减益为永久！",
                              ap == 0 ? "威震天" : "敌方威震天",
                              s_fusion_charges[ap], (boost - 1.0f) * 100.0f);
                skill_log("MEGATRON: P%d consumed %d charges, boosted damage to %.1f, debuff fusion active",
                          ap, s_fusion_charges[ap], ctx->modified_damage);
                s_fusion_charges[ap] = 0;
            } else {
                skill_overlay("[%s] 减益融合生效！对手身上的减益已转化为永久减益！",
                              ap == 0 ? "威震天" : "敌方威震天");
            }
        }
    }
}

static void megatron_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;

    int tp = ctx->target_player_index;
    if (s_debuff_frozen_permanent[tp]) {
        // 将施加到目标身上的减益时长覆盖为永久 (-1.0f)
        ctx->override_duration = -1.0f;
        skill_log("MEGATRON: Debuff [%s] on P%d converted to PERMANENT (-1.0s)",
                  ctx->modifier_id, tp);
    }
}

static void megatron_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_fusion_charges[player_index] = 0;
        s_last_charge_ms[player_index] = 0;
        s_debuff_frozen_permanent[player_index] = 0;
    }
}

BotSkillModule g_module_megatron = {
    .bot_prefix       = "megatron",
    .on_hit_connected = megatron_on_hit_connected,
    .on_buff_gated    = NULL,
    .on_buff_applied  = megatron_on_buff_applied,
    .on_evade_check   = NULL,
    .on_test_roll     = NULL,
    .on_fight_reset   = megatron_on_fight_reset,
};
