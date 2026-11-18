#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// ===========================================================================
// 眩晕 (Blackout) 专属战斗技能模块
// Bot ID: blackout_cin_tf
// 职业: 破坏分子 (Demolitions / demo) | 阵营: 霸天虎 (Decepticon)
// ===========================================================================
// 1. [被动 - 暴击几率 & 暴击伤害]
//    - 连击数每增加 5，获得 1 层 8% 暴击率与 1 层 16% 暴击伤害 (上限 10 层)。
//    - 被敌人命中打断连击时，全部移除。
// 2. [被动 - 无尽怒火] (Infinite Fury)
//    - 连击数达到 15 击及以上时 (暴击几率突破 100%)，激活暴伤溢出转化增益。
//    - 连击被打断受创时一并移除。
// 3. [被动 - 加特林机枪] (Gatling Gun)
//    - 连续 3 次远程攻击后 (无论是否命中)，获得加特林机枪超频增益 (+50% 远程伤害, +40% 射速)。
//    - 在防御、近战、重击、特殊攻击时精准移除。
// 4. [特殊技 1 - 能量炮] (SP1 Unblockable)
//    - 最后一击强行穿透对手防御，严禁产生流血效果 (纯净门禁)。
// 5. [特殊技 3 - 猎杀] (SP3 Burn & Crit Resist Debuff)
//    - 最后一击命中与特殊技退出时，向对手施加永久 20% 暴击抗性削弱减益 (PUA: \uE409)。
// 6. [觉醒 - 追猎] (I'll Hunt You Down!)
//    - 我方近战招式被对方闪避掉时，猎杀渴望激增，3 秒内恢复 5% 最大能量。
//    - 3 秒倒计时冷却结束前不可再次触发。
//    - 严格门禁：我方闪避/防御对手招式绝不触发回能。
// ===========================================================================

static int      s_blackout_combo[2]            = {0, 0};
static int      s_blackout_ranged_shots[2]     = {0, 0};
static int      s_blackout_gatling_active[2]   = {0, 0};
static int      s_blackout_fury_active[2]      = {0, 0};
static uint64_t s_blackout_last_hunt_ms[2]     = {0, 0};
static uint64_t s_blackout_melee_start_ms[2]   = {0, 0};
static int      s_blackout_melee_in_flight[2]  = {0, 0};
static int      s_blackout_attack_connected[2] = {0, 0};

// 触发觉醒技“追猎”
void blackout_trigger_hunt_if_ready(int blackout_p, const char* reason) {
    if (blackout_p < 0 || blackout_p >= 2) return;
    const char* bid = skill_get_bot_id(blackout_p);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    uint64_t now_ms = skill_now_ms();
    // 3 秒倒计时冷却保护 (官方描述: 3秒倒计时结束前不可再次触发)
    if (now_ms - s_blackout_last_hunt_ms[blackout_p] >= 3000) {
        s_blackout_last_hunt_ms[blackout_p] = now_ms;
        s_blackout_melee_in_flight[blackout_p] = 0;

        // 3格满气基准为 3.0f，5% 最大能量即为 0.15f
        skill_add_mana(blackout_p, 0.15f);

        // 显示 3 秒倒计时紫色追猎能量图标
        skill_apply_buff_dur(blackout_p, "blackout_sig_whiff_power_gain", 3.0f);
        skill_overlay("[%s] 追猎渴望激活！恢复5%%最大能量！", blackout_p == 0 ? "眩晕" : "敌方眩晕");
        skill_log("BLACKOUT: P%d Hunt activated (%s) -> +5%% mana (0.15 bars)", blackout_p, reason);
    }
}

// 战斗重置
static void blackout_on_fight_reset(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    s_blackout_combo[player_index] = 0;
    s_blackout_ranged_shots[player_index] = 0;
    s_blackout_gatling_active[player_index] = 0;
    s_blackout_fury_active[player_index] = 0;
    s_blackout_last_hunt_ms[player_index] = 0;
    s_blackout_melee_start_ms[player_index] = 0;
    s_blackout_melee_in_flight[player_index] = 0;
    s_blackout_attack_connected[player_index] = 0;
    skill_log("BLACKOUT: P%d reset combat state", player_index);
}

