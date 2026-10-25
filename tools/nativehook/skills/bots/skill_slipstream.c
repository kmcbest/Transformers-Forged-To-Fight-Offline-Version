#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdlib.h>

// ===========================================================================
// 滑流 (Slipstream) 技能模块
// Bot ID: slipstream_gs
// 职业: 侦察兵 (Scout) | 阵营: 霸天虎 (Decepticon)
// ===========================================================================
// 1. [被动 - 重击远程穿透] 重击全程不受远程普通攻击和远程重击伤害，显示黄色穿透图标。
// 2. [被动 - 暴击伤害] 重击命中后获得 15% 暴击伤害增益，持续 7 秒。
// 3. [被动 - 远程驱散] 基础远程攻击 100% 几率驱散对手一个护盾类增益。
// 4. [被动 - 攻击增益] 基础远程攻击 30% 几率获得 20% 攻击增益，持续 5 秒。
// 5. [被动 - 净化并震击] M2 命中净化自身震击，若成功净化则反击对手 60% ATK 8 秒震击 (单层)。
// 6. [被动 - 暴击几率] M2 命中获得 10% 暴击几率增益，持续 6 秒。
// 7. [被动 - 背刺] 暴击时 60% + 12%*能量 触发背刺 (0.5秒灰色E41E图标)，到期随机转化为暴抗削弱、能量损耗或逆火减益。
//    （三个减益都最大只能叠1层。如果已有某个减益，则随机在另两个中间选，如果已有两个，则必然变成第三个，如果三个都有，则刷新随机到的那个）
// 8. [觉醒技 - 利用弱点] 轻击与远程在对方有减益时 50%~70% 几率刷新对手随机 1 个减益持续时间；对方无减益则不ROLL。
// ===========================================================================

static int      s_is_heavy_active[2]     = {0, 0};
static uint64_t s_heavy_end_ms[2]        = {0, 0};

// 背刺 0.5 秒灰色图标与转化状态
static int      s_backstab_pending[2]    = {0, 0};
static uint64_t s_backstab_resolve_ms[2] = {0, 0};
static int      s_backstab_source_p[2]   = {0, 0};

static void slipstream_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "slipstream") == NULL) return;
    if (action_type == 4 || action_type == 0x100) {
        uint64_t now_ms = skill_now_ms();
        s_is_heavy_active[player_index] = 1;
        s_heavy_end_ms[player_index] = now_ms + 1500;
        skill_apply_buff_dur(player_index, "slipstream_heavy_range_immune", 1.5f);
        skill_log("SLIPSTREAM_HEAVY_START: P%d started heavy attack, range penetration active", player_index);
    }
}

static int slipstream_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    (void)ctx;
    (void)out_evade;
    // 滑流与风刃重击机制完全一致：采用 IgnoreCollisionDetection 机制真正穿透子弹飞行，绝不调用 SwitchState("EvadeRanged") 侧闪或翻滚！
    return 0;
}

