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
static uint64_t s_last_power_evade_ms[2] = {0, 0};
static uint64_t s_last_dash_evade_ms[2] = {0, 0};

// 严格隔离 G1 横炮 (sideswipe_gs) 与电影横炮 (sideswipe_cin_rotf)
static int is_g1_sideswipe(const char* bid) {
    return (bid && strstr(bid, "sideswipe_gs") != NULL);
}

static void sideswipe_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!is_g1_sideswipe(bid)) return;

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

    // 1. 横炮作为受击方 (Victim)
    if (is_g1_sideswipe(ctx->target_bot_id)) {
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
    if (is_g1_sideswipe(ctx->attacker_bot_id)) {
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

        // SP1 末击 40% 概率眩晕
        if (ctx->special_index == 1 && ctx->is_last_hit && !ctx->is_blocked) {
            if (skill_random_float() < 0.40f) {
                skill_apply_buff(tp, "sideswipe_s1_stun");
                skill_log("SIDESWIPE_SP1_STUN: last hit stunned P%d", tp);
            }
        }

        // SP2 命中：获得 8 秒 35% 近战规避增益，末击 100% 燃烧
        if (ctx->special_index == 2 && ctx->is_last_hit) {
            skill_apply_buff_dur(ap, "sideswipe_s2_melee_evade", 8.0f);
            skill_overlay("[%s] SP2 近战规避！获得8秒规避增益！", ap == 0 ? "横炮" : "敌方横炮");
            skill_log("SIDESWIPE_SP2_EVADE: P%d gained 8s melee evade (35%%)", ap);
            if (!ctx->is_blocked) {
                skill_apply_buff(tp, "sideswipe_s2_burn");
                skill_log("SIDESWIPE_SP2_BURN: last hit burned P%d", tp);
            }
        }

        // SP3 末击 100% 燃烧
        if (ctx->special_index == 3 && ctx->is_last_hit && !ctx->is_blocked) {
            skill_apply_buff(tp, "sideswipe_s3_burn");
            skill_log("SIDESWIPE_SP3_BURN: last hit burned P%d", tp);
        }
    }
}

static void sideswipe_on_dodge_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    if (!is_g1_sideswipe(skill_get_bot_id(player_index))) return;
    // 严格门禁：正常空放闪避或闪避近战绝不误触发回能；
    // 仅在 on_attack_ended 确认实际躲过远程子弹或前冲攻击时由精准判定通道触发！
    skill_log("SIDESWIPE_DODGE_ENTER: P%d entered dodge stance", player_index);
}

static int sideswipe_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    if (is_g1_sideswipe(ctx->bot_id)) {
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
    if (!is_g1_sideswipe(skill_get_bot_id(player_index))) return;
    // 被击倒失去 5 层暴击率增益
    if (skill_has_buff(player_index, "sideswipe_crit_rate_stack")) {
        skill_consume_buff(player_index, "sideswipe_crit_rate_stack", 5);
        skill_log("SIDESWIPE_KD_LOSS: P%d knocked down, lost up to 5 crit rate stacks", player_index);
    }
}

static void sideswipe_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_hit_count[player_index] = 0;
        s_last_power_evade_ms[player_index] = 0;
        s_last_dash_evade_ms[player_index] = 0;
    }
}

