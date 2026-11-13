#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 漂移 (Drift) 底层战斗技能模块
// Bot ID: drift_cin_aoe
// 职业: 格斗系 (Warrior) | 阵营: 汽车人 (Autobot)
// ===========================================================================
// 1. [集中体系] (Focus Combo Tracking)
//    - 连击达到 5 击：进入集中，暴击几率 +35%，降低对手 85% 规避率。
//    - 重击命中：未达集中时立即获得 5 击进入集中；已在集中则 +1 击。
//    - 连击达到 10 击：中度集中，+45% 暴击伤害。
//    - 连击达到 15 击：高度集中，新施加流血时长增加 150% (x2.5)。
//    - 漂移受创被击中时：连击中断，集中状态清零重计。
// 2. [近战规避] (Melee Evade on Bleeding Opponent)
//    - 对手处于流血状态时获得近战规避：基础 10%，集中 15%，中度 20%，高度 25%。
// ===========================================================================

static int s_drift_combo[2] = {0, 0};
static int s_drift_focus_level[2] = {0, 0}; // 0=无, 1=集中(5+), 2=中度(10+), 3=高度(15+)

// 检测对手是否处于流血状态 (任何带 bleed 的 Debuff)
static int drift_is_opponent_bleeding(int drift_p) {
    int opp = 1 - drift_p;
    return skill_has_buff(opp, "bleed");
}

// 模拟帧驱动: 实时监测对手流血状态，动态同步漂移的近战规避图标
static void drift_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "drift") == NULL) continue;

        int bleeding = drift_is_opponent_bleeding(p);
        if (bleeding) {
            if (!skill_has_buff(p, "drift_evade_buff")) {
                skill_apply_buff_dur(p, "drift_evade_buff", -1.0f);
                skill_log("DRIFT: P%d gained evade buff (opponent is bleeding)", p);
            }
        } else {
            if (skill_has_buff(p, "drift_evade_buff")) {
                skill_consume_buff(p, "drift_evade_buff", 99);
                skill_log("DRIFT: P%d lost evade buff (opponent stopped bleeding)", p);
            }
        }
    }
}

static void drift_update_focus(int drift_p) {
    int combo = s_drift_combo[drift_p];
    int old_level = s_drift_focus_level[drift_p];
    int new_level = 0;

    if (combo >= 15) {
        new_level = 3;
    } else if (combo >= 10) {
        new_level = 2;
    } else if (combo >= 5) {
        new_level = 1;
    } else {
        new_level = 0;
    }

    s_drift_focus_level[drift_p] = new_level;

    if (new_level != old_level) {
        // 清理旧图标
        skill_consume_buff(drift_p, "drift_focus_crit_rate", 99);
        skill_consume_buff(drift_p, "drift_focus_crit_dmg", 99);
        skill_consume_buff(drift_p, "drift_focus_bleed_boost", 99);

        if (new_level == 1) {
            skill_apply_buff_dur(drift_p, "drift_focus_crit_rate", -1.0f);
            skill_overlay("[%s] 5连击！进入集中状态 (+35%%暴击几率)！", drift_p == 0 ? "漂移" : "敌方漂移");
            skill_log("DRIFT: P%d reached 5 combo -> Focus Level 1 (+35%% crit rate)", drift_p);
        } else if (new_level == 2) {
            skill_apply_buff_dur(drift_p, "drift_focus_crit_rate", -1.0f);
            skill_apply_buff_dur(drift_p, "drift_focus_crit_dmg", -1.0f);
            skill_overlay("[%s] 10连击！进入中度集中 (+45%%暴击伤害)！", drift_p == 0 ? "漂移" : "敌方漂移");
            skill_log("DRIFT: P%d reached 10 combo -> Focus Level 2 (+45%% crit damage)", drift_p);
        } else if (new_level == 3) {
            skill_apply_buff_dur(drift_p, "drift_focus_crit_rate", -1.0f);
            skill_apply_buff_dur(drift_p, "drift_focus_crit_dmg", -1.0f);
            skill_apply_buff_dur(drift_p, "drift_focus_bleed_boost", -1.0f);
            skill_overlay("[%s] 15连击！进入高度集中 (流血时长+150%%)！", drift_p == 0 ? "漂移" : "敌方漂移");
            skill_log("DRIFT: P%d reached 15 combo -> Focus Level 3 (+150%% bleed duration)", drift_p);
        }
    }
}

