#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdio.h>
#include <stdlib.h>

// ===========================================================================
// 千斤顶 (Wheeljack) 技能模块
// Bot ID: wheeljack_gs_mp20
// 职业: 科技系 (Tech) | 阵营: 汽车人 (Autobot)
// ===========================================================================
// 1. [特殊技 1/2/3 - 科技三合一]
//    - 60% 基础几率施加震击 (200% ATK, 6秒，每个进攻升级+20%)
//    - 能量流失 (SP1: 50% 基础几率; SP2/SP3: 100% 基础几率，每个能量升级+20%)
//    - 10% 基础几率造成眩晕 (3秒，每个防御升级+20%)
// 2. [觉醒技 - 力量护盾]
//    - 生命值跌破 75%、50%、25% 时各触发一次 8 秒 100% 减伤力量护盾
//    - 单场战斗不可刷新，常规挨打与开局绝不误触发
// 3. [被动 - 升级构建]
//    - 每次发动重击启动 4 秒构建 (灰色倒计时图标)，构建期间受暴击则被打断
//    - 4 秒构建结束随机获得 进攻/防御/能量 升级中的一个 (上限 3 个)
//    - 受到重击或特技近战暴击时丢失最新升级
// 4. [被动 - 成功]
//    - 获得 3 个同类升级立即触发同频共振回血 10%~20% 最大生命值
// 5. [SP2 刷新升级]
//    - 随机重掷替换所有已有升级，若达成三同类立即回血
// 6. [SP3 升级对齐]
//    - 若已有 3 个升级，全部转为第 1 个升级同类型，必触发同频共振回血
// ===========================================================================

// 升级类型: 1 = 进攻升级, 2 = 防御升级, 3 = 能量升级
static int      s_upgrade_count[2]     = {0, 0};
static int      s_upgrades[2][3]       = {{0}};
static int      s_is_building[2]       = {0, 0};
static uint64_t s_build_end_ms[2]      = {0, 0};

// 力量护盾触发标记: bit0=75%, bit1=50%, bit2=25%
static uint32_t s_shield_triggered[2]     = {0, 0};
static int      s_shield_inited[2]        = {0, 0};
static uint64_t s_shield_active_end_ms[2] = {0, 0};

// 辅助函数: 统计各类型升级数量
static void count_upgrades(int p, int* out_atk, int* out_def, int* out_pow) {
    int atk = 0, def = 0, pow = 0;
    for (int i = 0; i < s_upgrade_count[p]; i++) {
        if (s_upgrades[p][i] == 1) atk++;
        else if (s_upgrades[p][i] == 2) def++;
        else if (s_upgrades[p][i] == 3) pow++;
    }
    if (out_atk) *out_atk = atk;
    if (out_def) *out_def = def;
    if (out_pow) *out_pow = pow;
}

// 辅助函数: 清理千斤顶身上的所有升级 Buff 图标
static void clear_all_upgrade_buffs(int p) {
    skill_consume_buff(p, "wheeljack_upgrade_attack", 99);
    skill_consume_buff(p, "wheeljack_upgrade_defense", 99);
    skill_consume_buff(p, "wheeljack_upgrade_power", 99);
}

// 辅助函数: 按照当前升级数组重新同步 Buff 图标
static void sync_upgrade_buffs(int p) {
    clear_all_upgrade_buffs(p);
    for (int i = 0; i < s_upgrade_count[p]; i++) {
        if (s_upgrades[p][i] == 1) {
            skill_apply_buff(p, "wheeljack_upgrade_attack");
        } else if (s_upgrades[p][i] == 2) {
            skill_apply_buff(p, "wheeljack_upgrade_defense");
        } else if (s_upgrades[p][i] == 3) {
            skill_apply_buff(p, "wheeljack_upgrade_power");
        }
    }
}

