#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void ratchet_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "ratchet") == NULL) return;
    int ap = ctx->attacker_player_index;
    if (ctx->is_heavy && ctx->is_last_hit && skill_get_hp_ratio(ap) < 0.50f) {
        skill_apply_buff_dur(ap, "ratchet_self_diagnosis", 10.0f);
        skill_apply_buff_dur(ap, "ratchet_self_diag_pwr", 10.0f);
        skill_heal(ap, skill_get_max_hp(ap) * 0.10f);
        skill_add_mana(ap, 0.60f);
        skill_log("RATCHET: P%d Heavy lastHit below 50%% HP triggered Self Diagnosis", ap);
    }
}

BotSkillModule g_module_ratchet = {
    .bot_prefix       = "ratchet",
    .display_name_zh  = "救护车",
    .on_hit_connected = ratchet_on_hit_connected,
};
