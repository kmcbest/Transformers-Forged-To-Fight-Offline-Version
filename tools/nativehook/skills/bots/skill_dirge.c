#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// ===========================================================================
// 挽歌 (Dirge) 战斗专属技能模块
// Bot ID: dirge_gs_deluxe2008
// 职业: 战士系 (Warrior) | 阵营: 霸天虎 (Decepticon) / 雇佣军 (Mercenary)
// ===========================================================================
// 【核心机制对照 (来自 Server/tftf_database.db 官方技能真理源)】：
// 1. [被动 - 恐惧 / Fear] (ID: 3038):
//    - 敌人开局带着恐惧状态（常驻红色图标，无倒计时）。
//    - 敌人用近战轻攻击击中挽歌有 20% 概率驱散恐惧，中等攻击有 40% 概率驱散。
// 2. [被动 - 恐惧阴影 / Fear Influence] (ID: 3039):
//    - 恐惧被驱散后敌人进入恐惧阴影状态（灰色图标）。
//    - 敌人格挡、后闪或者侧闪累计 3 次后变回红色恐惧状态。
//    - 累计到 3 次之前只要击中挽歌，计数器清零重新计数。
// 3. [觉醒 - 冷酷的嘲讽 / Grim Mockery] (ID: 3025):
//    - 恐惧状态下敌人近战攻击被挽歌闪避，挽歌获得 60% 攻击力增益持续 5 秒（可刷新）。
//    - 触发后对方驱散恐惧的概率降低 10%（轻击 10%，中击 30%），直到下次成功驱散后恢复。
// 4. [被动 - 恐惧流血 / Bleed by Fear] (ID: 3040):
//    - 处于恐惧状态的敌人每 10 秒倒计时（灰色图标）结束施加 2 秒 145% ATK 流血伤害。
//    - 恐惧被驱散时灰色倒计时图标消失；未被驱散则施加流血并重新进入 10 秒倒计时。
// 5. [被动 - 暴击几率 / Crit Rate] (ID: 3041):
//    - 对方处于恐惧状态下，挽歌攻击提升 40% 暴击率（黄色图标随恐惧出现/消失）。
// 6. [被动 - 攻击减益 / Attack Debuff] (ID: 3042):
//    - 处于恐惧状态的敌方每次后闪或侧闪，施加 1 层 40% 攻击力减益持续 5 秒。
// 7. [被动 - 暴击伤害 / Crit Damage] (ID: 3043):
//    - 对方流血状态下，挽歌所有攻击提升 30% 暴击伤害（黄色图标随流血出现/消失）。
// 8. [被动 - 能量功率 / Power Rate] (ID: 3044):
//    - 对方流血状态下，挽歌所有攻击提升 10% 能量功率（紫色图标随流血出现/消失）。
// 9. [SP1 - 特殊伤害 / Special Damage] (ID: 3045):
//    - 对方处于恐惧状态下，此技能增加 35% 伤害（施放时挽歌侧显示橙色图标）。
// 10. [SP2 - 燃烧 / Burn] (ID: 3046):
//     - 最后一击造成 35% ATK 燃烧 4 秒；若敌方处于恐惧，则造成 70% ATK 燃烧 8 秒。
// 11. [SP3 - 终极恐惧 / Fear] (ID: 3047):
//     - 技能完成后施加 30 秒强化恐惧（白色图标），此期间内恐惧无法驱散，流血伤害翻倍(290% ATK)。
// ===========================================================================

static int      s_dirge_active[2]              = {0, 0};
static int      s_initialized[2]               = {0, 0};
static int      s_fear_active[2]               = {0, 0}; // 敌方是否处于恐惧状态 (0 或 1)
static int      s_shadow_active[2]             = {0, 0}; // 敌方是否处于恐惧阴影状态 (0 或 1)
static int      s_shadow_counter[2]            = {0, 0}; // 恐惧阴影格挡/闪避累计计数器 (0..3)
static uint64_t s_next_bleed_tick_ms[2]        = {0, 0}; // 下一次 10 秒流血结算时间戳
static uint64_t s_sp3_fear_end_ms[2]           = {0, 0}; // SP3 30 秒不可驱散强化恐惧到期时间戳
static int      s_mockery_dispel_reduction[2]  = {0, 0}; // 冷酷嘲讽：使对手驱散几率 -10% (1=生效中, 0=未生效)
static uint64_t s_last_opp_dodge_tick_ms[2]    = {0, 0}; // 对手闪避去抖时间戳
static uint64_t s_last_opp_block_tick_ms[2]    = {0, 0}; // 对手格挡去抖时间戳

