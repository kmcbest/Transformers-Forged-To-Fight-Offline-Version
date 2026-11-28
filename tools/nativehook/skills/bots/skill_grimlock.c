#include "../skill_env.h"
#include "../skill_types.h"
#include <stdio.h>
#include <string.h>

/*
 * 钢锁 (grimlock_gs_mp08) 战斗逻辑模块：
 * 1. 受击被动：受到攻击时 14% 概率获 1 层 +16% 近战增益（5 秒，可叠加）
 * 2. 觉醒 恐龙之怒：受到带倒计时的持续伤害减益(流血/震击/燃烧/酸液等)后 1.0 秒自动净化该减益，
 *    并有 30% 概率获 1 层 +30% 近战增益（5 秒，可叠加）；即时直伤类减益不净化
 * 3. 重击全程不可阻挡：发动重击时进入不可阻挡直至重击结束/受击中断，并立即刷新身上所有近战增益倒计时(5秒)；
 *    重击非格挡命中 70% 概率施加 2 秒 50% 燃烧
 * 4. SP1：发动获 +12% 近战增益(5秒)，末击(喷火)非格挡命中 100% 施加 4 秒 100% 燃烧
 * 5. SP2：发动获 +18% 近战增益(5秒)
 * 6. SP3：发动获 +30% 近战增益(5秒)，命中 100% 施加 7 秒 150% 燃烧
 */

#define GRIMLOCK_MAX_PURIFY_SLOTS 16

typedef struct {
    int active;
    int target_player_index;
    uint64_t purify_at_ms;
    char mod_id[64];
} GrimPurifySlot;

static GrimPurifySlot s_purify_queue[GRIMLOCK_MAX_PURIFY_SLOTS];
static uint64_t s_heavy_unstop_start_ms[2] = {0, 0};

static int is_grimlock(const char* bot_id) {
    return bot_id && strstr(bot_id, "grimlock") != NULL;
}

static int grimlock_is_curable_dot(const char* mod_id, float override_dur) {
    if (!mod_id || !mod_id[0]) return 0;
    if (override_dur < 0.0f) return 0; // 永久 (-1) 非倒计时
    // 排除即时直伤/非净化类效果
    if (strstr(mod_id, "instant") != NULL ||
        strstr(mod_id, "direct") != NULL ||
        strstr(mod_id, "headshot") != NULL ||
        strstr(mod_id, "nullify_shock") != NULL ||
        strstr(mod_id, "dark_burn") != NULL ||
        strstr(mod_id, "gp_") != NULL) {
        return 0;
    }
    return (strstr(mod_id, "bleed") != NULL ||
            strstr(mod_id, "burn") != NULL ||
            strstr(mod_id, "shock") != NULL ||
            strstr(mod_id, "acid") != NULL ||
            strstr(mod_id, "poison") != NULL);
}

static void grimlock_refresh_buff_stacks(int p, const char* mod_id, float dur) {
    int cnt = skill_count_buffs(p, mod_id);
    if (cnt <= 0) return;
    skill_consume_buff(p, mod_id, cnt);
    for (int i = 0; i < cnt; i++) {
        skill_apply_buff_dur(p, mod_id, dur);
    }
}

static void grimlock_refresh_all_melee_buffs(int p) {
    const char* ids[] = {
        "grimlock_takehit_melee_buff",
        "grimlock_sig_melee_buff",
        "grimlock_sp1_melee_buff",
        "grimlock_sp2_melee_buff",
        "grimlock_sp3_melee_buff"
    };
    for (int i = 0; i < 5; i++) {
        grimlock_refresh_buff_stacks(p, ids[i], 5.0f);
    }
}

static void grimlock_end_heavy_unstoppable(int p) {
    if (p < 0 || p >= 2) return;
    if (s_heavy_unstop_start_ms[p] > 0 || skill_has_buff(p, "grimlock_heavy_unstoppable")) {
        s_heavy_unstop_start_ms[p] = 0;
        skill_consume_buff(p, "grimlock_heavy_unstoppable", 1);
        skill_set_unstoppable(p, 0);
    }
}

static void grimlock_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_heavy_unstop_start_ms[player_index] = 0;
        for (int i = 0; i < GRIMLOCK_MAX_PURIFY_SLOTS; i++) {
            if (s_purify_queue[i].active && s_purify_queue[i].target_player_index == player_index) {
                s_purify_queue[i].active = 0;
            }
        }
    }
}

static void grimlock_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx) return;
    int tp = ctx->target_player_index;
    if (tp < 0 || tp >= 2 || !is_grimlock(ctx->target_bot_id)) return;
    if (!grimlock_is_curable_dot(ctx->modifier_id, ctx->override_duration)) return;

    for (int i = 0; i < GRIMLOCK_MAX_PURIFY_SLOTS; i++) {
        if (!s_purify_queue[i].active) {
            s_purify_queue[i].active = 1;
            s_purify_queue[i].target_player_index = tp;
            s_purify_queue[i].purify_at_ms = ctx->now_ms + 1000ULL;
            snprintf(s_purify_queue[i].mod_id, sizeof(s_purify_queue[i].mod_id), "%s", ctx->modifier_id);
            skill_log("GRIMLOCK_SIG: P%d queued purify for '%s' in 1000ms", tp, ctx->modifier_id);
            break;
        }
    }
}

