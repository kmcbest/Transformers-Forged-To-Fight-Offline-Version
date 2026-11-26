#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 阿尔茜 (Arcee) 技能模块 (严格对照官方技能库 8 项实战能力全实现)
// 1. [被动 - 远程规避]: 20.7% 几率规避对手远程普攻与特技远程攻击 (无图标)
// 2. [被动 - 爆头射击]: 49.7% 几率在远程 / SP1 手枪射击中爆头 (60% ATK 直伤 + 3s 60% ATK 流血)
// 3. [被动 - 前冲惩罚]: 所有攻击命中前冲对手时 +50% 暴击率; 冲锋命中触发 arcee_headshot_rush 极速流血
// 4. [被动 - 能量获取]: 暴击时额外获得最大能量的 4% (+0.12 格)
// 5. [SP1 - 特技射击]: 跳过第 0 击踢腿，手枪命中后 6.5s 远程伤害 +35%, 射速 +40%
// 6. [SP2 - 流血]: 暴击 100% 触发 4s 108% ATK 流血 (原生 onCrit level=Special2)
// 7. [SP3 - 狙击]: 跳过前两击踢腿 (hit_index <= 1), 后续手枪/狙击段 100% 135% 直伤 + 9s 流血
// 8. [觉醒 - 守卫者的残暴]: 发动任意 SP 时 80% 概率获得 +25% 暴击率并彻底阻止对手规避, 持续 10s

static uint64_t s_arcee_ranged_evade_ms[2]  = {0, 0};
static int      s_arcee_ranged_evade_res[2] = {0, 0};

static int arcee_opp_is_dashing(int opp_idx, uint64_t now_ms) {
    uint64_t opp_dash_ms = skill_get_last_dash_ms(opp_idx);
    return (opp_dash_ms > 0 && now_ms >= opp_dash_ms && (now_ms - opp_dash_ms <= 850));
}

static void arcee_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    if (!ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "arcee") == NULL) return;

    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    uint64_t now_ms = skill_now_ms();
    int is_blocked = (ctx->is_blocked || (ctx->hit_flags & HIT_FLAG_BLOCKED) != 0);

    // 1. 暴击额外回能 4% 最大能量 (0.12 格)
    if (!is_blocked && ctx->is_crit && ap >= 0 && ap < 2) {
        skill_add_mana(ap, 0.12f);
        skill_log("ARCEE_CRIT_POWER_GAIN: P%d crit hit -> +4%% max power (+0.12 mana)", ap);
    }

    // 2. 爆头与前冲流血反制 (远程普攻、SP1 射击段、SP3 中间 4 发手枪射击; 不需要暴击，但被对方格挡时不触发)
    int is_sp1_shot = (ctx->special_index == 1 && ctx->hit_index > 0);
    int is_sp3_pistol_shot = (ctx->special_index == 3 && ctx->hit_index >= 2 && !ctx->is_last_hit);
    if (!is_blocked && (ctx->is_ranged || is_sp1_shot || is_sp3_pistol_shot)) {
        int opp_dashing = arcee_opp_is_dashing(tp, now_ms);
        float hs_roll = skill_random_float();
        if (hs_roll < 0.497f) {
            skill_apply_buff(tp, "arcee_headshot_direct");
            if (opp_dashing) {
                skill_apply_buff(tp, "arcee_headshot_rush");
                skill_overlay("[%s] 爆头惩罚！60%% 直伤 + 极速流血！", ap == 0 ? "阿尔茜" : "敌方阿尔茜");
                skill_log("ARCEE_HEADSHOT_RUSH: P%d headshot dashing P%d (sp=%d hit=%d roll=%.3f) -> direct + rush bleed",
                          ap, tp, ctx->special_index, ctx->hit_index, hs_roll);
            } else {
                skill_apply_buff(tp, "arcee_headshot_dot");
                skill_log("ARCEE_HEADSHOT: P%d headshot P%d (sp=%d hit=%d roll=%.3f < 0.497) -> direct + 3s bleed",
                          ap, tp, ctx->special_index, ctx->hit_index, hs_roll);
            }
        } else if (opp_dashing) {
            // 兼容原冲锋反制机制：命中前冲目标也触发极速流血标记
            skill_apply_buff(tp, "arcee_headshot_rush");
            skill_log("ARCEE_HEADSHOT_RUSH: P%d hit dashing P%d -> rush bleed", ap, tp);
        }
    }

    // 3. SP3 狙击: 仅最后一击 (is_last_hit，第 7 击狙击步枪) 100% 触发 135% 直伤与 9s 流血
    if (ctx->special_index == 3 && ctx->is_last_hit) {
        skill_apply_buff(tp, "arcee_sp3_snipe_direct");
        skill_apply_buff(tp, "arcee_sp3_snipe_bleed");
        skill_log("ARCEE_SP3_SNIPE: hit_index=%d (last_hit) applied snipe direct & bleed to P%d", ctx->hit_index, tp);
    }
}

