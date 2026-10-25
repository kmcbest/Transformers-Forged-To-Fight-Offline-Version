#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 反冲 (Kickback) 技能模块
// Bot ID: kickback_gs_kabam
// 职业: 侦察兵 (Scout) | 阵营: 霸天虎 (Decepticon)
// ===========================================================================
// 1. [被动 - 能量流失] 暴击时 100% 几率造成能量流失，10秒内扣除 9.6% 能量，上限 5 层。
// 2. [被动 - 暴击几率] L4 和 M2 命中时本次攻击暴击几率提升 30%。
// 3. [被动 - 能量功率] 对手处于能量流失时，近战攻击能量获取效率提升 50%。
// 4. [被动 - 近战规避] 前冲闪避时获得 2 秒 35% 近战规避增益。
// 5. [被动 - 重击净化] 发起重击时，净化自身所有震击、能量汲取、能量锁定并转化为能量获取。
// 6. [被动 - 重击汲取] 重击命中时，驱散对手所有能量功率和能量获取增益并转化为自身能量获取。
// 7. [觉醒技 - T-齿轮破坏] 重击命中 80% 几率破坏对手变形齿轮，能量功率降低 30%，对手若放重击则反噬眩晕 2 秒。
// 8. [SP1 - 震击] 对手每 1 层能量流失，施加 1 层 40% ATK 震击持续 5 秒。
// 9. [SP2 - 暴击与流血] 命中获得 30% 暴击率 8 秒；后续击暴击施加 26% ATK 流血与能量流失。
// 10. [SP3 - 修复] 对手每 1 层能量流失，反冲获得 5 秒内修复 3% 最大生命值。
// ===========================================================================

static uint64_t s_tcog_end_ms[2] = {0, 0};
static uint64_t s_dash_evade_end_ms[2] = {0, 0};

static void kickback_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    int opp_index = 1 - player_index;
    uint64_t now_ms = skill_now_ms();

    // 1. 反冲自身发起重击 (action_type == 4 || 0x100) -> 净化自身减益并转化为能量获取
    const char* atker_bid = skill_get_bot_id(player_index);
    if (atker_bid && strstr(atker_bid, "kickback") != NULL) {
        if (action_type == 4 || action_type == 0x100) {
        int cleansed = 0;
        if (skill_has_buff(player_index, "dmg_shock")) {
            cleansed += skill_count_buffs(player_index, "dmg_shock");
            skill_consume_buff(player_index, "dmg_shock", 99);
        }
        if (skill_has_buff(player_index, "power_leak")) {
            cleansed += skill_count_buffs(player_index, "power_leak");
            skill_consume_buff(player_index, "power_leak", 99);
        }
        if (skill_has_buff(player_index, "power_lock")) {
            cleansed += skill_count_buffs(player_index, "power_lock");
            skill_consume_buff(player_index, "power_lock", 99);
        }
        if (skill_has_buff(player_index, "power_drain")) {
            cleansed += skill_count_buffs(player_index, "power_drain");
            skill_consume_buff(player_index, "power_drain", 99);
        }

        if (cleansed > 0) {
            for (int i = 0; i < cleansed && i < 5; i++) {
                skill_apply_buff_dur(player_index, "kickback_heavy_power_gain", 2.0f);
            }
            skill_add_mana(player_index, 0.03f * (float)cleansed);
            skill_overlay("[%s] 消耗！净化自身%d个减益并转化为能量获取！",
                          player_index == 0 ? "反冲" : "敌方反冲", cleansed);
            skill_log("KICKBACK_CLEANSE: P%d cleansed %d debuffs on heavy start", player_index, cleansed);
        }
    }
    }

    // 2. 对手发起重击时检定：若对手持有反冲施加的 T-齿轮破坏，重击直接失败并陷入 2 秒眩晕！
    if (action_type == 4 || action_type == 0x100) {
        if (skill_has_buff(player_index, "kickback_tcog_disrupt")) {
            skill_consume_buff(player_index, "kickback_tcog_disrupt", 1);
            skill_stun_player(player_index, 2.0f);
            skill_overlay("[%s] T-齿轮破坏反噬！重击失败陷入眩晕！",
                          player_index == 0 ? "我方" : "敌方");
            skill_log("KICKBACK_TCOG_STUN: P%d heavy attack disrupted by T-Cog, stunned 2.0s", player_index);
        }
    }
}

