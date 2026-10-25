#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdlib.h>

// ===========================================================================
// 亡灵天尊 (Necrotronus) 技能模块
// Bot ID: necrotronus_gs_kabam
// 职业: 战士系 (Warrior) | 阵营: 霸天虎 (Decepticon)
// ===========================================================================
// 1. [被动 - 泰坦充能] (ID: 3209) 所有攻击命中时获得 1 层泰坦充能 (浅紫色E91A)，每层增加 1.5% 攻击力。
// 2. [被动 - 势不可挡] (ID: 3210) 达到 20 层时激活势不可挡模式 (红色E91A)，受近战伤害放大 30%。
// 3. [被动 - 全攻流血] (ID: 3207) 势不可挡激活时，所有攻击 100% 施加 6 秒流血 (25% ATK)，刷新不叠层。
// 4. [被动 - 能量压制] (ID: 3208) 对手能量高于自己时，对手能量功率降低 30% (红色E606)。
// 5. [被动 - 预判霸体] (ID: 3211) 对手放 SP 技时，30% 概率获得 0.95 秒不可阻挡 (黄色E915)。
// 6. [被动 - 重击暴击] (ID: 3212) 重击命中时每个泰坦充能增加 1% 暴击率。
// 7. [被动 - 规避克制] (ID: 3213) 近战攻击降低对手 20% 规避率。
// 8. [SP1 - 能量功率] (ID: 3214) 命中 60% 获 30% 功率 6 秒，消耗 10 层充能。
// 9. [SP2 - 暴击几率] (ID: 3199) 命中 65% 获 20% 暴率 12 秒，消耗 15 层充能。
// 10. [SP3 - 终极流血] (ID: 3200) 命中 85% 施加 40% ATK 流血 7 秒，消耗 20 层充能。
// 11. [觉醒 - 愤怒]   (ID: 3197) 泰坦充能上限提升至 40 层；势不可挡激活时暴伤增加 80.3%。
// ===========================================================================

static int s_sp_consumed_this_attack[2] = {0, 0};
static int s_necrotronus_charges[2] = {0, 0};

static void necrotronus_update_overwhelming_state(int ap) {
    int charges = s_necrotronus_charges[ap];
    int has_overwhelming = skill_has_buff(ap, "necrotronus_overwhelming_power");

    if (charges >= 20 && !has_overwhelming) {
        skill_apply_buff(ap, "necrotronus_overwhelming_power");
        skill_overlay("[%s] 势不可挡！进入势不可挡的力量模式！", ap == 0 ? "亡灵天尊" : "敌方亡灵天尊");
        skill_log("NECROTRONUS_OVERWHELMING_ENTER: P%d reached %d charges, entered Overwhelming Power", ap, charges);
    } else if (charges < 20 && has_overwhelming) {
        skill_consume_buff(ap, "necrotronus_overwhelming_power", 99);
        skill_overlay("[%s] 势不可挡的力量模式已解除", ap == 0 ? "亡灵天尊" : "敌方亡灵天尊");
        skill_log("NECROTRONUS_OVERWHELMING_EXIT: P%d charges dropped to %d, exited Overwhelming Power", ap, charges);
    }
}