// 辅助函数: 检定三同类升级回血
static void check_three_match_heal(int p) {
    if (s_upgrade_count[p] == 3 &&
        s_upgrades[p][0] == s_upgrades[p][1] &&
        s_upgrades[p][1] == s_upgrades[p][2]) {
        float heal_pct = 0.10f + skill_random_float() * 0.10f; // 10% ~ 20%
        float max_hp = skill_get_max_hp(p);
        float heal_amt = max_hp * heal_pct;
        skill_heal(p, heal_amt);
        skill_apply_buff_dur(p, "wheeljack_upgrade_success_heal", 1.5f);
        skill_overlay("[%s] 升级成功！三同调自愈 %.0f 点生命 (%.1f%%)！",
                      p == 0 ? "千斤顶" : "敌方千斤顶", heal_amt, heal_pct * 100.0f);
        skill_log("WHEELJACK_SUCCESS_HEAL: P%d three-match heal %.1f HP", p, heal_amt);
    }
}

static void wheeljack_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "wheeljack") == NULL) return;

    // 发动重击 (action_type == 0x100 || action_type == 4): 若未满3个且未在构建中，启动4秒构建
    if (action_type == 0x100 || action_type == 4) {
        if (s_upgrade_count[player_index] < 3 && !s_is_building[player_index]) {
            uint64_t now_ms = skill_now_ms();
            s_is_building[player_index] = 1;
            s_build_end_ms[player_index] = now_ms + 4000;
            skill_apply_buff_dur(player_index, "wheeljack_upgrade_building", 4.0f);
            skill_overlay("[%s] 启动升级构建！(4.0s)", player_index == 0 ? "千斤顶" : "敌方千斤顶");
            skill_log("WHEELJACK_BUILD: P%d started upgrade building (4.0s)", player_index);
        }
    }
}

