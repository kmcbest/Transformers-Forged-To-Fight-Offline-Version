#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 黄豹 (Cheetor) 技能模块
// Bot ID: cheetor_bw_transmetal
// 职业: 侦察兵 (Scout) | 阵营: 巨无霸 (Maximal)
// ===========================================================================
// 1. [被动 - 能量守护] 免疫能量流失与燃烧，此类技能无法扣减黄豹能量。
// 2. [被动 - 暴击流血] 近战暴击 45% 几率施加 4 秒流血 (65% ATK)。
// 3. [被动 - 能量获取] L4 或 M2 连击完成时获得 2.5% 最大能量。
// 4. [被动 - 重击穿透与规避] 重击过程中 35% 穿透远程攻击，若未穿透则 100% 触发规避。
// 5. [觉醒技 - 野生突击] 满格能量触发 4 秒野生突击：暴击率 +40%、无视护甲、禁对手规避、25% 近战闪避。
// 6. [SP1 - 禁疗与流血] 施加阻止修复禁疗，收招施加 8 秒流血 (100% ATK)。
// 7. [SP2 - 伤害放大与能量功率] 对手能量越少伤害越高 (最高 +50%)，获得 12 秒 50% 能量功率。
// 8. [SP3 - 终极残气放大、能量锁定与能量燃烧] 对手能量越少伤害越高 (最高 +100%)，施加 10 秒能量锁定并燃烧 3% 能量。
// ===========================================================================

static int s_is_heavy_active[2] = {0, 0};
static uint64_t s_heavy_end_ms[2] = {0, 0};
static float s_last_recorded_mana[2] = {0.0f, 0.0f};

static void cheetor_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "cheetor") == NULL) return;
    if (action_type == 4 || action_type == 0x100) {
        uint64_t now_ms = skill_now_ms();
        s_is_heavy_active[player_index] = 1;
        s_heavy_end_ms[player_index] = now_ms + 1500;
        skill_log("CHEETOR_HEAVY_START: P%d started heavy attack", player_index);
    }
}

static void cheetor_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 黄豹作为攻击方
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "cheetor") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 1. 重击收招
        if (ctx->is_heavy) {
            s_is_heavy_active[ap] = 0;
            s_heavy_end_ms[ap] = 0;
        }

        // 2. 近战暴击流血：45% 概率施加 4 秒流血 (65% ATK)
        if (ctx->is_crit && !ctx->is_ranged) {
            float roll_bleed = skill_random_float();
            if (roll_bleed < 0.45f) {
                skill_apply_buff_dur(tp, "cheetor_crit_bleed", 4.0f);
                skill_overlay("[%s] 暴击流血！施加4秒流血！", ap == 0 ? "黄豹" : "敌方黄豹");
                skill_log("CHEETOR_CRIT_BLEED: P%d inflicted bleed on P%d", ap, tp);
            }
        }

        // 3. 连击充能：L4 或 M2 命中获得 2.5% 最大能量 (0.075 格)
        if (!ctx->is_ranged && ctx->special_index == 0 && (ctx->hit_index == 3 || ctx->hit_index == 1)) {
            skill_add_mana(ap, 0.075f);
            skill_apply_buff_dur(ap, "cheetor_combo_power_gain", 1.0f);
            skill_overlay("[%s] 连击充能！+2.5%%能量！", ap == 0 ? "黄豹" : "敌方黄豹");
        }

        // 4. 野生突击增益生效中：暴击率增加 40%，且所有攻击无视护甲
        if (skill_has_buff(ap, "cheetor_signature_feral_strike")) {
            ctx->is_crit = true;
            if (ctx->is_blocked) {
                ctx->modified_damage *= 1.50f; // 破甲贯穿
            }
        }

        // 5. SP1：阻止修复与收招 100% 流血 8 秒 (100% ATK)
        if (ctx->special_index == 1 && ctx->is_last_hit) {
            skill_apply_buff_dur(tp, "cheetor_sp1_heal_block", 8.0f);
            skill_apply_buff_dur(tp, "cheetor_sp1_bleed", 8.0f);
            skill_overlay("[%s] SP1 跨金属创伤！施加禁疗与8秒流血！", ap == 0 ? "黄豹" : "敌方黄豹");
            skill_log("CHEETOR_SP1: P%d applied heal block and bleed on P%d", ap, tp);
        }

        // 6. SP2：对手能量越少伤害越高 (最高 +50%)，获得 12 秒能量功率
        if (ctx->special_index == 2) {
            // 对手残气增伤计算
            float bonus_mult = 0.50f * (1.0f - 0.0f); // 基础估算
            ctx->modified_damage *= (1.0f + bonus_mult);
            if (ctx->is_last_hit) {
                skill_apply_buff_dur(ap, "cheetor_sp2_power_buff", 12.0f);
                skill_overlay("[%s] SP2 能量功率！能量获取提升50%%！", ap == 0 ? "黄豹" : "敌方黄豹");
            }
        }

        // 7. SP3：对手能量越少伤害越高 (最高 +100%)，能量锁定 10 秒并扣减 3% 能量
        if (ctx->special_index == 3) {
            float bonus_mult = 1.00f * (1.0f - 0.0f);
            ctx->modified_damage *= (1.0f + bonus_mult);
            if (ctx->is_last_hit) {
                skill_apply_buff_dur(tp, "cheetor_sp3_power_lock", 10.0f);
                skill_add_mana(tp, -0.09f); // 扣除 3% 能量 (0.09 格)
                skill_apply_buff_dur(tp, "cheetor_sp3_power_burn", 0.5f);
                skill_overlay("[%s] SP3 终极打击！能量锁定并燃烧3%%能量！", ap == 0 ? "黄豹" : "敌方黄豹");
            }
        }
    }
}

