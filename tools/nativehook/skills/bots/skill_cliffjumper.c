#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void cliffjumper_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "cliffjumper") == NULL) return;

    if (action_type == 16 || action_type == 32 || action_type == 64 ||
        action_type == 0x201 || action_type == 0x202 || action_type == 0x203) {
        if (!skill_has_buff(player_index, "dmg_bleed") &&
            !skill_has_buff(player_index, "dmg_burn") &&
            !skill_has_buff(player_index, "dmg_shock") &&
            !skill_has_buff(player_index, "armor_break")) {
            skill_apply_buff_dur(player_index, "cliffjumper_clean_special_boost", 6.0f);
        }
    }
}

static int cliffjumper_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    (void)out_res;
    if (!ctx || !ctx->owner_bot_id || strstr(ctx->owner_bot_id, "cliffjumper") == NULL) return 0;
    if (ctx->current_special_index == 3 && ctx->current_hit_is_last && ctx->p_chance) {
        *ctx->p_chance += 0.60f;
    }
    return 0;
}

static void cliffjumper_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "cliffjumper") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    if (ctx->is_ranged && ctx->special_index == 0) {
        skill_apply_buff_dur(tp, "cliffjumper_ranged_glass_gas", 8.0f);
    }

    if (ctx->special_index == 2 && ctx->is_last_hit) {
        int gas = skill_count_buffs(tp, "glass_gas") + skill_count_buffs(tp, "cliffjumper_ranged_glass_gas");
        if (gas >= 10) {
            if (ctx->is_blocked) {
                ctx->is_blocked = false;
                ctx->modified_damage *= 2.0f;
            }
            skill_apply_buff_dur(ap, "cliffjumper_sp2_unblockable", 1.5f);
            skill_log("CLIFFJUMPER: SP2 lastHit Unblockable triggered vs %d glass gas stacks", gas);
        }
    } else if (ctx->special_index == 3 && ctx->is_last_hit) {
        skill_apply_buff_dur(ap, "cliffjumper_sp3_last_hit_crit_rate", 2.0f);
    }
}

BotSkillModule g_module_cliffjumper = {
    .bot_prefix       = "cliffjumper",
    .display_name_zh  = "飞过山",
    .on_hit_connected = cliffjumper_on_hit_connected,
    .on_attack_start  = cliffjumper_on_attack_start,
    .on_test_roll     = cliffjumper_on_test_roll,
};