static void wheeljack_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // =========================================================================
    // 1. 千斤顶作为攻击方
    // =========================================================================
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "wheeljack") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;
        int sp = ctx->special_index;

        // 重击命中托底：若未进入构建状态且未满3个，立即启动构建
        if (ctx->is_heavy && s_upgrade_count[ap] < 3 && !s_is_building[ap]) {
            uint64_t now_ms = skill_now_ms();
            s_is_building[ap] = 1;
            s_build_end_ms[ap] = now_ms + 4000;
            skill_apply_buff_dur(ap, "wheeljack_upgrade_building", 4.0f);
            skill_overlay("[%s] 启动升级构建！(4.0s)", ap == 0 ? "千斤顶" : "敌方千斤顶");
            skill_log("WHEELJACK_BUILD_HIT: P%d started upgrade building via heavy hit", ap);
        }

        // 进攻升级增伤: 每个进攻升级提升 30% 伤害
        int cur_atk_up = 0;
        count_upgrades(ap, &cur_atk_up, NULL, NULL);
        if (cur_atk_up > 0) {
            ctx->modified_damage *= (1.0f + (float)cur_atk_up * 0.30f);
        }

        // 特殊技收招最终击结算 (SP1/SP2/SP3)
        if (sp >= 1 && sp <= 3 && ctx->is_last_hit) {
            int atk_up = 0, def_up = 0, pow_up = 0;
            count_upgrades(ap, &atk_up, &def_up, &pow_up);

            char mod_shock[48], mod_leak[48], mod_stun[48];
            snprintf(mod_shock, sizeof(mod_shock), "wheeljack_sp%d_shock", sp);
            snprintf(mod_leak, sizeof(mod_leak), "wheeljack_sp%d_leak", sp);
            snprintf(mod_stun, sizeof(mod_stun), "wheeljack_sp%d_stun", sp);

            // a) 震击: 基础 60% 几率 + 每个进攻升级 20%
            float shock_chance = 0.60f + (float)atk_up * 0.20f;
            if (skill_random_float() < shock_chance) {
                skill_apply_buff_dur(tp, mod_shock, 6.0f);
                skill_apply_buff_dur(tp, "dmg_shock", 6.0f);
                skill_overlay("[%s] SP%d 震击发明！施加6秒震击！(几率: %.0f%%)",
                              ap == 0 ? "千斤顶" : "敌方千斤顶", sp, shock_chance * 100.0f);
                skill_log("WHEELJACK_SHOCK: P%d applied %s on P%d (chance=%.2f)", ap, mod_shock, tp, shock_chance);
            }

            // b) 能量流失: SP1 基础 50%, SP2/SP3 基础 100% + 每个能量升级 20%
            float leak_chance = ((sp == 1) ? 0.50f : 1.0f) + (float)pow_up * 0.20f;
            if (skill_random_float() < leak_chance) {
                skill_apply_buff_dur(tp, mod_leak, 3.0f);
                skill_apply_buff_dur(tp, "power_leak", 3.0f);
                skill_set_power_leak(tp, 3000, 0.0033f);
                skill_overlay("[%s] SP%d 能量流失！3秒内流失能量！", ap == 0 ? "千斤顶" : "敌方千斤顶", sp);
                skill_log("WHEELJACK_LEAK: P%d applied %s on P%d", ap, mod_leak, tp);
            }

            // c) 眩晕: 基础 10% 几率 + 每个防御升级 20%
            float stun_chance = 0.10f + (float)def_up * 0.20f;
            if (skill_random_float() < stun_chance) {
                skill_apply_buff_dur(tp, mod_stun, 3.0f);
                skill_overlay("[%s] SP%d 科技震荡！眩晕对手3秒！(几率: %.0f%%)",
                              ap == 0 ? "千斤顶" : "敌方千斤顶", sp, stun_chance * 100.0f);
                skill_log("WHEELJACK_STUN: P%d stunned P%d for 3.0s (chance=%.2f)", ap, tp, stun_chance);
            }

            // d) SP2 刷新升级: 随机替换全部已有升级
            if (sp == 2 && s_upgrade_count[ap] > 0) {
                for (int i = 0; i < s_upgrade_count[ap]; i++) {
                    float r = skill_random_float();
                    s_upgrades[ap][i] = (r < 0.333f) ? 1 : ((r < 0.666f) ? 2 : 3);
                }
                sync_upgrade_buffs(ap);
                skill_overlay("[%s] SP2 升级刷新！已重置所有科技升级！", ap == 0 ? "千斤顶" : "敌方千斤顶");
                skill_log("WHEELJACK_SP2_REROLL: P%d rerolled %d upgrades", ap, s_upgrade_count[ap]);
                check_three_match_heal(ap);
            }

            // e) SP3 升级对齐: 若已有3个升级，全部转为与第1个升级相同
            if (sp == 3 && s_upgrade_count[ap] == 3) {
                int first_type = s_upgrades[ap][0];
                s_upgrades[ap][1] = first_type;
                s_upgrades[ap][2] = first_type;
                sync_upgrade_buffs(ap);
                skill_overlay("[%s] SP3 升级对齐！三同升级同频共振！", ap == 0 ? "千斤顶" : "敌方千斤顶");
                skill_log("WHEELJACK_SP3_ALIGN: P%d aligned all upgrades to type %d", ap, first_type);
                check_three_match_heal(ap);
            }
        }
    }

    // =========================================================================
    // 2. 千斤顶作为受击方
    // =========================================================================
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "wheeljack") != NULL) {
        int tp = ctx->target_player_index;

        uint64_t now_ms = skill_now_ms();
        int is_shield_active = (s_shield_active_end_ms[tp] > 0 && now_ms < s_shield_active_end_ms[tp]);
        if (is_shield_active) {
            ctx->modified_damage = 0.0f;
            skill_overlay("[%s] 力量护盾吸收攻击伤害！", tp == 0 ? "千斤顶" : "敌方千斤顶");
        } else {
            if (s_shield_active_end_ms[tp] > 0 && now_ms >= s_shield_active_end_ms[tp]) {
                s_shield_active_end_ms[tp] = 0;
                skill_consume_buff(tp, "wheeljack_sig_force_shield", 99);
            }
            // 防御升级减伤: 每个防御升级提供 20% 伤害避免 (上限 60%)
            int cur_def_up = 0;
            count_upgrades(tp, NULL, &cur_def_up, NULL);
            if (cur_def_up > 0 && ctx->modified_damage > 0.0f) {
                float dr = (float)cur_def_up * 0.20f;
                if (dr > 0.60f) dr = 0.60f;
                ctx->modified_damage *= (1.0f - dr);
            }
        }

        // a) 升级构建打断: 构建过程中如果被暴击击中，构建失败
        if (s_is_building[tp] && ctx->is_crit) {
            s_is_building[tp] = 0;
            s_build_end_ms[tp] = 0;
            skill_consume_buff(tp, "wheeljack_upgrade_building", 99);
            skill_overlay("[%s] 受到暴击！升级构建被打断！", tp == 0 ? "千斤顶" : "敌方千斤顶");
            skill_log("WHEELJACK_BUILD_INTERRUPT: P%d build canceled by crit hit", tp);
        }

        // b) 丢失升级: 被来自重击或者特殊技的近战暴击击中，丢失最新的一个升级
        if (ctx->is_crit && !ctx->is_ranged && (ctx->is_heavy || ctx->special_index > 0)) {
            if (s_upgrade_count[tp] > 0) {
                s_upgrade_count[tp]--;
                int lost_type = s_upgrades[tp][s_upgrade_count[tp]];
                s_upgrades[tp][s_upgrade_count[tp]] = 0;
                if (lost_type == 1) skill_consume_buff(tp, "wheeljack_upgrade_attack", 1);
                else if (lost_type == 2) skill_consume_buff(tp, "wheeljack_upgrade_defense", 1);
                else if (lost_type == 3) skill_consume_buff(tp, "wheeljack_upgrade_power", 1);

                skill_overlay("[%s] 受到近战暴击！丢失最新升级！", tp == 0 ? "千斤顶" : "敌方千斤顶");
                skill_log("WHEELJACK_LOSE_UPGRADE: P%d lost upgrade type %d, remaining: %d",
                          tp, lost_type, s_upgrade_count[tp]);
            }
        }

        // 注：觉醒技力量护盾 75%/50%/25% 锁血与触发由 skill_wheeljack_filter_damage() 精确接管
    }
}