static void drift_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // A) 漂移作为进攻方命中
    const char* atk_id = ctx->attacker_bot_id;
    if (atk_id && strstr(atk_id, "drift") != NULL) {
        if (!ctx->is_blocked) {
            // 重击命中且未达 5 击时直接获得 5 击进入集中
            if (ctx->is_heavy) {
                if (s_drift_combo[ap] < 5) {
                    s_drift_combo[ap] = 5;
                } else {
                    s_drift_combo[ap]++;
                }
            } else {
                s_drift_combo[ap]++;
            }
            drift_update_focus(ap);
        }

        // 击中时立即驱动一次规避状态同步
        drift_on_simulation_tick(0);
    }
}

// 漂移受创 (Hitreact): 连击中断，集中状态清零
static void drift_on_hitreact_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "drift") == NULL) return;

    if (s_drift_combo[player_index] > 0) {
        skill_log("DRIFT: P%d was struck, combo reset from %d to 0", player_index, s_drift_combo[player_index]);
        s_drift_combo[player_index] = 0;
        drift_update_focus(player_index);
    }
}

// 闪避检定: 漂移近战规避与集中压制对手规避
static int drift_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;

    int def_p = ctx->player_index;
    int ap = 1 - def_p;

    // 1. 漂移作为防御方: 对手处于流血状态时的近战规避
    if (ctx->bot_id && strstr(ctx->bot_id, "drift") != NULL && !ctx->is_ranged) {
        int opp_is_bleeding = drift_is_opponent_bleeding(def_p);
        if (opp_is_bleeding) {
            float evade_chance = 0.10f; // 基础 10%
            int focus_lvl = s_drift_focus_level[def_p];
            if (focus_lvl == 1) evade_chance = 0.15f;
            else if (focus_lvl == 2) evade_chance = 0.20f;
            else if (focus_lvl >= 3) evade_chance = 0.25f;

            float roll = skill_random_float();
            if (roll < evade_chance) {
                *out_evade = 1;
                skill_overlay("[%s] 剑意空蝉！近战规避！", def_p == 0 ? "漂移" : "敌方漂移");
                skill_log("DRIFT: P%d evaded melee attack against bleeding opponent (chance=%.2f, roll=%.2f)",
                          def_p, evade_chance, roll);
            } else {
                *out_evade = 0;
                skill_log("DRIFT: P%d melee evade MISSED against bleeding opponent (chance=%.2f, roll=%.2f)",
                          def_p, evade_chance, roll);
            }
            return 1; // 明确已裁决，杜绝回退到 hook.c 兜底
        } else {
            // 对手未处于流血状态，漂移无近战规避能力
            *out_evade = 0;
            return 1; // 明确已裁决，杜绝回退到 hook.c 兜底
        }
    }

    // 2. 漂移作为攻击方 (处于集中状态): 压制对手 85% 规避率
    const char* atk_id = skill_get_bot_id(ap);
    if (atk_id && strstr(atk_id, "drift") != NULL) {
        if (s_drift_focus_level[ap] >= 1) {
            ctx->modified_chance *= 0.15f; // 降低 85% 规避率 (剩余 15%)
            skill_log("DRIFT: P%d Focus suppressed opponent evade chance by 85%%", ap);
        }
    }

    return 0;
}

static void drift_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_drift_combo[player_index] = 0;
        s_drift_focus_level[player_index] = 0;
        skill_consume_buff(player_index, "drift_evade_buff", 99);
    }
}

BotSkillModule g_module_drift = {
    .bot_prefix = "drift",
    .on_hit_connected = drift_on_hit_connected,
    .on_buff_gated = NULL,
    .on_buff_applied = NULL,
    .on_evade_check = drift_on_evade_check,
    .on_test_roll = NULL,
    .on_power_gain_rate = NULL,
    .on_reflect_proj = NULL,
    .on_projectile_speed = NULL,
    .on_fight_reset = drift_on_fight_reset,
    .on_simulation_tick = drift_on_simulation_tick,
    .on_block_state = NULL,
    .on_dodge_enter = NULL,
    .on_opponent_block_state = NULL,
    .on_opponent_dodge_enter = NULL,
    .on_hitreact_enter = drift_on_hitreact_enter,
    .on_attack_start = NULL,
};
