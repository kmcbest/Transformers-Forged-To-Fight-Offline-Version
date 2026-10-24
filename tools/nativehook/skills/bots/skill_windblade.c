#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 风刃 (Windblade) 技能模块
// Bot ID: windblade_gs
// ===========================================================================
// 1. [2905] 被动：剑刃暴击流血 (Critical Bleed)
//    近战（轻击/中击/重击）暴击时，66% 概率施加 4 秒流血 (68% ATK)。
// 2. [2907] 被动：剑刃暴击率 (Blade Crit Buff)
//    使用剑刃攻击时暴击率增加 25% (涵盖近战 L/M/Heavy 以及 SP1 和 SP2)。
// 3. [2908] 觉醒技：决心 (Resolution)
//    根据对手已损生命值百分比提升暴击率，最高提升 25% (如对手 50% HP 时提升 12.5%)。
// 4. [2919] 被动：重击远程穿透 (Heavy Range Immune)
//    重击全程规避远程普通攻击和远程重击 (100% 远程规避)，重击期间显示黄色规避图标。
// 5. [2920] 被动：流血远程眩晕 (Bleed Remote Stun)
//    若对手正处于流血状态，远程攻击命中有 35% 概率对目标造成 1.5 秒眩晕。
// 6. [2909] SP1：能量增益驱散 (Nullify Power Buff)
//    命中时若对手身上有能量增益，全部驱散并施加 80% 攻击力的即时伤害。
// 7. [2921] SP1：风暴喷发 (Stormfall Blast)
//    最后一击施加震击，造成 60% 攻击力能量伤害，持续 6 秒。
// 8. [2910] SP2：护甲穿透 (Armor Piercing)
//    最后一击命中后，自身获得 6 秒护甲穿透增益，所有攻击无视对手 100% 护甲。
// 9. [2922] SP3：终极眩晕 (SP3 Stun)
//    技能完成后，35% 概率造成 3 秒眩晕。
// ===========================================================================

static int s_is_heavy_active[2] = {0, 0};
static uint64_t s_heavy_end_ms[2] = {0, 0};
static uint64_t s_pierce_end_ms[2] = {0, 0};
static uint64_t s_sp1_last_shock_ms[2] = {0, 0};