static void wheeljack_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    uint64_t current_ms = skill_now_ms();

    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "wheeljack") == NULL) continue;

        // 检查护盾过期并清理 Buff
        if (s_shield_active_end_ms[p] > 0 && current_ms >= s_shield_active_end_ms[p]) {
            s_shield_active_end_ms[p] = 0;
            skill_consume_buff(p, "wheeljack_sig_force_shield", 99);
            skill_overlay("[%s] 力量护盾已耗尽！", p == 0 ? "千斤顶" : "敌方千斤顶");
            skill_log("WHEELJACK: Force Shield expired on P%d", p);
        }

        // 开局血量检查（防止非满血开局比如56%进场时，立即误触发75%护盾）
        if (!s_shield_inited[p]) {
            float cur = skill_get_hp(p);
            float max = skill_get_max_hp(p);
            if (max > 0.0f) {
                float ratio = cur / max;
                if (ratio <= 0.75f) s_shield_triggered[p] |= 1;
                if (ratio <= 0.50f) s_shield_triggered[p] |= 2;
                if (ratio <= 0.25f) s_shield_triggered[p] |= 4;
                s_shield_inited[p] = 1;
                skill_log("WHEELJACK_INIT_TICK: P%d battle start at %.1f%% HP -> pre-consumed mask=0x%x",
                          p, ratio * 100.0f, s_shield_triggered[p]);
            }
        }

        // 检定 4 秒构建完成
        if (s_is_building[p] && current_ms >= s_build_end_ms[p]) {
            s_is_building[p] = 0;
            s_build_end_ms[p] = 0;
            skill_consume_buff(p, "wheeljack_upgrade_building", 99);

            if (s_upgrade_count[p] < 3) {
                // 随机三选一: 1=进攻, 2=防御, 3=能量
                float r = skill_random_float();
                int up_type = (r < 0.333f) ? 1 : ((r < 0.666f) ? 2 : 3);
                s_upgrades[p][s_upgrade_count[p]] = up_type;
                s_upgrade_count[p]++;

                if (up_type == 1) {
                    skill_apply_buff(p, "wheeljack_upgrade_attack");
                    skill_overlay("[%s] 构建完成！获得【进攻升级】(+30%%攻击，+20%%震击几率)！",
                                  p == 0 ? "千斤顶" : "敌方千斤顶");
                    skill_log("WHEELJACK_UPGRADE: P%d gained Attack Upgrade (%d/3)", p, s_upgrade_count[p]);
                } else if (up_type == 2) {
                    skill_apply_buff(p, "wheeljack_upgrade_defense");
                    skill_overlay("[%s] 构建完成！获得【防御升级】(+20%%减伤，+20%%眩晕几率)！",
                                  p == 0 ? "千斤顶" : "敌方千斤顶");
                    skill_log("WHEELJACK_UPGRADE: P%d gained Defense Upgrade (%d/3)", p, s_upgrade_count[p]);
                } else {
                    skill_apply_buff(p, "wheeljack_upgrade_power");
                    skill_overlay("[%s] 构建完成！获得【能量升级】(+20%%功率，+20%%流失几率)！",
                                  p == 0 ? "千斤顶" : "敌方千斤顶");
                    skill_log("WHEELJACK_UPGRADE: P%d gained Power Upgrade (%d/3)", p, s_upgrade_count[p]);
                }

                // 检定三同类升级回血
                check_three_match_heal(p);
            }
        }
    }
}

