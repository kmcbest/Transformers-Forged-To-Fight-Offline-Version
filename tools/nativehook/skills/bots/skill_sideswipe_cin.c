#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// ===========================================================================
// 电影横炮 (Sideswipe ROTF) 专属战斗技能模块
// Bot ID: sideswipe_cin_rotf
// 职业: 格斗系 (Warrior) | 阵营: 汽车人 (Autobot)
// ===========================================================================
// 1. [觉醒 - 我真酷！]
//    - 主动闪避(后闪/侧闪)躲过敌人攻击时，获得 1 层 +180% 暴击伤害增益 (sideswipe_cin_sig_cool)；
//    - 可叠加，使下一次中等攻击 (M1 或 M2) 不可规避、必定暴击，非格挡命中后清零所有层数。
// 2. [被动 - L4/M2 终结爆发]
//    - 轻度或中度连击最后一击 (L4 或 M2) 不可规避、必定暴击并提升 +180% 暴击伤害；
//    - 可与招牌暴伤叠加，直接结算（无额外图标与 callout）。
// 3. [被动 - 前冲/重击远程穿透与规避]
//    - 前冲或重击期间，35% 概率穿透敌方基础远程与远程重击；未触发穿透则 100% 触发规避。
// 4. [被动 - 近战暴击流血 & 对流血目标暴击几率]
//    - 近战(含重击)暴击 45% 施加 65% ATK 4 秒流血；
//    - 对手处于流血状态时挂载黄图标 +24% 暴击几率，流血结束后移除。
// 5. [SP1 / SP2 / SP3]
//    - 技能期间自身 +75% 暴击伤害 (退出 SP 立即回收)；
//    - SP1 / SP2 全程不可被规避；
//    - SP1 末击 85% 驱散对手 1 个护甲增益 + 暴击 100% 施加 125% ATK 2s 流血；
//    - SP2 全段暴击 100% 施加 100% ATK 4s 流血；
//    - SP3 末击命中 100% 施加 150% ATK 10s 流血。
// ===========================================================================

static int      s_active_sp[2]            = {0, 0};
static int      s_last_dodge_ev_id[2]     = {-1, -1};
static uint64_t s_last_cool_ms[2]         = {0, 0};
static uint64_t s_pierce_roll_ms[2]       = {0, 0};
static int      s_pierce_roll_res[2]      = {0, 0};

static inline int is_movie_sideswipe(const char* bid) {
    return (bid != NULL && strstr(bid, "sideswipe_cin") != NULL);
}

static inline int is_dash_or_heavy_active(int player_index) {
    return (skill_is_heavy_attacking(player_index) || skill_is_dashing(player_index));
}

// 按 350ms 窗口统一掷骰一次 35% 穿透，保证前冲/重击穿透与兜底规避逻辑自洽
static int roll_ranged_pierce_window(int player_index) {
    if (player_index < 0 || player_index >= 2) return 0;
    uint64_t now_ms = skill_now_ms();
    if (s_pierce_roll_ms[player_index] == 0 ||
        now_ms < s_pierce_roll_ms[player_index] ||
        (now_ms - s_pierce_roll_ms[player_index] >= 350)) {
        s_pierce_roll_ms[player_index] = now_ms;
        s_pierce_roll_res[player_index] = (skill_random_float() < 0.35f) ? 1 : 0;
    }
    return s_pierce_roll_res[player_index];
}

// 同步“对手流血 -> +24% 暴击率”黄图标
static void sync_bleed_crit_rate_buff(int p) {
    if (p < 0 || p >= 2) return;
    const char* bid = skill_get_bot_id(p);
    if (!is_movie_sideswipe(bid)) return;

    int opp = 1 - p;
    int opp_bleeding = skill_has_buff(opp, "bleed");
    if (opp_bleeding) {
        if (!skill_has_buff(p, "sideswipe_cin_bleed_crit_rate")) {
            skill_apply_buff_dur(p, "sideswipe_cin_bleed_crit_rate", -1.0f);
            skill_log("SIDESWIPE_CIN: P%d gained +24%% crit rate (opponent P%d is bleeding)", p, opp);
        }
    } else {
        if (skill_has_buff(p, "sideswipe_cin_bleed_crit_rate")) {
            skill_consume_buff(p, "sideswipe_cin_bleed_crit_rate", 99);
            skill_log("SIDESWIPE_CIN: P%d lost +24%% crit rate (opponent P%d bleed ended)", p, opp);
        }
    }
}

static void sideswipe_cin_on_fight_reset(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    s_active_sp[player_index]        = 0;
    s_last_dodge_ev_id[player_index] = -1;
    s_last_cool_ms[player_index]     = 0;
    s_pierce_roll_ms[player_index]   = 0;
    s_pierce_roll_res[player_index]  = 0;
}