static void windblade_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 1. 风刃作为攻击方
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "windblade") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 重击命中处理：重击已经命中，穿透保护随之结束，清除绿色图标
        if (ctx->is_heavy) {
            s_is_heavy_active[ap] = 0;
            s_heavy_end_ms[ap] = 0;
            if (skill_has_buff(ap, "windblade_heavy_range_immune")) {
                skill_consume_buff(ap, "windblade_heavy_range_immune", 99);
            }
        }

        // --- [2905] 被动：近战暴击流血 66% 几率 4 秒 DOT (68% ATK) ---
        if (ctx->is_crit && !ctx->is_ranged) {
            float roll = skill_random_float();
            float chance = 0.66f;
            if (roll < chance) {
                skill_log("ROLL_DICE_PASS: [风刃] 剑刃暴击流血 PASS! (Roll: %.1f%% < %.1f%%, mod=windblade_crit_bleed)",
                          roll * 100.0f, chance * 100.0f);
                skill_apply_buff_dur(tp, "windblade_crit_bleed", 4.0f);
                skill_overlay("[%s] 剑刃暴击！触发4秒流血！", ap == 0 ? "风刃" : "敌方风刃");
                skill_log("WINDBLADE_BLEED: P%d applied 4s bleed on P%d", ap, tp);
            } else {
                skill_log("ROLL_DICE_FAIL: [风刃] 剑刃暴击流血 FAIL (Roll: %.1f%% >= %.1f%%, mod=windblade_crit_bleed)",
                          roll * 100.0f, chance * 100.0f);
            }
        }

        // --- [2920] 被动：流血远程眩晕 35% 几率 1.5 秒 ---
        // 优先级门禁：对手处于特殊技(S1/S2/S3)或格挡/霸体等不可受击打断状态时，绝不触发眩晕！
        // 只有在对手真正进入普通 HitStun 受击状态时才掷骰判定！
        if (ctx->is_ranged && skill_has_buff(tp, "bleed")) {
            if (!skill_is_special_attacking(tp) && !skill_is_unstoppable(tp) && !ctx->is_blocked && ((ctx->hit_flags & 1) != 0)) {
                float roll = skill_random_float();
                float chance = 0.35f;
                if (roll < chance) {
                    skill_log("ROLL_DICE_PASS: [风刃] 远程流血眩晕 PASS! (Roll: %.1f%% < %.1f%%, mod=windblade_bleed_remote_stun)",
                              roll * 100.0f, chance * 100.0f);
                    skill_stun_player(tp, 1.5f);
                    skill_apply_buff_dur(tp, "windblade_bleed_remote_stun", 1.5f);
                    skill_overlay("[%s] 流血压制！远程攻击命中眩晕1.5秒！", ap == 0 ? "风刃" : "敌方风刃");
                    skill_log("WINDBLADE_STUN: P%d remote stunned bleeding P%d for 1.5s", ap, tp);
                } else {
                    skill_log("ROLL_DICE_FAIL: [风刃] 远程流血眩晕 FAIL (Roll: %.1f%% >= %.1f%%, mod=windblade_bleed_remote_stun)",
                              roll * 100.0f, chance * 100.0f);
                }
            } else {
                skill_log("WINDBLADE_STUN_SUPPRESSED: Target P%d in Special/Unstoppable/Blocked/Non-hitstun state, stun suppressed", tp);
            }
        }

        // --- [2909] SP1：能量增益驱散并追加 80% 即时伤害 ---
        if (ctx->special_index == 1) {
            int power_stacks = 0;
            if (skill_has_buff(tp, "power_gain"))  power_stacks += skill_count_buffs(tp, "power_gain");
            if (skill_has_buff(tp, "power_flow"))  power_stacks += skill_count_buffs(tp, "power_flow");
            if (skill_has_buff(tp, "power_boost")) power_stacks += skill_count_buffs(tp, "power_boost");
            if (power_stacks > 0) {
                skill_consume_buff(tp, "power_gain", power_stacks);
                skill_consume_buff(tp, "power_flow", power_stacks);
                skill_consume_buff(tp, "power_boost", power_stacks);
                // 每个被驱散的能量增益追加相当于 80% 攻击力的直接伤害
                float instant_burst = ctx->base_damage * (0.80f / 1.80f) * (float)power_stacks;
                ctx->modified_damage += instant_burst;
                skill_overlay("[%s] 能量驱散！驱散%d层能量并追加瞬伤！",
                              ap == 0 ? "风刃" : "敌方风刃", power_stacks);
                skill_log("WINDBLADE_NULLIFY: P%d dispelled %d power buffs on P%d, bonus dmg=%.1f",
                          ap, power_stacks, tp, instant_burst);
            }
        }

        // --- [2921] SP1：最后一击风暴喷发 6.0 秒震击 (60% ATK) ---
        // 严格单层保障：仅在收招最终击 (is_last_hit) 且本轮 SP1 间隔 >= 2000ms 时施加恰好 1 层震击
        if (ctx->special_index == 1 && ctx->is_last_hit) {
            if (s_sp1_last_shock_ms[ap] == 0 || (now_ms >= s_sp1_last_shock_ms[ap] && now_ms - s_sp1_last_shock_ms[ap] >= 2000)) {
                s_sp1_last_shock_ms[ap] = now_ms;
                skill_apply_buff_dur(tp, "windblade_sp1_shock", 6.0f);
                skill_overlay("[%s] SP1 风暴喷发！施加6秒震击！", ap == 0 ? "风刃" : "敌方风刃");
                skill_log("WINDBLADE_SHOCK: P%d applied 6s storm shock on P%d (single stack guaranteed)", ap, tp);
            }
        }

        // --- [2910] SP2：最后一击护甲穿透 6.0 秒增益 ---
        if (ctx->special_index == 2 && ctx->is_last_hit) {
            s_pierce_end_ms[ap] = now_ms + 6000;
            skill_apply_buff_dur(ap, "windblade_sp2_armor_pierce", 6.0f);
            skill_overlay("[%s] SP2 护甲穿透！6秒内所有攻击无视100%%护甲！", ap == 0 ? "风刃" : "敌方风刃");
            skill_log("WINDBLADE_PIERCE: P%d gained 6s 100%% armor pierce", ap);
        }

        // 护甲穿透增益生效中：无视格挡减伤与护甲防御
        if (now_ms < s_pierce_end_ms[ap]) {
            if (ctx->is_blocked) {
                // 抵消格挡减免 (相当于 100% 真实穿透伤害)
                ctx->modified_damage *= 1.45f;
            }
        }

        // --- [2922] SP3：终极技完成后 35% 几率 3.0 秒眩晕 ---
        if (ctx->special_index == 3 && ctx->is_last_hit) {
            float roll = skill_random_float();
            float chance = 0.35f;
            if (roll < chance) {
                skill_log("ROLL_DICE_PASS: [风刃] SP3终极眩晕 PASS! (Roll: %.1f%% < %.1f%%, mod=windblade_sp3_stun)",
                          roll * 100.0f, chance * 100.0f);
                skill_stun_player(tp, 3.0f);
                skill_apply_buff_dur(tp, "windblade_sp3_stun", 3.0f);
                skill_overlay("[%s] SP3 剑舞终结！造成3秒致命眩晕！", ap == 0 ? "风刃" : "敌方风刃");
                skill_log("WINDBLADE_SP3_STUN: P%d stunned P%d for 3.0s", ap, tp);
            } else {
                skill_log("ROLL_DICE_FAIL: [风刃] SP3终极眩晕 FAIL (Roll: %.1f%% >= %.1f%%, mod=windblade_sp3_stun)",
                          roll * 100.0f, chance * 100.0f);
            }
        }
    }
}