static void necrotronus_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    int opp_index = 1 - player_index;

    // 1. 重置当前连招的 SP 消耗标志 (发招者)
    s_sp_consumed_this_attack[player_index] = 0;

    // 2. [ID: 3211] 对方发动特殊技时，我方亡灵天尊 30% 几率获得 0.95s 不可阻挡
    // action_type: 16 (SP1), 32 (SP2), 64 (SP3)
    int is_special = (action_type == 16 || action_type == 32 || action_type == 64 || action_type == 0x200);
    if (is_special) {
        // 关键逻辑：
        // player_index 是释放特殊技的进攻方（即“对方”）。
        // opp_index 是防守方。只有当防守方 (opp_index) 是亡灵天尊时，亡灵天尊才触发预判霸体！
        const char* defender_bot = skill_get_bot_id(opp_index);
        if (defender_bot && strstr(defender_bot, "necrotronus") != NULL) {
            float roll = skill_random_float();
            if (roll < 0.30f) {
                skill_set_unstoppable(opp_index, 950);
                skill_apply_buff_dur(opp_index, "necrotronus_unstoppable", 0.95f);
                skill_overlay("[%s] 预判霸体！获得0.95秒不可阻挡！", opp_index == 0 ? "亡灵天尊" : "敌方亡灵天尊");
                skill_log("NECROTRONUS_UNSTOPPABLE: Necrotronus P%d gained 0.95s unstoppable against opponent P%d SP (roll=%.1f%%)",
                          opp_index, player_index, roll * 100.0f);
            } else {
                skill_overlay("[%s] 霸体判定未触发 (30%%概率, roll=%.2f)", opp_index == 0 ? "亡灵天尊" : "敌方亡灵天尊", roll);
                skill_log("NECROTRONUS_UNSTOPPABLE_FAIL: Opponent P%d launched SP, Necrotronus P%d roll=%.2f >= 0.30",
                          player_index, opp_index, roll);
            }
        }
    }
}

static void necrotronus_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 亡灵天尊作为攻击方
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "necrotronus") != NULL) {

        // --- SP 充能消耗与特殊效果 (每个 SP 技能仅在第一击命中时结算消耗) ---
        if (ctx->special_index > 0 && !s_sp_consumed_this_attack[ap]) {
            s_sp_consumed_this_attack[ap] = 1;

            if (ctx->special_index == 1) {
                // SP1: 消耗 10 层泰坦充能
                s_necrotronus_charges[ap] -= 10;
                if (s_necrotronus_charges[ap] < 0) s_necrotronus_charges[ap] = 0;
                skill_consume_buff(ap, "necrotronus_titan_charge", 10);
                necrotronus_update_overwhelming_state(ap);
                // 60% 概率获 30% 能量功率增益 6 秒
                float roll = skill_random_float();
                if (roll < 0.60f) {
                    skill_apply_buff_dur(ap, "necrotronus_sp1_power_rate", 6.0f);
                    skill_overlay("[%s] 跌倒并再次崛起！能量功率提升30%%！", ap == 0 ? "亡灵天尊" : "敌方亡灵天尊");
                    skill_log("NECROTRONUS_SP1_POWER: P%d gained 30%% power rate for 6s", ap);
                }
            } else if (ctx->special_index == 2) {
                // SP2: 消耗 15 层泰坦充能
                s_necrotronus_charges[ap] -= 15;
                if (s_necrotronus_charges[ap] < 0) s_necrotronus_charges[ap] = 0;
                skill_consume_buff(ap, "necrotronus_titan_charge", 15);
                necrotronus_update_overwhelming_state(ap);
                // 65% 概率获 20% 暴击率增益 12 秒
                float roll = skill_random_float();
                if (roll < 0.65f) {
                    skill_apply_buff_dur(ap, "necrotronus_sp2_crit_buff", 12.0f);
                    skill_overlay("[%s] 暴击专精！暴击率提升20%%！", ap == 0 ? "亡灵天尊" : "敌方亡灵天尊");
                    skill_log("NECROTRONUS_SP2_CRIT: P%d gained 20%% crit rate for 12s", ap);
                }
            } else if (ctx->special_index == 3) {
                // SP3: 消耗 20 层泰坦充能
                s_necrotronus_charges[ap] -= 20;
                if (s_necrotronus_charges[ap] < 0) s_necrotronus_charges[ap] = 0;
                skill_consume_buff(ap, "necrotronus_titan_charge", 20);
                necrotronus_update_overwhelming_state(ap);
                // 85% 概率施加 40% ATK 7 秒流血
                float roll = skill_random_float();
                if (roll < 0.85f) {
                    skill_apply_buff_dur(tp, "necrotronus_sp3_bleed", 7.0f);
                    skill_overlay("[%s] 终极流血！造成40%%直接流血伤害！", ap == 0 ? "亡灵天尊" : "敌方亡灵天尊");
                    skill_log("NECROTRONUS_SP3_BLEED: P%d inflicted 7s bleed on P%d", ap, tp);
                }
            }
        }

        // --- [ID: 3209] 泰坦充能获取机制 ---
        // S技不获得泰坦充能；被对方防御时不获得充能；仅普通攻击/重击/远程攻击真实命中 (special_index == 0 && !ctx->is_blocked) 时获得 1 层泰坦充能 (上限 40 层)
        if (ctx->special_index == 0 && !ctx->is_blocked) {
            int max_charges = 40; // 默认支持觉醒 40 上限
            if (s_necrotronus_charges[ap] < max_charges) {
                s_necrotronus_charges[ap]++;
                skill_apply_buff(ap, "necrotronus_titan_charge");
                skill_log("NECROTRONUS_CHARGE: P%d gained 1 Titan Charge (total: %d)", ap, s_necrotronus_charges[ap]);
            }
            // 检查势不可挡状态切换
            necrotronus_update_overwhelming_state(ap);
        }

        // --- [ID: 3207] 势不可挡模式下：真实命中未被防御时 100% 施加 6 秒流血 (单层刷新) ---
        if (!ctx->is_blocked && skill_has_buff(ap, "necrotronus_overwhelming_power")) {
            skill_apply_buff_dur(tp, "necrotronus_overwhelming_bleed", 6.0f);
            skill_overlay("[%s] 势不可挡！攻击触发持续流血！", ap == 0 ? "亡灵天尊" : "敌方亡灵天尊");
            skill_log("NECROTRONUS_OVERWHELMING_BLEED: P%d applied 6s bleed on P%d", ap, tp);
        }
    }
}

