#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 犀牛 (Rhinox) 技能模块
// - SP1 驱散敌人 Buff 后触发流血 (rhinox_sp1_nullify_bleed)
// - 被动 流血增伤: 基本近战攻击对流血敌人额外造成 +20% 伤害
// - 觉醒 超频: 受重击/高额未格挡伤害反噬 160% ATK 震击 4 秒
// - SP3 末击 30% 概率触发流血

static void rhinox_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // 1. 犀牛作为攻击方 (Attacker)
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "rhinox") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 近战基本攻击对流血目标 +20% 伤害
        if (!ctx->is_ranged && ctx->special_index == 0 && skill_has_buff(tp, "bleed")) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= 1.20f;
            skill_log("RHINOX_BLEED_BOOST: P%d melee vs bleeding P%d: %.1f -> %.1f",
                      ap, tp, old_dmg, ctx->modified_damage);
        }

        // SP3 最后一击 30% 几率施加流血
        if (ctx->special_index == 3 && ctx->is_last_hit && !ctx->is_blocked) {
            if (skill_random_float() < 0.30f) {
                skill_apply_buff(tp, "rhinox_sp3_bleed");
                skill_overlay("[%s] SP3 末日机枪流血！(30%% 触发, 12s)", ap == 0 ? "犀牛" : "敌方犀牛");
                skill_log("RHINOX_SP3_BLEED: applied rhinox_sp3_bleed to P%d", tp);
            }
        }
    }

    // 2. 犀牛作为受击方 (Target) - 觉醒超频震击反制
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "rhinox") != NULL && !ctx->is_blocked) {
        int tp = ctx->target_player_index;
        int ap = ctx->attacker_player_index;
        float max_hp = skill_get_max_hp(tp);
        if (max_hp > 0.0f && ctx->modified_damage >= max_hp * 0.06f) {
            skill_apply_buff(ap, "rhinox_overclock_shock");
            skill_overlay("[%s] 超频反制！施加震击 (4s)", tp == 0 ? "犀牛" : "敌方犀牛");
            skill_log("RHINOX_OVERCLOCK: P%d took heavy hit (%.1f), shocked attacker P%d",
                      tp, ctx->modified_damage, ap);
        }
    }
}

static int rhinox_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    if (strstr(ctx->modifier_id, "rhinox_sp1_nullify_bleed") != NULL) {
        int nullified = skill_get_p1_buffs_nullified();
        if (nullified <= 0) {
            skill_log("RHINOX_NULLIFY_GATE: suppressed bleed because 0 buffs were nullified from P1");
            ctx->allow_application = false;
        } else {
            skill_log("RHINOX_NULLIFY_GATE: permitted bleed because %d buff(s) nullified from P1", nullified);
            ctx->allow_application = true;
        }
        return 1; // 已处理
    }

    return 0;
}

static void rhinox_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_rhinox = {
    .bot_prefix = "rhinox",
    .display_name_zh = "犀牛",
    .on_hit_connected = rhinox_on_hit_connected,
    .on_buff_gated = rhinox_on_buff_gated,
    .on_buff_applied = NULL,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_fight_reset = rhinox_on_fight_reset
};