static int arcee_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    if (strstr(ctx->modifier_id, "arcee_") != NULL) {
        if (strstr(ctx->modifier_id, "headshot_") != NULL && (ctx->last_hit_flags & HIT_FLAG_BLOCKED) != 0) {
            skill_log("ARCEE_HEADSHOT_BLOCK_GATE: suppressed %s on blocked hit", ctx->modifier_id);
            ctx->allow_application = false;
            return 1;
        }
        if (strstr(ctx->modifier_id, "sp1_") != NULL || strstr(ctx->modifier_id, "headshot_") != NULL) {
            if (ctx->current_special_index == 1 && ctx->last_hit_index == 0) {
                skill_log("ARCEE_SP1_KICK_GATE: suppressed %s on hit_index=%d (kick)", ctx->modifier_id, ctx->last_hit_index);
                ctx->allow_application = false;
                return 1;
            }
        }
        if (strstr(ctx->modifier_id, "sp3_") != NULL) {
            if (ctx->current_special_index == 3 && !ctx->current_hit_is_last) {
                skill_log("ARCEE_SP3_KICK_GATE: suppressed %s on hit_index=%d (non-last)", ctx->modifier_id, ctx->last_hit_index);
                ctx->allow_application = false;
                return 1;
            }
        }
    }

    return 0;
}

static void arcee_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return;

    if (strstr(ctx->modifier_id, "arcee_sp1_trick_shot") != NULL) {
        int tp = ctx->target_player_index;
        skill_set_ranged_boost(tp, 6500, 0.35f, 0.40f);
        skill_log("RANGED_BOOST_ACTIVATED: Arcee SP1 on P%d (dmg=+35%%, spd=+40%%, dur=6.5s)", tp);
    }
}

static int arcee_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade || !ctx->bot_id || strstr(ctx->bot_id, "arcee") == NULL) return 0;
    if (!ctx->is_ranged) return 0;

    int p = ctx->player_index;
    if (p < 0 || p > 1) return 0;

    uint64_t now_ms = skill_now_ms();
    if (s_arcee_ranged_evade_ms[p] > 0 && now_ms - s_arcee_ranged_evade_ms[p] < 80) {
        if (s_arcee_ranged_evade_res[p]) {
            *out_evade = 1;
            return 1;
        }
        return 0;
    }

    s_arcee_ranged_evade_ms[p] = now_ms;
    float r = skill_random_float();
    if (r < 0.207f) {
        s_arcee_ranged_evade_res[p] = 1;
        *out_evade = 1;
        skill_log("ARCEE_RANGED_EVADE: P%d evaded ranged attack (roll=%.3f < 0.207)", p, r);
        return 1;
    }
    s_arcee_ranged_evade_res[p] = 0;
    return 0;
}

static void arcee_on_evade_triggered(int evader_player_index, int is_ranged) {
    (void)is_ranged;
    const char* evader_bot = skill_get_bot_id(evader_player_index);
    if (!evader_bot || strstr(evader_bot, "arcee") == NULL) return;
    skill_apply_buff_dur(evader_player_index, "gp_evade_callout", 1.0f);
    skill_log("ARCEE_EVADE_CALLOUT: P%d triggered green evade callout", evader_player_index);
}

static int arcee_on_anti_evade_check(int attacker_player_index, const SkillEvadeContext* ctx) {
    if (attacker_player_index < 0 || attacker_player_index > 1 || !ctx) return 0;
    if (skill_has_buff(attacker_player_index, "arcee_sig_ferocity")) {
        skill_log("ARCEE_ANTI_EVADE: P%d Guardian's Ferocity suppressed evade on P%d (ranged=%d)",
                  attacker_player_index, ctx->player_index, ctx->is_ranged ? 1 : 0);
        return 1;
    }
    return 0;
}

static int arcee_on_crit_chance_mod(int player_index, int atk_level, float* out_bonus) {
    (void)atk_level;
    if (player_index < 0 || player_index > 1 || !out_bonus) return 0;
    int tp = 1 - player_index;
    uint64_t now_ms = skill_now_ms();
    if (arcee_opp_is_dashing(tp, now_ms)) {
        *out_bonus += 0.50f;
        skill_log("ARCEE_DASH_PUNISHMENT: P%d attacking dashing P%d -> +50%% crit chance", player_index, tp);
        return 1;
    }
    return 0;
}

static void arcee_on_special_state(int player_index, int sp_level, int entered) {
    if (!entered || player_index < 0 || player_index > 1) return;
    if (sp_level < 1 || sp_level > 3) return;
    float r = skill_random_float();
    if (r < 0.80f) {
        skill_apply_buff_dur(player_index, "arcee_sig_ferocity", 10.0f);
        skill_overlay("[%s] 守卫者的残暴！+25%% 暴击率与反规避 (10秒)", player_index == 0 ? "阿尔茜" : "敌方阿尔茜");
        skill_log("ARCEE_SIG_FEROCITY: P%d activated SP%d (roll=%.3f < 0.80) -> +25%% crit & anti-evade 10s",
                  player_index, sp_level, r);
    } else {
        skill_log("ARCEE_SIG_FEROCITY_MISS: P%d SP%d roll=%.3f >= 0.80", player_index, sp_level, r);
    }
}

static void arcee_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index <= 1) {
        s_arcee_ranged_evade_ms[player_index] = 0;
        s_arcee_ranged_evade_res[player_index] = 0;
    }
}

BotSkillModule g_module_arcee = {
    .bot_prefix = "arcee",
    .display_name_zh = "阿尔茜",
    .on_hit_connected = arcee_on_hit_connected,
    .on_buff_gated = arcee_on_buff_gated,
    .on_buff_applied = arcee_on_buff_applied,
    .on_evade_check = arcee_on_evade_check,
    .on_test_roll = NULL,
    .on_fight_reset = arcee_on_fight_reset,
    .on_special_state = arcee_on_special_state,
    .on_evade_triggered = arcee_on_evade_triggered,
    .on_anti_evade_check = arcee_on_anti_evade_check,
    .on_crit_chance_mod = arcee_on_crit_chance_mod
};
