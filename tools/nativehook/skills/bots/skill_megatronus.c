#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdlib.h>
#include <stdio.h>

// ===========================================================================
// 震天尊 (Megatronus) 技能模块
// Bot ID: megatronus_gs_kabam
// 职业: 破坏系 (Demolition) | 阵营: 霸天虎 (Decepticon)
// ===========================================================================
// 1. [被动 - 火种源能量] (ID: 1793029715892) 攻击/受击不产气，每秒自动产生 1.2% 最大能量 (0.036 bars/s)
// 2. [被动 - 狂怒遗迹]   (ID: 1793029715893) 开局激活(橙色E91A)，攻击力+60%，对手格挡精通-20%；每充满1格能量交替切换
// 3. [被动 - 保存遗迹]   (ID: 1793029715894) 伤害抗性+60%(蓝色E91A)，单次受击伤害上限截断为震天尊最大生命值20%
// 4. [被动 - 不朽遗迹]   (ID: 1793029715895) 生命值降至10%以下激活不朽遗迹8秒(暗紫E91A)，免疫所有伤害(单局限1次)
// 5. [被动 - 暴击几率]   (ID: 1793029715896) L4 与 M2 连招收尾命中时增加 40% 暴击几率
// 6. [被动 - 黑暗燃烧]   (ID: 1793029715897) 重击最后一击 100% 施加黑暗燃烧，造成 40% ATK 即时能量伤害
// 7. [SP1 - 破甲]       (ID: 1793029715898) 最后一击 60% 移除一层护甲并施加 8 秒破甲 (-30% 护甲)
// 8. [SP1 - 能量窃取]   (ID: 1793029715899) 狂怒遗迹生效时，最后一击 100% 窃取对手 35% 现有能量
// 9. [SP2 - 不可防御]   (ID: 1793029715900) 最后一击不可防御
// 10. [SP2 - 生命窃取]  (ID: 1793029715901) 保存遗迹生效时，第一击 100% 窃取对手 17.5% 震天尊最大生命值并自愈
// 11. [SP3 - 黑暗燃烧]  (ID: 1793029715902) 最后一击 100% 施加黑暗燃烧，造成 200% ATK 即时能量伤害
// 12. [SP3 - 能量窃取]  (ID: 1793029715903) 狂怒遗迹生效时，第一击 66% 窃取对手 35% 现有能量
// 13. [SP3 - 生命窃取]  (ID: 1793029715904) 保存遗迹生效时，第一击 66% 窃取对手 17.5% 最大生命值并自愈
// ===========================================================================

typedef enum {
    MEGATRONUS_RELIC_NONE = 0,
    MEGATRONUS_RELIC_FURY = 1,
    MEGATRONUS_RELIC_PRESERVATION = 2
} MegatronusRelic;

static MegatronusRelic s_active_relic[2]       = {MEGATRONUS_RELIC_NONE, MEGATRONUS_RELIC_NONE};
static uint64_t        s_last_tick_ms[2]       = {0, 0};
static int             s_last_power_bar[2]     = {0, 0};
static int             s_combat_started[2]     = {0, 0};

static int             s_immortality_used[2]   = {0, 0};
static int             s_immortality_active[2] = {0, 0};
static uint64_t        s_immortality_end_ms[2] = {0, 0};

static void megatronus_on_fight_reset(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "megatronus") == NULL) {
        s_active_relic[player_index]       = MEGATRONUS_RELIC_NONE;
        s_last_tick_ms[player_index]       = 0;
        s_last_power_bar[player_index]     = 0;
        s_immortality_used[player_index]   = 0;
        s_immortality_active[player_index] = 0;
        s_immortality_end_ms[player_index] = 0;
        return;
    }

    s_active_relic[player_index]       = MEGATRONUS_RELIC_FURY; // 开局处于狂怒遗迹状态
    s_last_tick_ms[player_index]       = 0; // 重置时钟，由正式开战的首个 tick 初始化
    s_last_power_bar[player_index]     = 0;
    s_combat_started[player_index]     = 0; // 标记未开战 (从天而降动画期间绝不充能)
    s_immortality_used[player_index]   = 0;
    s_immortality_active[player_index] = 0;
    s_immortality_end_ms[player_index] = 0;

    // 开局清空能量，确保从 0.0 开始自主充盈
    skill_set_mana(player_index, 0.0f);

    // 检查开局血量是否低于 10%
    float hp = skill_get_hp(player_index);
    float max_hp = skill_get_max_hp(player_index);
    if (max_hp > 0.0f && hp < max_hp * 0.10f) {
        s_immortality_used[player_index] = 1; // 开局少于10%则不激活
    }

    // 施加狂怒遗迹 Buff
    skill_apply_buff(player_index, "megatronus_relic_fury");
    skill_overlay("[%s] 激活狂怒遗迹！攻击力+60%%，格挡穿透+20%%！", player_index == 0 ? "震天尊" : "敌方震天尊");
    skill_log("MEGATRONUS: P%d fight reset, armed Relic of Fury", player_index);
}