static int wheeljack_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    if (strstr(ctx->modifier_id, "wheeljack_") != NULL) {
        if (strstr(ctx->modifier_id, "_shock") != NULL ||
            strstr(ctx->modifier_id, "_leak") != NULL ||
            strstr(ctx->modifier_id, "_stun") != NULL) {
            if (!ctx->current_hit_is_last) {
                skill_log("WHEELJACK_FINAL_HIT_GATE: suppressed %s (not final hit, flags=0x%x)", ctx->modifier_id, ctx->last_hit_flags);
                ctx->allow_application = false;
            } else {
                skill_log("WHEELJACK_FINAL_HIT_GATE: permitted %s on FINAL HIT (flags=0x%x)", ctx->modifier_id, ctx->last_hit_flags);
                ctx->allow_application = true;
            }
            return 1;
        }
    }

    return 0;
}

static void wheeljack_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id || !ctx->modifier_id[0]) return;

    if (strstr(ctx->modifier_id, "wheeljack_") != NULL && strstr(ctx->modifier_id, "_leak") != NULL) {
        skill_set_power_leak(ctx->target_player_index, 3000, 0.0033f);
        skill_log("POWER_LEAK_ACTIVATED: Wheeljack leak active for 3.0s on P%d", ctx->target_player_index);
    }
}

static int wheeljack_on_power_gain_rate(int player_index, float* out_mult) {
    if (player_index >= 0 && player_index < 2 && out_mult) {
        const char* bid = skill_get_bot_id(player_index);
        if (bid && strstr(bid, "wheeljack") != NULL) {
            int pow_up = 0;
            count_upgrades(player_index, NULL, NULL, &pow_up);
            if (pow_up > 0) {
                *out_mult = 1.0f + (float)pow_up * 0.20f; // 每个能量升级提升 20% 能量功率
                return 1;
            }
        }
    }
    return 0;
}