static void kickback_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 反冲作为攻击方
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "kickback") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 1. 暴击触发能量流失 (最多 5 叠)
        if (ctx->is_crit) {
            int cur_leak = skill_count_buffs(tp, "power_leak");
            if (cur_leak < 5) {
                skill_apply_buff_dur(tp, "kickback_crit_power_leak", 10.0f);
                skill_apply_buff_dur(tp, "power_leak", 10.0f);
                skill_overlay("[%s] 暴击造成能量流失！持续10秒！", ap == 0 ? "反冲" : "敌方反冲");
                skill_log("KICKBACK_POWER_LEAK: P%d inflicted power leak on P%d (total %d stacks)", ap, tp, cur_leak + 1);
            }
        }

        // 2. 对手处于能量流失时，反冲近战攻击能量获取提升 50%
        if (!ctx->is_ranged && ctx->special_index == 0 && skill_has_buff(tp, "power_leak")) {
            skill_add_mana(ap, 0.05f * 0.50f); // 额外补充 50% 能量获取
        }

        // 3. 重击命中对手：驱散对手所有能量增益并转化为自身能量获取；80% 触发 T-齿轮破坏
        if (ctx->is_heavy) {
            int dispelled = 0;
            if (skill_has_buff(tp, "power_gain")) {
                dispelled += skill_count_buffs(tp, "power_gain");
                skill_consume_buff(tp, "power_gain", 99);
            }
            if (skill_has_buff(tp, "power_rate")) {
                dispelled += skill_count_buffs(tp, "power_rate");
                skill_consume_buff(tp, "power_rate", 99);
            }
            if (dispelled > 0) {
                for (int i = 0; i < dispelled && i < 5; i++) {
                    skill_apply_buff_dur(ap, "kickback_heavy_power_gain", 2.0f);
                }
                skill_add_mana(ap, 0.03f * (float)dispelled);
                skill_overlay("[%s] 能量汲取！驱散对手%d层能量增益！", ap == 0 ? "反冲" : "敌方反冲", dispelled);
                skill_log("KICKBACK_HEAVY_NULLIFY: P%d dispelled %d power buffs on P%d", ap, dispelled, tp);
            }

            // 觉醒技：80% 几率施加 T-齿轮破坏
            float roll = skill_random_float();
            if (roll < 0.80f) {
                s_tcog_end_ms[tp] = now_ms + 10000;
                skill_apply_buff_dur(tp, "kickback_tcog_disrupt", 10.0f);
                skill_overlay("[%s] T-齿轮破坏！对手能量获取降低30%%！", ap == 0 ? "反冲" : "敌方反冲");
                skill_log("KICKBACK_TCOG_DISRUPT: P%d inflicted T-Cog Disrupt on P%d for 10s", ap, tp);
            }
        }

        // 4. SP1：对于对方身上每 1 层能量流失，施加 1 层 40% ATK 震击持续 5 秒
        if (ctx->special_index == 1 && ctx->is_last_hit) {
            int leak_count = skill_count_buffs(tp, "power_leak");
            if (leak_count > 0) {
                for (int i = 0; i < leak_count && i < 5; i++) {
                    skill_apply_buff_dur(tp, "kickback_sp1_shock", 5.0f);
                }
                float extra_shock_dmg = ctx->base_damage * 0.40f * (float)leak_count;
                ctx->modified_damage += extra_shock_dmg;
                skill_overlay("[%s] SP1 伤口震击！对%d层能量流失触发感电！",
                              ap == 0 ? "反冲" : "敌方反冲", leak_count);
                skill_log("KICKBACK_SP1_SHOCK: P%d applied %d stacks of shock on P%d", ap, leak_count, tp);
            }
        }

        // 5. SP2：获得 30% 暴击率增益持续 8 秒；后段暴击施加 26% ATK 流血
        if (ctx->special_index == 2) {
            if (ctx->hit_index == 0) {
                skill_apply_buff_dur(ap, "kickback_sp2_crit_buff", 8.0f);
                skill_overlay("[%s] SP2 暴击强化！暴击率提高30%%！", ap == 0 ? "反冲" : "敌方反冲");
            }
            if (ctx->hit_index >= 2 && ctx->is_crit) {
                skill_apply_buff_dur(tp, "kickback_sp2_bleed", 7.0f);
            }
        }

        // 6. SP3：终极流失与修复
        if (ctx->special_index == 3 && ctx->is_last_hit) {
            int leak_count = skill_count_buffs(tp, "power_leak");
            if (leak_count > 0) {
                for (int i = 0; i < leak_count && i < 5; i++) {
                    skill_apply_buff_dur(ap, "kickback_sp3_repair", 5.0f);
                    skill_heal(ap, 500.0f); // 修复 3% HP
                }
                skill_overlay("[%s] SP3 能量吸血修复！修复生命值！", ap == 0 ? "反冲" : "敌方反冲");
            }
        }
    }
}

static void kickback_on_dodge_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    uint64_t now_ms = skill_now_ms();
    // 反冲前冲或闪避获得 2 秒 35% 近战规避增益
    s_dash_evade_end_ms[player_index] = now_ms + 2000;
    skill_apply_buff_dur(player_index, "kickback_dash_evade", 2.0f);
    skill_log("KICKBACK_EVADE_GAIN: P%d gained 35%% melee evade for 2s", player_index);
}

static int kickback_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    if (ctx->bot_id && strstr(ctx->bot_id, "kickback") != NULL) {
        int p = ctx->player_index;
        // 近战规避增益生效中：35% 几率闪避近战攻击
        if (!ctx->is_ranged && skill_has_buff(p, "kickback_dash_evade")) {
            float roll = skill_random_float();
            if (roll < 0.35f) {
                *out_evade = 1;
                skill_log("KICKBACK_MELEE_EVADE: P%d evaded incoming melee attack!", p);
                return 1;
            }
        }
    }
    return 0;
}

static void kickback_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_tcog_end_ms[player_index] = 0;
        s_dash_evade_end_ms[player_index] = 0;
    }
}

BotSkillModule g_module_kickback = {
    .bot_prefix         = "kickback",
    .on_hit_connected   = kickback_on_hit_connected,
    .on_attack_start    = kickback_on_attack_start,
    .on_dodge_enter     = kickback_on_dodge_enter,
    .on_evade_check     = kickback_on_evade_check,
    .on_fight_reset     = kickback_on_fight_reset,
};