static void sideswipe_cin_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    sync_bleed_crit_rate_buff(0);
    sync_bleed_crit_rate_buff(1);
}

// SP1 / SP2 / SP3 进出同步 +75% 暴击伤害 与 规避克制(SP1/2)
static void sideswipe_cin_on_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!is_movie_sideswipe(bid)) return;

    if (entered) {
        s_active_sp[player_index] = sp_level;
        skill_apply_buff_dur(player_index, "sideswipe_cin_sp_crit_dmg", 6.0f);
        if (sp_level == 1 || sp_level == 2) {
            skill_apply_buff_dur(player_index, "sideswipe_cin_sp_anti_evade", 6.0f);
        }
        skill_log("SIDESWIPE_CIN: P%d entered SP%d -> +75%% crit dmg%s",
                  player_index, sp_level, (sp_level <= 2) ? " + Anti-Evade" : "");
    } else {
        if (s_active_sp[player_index] == sp_level) {
            s_active_sp[player_index] = 0;
        }
        skill_consume_buff(player_index, "sideswipe_cin_sp_crit_dmg", 99);
        skill_consume_buff(player_index, "sideswipe_cin_sp_anti_evade", 99);
        skill_log("SIDESWIPE_CIN: P%d exited SP%d -> cleared SP crit dmg & anti-evade",
                  player_index, sp_level);
    }
}

// 反规避检定: SP1/SP2 全程、L4、M2、或持有“我真酷”叠层时的 M1/M2 均不可规避
static int sideswipe_cin_on_anti_evade_check(int attacker_player_index, const SkillEvadeContext* ctx) {
    (void)ctx;
    if (attacker_player_index < 0 || attacker_player_index >= 2) return 0;
    const char* bid = skill_get_bot_id(attacker_player_index);
    if (!is_movie_sideswipe(bid)) return 0;

    if (s_active_sp[attacker_player_index] == 1 ||
        s_active_sp[attacker_player_index] == 2 ||
        skill_has_buff(attacker_player_index, "sideswipe_cin_sp_anti_evade")) {
        skill_log("SIDESWIPE_CIN_ANTI_EVADE: P%d SP%d suppressed evade", attacker_player_index, s_active_sp[attacker_player_index]);
        return 1;
    }

    int act = skill_get_current_action(attacker_player_index);
    int l_idx = skill_get_combo_light_index(attacker_player_index);
    int m_idx = skill_get_combo_medium_index(attacker_player_index);

    if (l_idx >= 4 || m_idx >= 2) {
        skill_log("SIDESWIPE_CIN_ANTI_EVADE: P%d L4/M2 finisher suppressed evade (act=%d l=%d m=%d)",
                  attacker_player_index, act, l_idx, m_idx);
        return 1;
    }

    if (skill_has_buff(attacker_player_index, "sideswipe_cin_sig_cool") &&
        (act == 2 || m_idx >= 1)) {
        skill_log("SIDESWIPE_CIN_ANTI_EVADE: P%d I'm So Cool M-attack suppressed evade", attacker_player_index);
        return 1;
    }

    return 0;
}

// 必暴击检定:
// - 招牌“我真酷！”激活期间，下一次 M1/M2 +100% 暴击率 (必定暴击)
// - 被动 L4 或 M2 终结击 +100% 暴击率 (必定暴击)
static int sideswipe_cin_on_crit_chance_mod(int player_index, int atk_level, float* out_bonus) {
    if (player_index < 0 || player_index >= 2 || !out_bonus) return 0;
    const char* bid = skill_get_bot_id(player_index);
    if (!is_movie_sideswipe(bid)) return 0;

    int l_idx = skill_get_combo_light_index(player_index);
    int m_idx = skill_get_combo_medium_index(player_index);

    int is_l4 = (atk_level == 1 && l_idx >= 4);
    int is_m2 = (atk_level == 2 && m_idx >= 2);
    int has_cool = (atk_level == 2 && skill_has_buff(player_index, "sideswipe_cin_sig_cool"));

    if (is_l4 || is_m2 || has_cool) {
        *out_bonus += 1.00f;
        skill_log("SIDESWIPE_CIN_GUARANTEED_CRIT: P%d +100%% crit (al=%d l=%d m=%d last=%d cool=%d)",
                  player_index, atk_level, l_idx, m_idx, skill_is_current_hit_last(), has_cool);
        return 1;
    }
    return 0;
}

