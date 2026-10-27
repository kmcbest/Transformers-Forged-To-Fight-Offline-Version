#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 野牛 (Tantrum) 技能模块
// Bot ID: tantrum_gs_kabam
// ===========================================================================
// 1. [3438] 被动：防御蓄力与不可阻挡
//    进入防御状态 1.5 秒后，获得 4.5 秒不可阻挡增益 (灰色倒计时 1.5s 后变黄色不可阻挡)。
//    若在 1.5 秒内被打断 (如重击击倒) 或主动松开防御，则不会进入不可阻挡状态，灰色图标消失。
// 2. [3450] 被动：前冲近战增益
//    前冲时获得 1 层近战增益 (+24% 近战伤害，最多 10 层)。
//    若后闪且身上没有不可阻挡状态，则失去所有近战增益。
// 3. [3439] 被动：格挡护甲 (tantrum_block_armor) - 减伤 16.5%
// 4. [3451] SP3：强力近战增益 (tantrum_sp3_melee_buff) - +80% 近战伤害
// ===========================================================================

static uint64_t s_tantrum_block_start_ms[2] = {0, 0};
static int      s_tantrum_charge_active[2]  = {0, 0};
static int      s_tantrum_dash_stacks[2]    = {0, 0};

static void tantrum_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // 1. 野牛作为受击方：格挡护甲减伤 (-16.5%，严格排除破甲 armor_break)
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "tantrum") != NULL) {
        int tp = ctx->target_player_index;
        if (skill_has_buff(tp, "tantrum_block_armor") || skill_has_buff(tp, "block_armor") || skill_has_buff(tp, "armor_up")) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= (1.0f - 0.165f); // 降低 16.5% 伤害
            skill_log("TANTRUM: Armor reduced damage on P%d: %.1f -> %.1f", tp, old_dmg, ctx->modified_damage);
        }
    }

    // 2. 野牛作为攻击方：应用前冲近战增益 (+24%/层) 与 SP3 近战增益 (+80%)
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "tantrum") != NULL) {
        int ap = ctx->attacker_player_index;
        if (!ctx->is_ranged) {
            float boost = 1.0f;
            int dash_stacks = s_tantrum_dash_stacks[ap];
            int buff_stacks = skill_count_buffs(ap, "tantrum_dash_melee_buff");
            if (buff_stacks > dash_stacks) dash_stacks = buff_stacks;
            if (dash_stacks > 0) {
                boost += 0.24f * (float)dash_stacks;
            }
            if (skill_has_buff(ap, "tantrum_sp3_melee_buff")) {
                boost += 0.80f; // SP3 强力近战增益 +80%
            }
            if (boost > 1.0f) {
                float old_dmg = ctx->modified_damage;
                ctx->modified_damage *= boost;
                skill_log("TANTRUM: Melee damage boosted x%.2f (%.1f -> %.1f, stacks=%d) on P%d",
                          boost, old_dmg, ctx->modified_damage, dash_stacks, ap);
            }
        }
    }
}

static void tantrum_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    if (strstr(ctx->modifier_id, "tantrum_dash_melee_buff") != NULL) {
        int tp = ctx->target_player_index;
        if (s_tantrum_dash_stacks[tp] < 10) {
            s_tantrum_dash_stacks[tp]++;
            skill_log("TANTRUM: Dash melee buff applied to P%d! current stacks=%d", tp, s_tantrum_dash_stacks[tp]);
        }
    }
}

static void tantrum_on_block_state(int p, int entered) {
    if (p < 0 || p >= 2) return;
    uint64_t now_ms = skill_now_ms();

    if (entered) {
        // 进入防御姿态: 如果当前身上已有不可阻挡，则不重复蓄力
        if (skill_is_unstoppable(p)) {
            skill_log("TANTRUM: P%d entered block while already unstoppable, skipping charge", p);
            return;
        }
        s_tantrum_charge_active[p] = 1;
        s_tantrum_block_start_ms[p] = now_ms;
        // 挂上灰色倒计时图标 (时长 1.5s)
        skill_apply_buff(p, "tantrum_block_charge");
        skill_log("TANTRUM: P%d entered block stance, armed 1.5s Unstoppable charge & applied gray icon", p);
    } else {
        // 松开防御姿态:
        // 若在 1.5s 蓄力期间松开，且未触发不可阻挡，则取消蓄力并移除灰色图标
        if (s_tantrum_charge_active[p]) {
            s_tantrum_charge_active[p] = 0;
            s_tantrum_block_start_ms[p] = 0;
            skill_consume_buff(p, "tantrum_block_charge", 1);
            skill_log("TANTRUM: P%d released block before 1.5s, cancelled Unstoppable charge", p);
        }
    }
}

