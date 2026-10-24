#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 滑流 (Slipstream) 技能模块
// Bot ID: slipstream_gs
// 职业: 侦察兵 (Scout) | 阵营: 霸天虎 (Decepticon)
// ===========================================================================
// 1. [被动 - 重击远程穿透] 重击全程不受远程普通攻击和远程重击伤害，显示黄色穿透图标。
// 2. [被动 - 暴击伤害] 重击命中后获得 15% 暴击伤害增益，持续 7 秒。
// 3. [被动 - 远程驱散] 基础远程攻击 100% 几率驱散对手一个护盾类增益。
// 4. [被动 - 攻击增益] 基础远程攻击 30% 几率获得 20% 攻击增益，持续 5 秒。
// 5. [被动 - 净化并震击] M2 命中净化自身震击，若成功净化则反击对手 60% ATK 8 秒震击。
// 6. [被动 - 暴击几率] M2 命中获得 10% 暴击几率增益，持续 6 秒。
// 7. [被动 - 背刺] 暴击时 60% + 12%*能量 施加背刺，转为暴抗削弱、能量损耗或逆火减益。
// 8. [觉醒技 - 利用弱点] 轻击与远程 50%~70% 几率刷新对手最快过期的减益。
// ===========================================================================

static int s_is_heavy_active[2] = {0, 0};
static uint64_t s_heavy_end_ms[2] = {0, 0};

static void slipstream_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    if (action_type == 4 || action_type == 0x100) {
        uint64_t now_ms = skill_now_ms();
        s_is_heavy_active[player_index] = 1;
        s_heavy_end_ms[player_index] = now_ms + 1500;
        skill_apply_buff_dur(player_index, "slipstream_heavy_range_immune", 1.5f);
        skill_log("SLIPSTREAM_HEAVY_START: P%d started heavy attack, range penetration active", player_index);
    }
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
            float opp_mana = 0.0f; // 结合对方能量
            float backstab_chance = 0.60f + 0.12f * opp_mana;
            if (backstab_chance > 0.96f) backstab_chance = 0.96f;
            float roll_bs = skill_random_float();
            if (roll_bs < backstab_chance) {
                // 优先选择对手尚未持有的减益类型
                int has_resist = skill_has_buff(tp, "slipstream_crit_resist_down");
                int has_drain = skill_has_buff(tp, "slipstream_power_drain");
                int has_backfire = skill_has_buff(tp, "slipstream_backfire");

                if (!has_resist) {
                    skill_apply_buff_dur(tp, "slipstream_crit_resist_down", 8.0f);
                    skill_overlay("[%s] 背刺！施加暴击抗性削弱！", ap == 0 ? "滑流" : "敌方滑流");
                } else if (!has_drain) {
                    skill_apply_buff_dur(tp, "slipstream_power_drain", 8.0f);
                    skill_overlay("[%s] 背刺！施加能量损耗减益！", ap == 0 ? "滑流" : "敌方滑流");
                } else if (!has_backfire) {
                    skill_apply_buff_dur(tp, "slipstream_backfire", 8.0f);
                    skill_overlay("[%s] 背刺！施加逆火反噬减益！", ap == 0 ? "滑流" : "敌方滑流");
                } else {
                    // 三者皆有时，刷新暴抗减益
                    skill_apply_buff_dur(tp, "slipstream_crit_resist_down", 8.0f);
                }
                skill_log("SLIPSTREAM_BACKSTAB: P%d inflicted backstab on P%d (chance=%.1f%%)",
                          ap, tp, backstab_chance * 100.0f);
            }
        }

        // 4. M2 命中：净化自身震击并反击对手 60% ATK 震击 8 秒，获得 10% 暴击率 6 秒
        // M2 通常是近战第 2 段 Medium 攻击
        if (!ctx->is_ranged && ctx->special_index == 0 && ctx->hit_index == 1) {
            if (skill_has_buff(ap, "dmg_shock") || skill_has_buff(ap, "shock")) {
                skill_consume_buff(ap, "dmg_shock", 99);
                skill_consume_buff(ap, "shock", 99);
                skill_apply_buff_dur(tp, "slipstream_m2_purify_shock", 8.0f);
                skill_overlay("[%s] 震击反制！净化自身震击并反噬对手！", ap == 0 ? "滑流" : "敌方滑流");
                skill_log("SLIPSTREAM_PURIFY_SHOCK: P%d purified shock and reflected to P%d", ap, tp);
            }
            skill_apply_buff_dur(ap, "slipstream_m2_crit_buff", 6.0f);
        }

        // 5. 觉醒技：利用弱点 (Exploit Weakness)
        if (ctx->is_ranged || (!ctx->is_heavy && ctx->special_index == 0)) {
            int opp_debuff_count = skill_count_buffs(tp, "slipstream") + skill_count_buffs(tp, "debuff");
            float exploit_chance = (opp_debuff_count < 4) ? 0.70f : 0.50f;
            float roll_exp = skill_random_float();
            if (roll_exp < exploit_chance) {
                // 刷新对手减益
                if (skill_has_buff(tp, "slipstream_crit_resist_down")) {
                    skill_apply_buff_dur(tp, "slipstream_crit_resist_down", 8.0f);
                }
                if (skill_has_buff(tp, "slipstream_power_drain")) {
                    skill_apply_buff_dur(tp, "slipstream_power_drain", 8.0f);
                }
                if (skill_has_buff(tp, "slipstream_backfire")) {
                    skill_apply_buff_dur(tp, "slipstream_backfire", 8.0f);
                }
                skill_overlay("[%s] 利用弱点！刷新对手减益持续时间！", ap == 0 ? "滑流" : "敌方滑流");
            }
        }
    }
}

static void slipstream_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (s_is_heavy_active[p]) {
            if (!skill_is_heavy_attacking(p) || now_ms >= s_heavy_end_ms[p]) {
                s_is_heavy_active[p] = 0;
                s_heavy_end_ms[p] = 0;
                if (skill_has_buff(p, "slipstream_heavy_range_immune")) {
                    skill_consume_buff(p, "slipstream_heavy_range_immune", 99);
                }
            }
        }
    }
}

static void slipstream_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_is_heavy_active[player_index] = 0;
        s_heavy_end_ms[player_index] = 0;
    }
}

BotSkillModule g_module_slipstream = {
    .bot_prefix         = "slipstream",
    .on_hit_connected   = slipstream_on_hit_connected,
    .on_attack_start    = slipstream_on_attack_start,
    .on_simulation_tick = slipstream_on_simulation_tick,
    .on_fight_reset     = slipstream_on_fight_reset,
};
