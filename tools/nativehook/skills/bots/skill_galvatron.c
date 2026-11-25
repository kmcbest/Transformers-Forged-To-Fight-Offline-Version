#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static uint64_t s_unicron_last_cd_ms[2] = {0, 0};

static void galvatron_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_unicron_last_cd_ms[player_index] = 0;
    }
}

static void galvatron_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "galvatron") == NULL) continue;
        int charges = skill_count_buffs(p, "dark_energy_charge");
        if (charges >= 30 && now_ms >= s_unicron_last_cd_ms[p]) {
            s_unicron_last_cd_ms[p] = now_ms + 10000;
            skill_set_unstoppable(p, 6000);
            skill_apply_buff_dur(p, "galvatron_unicron_unstoppable", 6.0f);
            skill_apply_buff_dur(p, "galvatron_unicron_power", 6.0f);
            skill_add_mana(p, 0.90f);
            skill_log("GALVATRON: P%d full dark energy triggered Unicron's Will", p);
        }
    }
}

static int galvatron_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    (void)out_res;
    if (!ctx || !ctx->owner_bot_id || strstr(ctx->owner_bot_id, "galvatron") == NULL) return 0;
    if (!ctx->is_ranged && ctx->current_special_index == 0 && !ctx->is_heavy &&
        (ctx->last_hit_index == 1 || ctx->last_hit_index >= 3) && ctx->p_chance) {
        *ctx->p_chance += 0.50f;
    }
    return 0;
}

static void galvatron_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "galvatron") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    int charges = skill_count_buffs(ap, "dark_energy_charge");

    if (ctx->is_ranged && charges > 0) {
        ctx->modified_damage *= (1.0f + 0.05f * (float)charges);
        skill_apply_buff_dur(ap, "galvatron_dark_ranged_boost", 0.5f);
    }

    if (!ctx->is_ranged && ctx->special_index == 0 && !ctx->is_heavy &&
        (ctx->hit_index == 1 || ctx->hit_index >= 3)) {
        skill_apply_buff_dur(ap, "galvatron_combo_crit_rate", 0.5f);
    }

    if (ctx->special_index == 1 && ctx->is_last_hit) {
        float stun_chance = 0.60f + 0.01f * (float)charges;
        if (stun_chance > 1.0f) stun_chance = 1.0f;
        if (skill_random_float() < stun_chance) {
            skill_apply_buff_dur(tp, "galvatron_sp1_stun", 3.0f);
            skill_stun_player(tp, 3.0f);
        }
    } else if (ctx->special_index == 2 && ctx->is_last_hit) {
        if (skill_random_float() < 0.60f || charges > 0) {
            skill_deal_damage(tp, skill_get_attack(ap) * 1.40f);
            skill_apply_buff_dur(tp, "galvatron_sp2_dark_burn", 0.5f);
            skill_consume_buff(ap, "dark_energy_charge", 99);
        }
    } else if (ctx->special_index == 3 && ctx->is_last_hit) {
        skill_deal_damage(tp, skill_get_attack(ap) * 1.40f);
        skill_apply_buff_dur(tp, "galvatron_sp3_dark_burn", 0.5f);
        skill_consume_buff(ap, "dark_energy_charge", 99);
    }
}

BotSkillModule g_module_galvatron = {
    .bot_prefix         = "galvatron",
    .display_name_zh    = "惊破天",
    .on_hit_connected   = galvatron_on_hit_connected,
    .on_test_roll       = galvatron_on_test_roll,
    .on_simulation_tick = galvatron_on_simulation_tick,
    .on_fight_reset     = galvatron_on_fight_reset,
};