// 千斤顶受击最终伤害过滤门禁 (由 hook_177 在最终计算出受到伤害后调用)
// 保证：
// 1. 若力量护盾处于激活状态 (8秒内)，完全免伤 (0.0f)；
// 2. 检查开场血量初始化 (若千斤顶非满血开局，如56%进场，提前标记已跨越的阈值如75%，只在后续战斗中跨越新阈值如50%/25%时触发)；
// 3. 若一次进攻会把他的体力打到 75%、50% 或 25% 以下：这次进攻依然有效并造成伤害，只是把最终体力精确卡在阈值 (75%/50%/25%)；
// 4. 同时激活8秒力量护盾与专属UI呼叫/覆盖层！
float skill_wheeljack_filter_damage(int target_player_index, float final_damage) {
    if (target_player_index < 0 || target_player_index >= 2) return final_damage;
    const char* bid = skill_get_bot_id(target_player_index);
    if (!bid || strstr(bid, "wheeljack") == NULL) return final_damage;

    uint64_t now_ms = skill_now_ms();

    // 1. 力量护盾激活中：8 秒内绝对免疫受到攻击的全部伤害 (0.0f)
    if (s_shield_active_end_ms[target_player_index] > 0) {
        if (now_ms < s_shield_active_end_ms[target_player_index]) {
            skill_log("WHEELJACK: Force Shield absorbed 100%% damage on P%d (%.1f -> 0.0)",
                      target_player_index, final_damage);
            return 0.0f;
        } else {
            s_shield_active_end_ms[target_player_index] = 0;
        }
    }

    float cur_hp = skill_get_hp(target_player_index);
    float max_hp = skill_get_max_hp(target_player_index);
    if (max_hp <= 0.0f) return final_damage;

    // 2. 开局血量检查（防止非满血开局比如56%进场时，立即误触发75%护盾）
    if (!s_shield_inited[target_player_index]) {
        float ratio = cur_hp / max_hp;
        if (ratio <= 0.75f) s_shield_triggered[target_player_index] |= 1;
        if (ratio <= 0.50f) s_shield_triggered[target_player_index] |= 2;
        if (ratio <= 0.25f) s_shield_triggered[target_player_index] |= 4;
        s_shield_inited[target_player_index] = 1;
        skill_log("WHEELJACK_INIT: P%d battle start at %.1f%% HP -> pre-consumed shield mask=0x%x",
                  target_player_index, ratio * 100.0f, s_shield_triggered[target_player_index]);
    }

    // 动态回血重置位掩码：如果当前生命值通过修复重新回升到了阈值以上，重置对应点位的触发状态，使其在再次跌破时能重新触发
    float cur_ratio = cur_hp / max_hp;
    if (cur_ratio > 0.75f) s_shield_triggered[target_player_index] &= ~1;
    if (cur_ratio > 0.50f) s_shield_triggered[target_player_index] &= ~2;
    if (cur_ratio > 0.25f) s_shield_triggered[target_player_index] &= ~4;

    // 3. 检查生命值跌破 75%、50%、25%
    // 门禁顺序从高到低检定未触发的下一个阈值
    float threshold = 0.0f;
    int triggered_bit = 0;
    int threshold_pct = 0;

    if (!(s_shield_triggered[target_player_index] & 1)) {
        threshold = max_hp * 0.75f;
        triggered_bit = 1;
        threshold_pct = 75;
    } else if (!(s_shield_triggered[target_player_index] & 2)) {
        threshold = max_hp * 0.50f;
        triggered_bit = 2;
        threshold_pct = 50;
    } else if (!(s_shield_triggered[target_player_index] & 4)) {
        threshold = max_hp * 0.25f;
        triggered_bit = 4;
        threshold_pct = 25;
    }

    if (triggered_bit != 0 && (cur_hp - final_damage <= threshold)) {
        // 本次攻击依然有效扣血，只是把最终体力卡在阈值
        float allowed = (cur_hp > threshold) ? (cur_hp - threshold) : 0.0f;
        float old_dmg = final_damage;
        final_damage = allowed;

        s_shield_triggered[target_player_index] |= triggered_bit;
        s_shield_active_end_ms[target_player_index] = now_ms + 8000;

        skill_apply_buff_dur(target_player_index, "wheeljack_sig_force_shield", 8.0f);

        skill_overlay("[%s] 生命跌破%d%%！锁定体力并激活8秒力量护盾！",
                      target_player_index == 0 ? "千斤顶" : "敌方千斤顶", threshold_pct);
        skill_log("WHEELJACK: P%d hit clamped damage %.1f -> %.1f, keeping HP at %d%% (%.1f/%.1f), activated 8s Force Shield!",
                  target_player_index, old_dmg, final_damage, threshold_pct, cur_hp - final_damage, max_hp);
    }

    return final_damage;
}

static void wheeljack_on_fight_reset(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    s_shield_triggered[player_index]     = 0;
    s_shield_inited[player_index]        = 0;
    s_shield_active_end_ms[player_index] = 0;
    s_upgrade_count[player_index]        = 0;
    s_upgrades[player_index][0]          = 0;
    s_upgrades[player_index][1]          = 0;
    s_upgrades[player_index][2]          = 0;
    s_is_building[player_index]          = 0;
    s_build_end_ms[player_index]         = 0;

    clear_all_upgrade_buffs(player_index);
    skill_consume_buff(player_index, "wheeljack_upgrade_building", 99);
    skill_consume_buff(player_index, "wheeljack_sig_force_shield", 99);
    skill_consume_buff(player_index, "wheeljack_upgrade_success_heal", 99);
}

BotSkillModule g_module_wheeljack = {
    .bot_prefix         = "wheeljack",
    .on_hit_connected   = wheeljack_on_hit_connected,
    .on_buff_gated      = wheeljack_on_buff_gated,
    .on_buff_applied    = wheeljack_on_buff_applied,
    .on_evade_check     = NULL,
    .on_simulation_tick = wheeljack_on_simulation_tick,
    .on_fight_reset     = wheeljack_on_fight_reset,
    .on_attack_start    = wheeljack_on_attack_start,
    .on_power_gain_rate = wheeljack_on_power_gain_rate,
};
