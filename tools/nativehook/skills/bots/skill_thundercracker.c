#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 惊天雷 (Thundercracker Leader 2015) 技能模块
// Bot ID: thundercracker_gs_leader2015
// ===========================================================================
// 1. [3404] 被动：近战 0 暴击 (Melee Zero Crit / White Damage)
// 2. [3409] 被动：重击净化 (Heavy Attack Purify)
// 3. [3410] 被动：净化转燃烧 (Purify to Burn Converter)
// 4. [3420] SP1：近战增益 (SP1 Melee Buff) - +50% 近战伤害，持续 6s
// 5. [3422] SP3：震击 (SP3 Shock)
//
// 核心机制：
// 惊天雷的近战攻击永远不产生暴击 (恒定为白字伤害)。
// 重击命中时净化自身减益，并根据净化的减益层数在对手身上施加高额火焰燃烧。
// 释放 SP1 后获得 6 秒近战增益 (+50% 近战伤害)。
// ===========================================================================

static int s_purified_count[2] = {0, 0};

static void thundercracker_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // 惊天雷作为攻击方：
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "thundercracker") != NULL) {
        int ap = ctx->attacker_player_index;

        // 1. 近战 0 暴击：强制将 is_crit 设为 false，打出白字伤害
        if (!ctx->is_ranged) {
            ctx->is_crit = false;
        }

        // 2. SP1 近战增益 (+50% 近战伤害，持续 6s)
        if (!ctx->is_ranged && (skill_has_buff(ap, "thundercracker_sp1_melee_buff") || skill_has_buff(ap, "melee_buff"))) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= 1.50f;
            skill_log("THUNDERCRACKER: SP1 Melee buff boosted damage on P%d: %.1f -> %.1f", ap, old_dmg, ctx->modified_damage);
        }

        // 3. 重击净化与燃烧转化：
        if (ctx->is_last_hit) {
            if (s_purified_count[ap] > 0) {
                float burn_mult = 1.0f + (0.50f * s_purified_count[ap]);
                ctx->modified_damage *= burn_mult;
                skill_overlay("[%s] 净化转化火焰爆发！重击追加 %.0f%% 燃烧伤害！",
                              ap == 0 ? "惊天雷" : "敌方惊天雷", (burn_mult - 1.0f) * 100.0f);
                skill_log("THUNDERCRACKER: P%d converted %d purified debuffs into burn boost",
                          ap, s_purified_count[ap]);
                s_purified_count[ap] = 0;
            } else {
                skill_overlay("[%s] 重击净化生效！自身负面状态已清除！",
                              ap == 0 ? "惊天雷" : "敌方惊天雷");
            }
        }
    }
}

static void thundercracker_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_purified_count[player_index] = 0;
    }
}

BotSkillModule g_module_thundercracker = {
    .bot_prefix       = "thundercracker",
    .on_hit_connected = thundercracker_on_hit_connected,
    .on_buff_gated    = NULL,
    .on_buff_applied  = NULL,
    .on_evade_check   = NULL,
    .on_test_roll     = NULL,
    .on_fight_reset   = thundercracker_on_fight_reset,
};