static int megatronus_on_power_gain_rate(int player_index, float* out_mult) {
    if (player_index >= 0 && player_index < 2 && out_mult) {
        const char* bid = skill_get_bot_id(player_index);
        if (bid && strstr(bid, "megatronus") != NULL) {
            *out_mult = 0.0f; // 常规回能归零 (火种源能量自主生成)
            return 1;
        }
    }
    return 0;
}

static void megatronus_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "megatronus") == NULL) continue;

        // 0. 真实开战初始化 (从天而降动画结束后，首个 tick 触发，确保从 0.00 开始充能)
        if (!s_combat_started[p]) {
            s_combat_started[p] = 1;
            s_last_tick_ms[p]   = now_ms;
            s_last_power_bar[p] = 0;
            skill_set_mana(p, 0.0f);
            skill_log("MEGATRONUS: P%d combat officially started, zeroed mana and armed tick clock", p);
            continue;
        }

        // 1. 火种源自主回能: 14秒充满一格能量 (1.0 / 14.0 = ~0.07142857 bars/s)
        float cur_mana = skill_get_mana(p);

        // 门禁 A: 若能量已达到满 3 格 (>= 3.0)，彻底停止充能并对齐时钟，严禁溢出或累积！
        if (cur_mana >= 3.0f - 0.005f) {
            s_last_tick_ms[p] = now_ms;
            if (cur_mana > 3.0f) {
                skill_set_mana(p, 3.0f);
            }
        }
        // 门禁 B: 匀速自主充能 (放 S 技完全不影响自发充气)
        else {
            if (s_last_tick_ms[p] == 0) {
                s_last_tick_ms[p] = now_ms;
            } else if (now_ms > s_last_tick_ms[p]) {
                uint64_t dt_ms = now_ms - s_last_tick_ms[p];
                s_last_tick_ms[p] = now_ms;



                if (!skill_has_buff(p, "power_lock")) {
                    float mana_delta = ((float)dt_ms / 1000.0f) * (1.0f / 14.0f);
                    skill_add_mana(p, mana_delta);

                    // 充能后如果超过 3 格，严格截断并写回
                    if (skill_get_mana(p) > 3.0f) {
                        skill_set_mana(p, 3.0f);
                    }
                }
            }
        }

        // 2. 遗迹流转交替: "每充满一格能量，交替切换"
        cur_mana = skill_get_mana(p);
        int cur_bar = (int)(cur_mana + 0.001f); // 0, 1, 2, 3
        if (cur_bar > 3) cur_bar = 3;
        if (cur_bar > s_last_power_bar[p]) {
            // 充满了一格能量！交替切换遗物
            if (s_active_relic[p] == MEGATRONUS_RELIC_FURY) {
                s_active_relic[p] = MEGATRONUS_RELIC_PRESERVATION;
                skill_consume_buff(p, "megatronus_relic_fury", 99);
                skill_apply_buff(p, "megatronus_relic_preservation");
                skill_overlay("[%s] 充盈第 %d 格能量！切换至保存遗迹！伤害抗性+60%%！",
                              p == 0 ? "震天尊" : "敌方震天尊", cur_bar);
                skill_log("MEGATRONUS: P%d mana reached %.2f (bar %d), switched to Relic of Preservation",
                          p, cur_mana, cur_bar);
            } else {
                s_active_relic[p] = MEGATRONUS_RELIC_FURY;
                skill_consume_buff(p, "megatronus_relic_preservation", 99);
                skill_apply_buff(p, "megatronus_relic_fury");
                skill_overlay("[%s] 充盈第 %d 格能量！切换至狂怒遗迹！攻击力+60%%！",
                              p == 0 ? "震天尊" : "敌方震天尊", cur_bar);
                skill_log("MEGATRONUS: P%d mana reached %.2f (bar %d), switched to Relic of Fury",
                          p, cur_mana, cur_bar);
            }
            s_last_power_bar[p] = cur_bar;
        } else if (cur_bar < s_last_power_bar[p]) {
            // 释放技能消耗了能量，同步当前 bar 记录
            s_last_power_bar[p] = cur_bar;
        }

        // 3. 不朽遗迹倒计时管理: 8 秒到期自动解除
        if (s_immortality_active[p]) {
            if (now_ms >= s_immortality_end_ms[p]) {
                s_immortality_active[p] = 0;
                skill_consume_buff(p, "megatronus_relic_immortality", 99);
                skill_overlay("[%s] 不朽遗迹持续时间结束", p == 0 ? "震天尊" : "敌方震天尊");
                skill_log("MEGATRONUS: Relic of Immortality expired on P%d", p);
            }
        }
    }
}