static void dirge_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (bid && strstr(bid, "dirge") != NULL) {
            int opp = 1 - p;

            // 1. 开局初始化恐惧状态
            if (!s_initialized[p]) {
                s_initialized[p] = 1;
                s_dirge_active[p] = 1;
                s_fear_active[opp] = 1;
                s_shadow_active[opp] = 0;
                s_shadow_counter[opp] = 0;
                s_next_bleed_tick_ms[opp] = now_ms + 10000;
                s_sp3_fear_end_ms[opp] = 0;
                s_mockery_dispel_reduction[p] = 0;

                // 敌方开局挂常驻红色恐惧图标与 10 秒流血预备图标
                skill_apply_buff_dur(opp, "dirge_fear_debuff", -1.0f);
                skill_apply_buff_dur(opp, "dirge_bleed_timer", 10.0f);
                // 挽歌开局获得黄色暴击几率图标
                skill_apply_buff_dur(p, "dirge_fear_crit_buff", -1.0f);

                skill_overlay("[%s] 散布恐惧！敌人开局陷入恐惧状态！", p == 0 ? "挽歌" : "敌方挽歌");
                skill_log("DIRGE: Battle started! Initialized Fear on opponent P%d", opp);
            }

            // 2. 检查 SP3 强化恐惧 (30s) 到期恢复
            if (s_sp3_fear_end_ms[opp] > 0 && now_ms >= s_sp3_fear_end_ms[opp]) {
                s_sp3_fear_end_ms[opp] = 0;
                if (s_fear_active[opp]) {
                    // 恢复常规红色恐惧图标
                    skill_apply_buff_dur(opp, "dirge_fear_debuff", -1.0f);
                }
                skill_overlay("[%s] 终极恐惧结束，恢复常规恐惧状态", p == 0 ? "挽歌" : "敌方挽歌");
                skill_log("DIRGE: SP3 Empowered Fear expired on P%d, restored normal Fear", opp);
            }

            // 同步外部/沙盒状态：若存在恐惧阴影 buff，标记阴影激活
            if (skill_has_buff(opp, "dirge_fear_shadow")) {
                s_shadow_active[opp] = 1;
                s_fear_active[opp] = 0;
            }

            // 3. 恐惧流血 10 秒周期性结算
            if (s_fear_active[opp]) {
                if (s_next_bleed_tick_ms[opp] > 0 && now_ms >= s_next_bleed_tick_ms[opp]) {
                    s_next_bleed_tick_ms[opp] = now_ms + 10000;
                    // 重新开启 10 秒流血倒计时图标
                    skill_apply_buff_dur(opp, "dirge_bleed_timer", 10.0f);

                    // 检查是否处于 SP3 强化期间 (流血伤害翻倍为 290% ATK)
                    int is_sp3_empowered = (s_sp3_fear_end_ms[opp] > now_ms);
                    if (is_sp3_empowered) {
                        // 施加 2 层达到 290% ATK 暴烈流血
                        skill_apply_buff_dur(opp, "dirge_fear_bleed", 2.0f);
                        skill_apply_buff_dur(opp, "dirge_fear_bleed", 2.0f);
                        skill_overlay("[%s] 终极恐惧流血！造成 290%% 攻击力暴烈流血！", p == 0 ? "挽歌" : "敌方挽歌");
                        skill_log("DIRGE: SP3 Empowered Fear Bleed triggered on P%d (2x stacks, 290%% ATK)", opp);
                    } else {
                        skill_apply_buff_dur(opp, "dirge_fear_bleed", 2.0f);
                        skill_overlay("[%s] 恐惧流血爆发！造成 145%% 攻击力流血！", p == 0 ? "挽歌" : "敌方挽歌");
                        skill_log("DIRGE: Fear Bleed triggered on P%d (145%% ATK)", opp);
                    }
                }
            }

            // 4. 维护挽歌因对手流血而激活的暴伤 (+30%) 与能量功率 (+10%) 图标
            int opp_bleeding = (skill_has_buff(opp, "bleed") || skill_has_buff(opp, "dirge_fear_bleed"));
            if (opp_bleeding) {
                if (!skill_has_buff(p, "dirge_bleed_crit_dmg")) {
                    skill_apply_buff_dur(p, "dirge_bleed_crit_dmg", -1.0f);
                }
                if (!skill_has_buff(p, "dirge_bleed_power_rate")) {
                    skill_apply_buff_dur(p, "dirge_bleed_power_rate", -1.0f);
                }
            } else {
                if (skill_has_buff(p, "dirge_bleed_crit_dmg")) {
                    skill_consume_buff(p, "dirge_bleed_crit_dmg", 99);
                }
                if (skill_has_buff(p, "dirge_bleed_power_rate")) {
                    skill_consume_buff(p, "dirge_bleed_power_rate", 99);
                }
            }
        }
    }
}