// 出招判定 (攻击开始)
static void blackout_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    uint64_t now_ms = skill_now_ms();

    // 1. 远程射击 (action_type == 8)
    if (action_type == 8) {
        s_blackout_melee_in_flight[player_index] = 0;
        s_blackout_attack_connected[player_index] = 0;
        s_blackout_ranged_shots[player_index]++;
        skill_log("BLACKOUT: P%d ranged shot fired (count=%d/3)", player_index, s_blackout_ranged_shots[player_index]);

        if (s_blackout_ranged_shots[player_index] >= 3) {
            if (!s_blackout_gatling_active[player_index]) {
                s_blackout_gatling_active[player_index] = 1;
                // 底层射速与伤害加成
                skill_set_ranged_boost(player_index, 15000, 0.50f, 0.40f);
                // 血条下方常驻/倒计时橙色图标 (E41B)
                skill_apply_buff_dur(player_index, "blackout_gatling_ranged_buff", 15.0f);
                skill_overlay("[%s] 连续3发远程射击！加特林机枪超频激活 (+50%%伤害, +40%%射速)！",
                              player_index == 0 ? "眩晕" : "敌方眩晕");
                skill_log("BLACKOUT: P%d Gatling Gun buff activated", player_index);
            }
        }
        return;
    }

    // 2. 近战出招 (轻击 1, 中击 2, 重击 4/0x100, 冲锋 32)
    int is_melee = (action_type == 1 || action_type == 2 || action_type == 4 || action_type == 0x100 || action_type == 32);
    if (is_melee) {
        s_blackout_melee_start_ms[player_index] = now_ms;
        s_blackout_melee_in_flight[player_index] = 1;
        s_blackout_attack_connected[player_index] = 0;
    } else {
        s_blackout_melee_in_flight[player_index] = 0;
    }

    // 3. 任何近战、重击、特殊攻击均移除加特林机枪增益
    if (s_blackout_ranged_shots[player_index] > 0 || s_blackout_gatling_active[player_index]) {
        s_blackout_ranged_shots[player_index] = 0;
        s_blackout_gatling_active[player_index] = 0;
        skill_set_ranged_boost(player_index, 0, 0.0f, 0.0f);
        skill_consume_buff(player_index, "blackout_gatling_ranged_buff", 99);
        skill_log("BLACKOUT: P%d Gatling Gun cancelled due to melee/heavy/special (action=%d)", player_index, action_type);
    }
}

// 同步【无尽怒火】图标状态：真实暴击率 > 100% 时点亮图标 (hook_179 实时 1:1 溢出转暴伤)，回落至 <= 100% 时移除
static void blackout_sync_infinite_fury(int p) {
    if (p < 0 || p >= 2) return;
    const char* bid = skill_get_bot_id(p);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    float total_cc = skill_get_total_crit_chance(p);
    if (total_cc > 1.0001f) {
        if (!s_blackout_fury_active[p]) {
            s_blackout_fury_active[p] = 1;
            skill_apply_buff_dur(p, "blackout_infinite_fury_crit_dmg", -1.0f);
            skill_overlay("[%s] 暴击率达%.0f%%！【无尽怒火】溢出+%.0f%%转为暴击伤害！",
                          p == 0 ? "眩晕" : "敌方眩晕", total_cc * 100.0f, (total_cc - 1.0f) * 100.0f);
            skill_log("BLACKOUT: P%d Infinite Fury ON (crit_chance=%.2f, overflow=+%.2f crit dmg)",
                      p, total_cc, total_cc - 1.0f);
        }
    } else {
        if (s_blackout_fury_active[p]) {
            s_blackout_fury_active[p] = 0;
            skill_consume_buff(p, "blackout_infinite_fury_crit_dmg", 99);
            skill_log("BLACKOUT: P%d Infinite Fury OFF (crit_chance=%.2f <= 1.00)", p, total_cc);
        }
    }
}

// 命中连接
static void blackout_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    const char* atk_id = ctx->attacker_bot_id;

    if (atk_id && strstr(atk_id, "blackout") != NULL) {
        // 近战真正命中对手，清除挥空标记
        s_blackout_attack_connected[ap] = 1;
        s_blackout_melee_in_flight[ap] = 0;

        // 连击数自增
        s_blackout_combo[ap]++;

        // 每增加 5 连击叠加 1 层 8% 暴击率与 16% 暴击伤害 (放开至引擎最大 99 层，使暴击率可自然突破 100%)
        if (s_blackout_combo[ap] % 5 == 0) {
            int stacks = s_blackout_combo[ap] / 5;
            if (stacks > 99) stacks = 99;

            skill_apply_buff_dur(ap, "blackout_combo_crit_rate", -1.0f);
            skill_apply_buff_dur(ap, "blackout_combo_crit_dmg", -1.0f);
            skill_overlay("[%s] %d 连击！暴击几率+8%%, 暴击伤害+16%% (第%d层)！",
                          ap == 0 ? "眩晕" : "敌方眩晕", s_blackout_combo[ap], stacks);
            skill_log("BLACKOUT: P%d combo reached %d -> applied crit rate & dmg layer %d",
                      ap, s_blackout_combo[ap], stacks);
        }

        // SP3 最后一击命中，主动施加永久暴击抗性减益 (PUA: \uE409)
        if (ctx->special_index == 3 && ctx->is_last_hit) {
            skill_apply_buff_dur(tp, "blackout_sp3_crit_resist_debuff", -1.0f);
            skill_overlay("[%s] 猎杀！对手暴击抗性永久降低20%%！", ap == 0 ? "眩晕" : "敌方眩晕");
            skill_log("BLACKOUT: P%d SP3 last hit -> applied permanent crit resist debuff to P%d", ap, tp);
        }

        // 实时检查暴击率是否突破 100%，同步【无尽怒火】状态
        blackout_sync_infinite_fury(ap);
    }
}

