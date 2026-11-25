#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static uint64_t s_bomb_detonate_ms[2] = {0, 0};
static int      s_bomb_attacker[2]    = {-1, -1};

static void chromia_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_bomb_detonate_ms[player_index] = 0;
        s_bomb_attacker[player_index]    = -1;
    }
}

static void chromia_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (s_bomb_detonate_ms[p] > 0 && now_ms >= s_bomb_detonate_ms[p]) {
            s_bomb_detonate_ms[p] = 0;
            int atk_p = s_bomb_attacker[p];
            s_bomb_attacker[p] = -1;
            if (atk_p >= 0 && atk_p < 2) {
                float dmg = skill_get_attack(atk_p);
                if (dmg > 0.0f) skill_deal_damage(p, dmg);
                skill_apply_buff(p, "chromia_bomb_direct_dmg");
                skill_apply_buff_dur(p, "chromia_bomb_stun", 2.5f);
                skill_stun_player(p, 2.5f);
                skill_log("CHROMIA: Acrolight Bomb detonated on P%d (dmg=%.1f + 2.5s stun)", p, dmg);
            }
        }
    }
}

static int chromia_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    if (skill_has_buff(ctx->player_index, "chromia_ranged_decel") ||
        skill_has_buff(ctx->player_index, "chromia_sp2_decel") ||
        skill_has_buff(ctx->player_index, "chromia_sp3_decel")) {
        *out_evade = 0;
        return 1;
    }
    return 0;
}

static void chromia_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 对手成功命中克劳莉娅时拆除炸弹
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "chromia") != NULL && !ctx->is_blocked) {
        if (s_bomb_detonate_ms[ap] > 0) {
            s_bomb_detonate_ms[ap] = 0;
            s_bomb_attacker[ap]    = -1;
            skill_consume_buff(ap, "chromia_acrolight_bomb", 1);
            skill_log("CHROMIA: Acrolight Bomb on P%d defused by hitting Chromia", ap);
        }
    }

    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "chromia") != NULL) {
        if (ctx->is_ranged && skill_random_float() < 0.60f) {
            skill_apply_buff_dur(tp, "chromia_ranged_decel", 3.2f);
        }

        if (ctx->special_index > 0 && ctx->is_last_hit) {
            skill_apply_buff_dur(ap, "chromia_sig_power_surge", 7.0f);
            skill_apply_buff_dur(ap, "chromia_sig_evade", 7.0f);
            skill_apply_buff_dur(tp, "chromia_acrolight_bomb", 5.0f);
            s_bomb_detonate_ms[tp] = skill_now_ms() + 5000;
            s_bomb_attacker[tp]    = ap;
            skill_log("CHROMIA: SP%d lastHit applied surge/evade + Acrolight Bomb on P%d",
                      ctx->special_index, tp);
        }
    }
}

BotSkillModule g_module_chromia = {
    .bot_prefix         = "chromia",
    .display_name_zh    = "克劳莉娅",
    .on_hit_connected   = chromia_on_hit_connected,
    .on_evade_check     = chromia_on_evade_check,
    .on_simulation_tick = chromia_on_simulation_tick,
    .on_fight_reset     = chromia_on_fight_reset,
};
