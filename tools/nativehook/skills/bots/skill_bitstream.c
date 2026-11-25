#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static int s_firewall_shields[2] = {4, 4};
static int s_opp_last_bars[2] = {0, 0};

static void bitstream_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_firewall_shields[player_index] = 4;
        s_opp_last_bars[player_index] = 0;
    }
}

static void bitstream_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "bitstream") == NULL) continue;
        int opp = 1 - p;
        float mana = skill_get_mana(opp);
        int bars = (mana >= 2.999f) ? 3 : (mana >= 1.999f) ? 2 : (mana >= 0.999f) ? 1 : 0;
        if (bars > s_opp_last_bars[p]) {
            if (skill_random_float() < 0.60f) {
                skill_add_mana(opp, -0.50f);
                skill_apply_buff_dur(opp, "bitstream_sig_refund_lock", 4.0f);
                skill_log("BITSTREAM: Zero-day refund lock triggered on P%d", opp);
            }
        }
        s_opp_last_bars[p] = bars;
    }
}

static void bitstream_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "bitstream") != NULL) {
        int tp = ctx->target_player_index;
        int ap = ctx->attacker_player_index;
        if (s_firewall_shields[tp] > 0) {
            float cap = skill_get_attack(ap) * 0.75f;
            if (cap > 0.0f && ctx->modified_damage > cap) {
                ctx->modified_damage = cap;
            }
            s_firewall_shields[tp]--;
            skill_consume_buff(tp, "bitstream_firewall_shield", 1);
            if (s_firewall_shields[tp] == 0) {
                skill_apply_buff_dur(ap, "bitstream_shield_backlash_shock", 4.0f);
                skill_log("BITSTREAM: Firewall shields exhausted on P%d -> shock backlash on P%d", tp, ap);
            }
        }
    }
}

BotSkillModule g_module_bitstream = {
    .bot_prefix         = "bitstream",
    .display_name_zh    = "比特流",
    .on_hit_connected   = bitstream_on_hit_connected,
    .on_simulation_tick = bitstream_on_simulation_tick,
    .on_fight_reset     = bitstream_on_fight_reset,
};
