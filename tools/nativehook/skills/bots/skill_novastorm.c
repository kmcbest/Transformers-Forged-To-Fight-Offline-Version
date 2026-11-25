#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static int s_novastorm_combo[2] = {0, 0};

static void novastorm_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_novastorm_combo[player_index] = 0;
    }
}

static void novastorm_on_hitreact_enter(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_novastorm_combo[player_index] = 0;
    }
}

static void novastorm_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "novastorm") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    if (!ctx->is_blocked) {
        s_novastorm_combo[ap]++;
        if (s_novastorm_combo[ap] % 5 == 0) {
            skill_apply_buff_dur(ap, "novastorm_combo_crit_rate", 6.0f);
            skill_apply_buff_dur(ap, "novastorm_combo_crit_dmg", 6.0f);
            skill_log("NOVASTORM: P%d combo=%d -> granted crit rate & crit dmg", ap, s_novastorm_combo[ap]);
        }
    }

    if (ctx->special_index > 0 && ctx->is_crit && skill_is_burning(tp)) {
        float dmg = skill_get_attack(ap) * 0.45f;
        skill_deal_damage(tp, dmg);
        skill_apply_buff(tp, "novastorm_sig_detonate");
        skill_log("NOVASTORM: SP%d crit detonated burn on P%d for %.1f dmg", ctx->special_index, tp, dmg);
    }
}

BotSkillModule g_module_novastorm = {
    .bot_prefix        = "novastorm",
    .display_name_zh   = "新星风",
    .on_hit_connected  = novastorm_on_hit_connected,
    .on_hitreact_enter = novastorm_on_hitreact_enter,
    .on_fight_reset    = novastorm_on_fight_reset,
};