static void megatronus_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // =======================================================================
    // 一、 震天尊作为受击方 (Defender)
    // =======================================================================
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "megatronus") != NULL) {
        int tp = ctx->target_player_index;

        // 1. 不朽遗迹绝对免伤: 持续时间内免除 100% 伤害
        if (s_immortality_active[tp]) {
            if (now_ms < s_immortality_end_ms[tp]) {
                ctx->modified_damage = 0.0f;
                skill_log("MEGATRONUS: Relic of Immortality absorbed 100%% damage on P%d", tp);
                return;
            }
        }

        // 2. 保存遗迹抗性与单次伤害上限截断 (减伤 60%，单次伤害不超过最大生命值 20%)
        if (s_active_relic[tp] == MEGATRONUS_RELIC_PRESERVATION) {
            ctx->modified_damage *= (1.0f - 0.60f); // 减伤 60%

            float max_hp = skill_get_max_hp(tp);
            if (max_hp > 0.0f) {
                float cap = max_hp * 0.20f;
                if (ctx->modified_damage > cap) {
                    float old_dmg = ctx->modified_damage;
                    ctx->modified_damage = cap;
                    skill_log("MEGATRONUS: Relic of Preservation capped damage on P%d: %.1f -> %.1f (20%% max HP)",
                              tp, old_dmg, ctx->modified_damage);
                }
            }
        }

        // 3. 生命值跌破 10% 触发不朽遗迹 (单局限 1 次)
        float cur_hp = skill_get_hp(tp);
        float max_hp = skill_get_max_hp(tp);
        if (!s_immortality_used[tp] && max_hp > 0.0f) {
            float threshold = max_hp * 0.10f;
            if (cur_hp - ctx->modified_damage <= threshold) {
                s_immortality_used[tp]   = 1;
                s_immortality_active[tp] = 1;
                s_immortality_end_ms[tp] = now_ms + 8000; // 持续 8 秒

                // 锁血截断：确保震天尊不会在这一击死亡，血量锁在 10%
                if (cur_hp - ctx->modified_damage < threshold) {
                    ctx->modified_damage = cur_hp - threshold;
                    if (ctx->modified_damage < 0.0f) ctx->modified_damage = 0.0f;
                }

                skill_apply_buff(tp, "megatronus_relic_immortality");
                skill_overlay("[%s] 生命危险！激活不朽遗迹！8秒内免疫所有伤害！",
                              tp == 0 ? "震天尊" : "敌方震天尊");
                skill_log("MEGATRONUS: P%d dropped below 10%% HP, activated 8s Relic of Immortality!", tp);
            }
        }
    }

    // =======================================================================
    // 二、 震天尊作为攻击方 (Attacker)
    // =======================================================================
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "megatronus") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 1. 狂怒遗迹增伤与格挡渗透 (+60% 攻击力，降低对手 20% 格挡精通)
        if (s_active_relic[ap] == MEGATRONUS_RELIC_FURY) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= 1.60f; // 攻击力提升 60%
            skill_log("MEGATRONUS: Relic of Fury boosted damage x1.60 (%.1f -> %.1f) on P%d",
                      old_dmg, ctx->modified_damage, ap);

            if (ctx->is_blocked) {
                // 降低对手 20% 格挡减伤效果 (格挡渗透)
                ctx->modified_damage *= 1.20f;
                skill_log("MEGATRONUS: Relic of Fury penetrated opponent block (+20%% dmg) on P%d", ap);
            }
        }

        // 2. 暴击几率: L4 (act=1, last=1) 与 M2 (act=2, last=1) 提升 40% 暴击率
        if ((ctx->action_type == 1 || ctx->action_type == 2) && ctx->is_last_hit) {
            if (!ctx->is_crit) {
                float roll = skill_random_float();
                if (roll < 0.40f) {
                    ctx->is_crit = true;
                    ctx->modified_damage *= 1.60f; // 基础暴击加成
                    skill_log("MEGATRONUS: L4/M2 combo finisher rolled +40%% crit success on P%d", ap);
                }
            }
        }

        // 3. 黑暗燃烧: 重击最后一击 100% 造成 40% ATK 即时能量伤害
        if ((ctx->action_type == 4 || ctx->is_heavy) && ctx->is_last_hit) {
            float atk = skill_get_attack(ap);
            float burn_dmg = atk * 0.40f;
            skill_deal_damage(tp, burn_dmg);
            skill_apply_buff(tp, "megatronus_dark_burn");
            skill_overlay("[%s] 重击触发黑暗燃烧！造成 %.0f 点即时能量伤害！",
                          ap == 0 ? "震天尊" : "敌方震天尊", burn_dmg);
            skill_log("MEGATRONUS: Heavy Dark Burn dealt %.1f instant dmg to P%d", burn_dmg, tp);
        }

        // 4. 特殊技 SP1 (action_type == 16 || special_index == 1)
        if (ctx->special_index == 1 || ctx->action_type == 16) {
            if (ctx->is_last_hit) {
                // a) 60% 破甲 (移除一层护甲增益，施加 8 秒破甲 -30%)
                float roll = skill_random_float();
                if (roll < 0.60f) {
                    skill_consume_buff(tp, "armor_up", 1);
                    skill_consume_buff(tp, "block_armor", 1);
                    skill_consume_buff(tp, "buff_armor", 1);
                    skill_apply_buff_dur(tp, "megatronus_sp1_armor_break", 8.0f);
                    skill_overlay("[%s] SP1 破甲成功！削弱对手 30%% 护甲！", ap == 0 ? "震天尊" : "敌方震天尊");
                    skill_log("MEGATRONUS: SP1 Armor Break applied to P%d", tp);
                }
                // b) 狂怒遗迹生效时，100% 窃取对手 35% 现有能量
                if (s_active_relic[ap] == MEGATRONUS_RELIC_FURY) {
                    float opp_mana = skill_get_mana(tp);
                    if (opp_mana > 0.0f) {
                        float stolen = opp_mana * 0.35f;
                        skill_add_mana(tp, -stolen);
                        skill_add_mana(ap, stolen);
                        skill_apply_buff_dur(tp, "megatronus_power_steal", 1.0f);
                        skill_overlay("[%s] 狂怒窃电！夺取对手 %.2f 格能量！", ap == 0 ? "震天尊" : "敌方震天尊", stolen);
                        skill_log("MEGATRONUS: SP1 Power Steal transferred %.2f mana from P%d to P%d", stolen, tp, ap);
                    }
                }
            }
        }

        // 5. 特殊技 SP2 (action_type == 32 || special_index == 2)
        if (ctx->special_index == 2 || ctx->action_type == 32) {
            // a) 最后一击不可防御 (穿透对手格挡)
            if (ctx->is_last_hit) {
                if (ctx->is_blocked) {
                    ctx->is_blocked = false;
                    ctx->modified_damage *= 2.0f; // 抵消格挡 50% 减伤，实现真实破防贯穿
                }
                skill_overlay("[%s] SP2 终结不可防御！", ap == 0 ? "震天尊" : "敌方震天尊");
                skill_log("MEGATRONUS: SP2 final hit penetrated block on P%d", ap);
            }
            // b) 保存遗迹生效时，第一击 100% 窃取对手 17.5% 震天尊最大生命值
            if (ctx->hit_index == 0 && s_active_relic[ap] == MEGATRONUS_RELIC_PRESERVATION) {
                float max_hp = skill_get_max_hp(ap);
                float steal_amount = max_hp * 0.175f;
                skill_deal_damage(tp, steal_amount);
                skill_heal(ap, steal_amount);
                skill_apply_buff_dur(tp, "megatronus_life_steal", 1.0f);
                skill_overlay("[%s] 守护汲取！生命窃取 %.0f 点！", ap == 0 ? "震天尊" : "敌方震天尊", steal_amount);
                skill_log("MEGATRONUS: SP2 Life Steal drained %.1f HP from P%d to P%d", steal_amount, tp, ap);
            }
        }

        // 6. 特殊技 SP3 (action_type == 64 || special_index == 3)
        if (ctx->special_index == 3 || ctx->action_type == 64) {
            // a) 最后一击 100% 黑暗燃烧: 造成 200% ATK 即时能量伤害
            if (ctx->is_last_hit) {
                float atk = skill_get_attack(ap);
                float burn_dmg = atk * 2.00f;
                skill_deal_damage(tp, burn_dmg);
                skill_apply_buff(tp, "megatronus_dark_burn");
                skill_overlay("[%s] SP3 终极黑暗燃烧！造成 %.0f 点即时能量伤害！",
                              ap == 0 ? "震天尊" : "敌方震天尊", burn_dmg);
                skill_log("MEGATRONUS: SP3 Dark Burn dealt %.1f instant dmg to P%d", burn_dmg, tp);
            }
            // b) 第一击协同:
            if (ctx->hit_index == 0) {
                // 狂怒遗迹生效时，66% 概率窃取对手 35% 现有能量
                if (s_active_relic[ap] == MEGATRONUS_RELIC_FURY) {
                    float roll = skill_random_float();
                    if (roll < 0.66f) {
                        float opp_mana = skill_get_mana(tp);
                        if (opp_mana > 0.0f) {
                            float stolen = opp_mana * 0.35f;
                            skill_add_mana(tp, -stolen);
                            skill_add_mana(ap, stolen);
                            skill_apply_buff_dur(tp, "megatronus_power_steal", 1.0f);
                            skill_overlay("[%s] SP3 狂怒窃电！夺取对手 %.2f 格能量！", ap == 0 ? "震天尊" : "敌方震天尊", stolen);
                            skill_log("MEGATRONUS: SP3 Power Steal transferred %.2f mana from P%d to P%d", stolen, tp, ap);
                        }
                    }
                }
                // 保存遗迹生效时，66% 概率窃取对手 17.5% 震天尊最大生命值
                if (s_active_relic[ap] == MEGATRONUS_RELIC_PRESERVATION) {
                    float roll = skill_random_float();
                    if (roll < 0.66f) {
                        float max_hp = skill_get_max_hp(ap);
                        float steal_amount = max_hp * 0.175f;
                        skill_deal_damage(tp, steal_amount);
                        skill_heal(ap, steal_amount);
                        skill_apply_buff_dur(tp, "megatronus_life_steal", 1.0f);
                        skill_overlay("[%s] SP3 守护汲取！生命窃取 %.0f 点！", ap == 0 ? "震天尊" : "敌方震天尊", steal_amount);
                        skill_log("MEGATRONUS: SP3 Life Steal drained %.1f HP from P%d to P%d", steal_amount, tp, ap);
                    }
                }
            }
        }
    }
}