// 敌方闪避 (后闪或侧闪) 回调
static void dirge_on_opponent_dodge_enter(int opponent_index) {
    if (opponent_index < 0 || opponent_index >= 2) return;
    int dirge_p = 1 - opponent_index;
    const char* bid = skill_get_bot_id(dirge_p);
    if (!bid || strstr(bid, "dirge") == NULL) return;

    uint64_t now_ms = skill_now_ms();
    if (now_ms - s_last_opp_dodge_tick_ms[opponent_index] < 150) return; // 去抖保护
    s_last_opp_dodge_tick_ms[opponent_index] = now_ms;

    int in_shadow = s_shadow_active[opponent_index] || skill_has_buff(opponent_index, "dirge_fear_shadow");
    int in_fear = s_fear_active[opponent_index] || skill_has_buff(opponent_index, "dirge_fear_debuff") || skill_has_buff(opponent_index, "dirge_sp3_fear_empower");

    // 场景 A：敌方处于恐惧阴影状态，闪避增加 1 次计数
    if (in_shadow) {
        s_shadow_active[opponent_index] = 1;
        s_fear_active[opponent_index] = 0;
        s_shadow_counter[opponent_index]++;
        skill_overlay("[%s] 闪避！恐惧阴影累计 %d/3 次",
                      opponent_index == 0 ? "我方" : "敌方", s_shadow_counter[opponent_index]);
        skill_log("DIRGE: Opponent P%d dodged under Fear Shadow, counter = %d/3",
                  opponent_index, s_shadow_counter[opponent_index]);

        if (s_shadow_counter[opponent_index] >= 3) {
            // 累计满 3 次变回红色恐惧状态
            s_shadow_counter[opponent_index] = 0;
            s_shadow_active[opponent_index] = 0;
            s_fear_active[opponent_index] = 1;
            skill_consume_buff(opponent_index, "dirge_fear_shadow", 99);
            skill_apply_buff_dur(opponent_index, "dirge_fear_debuff", -1.0f);
            skill_apply_buff_dur(opponent_index, "dirge_bleed_timer", 10.0f);
            s_next_bleed_tick_ms[opponent_index] = now_ms + 10000;
            skill_apply_buff_dur(dirge_p, "dirge_fear_crit_buff", -1.0f);

            skill_overlay("[%s] 累计满3次！恐惧阴影爆发，重新陷入恐惧！",
                          opponent_index == 0 ? "我方" : "敌方");
            skill_log("DIRGE: Fear Shadow counter reached 3! Restored Fear on P%d", opponent_index);
        }
    }
    // 场景 B：敌方处于恐惧状态，每次闪避施加 1 层 40% 攻击力减益 (5秒)
    else if (in_fear) {
        skill_apply_buff_dur(opponent_index, "dirge_evade_atk_debuff", 5.0f);
        skill_overlay("[%s] 恐惧中闪避！遭受 -40%% 攻击力减益 (5秒)！",
                      opponent_index == 0 ? "我方" : "敌方");
        skill_log("DIRGE: Opponent P%d dodged under Fear, applied 40%% attack debuff", opponent_index);
    }
}