static int cheetor_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    if (ctx->bot_id && strstr(ctx->bot_id, "cheetor") != NULL) {
        int p = ctx->player_index;

        // 1. 重击过程中应对远程攻击：35% 穿透，未穿透则 100% 闪避
        if (ctx->is_ranged && (s_is_heavy_active[p] || skill_is_heavy_attacking(p))) {
            float roll = skill_random_float();
            if (roll < 0.35f) {
                *out_evade = 1; // 穿透
                skill_log("CHEETOR_HEAVY_PENETRATE: P%d penetrated ranged attack during heavy!", p);
                return 1;
            } else {
                *out_evade = 1; // 100% 规避
                skill_log("CHEETOR_HEAVY_EVADE: P%d evaded ranged attack during heavy!", p);
                return 1;
            }
        }

        // 2. 野生突击状态中：25% 概率规避近战攻击
        if (!ctx->is_ranged && skill_has_buff(p, "cheetor_signature_feral_strike")) {
            float roll_melee = skill_random_float();
            if (roll_melee < 0.25f) {
                *out_evade = 1;
                skill_log("CHEETOR_FERAL_MELEE_EVADE: P%d evaded melee attack via Feral Strike!", p);
                return 1;
            }
        }
    }
    return 0;
}

static int cheetor_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id || !ctx->modifier_id[0]) return 0;
    const char* tgt_id = ctx->target_bot_id;
    if (tgt_id && strstr(tgt_id, "cheetor") != NULL) {
        if (strstr(ctx->modifier_id, "leak") != NULL ||
            strstr(ctx->modifier_id, "drain") != NULL ||
            strstr(ctx->modifier_id, "power_burn") != NULL) {
            ctx->allow_application = false;
            skill_overlay("[%s] 能量守护！免疫能量流失与燃烧！", ctx->target_player_index == 0 ? "黄豹" : "敌方黄豹");
            skill_log("CHEETOR_IMMUNITY: Gated and blocked buff '%s' on Cheetor P%d", ctx->modifier_id, ctx->target_player_index);
            return 1;
        }
    }
    return 0;
}

static void cheetor_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        // 重击超时清理
        if (s_is_heavy_active[p]) {
            if (!skill_is_heavy_attacking(p) || now_ms >= s_heavy_end_ms[p]) {
                s_is_heavy_active[p] = 0;
                s_heavy_end_ms[p] = 0;
            }
        }

        // 觉醒技 - 野生突击：每填满一格能量触发 4 秒野生突击
        const char* bid = skill_get_bot_id(p);
        if (bid && strstr(bid, "cheetor") != NULL) {
            float cur_mana = skill_get_mana(p);
            float last_mana = s_last_recorded_mana[p];
            int cur_bars = (int)cur_mana;
            int last_bars = (int)last_mana;
            if (cur_bars > last_bars && cur_bars >= 1) {
                skill_apply_buff_dur(p, "cheetor_signature_feral_strike", 4.0f);
                int opp = 1 - p;
                skill_apply_buff_dur(opp, "cheetor_feral_no_evade", 4.0f);
                skill_overlay("[%s] 觉醒技！野生突击激活4秒！", p == 0 ? "黄豹" : "敌方黄豹");
                skill_log("CHEETOR_FERAL_STRIKE: P%d filled power bar (%d -> %d), activated Feral Strike 4.0s!",
                          p, last_bars, cur_bars);
            }
            s_last_recorded_mana[p] = cur_mana;
        }
    }
}

static void cheetor_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_is_heavy_active[player_index] = 0;
        s_heavy_end_ms[player_index] = 0;
        s_last_recorded_mana[player_index] = 0.0f;
    }
}

BotSkillModule g_module_cheetor = {
    .bot_prefix         = "cheetor",
    .on_hit_connected   = cheetor_on_hit_connected,
    .on_attack_start    = cheetor_on_attack_start,
    .on_buff_gated       = cheetor_on_buff_gated,
    .on_evade_check     = cheetor_on_evade_check,
    .on_simulation_tick = cheetor_on_simulation_tick,
    .on_fight_reset     = cheetor_on_fight_reset,
};