static void slipstream_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 滑流作为攻击方
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "slipstream") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 1. 重击收招处理：清除黄色穿透图标，获得 15% 暴伤增益 7 秒
        if (ctx->is_heavy) {
            s_is_heavy_active[ap] = 0;
            s_heavy_end_ms[ap] = 0;
            if (skill_has_buff(ap, "slipstream_heavy_range_immune")) {
                skill_consume_buff(ap, "slipstream_heavy_range_immune", 99);
            }
            skill_apply_buff_dur(ap, "slipstream_heavy_crit_damage", 7.0f);
            skill_overlay("[%s] 暴击伤害！爆伤提高15%%！", ap == 0 ? "滑流" : "敌方滑流");
            skill_log("SLIPSTREAM_HEAVY_CRIT_DMG: P%d gained 15%% crit damage for 7s", ap);
        }

        // 2. 基础远程攻击：100% 驱散护盾，30% 几率获得 20% 攻击增益 5 秒
        if (ctx->is_ranged && ctx->special_index == 0) {
            if (skill_has_buff(tp, "shield")) {
                skill_consume_buff(tp, "shield", 1);
                skill_overlay("[%s] 远程破盾！驱散对手力场护盾！", ap == 0 ? "滑流" : "敌方滑流");
                skill_log("SLIPSTREAM_NULLIFY_SHIELD: P%d dispelled shield on P%d", ap, tp);
            }
            float roll_atk = skill_random_float();
            if (roll_atk < 0.30f) {
                skill_apply_buff_dur(ap, "slipstream_ranged_atk_buff", 5.0f);
                skill_overlay("[%s] 攻击强化！攻击力提升20%%！", ap == 0 ? "滑流" : "敌方滑流");
            }
        }

        // 3. 暴击触发背刺 (Backstab)：基础 60% + 每格能量 12%
        if (ctx->is_crit) {
            // 当滑流自身带有伤害性减益时，无法执行背刺
            int self_has_dmg_debuff = skill_has_buff(ap, "dmg_bleed") || skill_has_buff(ap, "bleed") ||
                                      skill_has_buff(ap, "dmg_shock") || skill_has_buff(ap, "shock") ||
                                      skill_has_buff(ap, "dmg_burn")  || skill_has_buff(ap, "burn");
            if (!self_has_dmg_debuff) {
                float opp_mana = 0.0f; // 结合对方能量
                float backstab_chance = 0.60f + 0.12f * opp_mana;
                if (backstab_chance > 0.96f) backstab_chance = 0.96f;
                float roll_bs = skill_random_float();
                if (roll_bs < backstab_chance) {
                    // 规则 2：先施加一个灰色的 E41E 图标，持续 0.5 秒，然后消失转化为后续三种减益之一
                    skill_apply_buff_dur(tp, "slipstream_backstab", 0.5f);
                    s_backstab_pending[tp] = 1;
                    s_backstab_resolve_ms[tp] = now_ms + 500;
                    s_backstab_source_p[tp] = ap;
                    skill_overlay("[%s] 暴击触发背刺！(0.5秒后随机转化)", ap == 0 ? "滑流" : "敌方滑流");
                    skill_log("SLIPSTREAM_BACKSTAB: P%d triggered backstab (0.5s gray icon) on P%d (chance=%.1f%%)",
                              ap, tp, backstab_chance * 100.0f);
                }
            }
        }

        // 4. M2 命中：无论单按 M2 还是 5 连击收尾，只要 M2 命中即可触发！
        // 判定条件：非远程、非SP技、Medium动作 (action_type == 2)，且为 M2 段 (is_last_hit 或 hit_index >= 1)
        if (!ctx->is_ranged && ctx->special_index == 0 && ctx->action_type == 2 && ctx->is_last_hit) {
            // a) M2 获得 10% 暴击率 6 秒
            skill_apply_buff_dur(ap, "slipstream_m2_crit_buff", 6.0f);
            skill_overlay("[%s] M2命中！获得10%%暴击率增益(6秒)！", ap == 0 ? "滑流" : "敌方滑流");
            skill_log("SLIPSTREAM_M2_CRIT: P%d gained 10%% crit rate from M2 for 6s", ap);

            // b) M2 净化自身震击并反击对手 60% ATK 震击 8 秒 (严格单层)
            if (skill_has_buff(ap, "dmg_shock") || skill_has_buff(ap, "shock")) {
                skill_consume_buff(ap, "dmg_shock", 99);
                skill_consume_buff(ap, "shock", 99);
                skill_apply_buff_dur(tp, "slipstream_m2_purify_shock", 8.0f);
                skill_overlay("[%s] 震击反制！净化自身震击并反噬对手！", ap == 0 ? "滑流" : "敌方滑流");
                skill_log("SLIPSTREAM_PURIFY_SHOCK: P%d purified shock and reflected to P%d (8.0s)", ap, tp);
            }
        }

        // 5. 觉醒技：利用弱点 (Exploit Weakness)
        // 规则 1：轻击与远程命中时判定；对方无减益时绝对不 ROLL！
        // 规则 2：若对方有减益，掷骰成功后【只能随机刷新其中 1 个减益的持续时间】！绝不同时刷新所有减益！
        if (ctx->is_ranged || (!ctx->is_heavy && ctx->special_index == 0 && ctx->action_type == 1)) {
            const char* active_ids[16];
            int active_count = 0;
            if (skill_has_buff(tp, "slipstream_crit_resist_down")) active_ids[active_count++] = "slipstream_crit_resist_down";
            if (skill_has_buff(tp, "slipstream_power_drain"))       active_ids[active_count++] = "slipstream_power_drain";
            if (skill_has_buff(tp, "slipstream_backfire"))          active_ids[active_count++] = "slipstream_backfire";
            if (skill_has_buff(tp, "slipstream_m2_purify_shock"))   active_ids[active_count++] = "slipstream_m2_purify_shock";
            if (skill_has_buff(tp, "bleed"))                       active_ids[active_count++] = "bleed";
            if (skill_has_buff(tp, "shock"))                       active_ids[active_count++] = "shock";
            if (skill_has_buff(tp, "burn"))                        active_ids[active_count++] = "burn";
            if (skill_has_buff(tp, "armor_break"))                 active_ids[active_count++] = "armor_break";
            if (skill_has_buff(tp, "power_leak"))                  active_ids[active_count++] = "power_leak";
            if (skill_has_buff(tp, "daze"))                        active_ids[active_count++] = "daze";

            if (active_count > 0) {
                float exploit_chance = (active_count < 4) ? 0.70f : 0.50f;
                float roll_exp = skill_random_float();
                if (roll_exp < exploit_chance) {
                    // 严格随机选择其中 1 个减益刷新持续时间
                    int picked = rand() % active_count;
                    const char* target_mod = active_ids[picked];
                    skill_apply_buff_dur(tp, target_mod, 8.0f);
                    skill_overlay("[%s] 利用弱点！刷新对手 1 个减益持续时间！", ap == 0 ? "滑流" : "敌方滑流");
                    skill_log("SLIPSTREAM_EXPLOIT: P%d refreshed single debuff '%s' on P%d (active_count=%d, chance=%.0f%%)",
                              ap, target_mod, tp, active_count, exploit_chance * 100.0f);
                }
            }
        }
    }
}

