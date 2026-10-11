#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// 警车 (Prowl) 技能模块
// - SP2 远程增益 (prowl_s2_ranged_boost): 获得 6.0s 远程伤害+50%, 远程射速+50%

static void prowl_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return;

    if (strstr(ctx->modifier_id, "prowl_s2_ranged_boost") != NULL) {
        skill_set_ranged_boost(0, 6000, 0.50f, 0.50f);
        skill_log("RANGED_BOOST_ACTIVATED: Prowl SP2 (dmg=+50%%, spd=+50%%, dur=6.0s)");
    }
}

static void prowl_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_prowl = {
    .bot_prefix = "prowl",
    .on_hit_connected = NULL,
    .on_buff_gated = NULL,
    .on_buff_applied = prowl_on_buff_applied,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_fight_reset = prowl_on_fight_reset
};
