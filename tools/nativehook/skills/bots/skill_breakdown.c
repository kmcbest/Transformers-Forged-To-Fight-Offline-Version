#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static uint64_t s_paranoia_evade_cd_ms[2] = {0, 0};
static uint64_t s_paranoia_crit_cd_ms[2]  = {0, 0};
static uint64_t s_opp_heavy_start_ms[2]   = {0, 0};

static void breakdown_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_paranoia_evade_cd_ms[player_index] = 0;
        s_paranoia_crit_cd_ms[player_index]  = 0;
        s_opp_heavy_start_ms[player_index]   = 0;
    }
}

static void breakdown_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "breakdown") == NULL) continue;
        float opp_hp = skill_get_hp_ratio(1 - p);
        if (opp_hp <= 0.0f) continue;

        if (opp_hp > 0.50f) {
            if (!skill_has_buff(p, "breakdown_paranoia_evade") &&
                now_ms >= s_paranoia_evade_cd_ms[p]) {
                skill_apply_buff(p, "breakdown_paranoia_evade");
            }
        } else {
            if (!skill_has_buff(p, "breakdown_paranoia_crit") &&
                now_ms >= s_paranoia_crit_cd_ms[p]) {
                skill_apply_buff(p, "breakdown_paranoia_crit");
            }
        }
    }
}

static void breakdown_on_attack_start(int attacker_index, int action_type) {
    if (attacker_index < 0 || attacker_index >= 2) return;
    int opp = 1 - attacker_index;
    const char* opp_bid = skill_get_bot_id(opp);
    if (opp_bid && strstr(opp_bid, "breakdown") != NULL) {
        if (action_type == 4 || action_type == 0x100) {
            s_opp_heavy_start_ms[opp] = skill_now_ms();
        }
    }
}

static void breakdown_on_dodge_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "breakdown") == NULL) return;
    uint64_t now_ms = skill_now_ms();
    if (s_opp_heavy_start_ms[player_index] > 0 && now_ms - s_opp_heavy_start_ms[player_index] <= 800) {
        skill_apply_buff(player_index, "breakdown_shield_break_buff");
    }
}

static int breakdown_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade || !ctx->bot_id || strstr(ctx->bot_id, "breakdown") == NULL) return 0;
    int p = ctx->player_index;
    if (!ctx->is_ranged && skill_has_buff(p, "breakdown_paranoia_evade")) {
        if (skill_random_float() < 0.40f) {
            *out_evade = 1;
            skill_consume_buff(p, "breakdown_paranoia_evade", 1);
            s_paranoia_evade_cd_ms[p] = skill_now_ms() + 5000;
            if (skill_is_heavy_attacking(1 - p)) {
                skill_apply_buff(p, "breakdown_shield_break_buff");
            }
            return 1;
        }
    }
    return 0;
}

static void breakdown_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "breakdown") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 1. 护盾崩解消耗 (近战命中清除对手护盾并追加 50% ATK 直接伤害)
    if (!ctx->is_ranged && ctx->special_index == 0 && skill_has_buff(ap, "breakdown_shield_break_buff")) {
        skill_consume_buff(tp, "armor_up", 10);
        skill_consume_buff(tp, "shield", 10);
        skill_apply_buff(tp, "breakdown_shield_break_nullify");
        skill_deal_damage(tp, skill_get_attack(ap) * 0.50f);
        skill_apply_buff(tp, "breakdown_shield_break_dmg");
        skill_consume_buff(ap, "breakdown_shield_break_buff", 1);
    }

    // 2. 神经质暴击消耗
    if (ctx->is_crit && skill_has_buff(ap, "breakdown_paranoia_crit")) {
        skill_consume_buff(ap, "breakdown_paranoia_crit", 1);
        s_paranoia_crit_cd_ms[ap] = skill_now_ms() + 5000;
    }

    // 3. L4 / M2 被格挡 75% 获得 4s 近战规避
    if (ctx->is_blocked && !ctx->is_ranged && ctx->special_index == 0 &&
        (ctx->hit_index == 1 || ctx->hit_index >= 3)) {
        if (skill_random_float() < 0.75f) {
            skill_apply_buff_dur(ap, "breakdown_block_evade", 4.0f);
        }
    }

    // 4. SP1 最后一击
    if (ctx->special_index == 1 && ctx->is_last_hit) {
        if (skill_random_float() < 0.50f) {
            skill_apply_buff_dur(tp, "breakdown_sp1_power_leak", 5.0f);
        }
        if (skill_random_float() < 0.35f) {
            skill_apply_buff_dur(ap, "breakdown_sp1_crit_rate", 8.0f);
        }
    }

    // 5. SP2 最后一击
    if (ctx->special_index == 2 && ctx->is_last_hit) {
        skill_apply_buff_dur(tp, "breakdown_sp2_burn", 4.0f);
        skill_apply_buff_dur(tp, "breakdown_sp2_certainty", 30.0f);
    }
}

BotSkillModule g_module_breakdown = {
    .bot_prefix         = "breakdown",
    .display_name_zh    = "死火",
    .on_hit_connected   = breakdown_on_hit_connected,
    .on_attack_start    = breakdown_on_attack_start,
    .on_dodge_enter     = breakdown_on_dodge_enter,
    .on_evade_check     = breakdown_on_evade_check,
    .on_simulation_tick = breakdown_on_simulation_tick,
    .on_fight_reset     = breakdown_on_fight_reset,
};