// 敌方格挡回调
static void dirge_on_opponent_block_state(int opponent_index, int entered) {
    if (opponent_index < 0 || opponent_index >= 2 || !entered) return;
    int dirge_p = 1 - opponent_index;
    const char* bid = skill_get_bot_id(dirge_p);
    if (!bid || strstr(bid, "dirge") == NULL) return;

    uint64_t now_ms = skill_now_ms();
    if (now_ms - s_last_opp_block_tick_ms[opponent_index] < 150) return; // 去抖保护
    s_last_opp_block_tick_ms[opponent_index] = now_ms;

    int in_shadow = s_shadow_active[opponent_index] || skill_has_buff(opponent_index, "dirge_fear_shadow");

    // 敌方处于恐惧阴影状态，格挡增加 1 次计数
    if (in_shadow) {
        s_shadow_active[opponent_index] = 1;
        s_fear_active[opponent_index] = 0;
        s_shadow_counter[opponent_index]++;
        skill_overlay("[%s] 格挡！恐惧阴影累计 %d/3 次",
                      opponent_index == 0 ? "我方" : "敌方", s_shadow_counter[opponent_index]);
        skill_log("DIRGE: Opponent P%d blocked under Fear Shadow, counter = %d/3",
                  opponent_index, s_shadow_counter[opponent_index]);

        if (s_shadow_counter[opponent_index] >= 3) {
            // 累计满 3 次变回红色恐惧状态
            s_shadow_counter[opponent_index] = 0;
            s_shadow_active[opponent_index] = 0;
            s_fear_active[opponent_index] = 1;
            skill_consume_buff(opponent_index, "dirge_fear_shadow", 99);
            skill_apply_buff_dur(opponent_index, "dirge_fear_debuff", -1.0f);
            skill_apply_buff_dur(opponent_index, "dirge_bleed_timer", 10.0f);
            s_next_bleed_tick_ms[opponent_index] = now_ms + 10000;
            skill_apply_buff_dur(dirge_p, "dirge_fear_crit_buff", -1.0f);

            skill_overlay("[%s] 累计满3次！恐惧阴影爆发，重新陷入恐惧！",
                          opponent_index == 0 ? "我方" : "敌方");
            skill_log("DIRGE: Fear Shadow counter reached 3! Restored Fear on P%d", opponent_index);
        }
    }
}

// 闪避检定回调 (觉醒：冷酷嘲讽)
static int dirge_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx) return 0;
    if (ctx->bot_id && strstr(ctx->bot_id, "dirge") != NULL) {
        int p = ctx->player_index;
        int opp = 1 - p;

        // 若为近战攻击且挽歌成功规避
        if (!ctx->is_ranged && (ctx->original_evade_result || ctx->force_guaranteed)) {
            if (s_fear_active[opp]) {
                // 激活冷酷嘲讽：+60% 攻击力增益持续 5 秒 (不可叠加，可刷新)
                skill_apply_buff_dur(p, "dirge_sig_mockery", 5.0f);
                // 对方驱散恐惧的概率降低 10%，直到下次成功驱散后恢复
                s_mockery_dispel_reduction[p] = 1;

                skill_overlay("[%s] 闪避近战！冷酷嘲讽：+60%% 攻击力(5秒)，对手驱散几率-10%%！",
                              p == 0 ? "挽歌" : "敌方挽歌");
                skill_log("DIRGE: Evaded melee under fear! Activated Grim Mockery (+60%% ATK, -10%% dispel chance)");
            }
        }
    }
    return 0;
}