// 供外部与模拟器快速读取遗迹状态与不朽状态
static void megatronus_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "megatronus") == NULL) return;

    // 当释放 SP3 (action_type == 64) 消耗 3 格气时，将内部记录同步清零
    if (action_type == 64 || action_type == 0x40) {
        s_last_power_bar[player_index] = 0;
    }
}

int skill_get_megatronus_relic(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        return (int)s_active_relic[player_index];
    }
    return 0;
}

int skill_is_megatronus_immortal(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        return s_immortality_active[player_index];
    }
    return 0;
}

BotSkillModule g_module_megatronus = {
    .bot_prefix          = "megatronus",
    .on_hit_connected    = megatronus_on_hit_connected,
    .on_buff_gated       = NULL,
    .on_buff_applied     = NULL,
    .on_evade_check      = NULL,
    .on_test_roll        = NULL,
    .on_power_gain_rate  = megatronus_on_power_gain_rate,
    .on_reflect_proj     = NULL,
    .on_projectile_speed = NULL,
    .on_fight_reset      = megatronus_on_fight_reset,
    .on_simulation_tick  = megatronus_on_simulation_tick,
    .on_block_state      = NULL,
    .on_dodge_enter      = NULL,
    .on_hitreact_enter   = NULL,
    .on_attack_start     = megatronus_on_attack_start,
};