static void necrotronus_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    for (int p = 0; p < 2; p++) {
        // --- [ID: 3208] 能量功率减益动态维护 ---
        // 当对手比自己能量更多时，对手能量功率降低 30% (红色E606图标)；能量少于或等于我方时减益消失
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "necrotronus") == NULL) continue;

        int opp = 1 - p;
        float my_mana = skill_get_mana(p);
        float opp_mana = skill_get_mana(opp);

        if (opp_mana > my_mana) {
            if (!skill_has_buff(opp, "necrotronus_power_rate_debuff")) {
                skill_apply_buff_dur(opp, "necrotronus_power_rate_debuff", -1.0f);
                skill_overlay("[%s] 能量压制！对手能量功率降低30%%！", p == 0 ? "亡灵天尊" : "敌方亡灵天尊");
                skill_log("NECROTRONUS_POWER_DEBUFF: Opponent P%d mana (%.2f) > Necrotronus P%d mana (%.2f), applied power debuff",
                          opp, opp_mana, p, my_mana);
            }
        } else {
            if (skill_has_buff(opp, "necrotronus_power_rate_debuff")) {
                skill_consume_buff(opp, "necrotronus_power_rate_debuff", 99);
                skill_log("NECROTRONUS_POWER_DEBUFF: Opponent P%d mana (%.2f) <= Necrotronus P%d mana (%.2f), removed power debuff",
                          opp, opp_mana, p, my_mana);
            }
        }
    }
}

static int necrotronus_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    (void)ctx;
    (void)out_evade;
    return 0;
}

static void necrotronus_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_sp_consumed_this_attack[player_index] = 0;
        s_necrotronus_charges[player_index] = 0;
    }
}

BotSkillModule g_module_necrotronus = {
    .bot_prefix         = "necrotronus",
    .on_hit_connected   = necrotronus_on_hit_connected,
    .on_buff_gated      = NULL,
    .on_buff_applied    = NULL,
    .on_evade_check     = necrotronus_on_evade_check,
    .on_test_roll       = NULL,
    .on_power_gain_rate = NULL,
    .on_reflect_proj    = NULL,
    .on_fight_reset     = necrotronus_on_fight_reset,
    .on_simulation_tick = necrotronus_on_simulation_tick,
    .on_attack_start    = necrotronus_on_attack_start,
};
