#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 铁皮 (Ironhide) 技能模块
// 严格隔离电影铁皮 (ironhide_cin_rotf) 与 G1 铁皮 (ironhide_gs_kabam) 两套机制

static int s_ironhide_burned_this_hit[2] = {0, 0};
static int s_obliteration_used[2] = {0, 0};
static int s_obliteration_active[2] = {0, 0};
static uint64_t s_ironhide_gs_sp2_armor_ms[2] = {0, 0};

static inline int is_movie_ironhide(const char* bid) {
    return (bid != NULL && strstr(bid, "ironhide_cin") != NULL);
}

static inline int is_g1_ironhide(const char* bid) {
    return (bid != NULL && strstr(bid, "ironhide_gs") != NULL);
}

static inline int is_movie_missile_hit(const SkillHitContext* ctx) {
    if (!ctx) return 0;
    if (ctx->is_heavy) return 1;
    if (ctx->special_index == 1 && ctx->is_last_hit) return 1;
    if (ctx->special_index == 2) return 1;
    return 0;
}

static void ironhide_on_hit_begin(void) {
    s_ironhide_burned_this_hit[0] = 0;
    s_ironhide_burned_this_hit[1] = 0;
}

static void ironhide_on_fight_reset(int player_index) {
    s_ironhide_burned_this_hit[0] = 0;
    s_ironhide_burned_this_hit[1] = 0;
    if (player_index >= 0 && player_index < 2) {
        s_obliteration_used[player_index] = 0;
        s_obliteration_active[player_index] = 0;
        s_ironhide_gs_sp2_armor_ms[player_index] = 0;
    }
}

// 导弹暴击 (+100% 暴击率): 仅限电影铁皮的重击 / SP1 最后一击 / SP2 全部攻击
static int ironhide_on_crit_chance_mod(int player_index, int atk_level, float* out_bonus) {
    if (player_index < 0 || player_index > 1 || !out_bonus) return 0;
    const char* bid = skill_get_bot_id(player_index);
    if (!is_movie_ironhide(bid)) return 0;

    int is_missile = 0;
    if (atk_level == 4 || atk_level == 32) {
        is_missile = 1;
    } else if (atk_level == 16 && skill_is_current_hit_last()) {
        is_missile = 1;
    }

    if (is_missile) {
        *out_bonus += 1.00f;
        skill_log("IRONHIDE_CIN: P%d missile crit +100%% (al=%d last=%d)",
                  player_index, atk_level, skill_is_current_hit_last());
        return 1;
    }
    return 0;
}

// [觉醒 - 抹杀 Obliteration]:
// 仅在特殊技 (SP1/SP2/SP3) 最后一击且该击暴击时才进行 50% 概率检定；
// 若未暴击则不参与骰子，若本次 50% 骰失败则下次特殊技仍可继续 ROLL；一旦触发则全场限 1 次 (+600% 暴击伤害即时作用于本次终击)
static void ironhide_on_crit_rolled(int player_index, int atk_level, int is_last_hit, int is_crit) {
    if (player_index < 0 || player_index > 1) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!is_movie_ironhide(bid)) return;

    int sp_level = 0;
    if (atk_level == 16) sp_level = 1;
    else if (atk_level == 32) sp_level = 2;
    else if (atk_level == 64) sp_level = 3;
    if (sp_level == 0) return;

    if (!is_last_hit || !is_crit) return;
    if (s_obliteration_used[player_index]) return;

    float r = skill_random_float();
    if (r < 0.50f) {
        s_obliteration_used[player_index] = 1;
        s_obliteration_active[player_index] = 1;
        skill_apply_buff_dur(player_index, "ironhide_sig_obliteration", 8.0f);
        skill_overlay("[%s] 抹杀！特技终击 +600%% 暴击伤害",
                      player_index == 0 ? "电影铁皮" : "敌方电影铁皮");
        skill_log("IRONHIDE_CIN_OBLITERATION: P%d SP%d lastHit crit triggered Obliteration (+600%% crit dmg, roll=%.3f<0.50)",
                  player_index, sp_level, r);
    } else {
        skill_log("IRONHIDE_CIN_OBLITERATION: P%d SP%d lastHit crit missed Obliteration (roll=%.3f>=0.50, can retry next SP)",
                  player_index, sp_level, r);
    }
}

