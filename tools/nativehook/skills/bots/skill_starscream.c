#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static int starscream_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade || !ctx->bot_id || strstr(ctx->bot_id, "fte_stars") == NULL) return 0;
    if (!ctx->is_ranged && skill_is_heavy_attacking(1 - ctx->player_index)) {
        if (skill_random_float() < 0.20f) {
            *out_evade = 1;
            skill_apply_buff_dur(ctx->player_index, "starscream_evade_heavy_melee", 0.5f);
            skill_log("STARSCREAM: P%d evaded incoming heavy melee", ctx->player_index);
            return 1;
        }
    }
    return 0;
}

BotSkillModule g_module_starscream = {
    .bot_prefix      = "fte_stars",
    .display_name_zh = "红蜘蛛",
    .on_evade_check  = starscream_on_evade_check,
};