// --- [2919] 被动：重击全程远程穿透 (100% 规避远程普通与远程重击) ---

static void windblade_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    if (action_type == 0x100 || action_type == 4) { // Heavy Attack (0x100)
        uint64_t now_ms = skill_now_ms();
        s_is_heavy_active[player_index] = 1;
        s_heavy_end_ms[player_index] = now_ms + 1500;
        skill_apply_buff_dur(player_index, "windblade_heavy_range_immune", 1.5f);
        skill_log("WINDBLADE_HEAVY_START: P%d started heavy attack, range penetration active", player_index);
    }
}

static int windblade_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    (void)ctx;
    (void)out_evade;
    // 风刃重击采用 IgnoreCollisionDetection 机制真正穿透子弹飞行，绝不调用 SwitchState("EvadeRanged") 侧闪或翻滚！
    return 0;
}

static void windblade_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        // 重击已结束：只要脱离重击动作或超时，立即清除绿色图标与穿透标记
        if (s_is_heavy_active[p]) {
            if (!skill_is_heavy_attacking(p) || now_ms >= s_heavy_end_ms[p]) {
                s_is_heavy_active[p] = 0;
                s_heavy_end_ms[p] = 0;
                if (skill_has_buff(p, "windblade_heavy_range_immune")) {
                    skill_consume_buff(p, "windblade_heavy_range_immune", 99);
                }
            }
        }
    }
}

static void windblade_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_is_heavy_active[player_index] = 0;
        s_heavy_end_ms[player_index] = 0;
        s_pierce_end_ms[player_index] = 0;
        s_sp1_last_shock_ms[player_index] = 0;
        if (skill_has_buff(player_index, "windblade_heavy_range_immune")) {
            skill_consume_buff(player_index, "windblade_heavy_range_immune", 99);
        }
    }
}

BotSkillModule g_module_windblade = {
    .bot_prefix         = "windblade",
    .on_hit_connected   = windblade_on_hit_connected,
    .on_buff_gated      = NULL,
    .on_buff_applied    = NULL,
    .on_evade_check     = windblade_on_evade_check,
    .on_test_roll       = NULL,
    .on_power_gain_rate = NULL,
    .on_reflect_proj    = NULL,
    .on_fight_reset     = windblade_on_fight_reset,
    .on_simulation_tick = windblade_on_simulation_tick,
    .on_attack_start    = windblade_on_attack_start,
};