// 远程穿透判定: 前冲或重击过程中 35% 概率直接穿透对方基础远程与远程重击
static int sideswipe_cin_on_ranged_pierce_check(int player_index, int atk_level) {
    (void)atk_level;
    if (player_index < 0 || player_index >= 2) return 0;
    const char* bid = skill_get_bot_id(player_index);
    if (!is_movie_sideswipe(bid)) return 0;
    if (!is_dash_or_heavy_active(player_index)) return 0;

    int pierce = roll_ranged_pierce_window(player_index);
    if (pierce) {
        skill_log("SIDESWIPE_CIN_PIERCE: P%d pierced ranged attack during dash/heavy!", player_index);
    }
    return pierce;
}

// 远程兜底规避: 前冲/重击期间若未触发 35% 穿透，则 100% 触发绿色“规避” Callout
static int sideswipe_cin_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    if (!ctx->is_ranged) return 0;
    if (!is_movie_sideswipe(ctx->bot_id)) return 0;

    int p = ctx->player_index;
    if (!is_dash_or_heavy_active(p)) return 0;

    // 若 35% 穿透检定尚未决定且本次命中了穿透，则交给穿透通道；未穿透则 100% 规避
    if (roll_ranged_pierce_window(p)) {
        *out_evade = 0;
        return 0;
    }

    *out_evade = 1;
    skill_apply_buff_dur(p, "sideswipe_cin_ranged_evade_callout", 0.8f);
    skill_overlay("[%s] 极速闪影！规避远程打击！", p == 0 ? "电影横炮" : "敌方电影横炮");
    skill_log("SIDESWIPE_CIN_EVADE_RANGED: P%d evaded ranged attack during dash/heavy (callout 规避)", p);
    return 1;
}

// 觉醒技“我真酷！”：主动后闪/侧闪躲过敌人一次攻击时叠 1 层 +180% 暴伤
static void sideswipe_cin_on_attack_ended(SkillAttackEndContext* ctx) {
    if (!ctx || !ctx->is_missed) return;
    if (!is_movie_sideswipe(ctx->target_bot_id)) return;

    int tp = ctx->target_player_index;
    if (tp < 0 || tp >= 2) return;

    uint64_t now_ms = skill_now_ms();
    uint64_t back_ms = skill_get_last_backdash_ms(tp);
    uint64_t side_ms = skill_get_last_sidestep_ms(tp);
    uint64_t last_dodge_ms = (back_ms > side_ms) ? back_ms : side_ms;

    // 严格要求处于主动闪避时间窗内 (850ms)，避免前冲/重击自带的被动远程规避误叠加招牌
    bool active_dodge_window = (last_dodge_ms > 0 && now_ms >= last_dodge_ms && (now_ms - last_dodge_ms <= 850));
    if (!active_dodge_window) return;

    if (ctx->event_id > 1 && ctx->event_id == s_last_dodge_ev_id[tp]) return;
    if (s_last_cool_ms[tp] > 0 && now_ms >= s_last_cool_ms[tp] && (now_ms - s_last_cool_ms[tp] < 200)) return;

    s_last_dodge_ev_id[tp] = ctx->event_id;
    s_last_cool_ms[tp] = now_ms;
    skill_apply_buff_dur(tp, "sideswipe_cin_sig_cool", -1.0f);
    int stacks = skill_count_buffs(tp, "sideswipe_cin_sig_cool");
    skill_overlay("[%s] 我真酷！闪避叠层 (+%d%% 暴伤 x%d)",
                  tp == 0 ? "电影横炮" : "敌方电影横炮", stacks * 180, stacks);
    skill_log("SIDESWIPE_CIN_SIG_COOL: P%d actively dodged attack (al=%d) -> cool stacks=%d (+%d%% crit dmg)",
              tp, ctx->attack_level, stacks, stacks * 180);
}

