#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

static void blaster_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 1. 干扰 (被动): 普通远程命中或被防 80% 施加干扰
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "blaster") != NULL) {
        if (ctx->is_ranged && ctx->special_index == 0) {
            if (skill_random_float() < 0.80f) {
                skill_apply_buff_dur(tp, "blaster_interference", 10.0f);
            }
        }
    }

    // 2. 觉醒吸收护盾: 护盾状态下受远程/投射物打击时获得远程霸体并 40% 修复
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "blaster") != NULL) {
        int has_shield = skill_has_buff(tp, "blaster_block_shield") ||
                         skill_has_buff(tp, "blaster_sig_absorb_dr") ||
                         skill_has_buff(tp, "armor_up");
        if (has_shield && (ctx->is_ranged || ctx->special_index > 0)) {
            skill_set_unstoppable(tp, 500);
            skill_apply_buff_dur(tp, "blaster_sig_absorb_unstoppable", 0.5f);
            if (skill_random_float() < 0.40f) {
                float atk = skill_get_attack(ap);
                if (ctx->special_index > 0) {
                    skill_heal(tp, atk * 0.34f);
                    skill_apply_buff_dur(tp, "blaster_sig_repair_special", 0.5f);
                } else {
                    skill_heal(tp, atk * 0.17f);
                    skill_apply_buff_dur(tp, "blaster_sig_repair_basic", 0.5f);
                }
            }
        }
    }
}

BotSkillModule g_module_blaster = {
    .bot_prefix       = "blaster",
    .display_name_zh  = "录音机",
    .on_hit_connected = blaster_on_hit_connected,
};