// 命中伤害与状态转换回调
static void dirge_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // =========================================================================
    // 1. 挽歌作为受击方 (Target): 判定对手轻/中击驱散恐惧，或阴影计数器清零
    // =========================================================================
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "dirge") != NULL) {
        int dirge_p = ctx->target_player_index;
        int opp = ctx->attacker_player_index;

        // a) 阴影状态下击中挽歌：计数器清零重新计数
        if (s_shadow_active[opp]) {
            if (s_shadow_counter[opp] > 0) {
                s_shadow_counter[opp] = 0;
                skill_overlay("[%s] 击中挽歌！恐惧阴影计数清零重新计数！",
                              opp == 0 ? "我方" : "敌方");
                skill_log("DIRGE: Opponent P%d hit Dirge under Fear Shadow, counter reset to 0", opp);
            }
        }

        // b) 恐惧状态下近战轻击/中击击中挽歌：概率驱散恐惧
        if (s_fear_active[opp]) {
            // SP3 强化恐惧期间无法被驱散
            if (s_sp3_fear_end_ms[opp] > now_ms) {
                skill_log("DIRGE: Opponent hit Dirge but Fear is SP3 Empowered (cannot be dispelled)");
            } else if (!ctx->is_ranged && ctx->special_index == 0) {
                float base_chance = 0.0f;
                if (ctx->action_type == 1) {
                    base_chance = 0.20f; // 轻攻击 20% 几率
                } else if (ctx->action_type == 2) {
                    base_chance = 0.40f; // 中等攻击 40% 几率
                }

                if (base_chance > 0.0f) {
                    if (s_mockery_dispel_reduction[dirge_p]) {
                        base_chance -= 0.10f; // 冷酷嘲讽：使驱散几率降低 10%
                    }
                    if (base_chance < 0.05f) base_chance = 0.05f;

                    float roll = skill_random_float();
                    if (roll < base_chance) {
                        // 驱散成功！
                        s_fear_active[opp] = 0;
                        s_shadow_active[opp] = 1;
                        s_shadow_counter[opp] = 0;
                        s_mockery_dispel_reduction[dirge_p] = 0; // 成功驱散后恢复降率

                        // 移除敌方恐惧与流血预备图标
                        skill_consume_buff(opp, "dirge_fear_debuff", 99);
                        skill_consume_buff(opp, "dirge_bleed_timer", 99);
                        // 移除挽歌暴击几率黄色图标
                        skill_consume_buff(dirge_p, "dirge_fear_crit_buff", 99);
                        // 施加敌方恐惧阴影灰色图标
                        skill_apply_buff_dur(opp, "dirge_fear_shadow", -1.0f);

                        skill_overlay("[%s] 近战命中！成功驱散恐惧，进入恐惧阴影！",
                                      opp == 0 ? "我方" : "敌方");
                        skill_log("DIRGE: Opponent P%d dispelled Fear (roll=%.2f < %.2f), entered Fear Shadow",
                                  opp, roll, base_chance);
                    } else {
                        skill_log("DIRGE: Opponent P%d failed to dispel Fear (roll=%.2f >= %.2f)",
                                  opp, roll, base_chance);
                    }
                }
            }
        }

        // c) 处于恐惧状态的对手身上有攻击减益时，承受伤害削减 40%
        if (skill_has_buff(opp, "dirge_evade_atk_debuff")) {
            ctx->modified_damage *= 0.60f;
            skill_log("DIRGE: Feared opponent attack damage reduced by 40%% (%.1f -> %.1f)",
                      ctx->base_damage, ctx->modified_damage);
        }
    }

    // =========================================================================
    // 2. 挽歌作为攻击方 (Attacker): 暴伤加成、SP1加成、SP2双模燃烧、SP3强化恐惧
    // =========================================================================
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "dirge") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // a) 冷酷嘲讽 60% 攻击力增益
        if (skill_has_buff(ap, "dirge_sig_mockery")) {
            ctx->modified_damage *= 1.60f;
            skill_log("DIRGE: Grim Mockery active, damage boosted x1.60");
        }

        // b) 敌方处于流血状态时，挽歌暴击提升 30% 暴击伤害
        if (ctx->is_crit && (skill_has_buff(tp, "bleed") || skill_has_buff(tp, "dirge_fear_bleed"))) {
            ctx->modified_damage *= 1.30f;
            skill_overlay("[%s] 暴伤强化！暴击伤害提升 30%%！", ap == 0 ? "挽歌" : "敌方挽歌");
            skill_log("DIRGE: Crit damage boosted x1.30 against bleeding opponent P%d", tp);
        }

        // c) SP1 特殊伤害：对方处于恐惧状态下，此技能增加 35% 伤害
        if (ctx->special_index == 1 && s_fear_active[tp]) {
            ctx->modified_damage *= 1.35f;
            skill_overlay("[%s] 特殊伤害！SP1 增加 35%% 伤害！", ap == 0 ? "挽歌" : "敌方挽歌");
            skill_log("DIRGE: SP1 damage boosted x1.35 against feared opponent P%d", tp);
        }

        // d) SP2 燃烧：最后一击命中时施加燃烧
        if (ctx->special_index == 2 && ctx->is_last_hit) {
            if (s_fear_active[tp]) {
                // 恐惧状态下造成 70% 攻击力燃烧持续 8 秒
                skill_apply_buff_dur(tp, "dirge_sp2_burn_fear", 8.0f);
                skill_overlay("[%s] 暴烈燃烧！施加 8秒 70%% 攻击力燃烧！", ap == 0 ? "挽歌" : "敌方挽歌");
                skill_log("DIRGE: Applied 8s 70%% Burn against feared opponent P%d", tp);
            } else {
                // 普通状态下造成 35% 攻击力燃烧持续 4 秒
                skill_apply_buff_dur(tp, "dirge_sp2_burn", 4.0f);
                skill_overlay("[%s] 烈焰喷射！施加 4秒 35%% 攻击力燃烧！", ap == 0 ? "挽歌" : "敌方挽歌");
                skill_log("DIRGE: Applied 4s 35%% Burn against opponent P%d", tp);
            }
        }

        // e) SP3 终极恐惧：技能完成后施加 30 秒恐惧，绝对无法驱散，流血伤害翻倍
        if (ctx->special_index == 3 && ctx->is_last_hit) {
            s_sp3_fear_end_ms[tp] = now_ms + 30000;
            s_fear_active[tp] = 1;
            s_shadow_active[tp] = 0;
            s_shadow_counter[tp] = 0;

            // 替换为白色终极恐惧图标
            skill_consume_buff(tp, "dirge_fear_debuff", 99);
            skill_consume_buff(tp, "dirge_fear_shadow", 99);
            skill_apply_buff_dur(tp, "dirge_sp3_fear_empower", 30.0f);
            skill_apply_buff_dur(ap, "dirge_fear_crit_buff", -1.0f);

            // 重新开启 10 秒流血倒计时
            skill_apply_buff_dur(tp, "dirge_bleed_timer", 10.0f);
            s_next_bleed_tick_ms[tp] = now_ms + 10000;

            skill_overlay("[%s] SP3 无处可逃！30秒终极恐惧：不可驱散，流血翻倍！",
                          ap == 0 ? "挽歌" : "敌方挽歌");
            skill_log("DIRGE: SP3 finished! Applied 30s Empowered Fear on opponent P%d", tp);
        }
    }
}