static void tantrum_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        // 检查蓄力是否满 1.5s:
        if (s_tantrum_charge_active[p] && s_tantrum_block_start_ms[p] > 0) {
            uint64_t elapsed = now_ms - s_tantrum_block_start_ms[p];
            if (elapsed >= 1500) {
                // 蓄力完成！
                s_tantrum_charge_active[p] = 0;
                s_tantrum_block_start_ms[p] = 0;

                // 移除灰色倒计时图标
                skill_consume_buff(p, "tantrum_block_charge", 1);

                // 赋予 4.5s 不可阻挡状态 (引擎底层霸体 4500ms)
                skill_set_unstoppable(p, 4500);

                // 挂上黄色不可阻挡 Buff 图标 (倒计时 4.5s)
                skill_apply_buff(p, "tantrum_block_unstoppable");

                skill_overlay("[%s] 防御蓄力完成！激活 4.5s 不可阻挡霸体！",
                              p == 0 ? "野牛" : "敌方野牛");
                skill_log("TANTRUM: Block held for 1.5s on P%d! Activated 4.5s Unstoppable", p);
            }
        }
    }
}

static void tantrum_on_hitreact_enter(int p) {
    if (p < 0 || p >= 2) return;
    // 受到重击击倒等打断时，取消蓄力
    if (s_tantrum_charge_active[p]) {
        s_tantrum_charge_active[p] = 0;
        s_tantrum_block_start_ms[p] = 0;
        skill_consume_buff(p, "tantrum_block_charge", 1);
        skill_log("TANTRUM: P%d block stance interrupted by hitreact, cancelled Unstoppable charge", p);
    }
}

static void tantrum_on_dodge_enter(int p) {
    if (p < 0 || p >= 2) return;
    // 后闪时：若身上没有不可阻挡状态，则失去所有前冲近战增益
    if (!skill_is_unstoppable(p)) {
        if (s_tantrum_dash_stacks[p] > 0) {
            skill_log("TANTRUM: P%d dashed back without Unstoppable, lost all %d dash melee stacks",
                      p, s_tantrum_dash_stacks[p]);
            s_tantrum_dash_stacks[p] = 0;
            skill_consume_buff(p, "tantrum_dash_melee_buff", 99);
            skill_overlay("[%s] 后闪打断！失去所有前冲近战增益！",
                          p == 0 ? "野牛" : "敌方野牛");
        }
    } else {
        skill_log("TANTRUM: P%d dashed back while Unstoppable, preserved dash melee stacks (%d)",
                  p, s_tantrum_dash_stacks[p]);
    }

    // 后闪也会取消防御蓄力
    if (s_tantrum_charge_active[p]) {
        s_tantrum_charge_active[p] = 0;
        s_tantrum_block_start_ms[p] = 0;
        skill_consume_buff(p, "tantrum_block_charge", 1);
    }
}

static int tantrum_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id) return 0;

    // 当野牛身上已有黄色不可阻挡时，阻止再次挂上灰色 tantrum_block_charge
    if (strstr(ctx->modifier_id, "tantrum_block_charge") != NULL) {
        int tp = ctx->target_player_index;
        if (skill_is_unstoppable(tp)) {
            ctx->allow_application = false;
            skill_log("TANTRUM: Suppressed tantrum_block_charge on P%d because already unstoppable", tp);
            return 1;
        }
    }

    return 0;
}

static void tantrum_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_tantrum_block_start_ms[player_index] = 0;
        s_tantrum_charge_active[player_index]  = 0;
        s_tantrum_dash_stacks[player_index]   = 0;
    }
}

BotSkillModule g_module_tantrum = {
    .bot_prefix          = "tantrum",
    .on_hit_connected    = tantrum_on_hit_connected,
    .on_buff_gated       = tantrum_on_buff_gated,
    .on_buff_applied     = tantrum_on_buff_applied,
    .on_evade_check      = NULL,
    .on_test_roll        = NULL,
    .on_power_gain_rate  = NULL,
    .on_reflect_proj     = NULL,
    .on_fight_reset      = tantrum_on_fight_reset,
    .on_simulation_tick  = tantrum_on_simulation_tick,
    .on_block_state      = tantrum_on_block_state,
    .on_dodge_enter      = tantrum_on_dodge_enter,
    .on_hitreact_enter   = tantrum_on_hitreact_enter,
};