static void slipstream_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        // 重击穿透计时
        if (s_is_heavy_active[p]) {
            if (!skill_is_heavy_attacking(p) || now_ms >= s_heavy_end_ms[p]) {
                s_is_heavy_active[p] = 0;
                s_heavy_end_ms[p] = 0;
                if (skill_has_buff(p, "slipstream_heavy_range_immune")) {
                    skill_consume_buff(p, "slipstream_heavy_range_immune", 99);
                }
            }
        }

        // 规则 2 & 4: 背刺 0.5s 灰色图标到期转化为三态减益之一
        if (s_backstab_pending[p] && now_ms >= s_backstab_resolve_ms[p]) {
            s_backstab_pending[p] = 0;
            int ap = s_backstab_source_p[p];
            int tp = p;

            // 0.5s 灰色背刺图标消失
            if (skill_has_buff(tp, "slipstream_backstab")) {
                skill_consume_buff(tp, "slipstream_backstab", 99);
            }

            // 规则 4：
            // 三个减益都最大只能叠1层。
            // 如果已有某个减益，则随机在另两个中间选；
            // 如果已有两个，则必然变成第三个；
            // 如果三个都有，则刷新随机到的那个
            int has[3];
            has[0] = skill_has_buff(tp, "slipstream_crit_resist_down");
            has[1] = skill_has_buff(tp, "slipstream_power_drain");
            has[2] = skill_has_buff(tp, "slipstream_backfire");

            int missing[3];
            int missing_count = 0;
            for (int i = 0; i < 3; i++) {
                if (!has[i]) {
                    missing[missing_count++] = i;
                }
            }

            int chosen = -1;
            if (missing_count == 3) {
                // 3个都未拥有：在3个中间随机选1个
                chosen = rand() % 3;
            } else if (missing_count == 2) {
                // 已有1个：在另两个中间随机选1个
                chosen = missing[rand() % 2];
            } else if (missing_count == 1) {
                // 已有2个：必然变成第3个
                chosen = missing[0];
            } else {
                // 3个都有：随机刷新其中一个的持续时间
                chosen = rand() % 3;
            }

            const char* chosen_id = NULL;
            const char* chosen_name = NULL;
            if (chosen == 0) {
                chosen_id = "slipstream_crit_resist_down";
                chosen_name = "暴击抗性削弱";
            } else if (chosen == 1) {
                chosen_id = "slipstream_power_drain";
                chosen_name = "能量功率降低";
            } else {
                chosen_id = "slipstream_backfire";
                chosen_name = "逆火反噬";
            }

            skill_apply_buff_dur(tp, chosen_id, 8.0f);
            skill_overlay("[%s] 背刺！施加%s (8秒)！", ap == 0 ? "滑流" : "敌方滑流", chosen_name);
            skill_log("SLIPSTREAM_BACKSTAB_RESOLVED: P%d backstab on P%d transformed into '%s' (8.0s, missing_count=%d)",
                      ap, tp, chosen_id, missing_count);
        }
    }
}

static void slipstream_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_is_heavy_active[player_index] = 0;
        s_heavy_end_ms[player_index] = 0;
        s_backstab_pending[player_index] = 0;
        s_backstab_resolve_ms[player_index] = 0;
        s_backstab_source_p[player_index] = 0;
        if (skill_has_buff(player_index, "slipstream_heavy_range_immune")) {
            skill_consume_buff(player_index, "slipstream_heavy_range_immune", 99);
        }
    }
}

BotSkillModule g_module_slipstream = {
    .bot_prefix         = "slipstream",
    .on_hit_connected   = slipstream_on_hit_connected,
    .on_buff_gated      = NULL,
    .on_buff_applied    = NULL,
    .on_evade_check     = slipstream_on_evade_check,
    .on_test_roll       = NULL,
    .on_power_gain_rate = NULL,
    .on_reflect_proj    = NULL,
    .on_fight_reset     = slipstream_on_fight_reset,
    .on_simulation_tick = slipstream_on_simulation_tick,
    .on_attack_start    = slipstream_on_attack_start,
};
