#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void rodimus_try_dash_purify(int p) {
    const char* bid = skill_get_bot_id(p);
    if (!bid || strstr(bid, "rodimus") == NULL) return;
    if (skill_random_float() < 0.70f) {
        const char* debuffs[] = {"dmg_bleed", "dmg_burn", "dmg_shock", "armor_break", "power_leak", "power_lock"};
        for (int i = 0; i < 6; i++) {
            if (skill_has_buff(p, debuffs[i])) {
                skill_consume_buff(p, debuffs[i], 1);
                skill_apply_buff_dur(p, "rodimus_dash_purify", 0.5f);
                skill_overlay("[补天士] 净化！");
                skill_log("RODIMUS: P%d purified debuff %s on dash", p, debuffs[i]);
                break;
            }
        }
    }
}

static void rodimus_on_attack_start(int player_index, int action_type) {
    if (action_type == 2 || action_type == 32) {
        rodimus_try_dash_purify(player_index);
    }
}

static void rodimus_on_dodge_enter(int player_index) {
    rodimus_try_dash_purify(player_index);
}

BotSkillModule g_module_rodimus = {
    .bot_prefix      = "rodimus",
    .display_name_zh = "补天士",
    .on_attack_start = rodimus_on_attack_start,
    .on_dodge_enter  = rodimus_on_dodge_enter,
};