static void ironhide_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || ctx->is_blocked) return;

    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // A. 电影铁皮作为攻击方: 导弹燃烧 / SP1 末击眩晕 / SP3 末击燃烧
    if (ap >= 0 && ap < 2 && tp >= 0 && tp < 2 && is_movie_ironhide(ctx->attacker_bot_id)) {
        // 1. 所有导弹攻击 (重击 / SP1 末击 / SP2 全段) 70% 几率造成燃烧
        if (is_movie_missile_hit(ctx)) {
            float r = skill_random_float();
            if (r < 0.70f) {
                int already_burning = skill_has_buff(tp, "burn");
                if (already_burning) {
                    skill_apply_buff_dur(tp, "ironhide_missile_burn_stack", 4.0f);
                    skill_log("IRONHIDE_CIN: P%d missile hit P%d (roll=%.3f<0.70) -> stacked burn (30%% ATK, 4s, sp=%d last=%d heavy=%d)",
                              ap, tp, r, ctx->special_index, ctx->is_last_hit ? 1 : 0, ctx->is_heavy ? 1 : 0);
                } else {
                    skill_apply_buff_dur(tp, "ironhide_missile_burn", 4.0f);
                    skill_log("IRONHIDE_CIN: P%d missile hit P%d (roll=%.3f<0.70) -> initial burn (80%% ATK, 4s, sp=%d last=%d heavy=%d)",
                              ap, tp, r, ctx->special_index, ctx->is_last_hit ? 1 : 0, ctx->is_heavy ? 1 : 0);
                }
                s_ironhide_burned_this_hit[tp] = 1;
            } else {
                skill_log("IRONHIDE_CIN: P%d missile burn missed roll=%.3f>=0.70 (sp=%d last=%d heavy=%d)",
                          ap, r, ctx->special_index, ctx->is_last_hit ? 1 : 0, ctx->is_heavy ? 1 : 0);
            }
        }

        // 2. SP1 最后一击: 80% 概率造成 2.5 秒眩晕
        if (ctx->special_index == 1 && ctx->is_last_hit) {
            float r = skill_random_float();
            if (r < 0.80f) {
                skill_apply_buff_dur(tp, "ironhide_sp1_stun", 2.5f);
                skill_overlay("[%s] 感觉走运！目标眩晕 2.5 秒", ap == 0 ? "电影铁皮" : "敌方电影铁皮");
                skill_log("IRONHIDE_CIN: P%d SP1 lastHit stunned P%d for 2.5s (roll=%.3f<0.80)", ap, tp, r);
            } else {
                skill_log("IRONHIDE_CIN: P%d SP1 stun missed roll=%.3f>=0.80", ap, r);
            }
        }

        // 3. SP3 最后一击: 30% 几率造成 100% ATK 燃烧 (持续 8 秒)
        if (ctx->special_index == 3 && ctx->is_last_hit) {
            float r = skill_random_float();
            if (r < 0.30f) {
                skill_apply_buff_dur(tp, "ironhide_s3_burn", 8.0f);
                skill_overlay("[%s] 全金属军械库！烈焰燃烧 8 秒", ap == 0 ? "电影铁皮" : "敌方电影铁皮");
                skill_log("IRONHIDE_CIN: P%d SP3 lastHit burned P%d (100%% ATK, 8s, roll=%.3f<0.30)", ap, tp, r);
            } else {
                skill_log("IRONHIDE_CIN: P%d SP3 burn missed roll=%.3f>=0.30", ap, r);
            }
        }
    }

    // B. 电影铁皮作为受击方: 受到攻击时 12% 概率获得 +140% 暴击伤害增益 (持续 8 秒)
    if (tp >= 0 && tp < 2 && is_movie_ironhide(ctx->target_bot_id)) {
        float r = skill_random_float();
        if (r < 0.12f) {
            skill_apply_buff_dur(tp, "ironhide_struck_crit_dmg", 8.0f);
            skill_overlay("[%s] 重装甲激发！+140%% 暴击伤害 (8秒)", tp == 0 ? "电影铁皮" : "敌方电影铁皮");
            skill_log("IRONHIDE_CIN: P%d struck (roll=%.3f<0.12) -> ironhide_struck_crit_dmg +140%% (8s)", tp, r);
        }
    }
}

static void ironhide_on_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid) return;

    // A. 电影铁皮 [觉醒 - 抹杀] 退出特殊技时立即回收临时暴伤加成
    if (is_movie_ironhide(bid) && sp_level >= 1 && sp_level <= 3) {
        if (!entered && (s_obliteration_active[player_index] || skill_has_buff(player_index, "ironhide_sig_obliteration"))) {
            s_obliteration_active[player_index] = 0;
            skill_consume_buff(player_index, "ironhide_sig_obliteration", 99);
            skill_log("IRONHIDE_CIN_OBLITERATION: P%d SP%d exited -> consumed Obliteration buff",
                      player_index, sp_level);
        }
        return;
    }

    // B. G1 铁皮 (ironhide_gs_kabam) SP1 / SP2 结束效果 (保持原有行为完全不变)
    if (entered == 0 && is_g1_ironhide(bid)) {
        if (sp_level == 1) {
            skill_apply_buff_dur(player_index, "ironhide_sp1_melee_buff", 8.0f);
            skill_log("IRONHIDE_GS: P%d SP1 expired -> granted ironhide_sp1_melee_buff (8.0s)", player_index);
        } else if (sp_level == 2) {
            skill_apply_buff_dur(player_index, "ironhide_sp2_unstoppable", 7.0f);
            skill_set_unstoppable(player_index, 7000);
            s_ironhide_gs_sp2_armor_ms[player_index] = skill_now_ms() + 7000;
            skill_log("IRONHIDE_GS: P%d SP2 expired -> granted unstoppable (7.0s), queued armor_up", player_index);
        }
    }
}

static void ironhide_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (s_ironhide_gs_sp2_armor_ms[p] > 0 && now_ms >= s_ironhide_gs_sp2_armor_ms[p]) {
            s_ironhide_gs_sp2_armor_ms[p] = 0;
            const char* bid = skill_get_bot_id(p);
            if (is_g1_ironhide(bid)) {
                for (int i = 0; i < 3; i++) {
                    skill_apply_buff_dur(p, "ironhide_sp2_armor_up", 10.0f);
                }
                skill_log("IRONHIDE_GS: P%d SP2 unstoppable ended -> granted 3x ironhide_sp2_armor_up (10.0s)", p);
            }
        }
    }
}

BotSkillModule g_module_ironhide = {
    .bot_prefix         = "ironhide",
    .display_name_zh    = "铁皮",
    .on_hit_begin       = ironhide_on_hit_begin,
    .on_hit_connected   = ironhide_on_hit_connected,
    .on_crit_chance_mod = ironhide_on_crit_chance_mod,
    .on_crit_rolled     = ironhide_on_crit_rolled,
    .on_fight_reset     = ironhide_on_fight_reset,
    .on_special_state   = ironhide_on_special_state,
    .on_simulation_tick = ironhide_on_simulation_tick,
};
