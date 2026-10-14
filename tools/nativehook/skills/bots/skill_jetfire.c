#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 天火 (Jetfire GS Leader 2014) 技能模块
// Bot ID: jetfire_gs_leader2014
// ===========================================================================
// 1. [2656] 被动：招架护盾 (Parry Shield)
//    - 在最接近状态下对普通远程攻击和远程重击进行格挡会激活招架护盾，
//      将该远程攻击以100%的原始攻击力反弹回去。
//    - 在最接近状态下对普通近战攻击进行格挡会激活招架护盾，
//      本次格挡不产生防御伤害，并且对手会眩晕1秒。
//    - 连续射击特性：敌人连开三枪时，招架一次可以反弹这全部三枪 (持续反弹护盾窗口 1.2 秒)。
//    - 护盾视觉：出护盾的时候有一个专门的光圈与 HUD 提示。
// 2. [2657] 被动：能量充能 (Energy Charge)
//    - 每次成功招架，获得一个能量充能，最多10层 (紫色图标，无倒计时)。
//    - 每层能量充能提升能量功率(Power Rate) 5% (满层10层提升50%)。
// ===========================================================================

#define JETFIRE_PARRY_WINDOW_MS     380   // 格挡起手至受击的完美招架判定窗口 (毫秒)
#define JETFIRE_SHIELD_DURATION_MS  1200  // 招架护盾持续反弹窗口 (毫秒，覆盖连射)

static int      s_jetfire_energy_charges[2] = {0, 0};
static uint64_t s_jetfire_shield_expire_ms[2] = {0, 0};

static void jetfire_add_energy_charge(int tp) {
    if (tp < 0 || tp >= 2) return;
    if (s_jetfire_energy_charges[tp] < 10) {
        s_jetfire_energy_charges[tp]++;
        skill_apply_buff(tp, "jetfire_energy_charge");
        skill_log("JETFIRE: Gained Energy Charge on P%d! Now %d/10 stacks (+%d%% Power Rate)",
                  tp, s_jetfire_energy_charges[tp], s_jetfire_energy_charges[tp] * 5);
    }
}

static int jetfire_on_reflect_proj(int player_index, float* out_reflect_mod) {
    if (player_index < 0 || player_index >= 2 || !out_reflect_mod) return 0;
    uint64_t now_ms = skill_now_ms();
    uint64_t block_start = skill_get_block_enter_ms(player_index);
    uint64_t held_ms = (block_start > 0 && now_ms >= block_start) ? (now_ms - block_start) : 999999;

    bool is_fresh_parry = (block_start > 0 && held_ms <= JETFIRE_PARRY_WINDOW_MS);
    bool is_shield_active = (now_ms <= s_jetfire_shield_expire_ms[player_index]);

    if (is_fresh_parry || is_shield_active) {
        if (!is_shield_active) {
            s_jetfire_shield_expire_ms[player_index] = now_ms + JETFIRE_SHIELD_DURATION_MS;
            jetfire_add_energy_charge(player_index);
            skill_overlay("[%s] 招架护盾展开！反弹远程攻击！能量充能 (%d/10层，能量功率 +%d%%)",
                          player_index == 0 ? "天火" : "敌方天火",
                          s_jetfire_energy_charges[player_index],
                          s_jetfire_energy_charges[player_index] * 5);
        }
        skill_log("JETFIRE: Projectile reflected on P%d! held_ms=%llu, charges=%d",
                  player_index, (unsigned long long)held_ms, s_jetfire_energy_charges[player_index]);
        *out_reflect_mod = 1.0f; // 原生引擎 100% 原始攻击力反弹
        return 1;
    }
    return 0;
}