// 能量功率加成回调
static int dirge_on_power_gain_rate(int player_index, float* out_mult) {
    if (!out_mult) return 0;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "dirge") == NULL) return 0;

    int opp = 1 - player_index;
    if (skill_has_buff(opp, "bleed") || skill_has_buff(opp, "dirge_fear_bleed")) {
        *out_mult = 1.10f; // 对方流血状态下提升 10% 能量功率
        return 1;
    }
    return 0;
}

// 特殊攻击动作发起回调 (SP1 橙色图标展示)
static void dirge_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "dirge") == NULL) return;

    // SP1 发动时 (action_type == 16)
    if (action_type == 16) {
        int opp = 1 - player_index;
        if (s_fear_active[opp]) {
            skill_apply_buff_dur(player_index, "dirge_sp1_fear_boost", 3.0f);
            skill_log("DIRGE: SP1 started against feared opponent, displayed orange boost icon");
        }
    }
}

// 战斗重置回调
static void dirge_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_dirge_active[player_index]             = 0;
        s_initialized[player_index]              = 0;
        s_fear_active[player_index]              = 0;
        s_shadow_active[player_index]            = 0;
        s_shadow_counter[player_index]           = 0;
        s_next_bleed_tick_ms[player_index]       = 0;
        s_sp3_fear_end_ms[player_index]          = 0;
        s_mockery_dispel_reduction[player_index] = 0;
        s_last_opp_dodge_tick_ms[player_index]   = 0;
        s_last_opp_block_tick_ms[player_index]   = 0;
    }
}

BotSkillModule g_module_dirge = {
    .bot_prefix              = "dirge",
    .on_hit_connected        = dirge_on_hit_connected,
    .on_buff_gated           = NULL,
    .on_buff_applied         = NULL,
    .on_evade_check          = dirge_on_evade_check,
    .on_test_roll            = NULL,
    .on_power_gain_rate      = dirge_on_power_gain_rate,
    .on_reflect_proj         = NULL,
    .on_projectile_speed     = NULL,
    .on_fight_reset          = dirge_on_fight_reset,
    .on_simulation_tick      = dirge_on_simulation_tick,
    .on_block_state          = NULL,
    .on_dodge_enter          = NULL,
    .on_opponent_block_state = dirge_on_opponent_block_state,
    .on_opponent_dodge_enter = dirge_on_opponent_dodge_enter,
    .on_hitreact_enter       = NULL,
    .on_attack_start         = dirge_on_attack_start,
};