// 防御状态变化：防御时清除加特林机枪增益 (纯净防守，绝不增加能量)
static void blackout_on_block_state(int player_index, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    if (entered) {
        if (s_blackout_ranged_shots[player_index] > 0 || s_blackout_gatling_active[player_index]) {
            s_blackout_ranged_shots[player_index] = 0;
            s_blackout_gatling_active[player_index] = 0;
            skill_set_ranged_boost(player_index, 0, 0.0f, 0.0f);
            skill_consume_buff(player_index, "blackout_gatling_ranged_buff", 99);
            skill_log("BLACKOUT: P%d Gatling Gun cancelled due to block", player_index);
        }
    }
}

// 受创硬直：被打断连击，全部清空暴击增益
static void blackout_on_hitreact_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    s_blackout_melee_in_flight[player_index] = 0;

    if (s_blackout_combo[player_index] > 0) {
        skill_log("BLACKOUT: P%d hit, combo reset from %d to 0", player_index, s_blackout_combo[player_index]);
        s_blackout_combo[player_index] = 0;
        s_blackout_fury_active[player_index] = 0;

        skill_consume_buff(player_index, "blackout_combo_crit_rate", 99);
        skill_consume_buff(player_index, "blackout_combo_crit_dmg", 99);
        skill_consume_buff(player_index, "blackout_infinite_fury_crit_dmg", 99);
    }
}

// 对手进入闪避：我方近战招式被对方闪避掉时激活“追猎”
static void blackout_on_opponent_dodge_enter(int opponent_index) {
    if (opponent_index < 0 || opponent_index >= 2) return;
    int blackout_p = 1 - opponent_index;
    const char* bid = skill_get_bot_id(blackout_p);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    uint64_t now_ms = skill_now_ms();
    uint64_t melee_start = s_blackout_melee_start_ms[blackout_p];

    // 检查眩晕是否正处于近战出招中、或 700ms 内刚刚发起了近战攻击
    int is_melee_active = s_blackout_melee_in_flight[blackout_p] || skill_is_melee_attacking(blackout_p);
    int in_recent_melee = (melee_start > 0 && now_ms >= melee_start && (now_ms - melee_start <= 700));

    // 且本次近战攻击未命中对手 (确实被对方闪避掉)
    if ((is_melee_active || in_recent_melee) && !s_blackout_attack_connected[blackout_p]) {
        blackout_trigger_hunt_if_ready(blackout_p, "opponent dodged our melee attack");
    }
}

// 修饰器过滤门禁：严格杜绝 SP1 误触发流血
static int blackout_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    int ap = ctx->attacker_player_index;
    const char* atk_id = skill_get_bot_id(ap);
    if (!atk_id || strstr(atk_id, "blackout") == NULL) return 0;

    // SP1 绝不施加流血！流血是 SP2 专属！
    if (ctx->current_special_index == 1) {
        if (strstr(ctx->modifier_id, "bleed") != NULL) {
            skill_log("BLACKOUT_GATE: suppressed bleed modifier during SP1 (mod=%s)", ctx->modifier_id);
            ctx->allow_application = false;
            return 1;
        }
    }

    return 0;
}

// 轻量级周期同步：仅检测【无尽怒火】暴击率是否跨越 100% 阈值 (每 250ms 一次，绝不干涉追猎)
static uint64_t s_blackout_last_fury_sync_ms = 0;
static void blackout_on_simulation_tick(uint64_t now_ms) {
    if (now_ms < s_blackout_last_fury_sync_ms + 250) return;
    s_blackout_last_fury_sync_ms = now_ms;
    for (int p = 0; p < 2; p++) {
        blackout_sync_infinite_fury(p);
    }
}

BotSkillModule g_module_blackout = {
    .bot_prefix             = "blackout",
    .on_hit_connected       = blackout_on_hit_connected,
    .on_buff_gated          = blackout_on_buff_gated,
    .on_buff_applied        = NULL,
    .on_evade_check         = NULL,
    .on_test_roll           = NULL,
    .on_power_gain_rate     = NULL,
    .on_reflect_proj        = NULL,
    .on_projectile_speed    = NULL,
    .on_fight_reset         = blackout_on_fight_reset,
    .on_simulation_tick     = blackout_on_simulation_tick,
    .on_block_state         = blackout_on_block_state,
    .on_dodge_enter         = NULL,
    .on_opponent_block_state= NULL,
    .on_opponent_dodge_enter= blackout_on_opponent_dodge_enter,
    .on_hitreact_enter      = blackout_on_hitreact_enter,
    .on_attack_start        = blackout_on_attack_start
};
