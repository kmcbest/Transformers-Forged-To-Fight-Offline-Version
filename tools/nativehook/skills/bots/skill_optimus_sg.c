#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void optimus_sg_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    int tp = ctx->target_player_index;
    const char* bid = skill_get_bot_id(tp);
    if (!bid || strstr(bid, "optimusprime_sg") == NULL) return;

    if (strstr(ctx->modifier_id, "bleed") != NULL ||
        strstr(ctx->modifier_id, "burn") != NULL ||
        strstr(ctx->modifier_id, "shock") != NULL ||
        strstr(ctx->modifier_id, "acid") != NULL) {
        skill_apply_buff_dur(tp, "optimusprime_sg_struggle_attack_buff", 6.0f);
    }
}

static void optimus_sg_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "optimusprime_sg") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    int has_bleed = skill_has_buff(ap, "bleed");
    int has_burn  = skill_has_buff(ap, "burn");
    int has_shock = skill_has_buff(ap, "shock");
    int has_acid  = skill_has_buff(ap, "acid");

    if (has_bleed || has_burn || has_shock || has_acid) {
        if (!skill_has_buff(ap, "optimusprime_sg_struggle_attack_buff")) {
            skill_apply_buff_dur(ap, "optimusprime_sg_struggle_attack_buff", 6.0f);
        }
    }

    if (has_bleed && skill_random_float() < 0.10f) {
        skill_apply_buff_dur(tp, "optimusprime_sg_cycle_burn", 3.0f);
    }
    if (has_burn && skill_random_float() < 0.10f) {
        skill_apply_buff_dur(tp, "optimusprime_sg_cycle_shock", 3.0f);
    }
    if (has_shock && skill_random_float() < 0.10f) {
        skill_apply_buff_dur(tp, "optimusprime_sg_cycle_acid", 3.0f);
    }
    if (has_acid && skill_random_float() < 0.10f) {
        skill_apply_buff_dur(tp, "optimusprime_sg_cycle_bleed", 3.0f);
    }
}

BotSkillModule g_module_optimus_sg = {
    .bot_prefix       = "optimusprime_sg",
    .display_name_zh  = "倾天柱",
    .on_hit_connected = optimus_sg_on_hit_connected,
    .on_buff_applied  = optimus_sg_on_buff_applied,
};