// 统一在打击终态事件 (ResolveAttackEvent / Projectile.OnDisable) 判定极限闪避：
// 1) 每个 event_id 仅触发一次，杜绝 RegisterHitResult 逐帧连发导致疯狂加气；
// 2) 只通过原生 power_gain Buff (m=117.0 / 900.0 = 13%, 1s) 加气，绝不叠加手动 skill_add_mana；
// 3) 必须配合主动后闪/侧闪时间窗 (<= 850ms)，站桩远距离敌方打空不计为极限闪避。
static void sideswipe_on_attack_ended(SkillAttackEndContext* ctx) {
    if (!ctx || !ctx->is_missed) return;
    if (!is_g1_sideswipe(ctx->target_bot_id)) return;

    int tp = ctx->target_player_index;
    int ap = ctx->attacker_player_index;
    if (tp < 0 || tp >= 2 || ap < 0 || ap >= 2) return;

    uint64_t now_ms = skill_now_ms();
    uint64_t back_ms = skill_get_last_backdash_ms(tp);
    uint64_t side_ms = skill_get_last_sidestep_ms(tp);
    uint64_t last_dodge_ms = (back_ms > side_ms) ? back_ms : side_ms;

    // 校验横炮自身在最近 850ms 内确实做过闪避动作 (或原生旗标明确标记 Evaded/Avoided)
    bool explicit_evade_flag = (ctx->flags & (HIT_FLAG_EVADED | HIT_FLAG_AVOIDED)) != 0;
    bool active_dodge_window = (last_dodge_ms > 0 && now_ms >= last_dodge_ms && (now_ms - last_dodge_ms <= 850));
    if (!explicit_evade_flag && !active_dodge_window) return;

    int al = ctx->attack_level;
    int is_ranged_attack = (al == 8 || (al == 4 && skill_bot_has_ranged_heavy(ctx->attacker_bot_id)));
    if (is_ranged_attack) {
        if (s_last_power_evade_ms[tp] == 0 || (now_ms >= s_last_power_evade_ms[tp] && now_ms - s_last_power_evade_ms[tp] >= 800)) {
            s_last_power_evade_ms[tp] = now_ms;
            skill_apply_buff_dur(tp, "sideswipe_evade_ranged_power", 1.0f);
            skill_overlay("[%s] 极限闪避远程！获得13%%最大能量 (1秒)！", tp == 0 ? "横炮" : "敌方横炮");
            skill_log("SIDESWIPE_EVADE_RANGED: P%d evaded ranged attack (al=%d ev=%d flags=0x%x), applied +13%% power_gain",
                      tp, al, ctx->event_id, ctx->flags);
        }
        return;
    }

    // 闪避对方前冲攻击 (Dash Attack 以 AttackLevel.Medium = 2 结算，配合对手近期前冲时间戳)
    uint64_t opp_dash_ms = skill_get_last_dash_ms(ap);
    bool is_dash_attack = (al == 2 && opp_dash_ms > 0 && now_ms >= opp_dash_ms && (now_ms - opp_dash_ms <= 1000));
    if (is_dash_attack) {
        if (s_last_dash_evade_ms[tp] == 0 || (now_ms >= s_last_dash_evade_ms[tp] && now_ms - s_last_dash_evade_ms[tp] >= 800)) {
            s_last_dash_evade_ms[tp] = now_ms;
            skill_apply_buff_dur(tp, "sideswipe_evade_dash_crit_damage", 6.0f);
            skill_overlay("[%s] 闪避冲锋！暴击伤害提升+108%%！", tp == 0 ? "横炮" : "敌方横炮");
            skill_log("SIDESWIPE_EVADE_DASH: P%d evaded dash (al=%d ev=%d), applied +108%% crit dmg (6s)",
                      tp, al, ctx->event_id);
        }
    }
}

static int sideswipe_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;
    if (!is_g1_sideswipe(ctx->owner_bot_id)) return 0;

    // SP1 仅最后一击闪踢眩晕; SP2 和 SP3 仅最后一击燃烧
    if (strstr(ctx->modifier_id, "sideswipe_s1_stun") != NULL ||
        strstr(ctx->modifier_id, "sideswipe_s2_burn") != NULL ||
        strstr(ctx->modifier_id, "sideswipe_s3_burn") != NULL) {
        if (!ctx->current_hit_is_last) {
            skill_log("SIDESWIPE_GATE: non-last hit, skip roll: %s", ctx->modifier_id);
            *out_res = 0;
            return 1;
        }
    }
    // SP3 驱散: 除最后一击外，每一击概率驱散
    if (strstr(ctx->modifier_id, "sideswipe_s3_nullify") != NULL) {
        if (ctx->current_hit_is_last) {
            skill_log("SIDESWIPE_GATE: last hit, skip nullify roll: %s", ctx->modifier_id);
            *out_res = 0;
            return 1;
        }
    }

    return 0;
}

BotSkillModule g_module_sideswipe = {
    .bot_prefix         = "sideswipe_gs",
    .display_name_zh    = "横炮",
    .on_hit_connected   = sideswipe_on_hit_connected,
    .on_attack_start    = sideswipe_on_attack_start,
    .on_dodge_enter     = sideswipe_on_dodge_enter,
    .on_evade_check     = sideswipe_on_evade_check,
    .on_test_roll       = sideswipe_on_test_roll,
    .on_hitreact_enter  = sideswipe_on_hitreact_enter,
    .on_attack_ended    = sideswipe_on_attack_ended,
    .on_fight_reset     = sideswipe_on_fight_reset,
};
