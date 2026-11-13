#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 恐龙勇士 (Dinobot BW) 底层战斗技能模块
// Bot ID: dinobot_bw_kabam
// 职业: 战术系 (Tactician) | 阵营: 巨无霸 (Maximal)
// ===========================================================================
// 1. [被动 - 格挡反伤] (Blocking Damage)
//    - 格挡对方近战攻击时，60% 几率反向造成对手攻击力 10% 的伤害。
//    - 格挡对方前冲攻击时，100% 几率反向造成对手攻击力 20% 的伤害。
// 2. [被动 - 即时格挡精通] (Block Proficiency)
//    - 即时格挡 (held_ms <= 400ms) 时增加 50% 格挡精通，降低格挡伤害 50%。
// 3. [觉醒 - 适者生存] (Survival of the Fittest)
//    - 对手破甲状态下格挡恐龙勇士时，穿透格挡伤害提高 20%。
//    - 恐龙勇士攻击对手时，有 20% 的几率触发破防 (取消格挡判定)。
// ===========================================================================

#define DINOBOT_PERFECT_BLOCK_MS 400

static void dinobot_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    uint64_t now_ms = skill_now_ms();

    // -----------------------------------------------------------------------
    // A) 恐龙勇士作为格挡防守方 (受击): 格挡精通与格挡反伤
    // -----------------------------------------------------------------------
    const char* def_id = ctx->target_bot_id;
    if (def_id && strstr(def_id, "dinobot") != NULL && ctx->is_blocked) {
        uint64_t block_start = skill_get_block_enter_ms(tp);
        uint64_t held_ms = (block_start > 0 && now_ms >= block_start) ? (now_ms - block_start) : 999999;

        // 1. 即时格挡精通：400ms 内即时格挡伤害减免 50%
        if (held_ms <= DINOBOT_PERFECT_BLOCK_MS) {
            ctx->modified_damage *= 0.50f;
            skill_overlay("[%s] 适时格挡！格挡伤害降低50%%！", tp == 0 ? "恐龙勇士" : "敌方恐龙勇士");
            skill_log("DINOBOT: P%d well-timed block (held=%ld ms), damage reduced by 50%%", tp, (long)held_ms);
        }

        // 2. 格挡反伤
        // 前冲攻击判定 (action_type == 32 或 2, 或距离极速接近)
        int is_dash = (ctx->action_type == 32 || ctx->action_type == 2);
        if (is_dash) {
            // 格挡前冲攻击：100% 概率反弹 20% 对手攻击力
            float opp_atk = skill_get_attack(ap);
            if (opp_atk <= 0.0f) opp_atk = 3000.0f;
            float reflect_dmg = opp_atk * 0.20f;
            skill_deal_damage(ap, reflect_dmg);
            skill_overlay("[%s] 完美格挡前冲！反弹20%%伤害！", tp == 0 ? "恐龙勇士" : "敌方恐龙勇士");
            skill_log("DINOBOT: P%d blocked Dash attack from P%d, reflected 20%% damage (%.1f)", tp, ap, reflect_dmg);
        } else if (!ctx->is_ranged) {
            // 格挡常规近战攻击：60% 概率反弹 10% 对手攻击力
            float roll = skill_random_float();
            if (roll < 0.60f) {
                float opp_atk = skill_get_attack(ap);
                if (opp_atk <= 0.0f) opp_atk = 3000.0f;
                float reflect_dmg = opp_atk * 0.10f;
                skill_deal_damage(ap, reflect_dmg);
                skill_overlay("[%s] 格挡反伤！反弹10%%近战伤害！", tp == 0 ? "恐龙勇士" : "敌方恐龙勇士");
                skill_log("DINOBOT: P%d blocked Melee attack from P%d (roll=%.2f < 0.60), reflected 10%% damage (%.1f)",
                          tp, ap, roll, reflect_dmg);
            }
        }
    }

    // -----------------------------------------------------------------------
    // B) 恐龙勇士作为进攻方: 适者生存 (破甲增伤与不可防御)
    // -----------------------------------------------------------------------
    const char* atk_id = ctx->attacker_bot_id;
    if (atk_id && strstr(atk_id, "dinobot") != NULL) {
        int opp_has_armor_break = skill_has_buff(tp, "armor_break") ||
                                  skill_has_buff(tp, "dinobot_dash_block_break") ||
                                  skill_has_buff(tp, "dinobot_sp1_armor_break");
        if (opp_has_armor_break) {
            // 对手在破甲状态下格挡恐龙勇士的任何攻击，格挡穿透伤害提高 20%
            if (ctx->is_blocked) {
                ctx->modified_damage *= 1.20f;
                skill_log("DINOBOT: Opponent P%d blocked under Armor Break, pierced damage boosted by 20%%", tp);
            }
            // 20% 几率破防 (取消格挡判定)
            float roll = skill_random_float();
            if (roll < 0.20f && ctx->is_blocked) {
                ctx->is_blocked = false;
                skill_overlay("[%s] 适者生存！粉碎对手防御！", ap == 0 ? "恐龙勇士" : "敌方恐龙勇士");
                skill_log("DINOBOT: Survival of the Fittest triggered unblockable attack! (roll=%.2f < 0.20)", roll);
            }
        }
    }
}

BotSkillModule g_module_dinobot = {
    .bot_prefix = "dinobot",
    .on_hit_connected = dinobot_on_hit_connected,
    .on_buff_gated = NULL,
    .on_buff_applied = NULL,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_power_gain_rate = NULL,
    .on_reflect_proj = NULL,
    .on_projectile_speed = NULL,
    .on_fight_reset = NULL,
    .on_simulation_tick = NULL,
    .on_block_state = NULL,
    .on_dodge_enter = NULL,
    .on_opponent_block_state = NULL,
    .on_opponent_dodge_enter = NULL,
    .on_hitreact_enter = NULL,
    .on_attack_start = NULL,
};
