#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 横炮 (Sideswipe) 技能模块
// Bot ID: sideswipe_gs
// 职业: 侦察兵 (Scout) | 阵营: 汽车人 (Autobot)
// ===========================================================================
// 1. [被动 - 受击近战规避] 受到 7 次基础普通攻击后，获得持续 4 秒 38% 近战规避增益。
// 2. [被动 - 暴击率叠层] 暴击时获得一层 3.8% 暴击率增益，被击倒失去 5 层。
// 3. [被动 - 重击净化] 重击起手净化自身所有震击减益。
// 4. [被动 - 重击刷新] 重击命中刷新所有暴击伤害增益的持续时间。
// 5. [觉醒技 - 最大推力] 开局 12 秒内获得最大能量的 50%。
// 6. [SP1 - 眩晕与暴击几率] 本技能内暴击率 +25.5%，闪踢最后一击 40% 眩晕 2.5 秒。
// 7. [SP2 - 排气烈焰与近战规避] 尾击 80% ATK 燃烧 6 秒；命中获得 8 秒 35% 近战规避增益。
// 8. [SP3 - 尾击烈焰与增益驱散] 尾击 100% ATK 燃烧 4 秒；前段每击 60% 几率驱散对方增益。
// 9. [被动 - 闪避远程回能] 闪避远程普通攻击与重击时，获得 13% 最大能量。
// 10. [被动 - 闪避前冲暴伤] 闪避对方前冲攻击时，获得 108% 暴击伤害增益，持续 6 秒。
// ===========================================================================

static int s_hit_count[2] = {0, 0};

static void sideswipe_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;

    // 横炮发起重击：净化自身震击减益
    if (action_type == 4 || action_type == 0x100) {
        if (skill_has_buff(player_index, "dmg_shock") || skill_has_buff(player_index, "shock")) {
            skill_consume_buff(player_index, "dmg_shock", 99);
            skill_consume_buff(player_index, "shock", 99);
            skill_overlay("[%s] 重击净化！净化自身所有震击！", player_index == 0 ? "横炮" : "敌方横炮");
            skill_log("SIDESWIPE_HEAVY_PURIFY: P%d cleansed shock on heavy start", player_index);
        }
    }
}

static void sideswipe_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 1. 横炮作为受击方 (Victim)
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "sideswipe") != NULL) {
        int tp = ctx->target_player_index;

        // 受到普通攻击受击计数 (特殊技中的攻击不计数)
        if (ctx->special_index == 0) {
            s_hit_count[tp]++;
            if (s_hit_count[tp] < 7) {
                skill_apply_buff_dur(tp, "sideswipe_evade_counter", -1.0f);
            } else {
                // 满 7 次，转化为持续 4 秒的绿色 38% 近战规避增益
                s_hit_count[tp] = 0;
                skill_consume_buff(tp, "sideswipe_evade_counter", 99);
                skill_apply_buff_dur(tp, "sideswipe_melee_evade", 4.0f);
                skill_overlay("[%s] 受到7次攻击！激活4秒近战规避！", tp == 0 ? "横炮" : "敌方横炮");
                skill_log("SIDESWIPE_EVADE_ACTIVATED: P%d reached 7 hits, gained 4s melee evade (38%%)", tp);
            }
        }
    }

    // 2. 横炮作为攻击方 (Attacker)
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "sideswipe") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 暴击获得 3.8% 暴击率增益叠层
        if (ctx->is_crit) {
            skill_apply_buff_dur(ap, "sideswipe_crit_rate_stack", 15.0f);
            skill_log("SIDESWIPE_CRIT_STACK: P%d gained 1 stack of crit rate (+3.8%%)", ap);
        }

        // 重击命中：刷新所有暴伤增益持续时间
        if (ctx->is_heavy) {
            if (skill_has_buff(ap, "sideswipe_evade_dash_crit_damage")) {
                skill_apply_buff_dur(ap, "sideswipe_evade_dash_crit_damage", 6.0f);
                skill_overlay("[%s] 重击刷新！暴击伤害倒计时重置！", ap == 0 ? "横炮" : "敌方横炮");
            }
        }

        // SP2 命中：获得 8 秒 35% 近战规避增益
        if (ctx->special_index == 2 && ctx->is_last_hit) {
            skill_apply_buff_dur(ap, "sideswipe_s2_melee_evade", 8.0f);
            skill_overlay("[%s] SP2 近战规避！获得8秒规避增益！", ap == 0 ? "横炮" : "敌方横炮");
            skill_log("SIDESWIPE_SP2_EVADE: P%d gained 8s melee evade (35%%)", ap);
        }
    }
}

static void sideswipe_on_dodge_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    int opp_index = 1 - player_index;

    // 闪避冲锋攻击触发 +108% 暴击伤害 6 秒
    skill_apply_buff_dur(player_index, "sideswipe_evade_dash_crit_damage", 6.0f);
    // 闪避远程攻击获得 13% 能量
    skill_add_mana(player_index, 0.39f);
    skill_apply_buff_dur(player_index, "sideswipe_evade_ranged_power", 1.0f);
    skill_overlay("[%s] 极速闪避！获得108%%暴击伤害与+13%%能量！",
                  player_index == 0 ? "横炮" : "敌方横炮");
    skill_log("SIDESWIPE_DODGE: P%d gained 108%% crit dmg and 13%% power from dodge", player_index);
}

static int sideswipe_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    if (ctx->bot_id && strstr(ctx->bot_id, "sideswipe") != NULL) {
        int p = ctx->player_index;

        // 仅规避近战攻击 (普通近战与 SP1/SP2 近战攻击)
        if (!ctx->is_ranged) {
            if (skill_has_buff(p, "sideswipe_melee_evade")) {
                float roll = skill_random_float();
                if (roll < 0.38f) {
                    *out_evade = 1;
                    skill_log("SIDESWIPE_MELEE_EVADE: P%d evaded melee hit (38%% chance)", p);
                    return 1;
                }
            }
            if (skill_has_buff(p, "sideswipe_s2_melee_evade")) {
                float roll2 = skill_random_float();
                if (roll2 < 0.35f) {
                    *out_evade = 1;
                    skill_log("SIDESWIPE_S2_EVADE: P%d evaded melee hit (35%% chance)", p);
                    return 1;
                }
            }
        }
    }
    return 0;
}

static void sideswipe_on_hitreact_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    // 被击倒失去 5 层暴击率增益
    if (skill_has_buff(player_index, "sideswipe_crit_rate_stack")) {
        skill_consume_buff(player_index, "sideswipe_crit_rate_stack", 5);
        skill_log("SIDESWIPE_KD_LOSS: P%d knocked down, lost up to 5 crit rate stacks", player_index);
    }
}

static void sideswipe_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_hit_count[player_index] = 0;
    }
}

BotSkillModule g_module_sideswipe = {
    .bot_prefix         = "sideswipe",
    .on_hit_connected   = sideswipe_on_hit_connected,
    .on_attack_start    = sideswipe_on_attack_start,
    .on_dodge_enter     = sideswipe_on_dodge_enter,
    .on_evade_check     = sideswipe_on_evade_check,
    .on_hitreact_enter  = sideswipe_on_hitreact_enter,
    .on_fight_reset     = sideswipe_on_fight_reset,
};