static void sideswipe_cin_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    if (!is_movie_sideswipe(ctx->attacker_bot_id)) return;

    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    if (ap < 0 || ap >= 2 || tp < 0 || tp >= 2) return;

    int is_l4 = (ctx->special_index == 0 && !ctx->is_ranged &&
                 ctx->action_type == 1 && (skill_get_combo_light_index(ap) >= 4 || ctx->hit_index == 3));
    int is_m2 = (ctx->special_index == 0 && !ctx->is_ranged &&
                 ctx->action_type == 2 && (skill_get_combo_medium_index(ap) >= 2 || ctx->hit_index == 1));
    int is_m  = (ctx->special_index == 0 && !ctx->is_ranged && ctx->action_type == 2);

    int cool_stacks = skill_count_buffs(ap, "sideswipe_cin_sig_cool");

    // 1. L4 或 M2 终结一击 +180% 暴击伤害 (与“我真酷！”叠加，无图标无 callout 直接按倍率差放大结算)
    if ((is_l4 || is_m2) && ctx->is_crit) {
        float cur_mult = 1.50f + 1.80f * (float)cool_stacks;
        float target_mult = cur_mult + 1.80f;
        ctx->modified_damage *= (target_mult / cur_mult);
        skill_log("SIDESWIPE_CIN_FINISHER_CDMG: P%d %s crit scaled %.2fx -> %.2fx (cool=%d, dmg=%.1f)",
                  ap, is_l4 ? "L4" : "M2", cur_mult, target_mult, cool_stacks, ctx->modified_damage);
    }

    // 2. 下一次中等攻击 (M1 或 M2) 命中后，消耗所有“我真酷！”层数
    if (is_m && !ctx->is_blocked && cool_stacks > 0) {
        skill_consume_buff(ap, "sideswipe_cin_sig_cool", 99);
        skill_log("SIDESWIPE_CIN_SIG_COOL_SPENT: P%d Medium hit (%s) consumed %d cool stack(s)",
                  ap, is_m2 ? "M2" : "M1", cool_stacks);
    }

    // 格挡门禁：以下流血与护甲驱散仅在未格挡命中时触发
    if (ctx->is_blocked) {
        sync_bleed_crit_rate_buff(ap);
        return;
    }

    // 3. 被动：近战(含重击)暴击 45% 施加 65% ATK 4 秒流血
    if (ctx->special_index == 0 && !ctx->is_ranged && ctx->is_crit) {
        float r = skill_random_float();
        if (r < 0.45f) {
            skill_apply_buff_dur(tp, "sideswipe_cin_crit_bleed", 4.0f);
            skill_log("SIDESWIPE_CIN_MELEE_BLEED: P%d melee crit inflicted bleed (65%% ATK, 4s) on P%d (roll=%.3f<0.45)",
                      ap, tp, r);
        }
    }

    // 4. SP1：末击 85% 驱散对手 1 个护甲增益 + 暴击 100% 施加 125% ATK 2s 流血
    if (ctx->special_index == 1 && ctx->is_last_hit) {
        float rn = skill_random_float();
        if (rn < 0.85f) {
            char removed_id[64] = {0};
            if (skill_dispel_random_buff_by_category(tp, 0, 1, removed_id, sizeof(removed_id))) {
                skill_overlay("[敌方] 护甲移除！(%s)", removed_id);
                skill_log("SIDESWIPE_CIN_SP1_NULLIFY: P%d dispelled armor buff '%s' on P%d (roll=%.3f<0.85)",
                          ap, removed_id, tp, rn);
            }
        }
        if (ctx->is_crit) {
            skill_apply_buff_dur(tp, "sideswipe_cin_sp1_bleed", 2.0f);
            skill_log("SIDESWIPE_CIN_SP1_BLEED: P%d SP1 lastHit crit inflicted bleed (125%% ATK, 2s) on P%d", ap, tp);
        }
    }

    // 5. SP2：所有暴击命中 100% 施加 100% ATK 4s 流血
    if (ctx->special_index == 2 && ctx->is_crit) {
        skill_apply_buff_dur(tp, "sideswipe_cin_sp2_bleed", 4.0f);
        skill_log("SIDESWIPE_CIN_SP2_BLEED: P%d SP2 hit%d crit inflicted bleed (100%% ATK, 4s) on P%d",
                  ap, ctx->hit_index, tp);
    }

    // 6. SP3：末击命中 100% 施加 150% ATK 10s 史诗级流血
    if (ctx->special_index == 3 && ctx->is_last_hit) {
        skill_apply_buff_dur(tp, "sideswipe_cin_sp3_bleed", 10.0f);
        skill_log("SIDESWIPE_CIN_SP3_BLEED: P%d SP3 lastHit inflicted bleed (150%% ATK, 10s) on P%d", ap, tp);
    }

    // 命中后立即同步对手流血状态给予 +24% 暴击率
    sync_bleed_crit_rate_buff(ap);
}

BotSkillModule g_module_sideswipe_cin = {
    .bot_prefix             = "sideswipe_cin",
    .display_name_zh        = "电影横炮",
    .on_fight_reset         = sideswipe_cin_on_fight_reset,
    .on_simulation_tick     = sideswipe_cin_on_simulation_tick,
    .on_special_state       = sideswipe_cin_on_special_state,
    .on_anti_evade_check    = sideswipe_cin_on_anti_evade_check,
    .on_crit_chance_mod     = sideswipe_cin_on_crit_chance_mod,
    .on_ranged_pierce_check = sideswipe_cin_on_ranged_pierce_check,
    .on_evade_check         = sideswipe_cin_on_evade_check,
    .on_attack_ended        = sideswipe_cin_on_attack_ended,
    .on_hit_connected       = sideswipe_cin_on_hit_connected,
};