static void grimlock_simulation_tick(uint64_t now_ms) {
    // 1. 觉醒：到期(1s后)真正净化伤害减益并 30% 获 +30% 近战增益 (5s)
    for (int i = 0; i < GRIMLOCK_MAX_PURIFY_SLOTS; i++) {
        if (s_purify_queue[i].active && now_ms >= s_purify_queue[i].purify_at_ms) {
            int tp = s_purify_queue[i].target_player_index;
            if (tp >= 0 && tp < 2 && is_grimlock(skill_get_bot_id(tp))) {
                if (skill_has_buff(tp, s_purify_queue[i].mod_id)) {
                    skill_consume_buff(tp, s_purify_queue[i].mod_id, 1);
                    skill_apply_buff_dur(tp, "grimlock_dino_rage", 1.5f);
                    int gained = 0;
                    if (skill_random_float() < 0.30f) {
                        skill_apply_buff_dur(tp, "grimlock_sig_melee_buff", 5.0f);
                        gained = 1;
                    }
                    skill_overlay("[%s] 恐龙之怒净化减益%s！",
                                  tp == 0 ? "钢锁" : "敌方钢锁",
                                  gained ? " (+30%近战)" : "");
                    skill_log("GRIMLOCK_SIG: P%d purified '%s', sig_melee_gained=%d",
                              tp, s_purify_queue[i].mod_id, gained);
                }
            }
            s_purify_queue[i].active = 0;
        }
    }

    // 2. 重击不可阻挡兜底收敛：重击状态已退出超过 250ms 后自动卸除
    for (int p = 0; p < 2; p++) {
        if (s_heavy_unstop_start_ms[p] > 0 && now_ms - s_heavy_unstop_start_ms[p] > 250ULL) {
            if (!skill_is_heavy_attacking(p)) {
                grimlock_end_heavy_unstoppable(p);
            }
        }
    }
}

static void grimlock_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    if (!is_grimlock(skill_get_bot_id(player_index))) return;
    if ((action_type == 4 || action_type == 0x100) &&
        !skill_has_buff(player_index, "grimlock_heavy_unstoppable")) {
        s_heavy_unstop_start_ms[player_index] = skill_now_ms();
        skill_apply_buff_dur(player_index, "grimlock_heavy_unstoppable", 2.0f);
        skill_set_unstoppable(player_index, 2000);
        grimlock_refresh_all_melee_buffs(player_index);
        skill_log("GRIMLOCK_HEAVY: P%d started Heavy -> Unstoppable + refreshed all melee buffs to 5.0s", player_index);
    }
}

static void grimlock_attack_ended(SkillAttackEndContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    if (ap >= 0 && ap < 2 && is_grimlock(ctx->attacker_bot_id) && ctx->attack_level == 4) {
        grimlock_end_heavy_unstoppable(ap);
    }
}

static void grimlock_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2 || !entered) return;
    if (!is_grimlock(skill_get_bot_id(player_index))) return;
    if (sp_level == 1) {
        skill_apply_buff_dur(player_index, "grimlock_sp1_melee_buff", 5.0f);
        skill_log("GRIMLOCK_SP1: P%d gained +12%% melee buff (5.0s)", player_index);
    } else if (sp_level == 2) {
        skill_apply_buff_dur(player_index, "grimlock_sp2_melee_buff", 5.0f);
        skill_log("GRIMLOCK_SP2: P%d gained +18%% melee buff (5.0s)", player_index);
    } else if (sp_level == 3) {
        skill_apply_buff_dur(player_index, "grimlock_sp3_melee_buff", 5.0f);
        skill_log("GRIMLOCK_SP3: P%d gained +30%% melee buff (5.0s)", player_index);
    }
}

static void grimlock_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 1. 受击被动：14% 概率获 1 层 +16% 近战增益 (5s)
    if (tp >= 0 && tp < 2 && is_grimlock(ctx->target_bot_id)) {
        if (skill_random_float() < 0.14f) {
            skill_apply_buff_dur(tp, "grimlock_takehit_melee_buff", 5.0f);
            skill_log("GRIMLOCK_PASSIVE: P%d struck -> +16%% melee buff (5.0s)", tp);
        }
    }

    // 2. 钢锁进攻
    if (ap >= 0 && ap < 2 && is_grimlock(ctx->attacker_bot_id)) {
        if (ctx->is_melee) {
            float bonus = 0.0f;
            bonus += 0.16f * (float)skill_count_buffs(ap, "grimlock_takehit_melee_buff");
            bonus += 0.30f * (float)skill_count_buffs(ap, "grimlock_sig_melee_buff");
            bonus += 0.12f * (float)skill_count_buffs(ap, "grimlock_sp1_melee_buff");
            bonus += 0.18f * (float)skill_count_buffs(ap, "grimlock_sp2_melee_buff");
            bonus += 0.30f * (float)skill_count_buffs(ap, "grimlock_sp3_melee_buff");
            if (bonus > 0.0f) {
                ctx->modified_damage *= (1.0f + bonus);
            }
        }

        if (!ctx->is_blocked) {
            if (ctx->is_heavy && skill_random_float() < 0.70f) {
                skill_apply_buff_dur(tp, "grimlock_heavy_burn", 2.0f);
            } else if (ctx->special_index == 1 && ctx->is_last_hit) {
                skill_apply_buff_dur(tp, "grimlock_sp1_burn", 4.0f);
            } else if (ctx->special_index == 3 && ctx->is_last_hit) {
                skill_apply_buff_dur(tp, "grimlock_sp3_burn", 7.0f);
            }
        }
    }
}

BotSkillModule g_module_grimlock = {
    .bot_prefix         = "grimlock",
    .display_name_zh    = "钢锁",
    .on_hit_connected   = grimlock_hit_connected,
    .on_buff_applied    = grimlock_buff_applied,
    .on_fight_reset     = grimlock_fight_reset,
    .on_simulation_tick = grimlock_simulation_tick,
    .on_attack_start    = grimlock_attack_start,
    .on_attack_ended    = grimlock_attack_ended,
    .on_special_state   = grimlock_special_state,
};
