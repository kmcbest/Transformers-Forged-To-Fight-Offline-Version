#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 碎骨魔 (Bonecrusher ROTF) 技能模块
// Bot ID: bonecrusher_cin_rotf
// 职业: 格斗系 (Warrior)
// ===========================================================================
// 1. [被动 - 受到近战暴击流血 (Bleed when Struck by Crit)]
//    - 官方描述: "受到近战暴击时，90%的几率给予对方施加流血，在7秒内造成攻击力89.6%伤害，可叠加。"
// 2. [被动 - 重击流血 (Heavy Attacks Bleed)]
//    - 官方描述: "重击命中时，70%的几率触发流血，造成攻击力45%伤害，持续5.6秒。"
// 3. [SP1 - 蝎尾针 (Scorpion Sting)]
//    - 官方描述: "每一击90%的概率触发流血，造成攻击力115%的伤害，持续2秒。"
// 4. [SP2 - 特殊技 2]
//    - 官方描述: "每一击71%的概率触发流血，造成攻击力72%的伤害，持续7秒。"
// 5. [SP3 - 仇恨风暴 (Abhornado)]
//    - 官方描述: "每一击45%的概率触发流血，造成攻击力198%的伤害，持续18秒。"
// ===========================================================================

static void bonecrusher_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // 1. 碎骨魔作为受击方：受到近战暴击时 90% 概率反噬对手流血
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "bonecrusher") != NULL) {
        if (ctx->is_crit && !ctx->is_ranged) {
            float roll = skill_random_float();
            float chance = 0.90f;
            if (roll < chance) {
                skill_log("ROLL_DICE_PASS: [碎骨魔] 被动流血 PASS! (Roll: %.1f%% < %.1f%%, mod=bonecrusher_struck_crit_bleed)",
                          roll * 100.0f, chance * 100.0f);
                skill_overlay("[碎骨魔] 受暴击触发流血反噬！(90%% PASS!)");
                skill_apply_buff_dur(ctx->attacker_player_index, "bonecrusher_struck_crit_bleed", 7.0f);
            } else {
                skill_log("ROLL_DICE_FAIL: [碎骨魔] 被动流血 FAIL (Roll: %.1f%% >= %.1f%%, mod=bonecrusher_struck_crit_bleed)",
                          roll * 100.0f, chance * 100.0f);
                skill_overlay("[碎骨魔] 被动流血 检定未通过 (Roll: %.1f%% >= %.1f%%)",
                              roll * 100.0f, chance * 100.0f);
            }
        }
    }

    // 2. 碎骨魔作为攻击方：重击与特技触发流血
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "bonecrusher") != NULL) {
        int tp = ctx->target_player_index;

        // 2.1 重击命中：70% 几率流血 5.6秒
        if (ctx->is_heavy) {
            float roll = skill_random_float();
            float chance = 0.70f;
            if (roll < chance) {
                skill_log("ROLL_DICE_PASS: [碎骨魔] 重击流血 PASS! (Roll: %.1f%% < %.1f%%, mod=bonecrusher_heavy_bleed)",
                          roll * 100.0f, chance * 100.0f);
                skill_overlay("[碎骨魔] 重击触发流血！(70%% PASS!)");
                skill_apply_buff_dur(tp, "bonecrusher_heavy_bleed", 5.6f);
            } else {
                skill_log("ROLL_DICE_FAIL: [碎骨魔] 重击流血 FAIL (Roll: %.1f%% >= %.1f%%, mod=bonecrusher_heavy_bleed)",
                          roll * 100.0f, chance * 100.0f);
                skill_overlay("[碎骨魔] 重击流血 检定未通过 (Roll: %.1f%% >= %.1f%%)",
                              roll * 100.0f, chance * 100.0f);
            }
        }
        // 2.2 SP1: 90% 几率流血 2秒
        else if (ctx->special_index == 1) {
            float roll = skill_random_float();
            float chance = 0.90f;
            if (roll < chance) {
                skill_log("ROLL_DICE_PASS: [碎骨魔] SP1 蝎尾流血 PASS! (Roll: %.1f%% < %.1f%%, mod=bonecrusher_sp1_bleed)",
                          roll * 100.0f, chance * 100.0f);
                skill_overlay("[碎骨魔] SP1 触发蝎尾流血！(90%% PASS!)");
                skill_apply_buff_dur(tp, "bonecrusher_sp1_bleed", 2.0f);
            } else {
                skill_log("ROLL_DICE_FAIL: [碎骨魔] SP1 蝎尾流血 FAIL (Roll: %.1f%% >= %.1f%%, mod=bonecrusher_sp1_bleed)",
                          roll * 100.0f, chance * 100.0f);
            }
        }
        // 2.3 SP2: 71% 几率流血 7秒
        else if (ctx->special_index == 2) {
            float roll = skill_random_float();
            float chance = 0.71f;
            if (roll < chance) {
                skill_log("ROLL_DICE_PASS: [碎骨魔] SP2 流血 PASS! (Roll: %.1f%% < %.1f%%, mod=bonecrusher_sp2_bleed)",
                          roll * 100.0f, chance * 100.0f);
                skill_overlay("[碎骨魔] SP2 触发强效流血！(71%% PASS!)");
                skill_apply_buff_dur(tp, "bonecrusher_sp2_bleed", 7.0f);
            } else {
                skill_log("ROLL_DICE_FAIL: [碎骨魔] SP2 流血 FAIL (Roll: %.1f%% >= %.1f%%, mod=bonecrusher_sp2_bleed)",
                          roll * 100.0f, chance * 100.0f);
            }
        }
        // 2.4 SP3: 45% 几率长效流血 18秒
        else if (ctx->special_index == 3) {
            float roll = skill_random_float();
            float chance = 0.45f;
            if (roll < chance) {
                skill_log("ROLL_DICE_PASS: [碎骨魔] SP3 仇恨风暴流血 PASS! (Roll: %.1f%% < %.1f%%, mod=bonecrusher_sp3_bleed)",
                          roll * 100.0f, chance * 100.0f);
                skill_overlay("[碎骨魔] SP3 触发仇恨风暴长效流血！(45%% PASS!)");
                skill_apply_buff_dur(tp, "bonecrusher_sp3_bleed", 18.0f);
            } else {
                skill_log("ROLL_DICE_FAIL: [碎骨魔] SP3 仇恨风暴流血 FAIL (Roll: %.1f%% >= 45.0%%, mod=bonecrusher_sp3_bleed)",
                          roll * 100.0f, chance * 100.0f);
            }
        }
    }
}

static void bonecrusher_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_bonecrusher = {
    .bot_prefix       = "bonecrusher",
    .on_hit_connected = bonecrusher_on_hit_connected,
    .on_buff_gated    = NULL,
    .on_buff_applied  = NULL,
    .on_evade_check   = NULL,
    .on_test_roll     = NULL,
    .on_fight_reset   = bonecrusher_on_fight_reset,
};