static void jetfire_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 天火作为受击/防御方 (Defender):
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "jetfire") != NULL) {
        int tp = ctx->target_player_index;
        int ap = ctx->attacker_player_index;

        if (ctx->is_blocked) {
            uint64_t block_start = skill_get_block_enter_ms(tp);
            uint64_t held_ms = (block_start > 0 && now_ms >= block_start) ? (now_ms - block_start) : 999999;
            bool is_fresh_parry = (held_ms <= JETFIRE_PARRY_WINDOW_MS);
            bool is_shield_active = (now_ms <= s_jetfire_shield_expire_ms[tp]);

            // 分支 A: 普通近战攻击 (Basic Melee Hits) -> 完美招架完全免伤、击晕对手 1 秒并获得能量充能
            if (!ctx->is_ranged && ctx->special_index == 0) {
                if (is_fresh_parry) {
                    ctx->modified_damage = 0.0f; // 格挡完全免伤 (100% Block Proficiency)
                    skill_stun_player(ap, 1.0f); // 击晕对手 1秒
                    jetfire_add_energy_charge(tp); // 获得 1 层能量充能！
                    skill_overlay("[%s] 完美近战招架！完全免伤，击晕对手1秒！能量充能 (%d/10层)",
                                  tp == 0 ? "天火" : "敌方天火",
                                  s_jetfire_energy_charges[tp]);
                    skill_log("JETFIRE: Melee parry on P%d! Absorbed hit from P%d, stunned 1.0s, charges=%d",
                              tp, ap, s_jetfire_energy_charges[tp]);
                }
            }
            // 分支 B: 远程攻击兜底 (未走投射物管线的远程攻击)
            else if (ctx->is_ranged) {
                if (is_fresh_parry || is_shield_active) {
                    if (!is_shield_active) {
                        s_jetfire_shield_expire_ms[tp] = now_ms + JETFIRE_SHIELD_DURATION_MS;
                        jetfire_add_energy_charge(tp);
                    }
                    float reflect_dmg = ctx->base_damage;
                    ctx->modified_damage = 0.0f;
                    skill_deal_damage(ap, reflect_dmg);
                    skill_overlay("[%s] 招架护盾反弹！反伤 %.0f 点！",
                                  tp == 0 ? "天火" : "敌方天火", reflect_dmg);
                    skill_log("JETFIRE: Fallback reflected %.1f ranged damage to P%d", reflect_dmg, ap);
                }
            }
        } else {
            // 未处于格挡状态受击，护盾失效
            s_jetfire_shield_expire_ms[tp] = 0;
        }
    }

    // 天火作为攻击方 (Attacker):
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "jetfire") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // [2658] 被动：震击 (Shock)
        // 重击命中时，消耗一个能量充能，给对手施加一层震击，造成攻击力90%的伤害，持续4秒。
        if (ctx->is_heavy && !ctx->is_blocked) {
            if (s_jetfire_energy_charges[ap] > 0) {
                s_jetfire_energy_charges[ap]--;
                // 1. 消耗自身 1 层能量充能
                skill_consume_buff(ap, "jetfire_energy_charge", 1);
                // 2. 调用天火自身 SMC 的 ApplyStatModifier("jetfire_heavy_shock")，其 Target 为 Opponent，自动给对手施加震击
                skill_apply_buff(ap, "jetfire_heavy_shock");
                skill_overlay("[%s] 重击消耗充能！给对手施加【震击】！(剩余充能 %d/10层)",
                              ap == 0 ? "天火" : "敌方天火",
                              s_jetfire_energy_charges[ap]);
                skill_log("JETFIRE: Heavy hit connected! Consumed 1 charge (rem=%d), applied shock to opponent P%d",
                          s_jetfire_energy_charges[ap], tp);
            }
        }
    }
}

static int jetfire_on_power_gain_rate(int player_index, float* out_mult) {
    if (player_index < 0 || player_index >= 2 || !out_mult) return 0;
    int stacks = s_jetfire_energy_charges[player_index];
    if (stacks > 0) {
        *out_mult = 1.0f + (0.05f * stacks);
        return 1;
    }
    return 0;
}

static void jetfire_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_jetfire_energy_charges[player_index] = 0;
        s_jetfire_shield_expire_ms[player_index] = 0;
    }
}

BotSkillModule g_module_jetfire = {
    .bot_prefix          = "jetfire",
    .on_hit_connected    = jetfire_on_hit_connected,
    .on_buff_gated       = NULL,
    .on_buff_applied     = NULL,
    .on_evade_check      = NULL,
    .on_test_roll        = NULL,
    .on_power_gain_rate  = jetfire_on_power_gain_rate,
    .on_reflect_proj     = jetfire_on_reflect_proj,
    .on_fight_reset      = jetfire_on_fight_reset,
};
