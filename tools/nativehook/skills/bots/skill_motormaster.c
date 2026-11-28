#include "../skill_env.h"
#include "../skill_types.h"
#include <string.h>

/*
 * 汽车大师 (motormaster_gs_voyager2015) 战斗逻辑模块：
 * 1. 前冲不可阻挡：远距主动前冲进入不可阻挡状态
 * 2. 重击冲压：非格挡重击命中随机施加 3 选 1 减益（6 秒：21.6% 攻击减益 / 29.7% 破甲 / 24.3% 能量功率减益）
 * 3. 觉醒 公路之王：每损失 20% 生命得 1 层 +60% 近战增益（最大 4 层，无倒计时，随血量动态增减）
 * 4. SP1：末击非格挡即时扣除对手 2% 最大能量 (-0.06)
 * 5. SP2：发动进入 4.5 秒不可阻挡状态
 * 6. SP3：最后一击伤害 +150%，自伤 90% 攻击力（最低保留 1 点生命），并随机施加 6 层 6 秒冲压减益
 */

static int is_motormaster(const char* bot_id) {
    return bot_id && strstr(bot_id, "motormaster") != NULL;
}

static uint64_t s_mm_sp2_unstop_end[2] = {0, 0};

static void mm_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_mm_sp2_unstop_end[player_index] = 0;
    }
}

static void mm_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (!is_motormaster(skill_get_bot_id(p))) continue;

        if (s_mm_sp2_unstop_end[p] > 0 && now_ms >= s_mm_sp2_unstop_end[p]) {
            s_mm_sp2_unstop_end[p] = 0;
            skill_set_unstoppable(p, 0);
        }

        float hp_r = skill_get_hp_ratio(p);
        if (hp_r < 0.0f) hp_r = 0.0f;
        if (hp_r > 1.0f) hp_r = 1.0f;
        int desired = (int)((1.0f - hp_r) / 0.20f);
        if (desired > 4) desired = 4;
        if (desired < 0) desired = 0;
        int cur = skill_count_buffs(p, "motormaster_sig_king");
        if (cur < desired) {
            for (int k = cur; k < desired; k++) {
                skill_apply_buff_dur(p, "motormaster_sig_king", -1.0f);
            }
            skill_log("MOTORMASTER_SIG: P%d HP %.1f%% -> King of the Road stacks=%d (+%d%% melee)",
                      p, hp_r * 100.0f, desired, desired * 60);
        } else if (cur > desired) {
            skill_consume_buff(p, "motormaster_sig_king", cur - desired);
            skill_log("MOTORMASTER_SIG: P%d HP %.1f%% -> King of the Road reduced to stacks=%d (+%d%% melee)",
                      p, hp_r * 100.0f, desired, desired * 60);
        }
    }
}

static void mm_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    if (!is_motormaster(skill_get_bot_id(player_index))) return;

    if (action_type == 2) {
        float dist = skill_get_opponent_distance(player_index);
        if (dist >= 10.0f) {
            skill_set_motormaster_dash_unstoppable(player_index, 600);
            skill_apply_buff_dur(player_index, "motormaster_dash_unstoppable", 0.6f);
            skill_log("MOTORMASTER_DASH: P%d long dash (dist=%.1f) -> Unstoppable 0.6s", player_index, dist);
        }
    } else if (action_type == 320 || action_type == 0x202) {
        s_mm_sp2_unstop_end[player_index] = skill_now_ms() + 4500ULL;
        skill_set_unstoppable(player_index, 4500);
        skill_apply_buff_dur(player_index, "motormaster_sp2_unstoppable", 4.5f);
        skill_log("MOTORMASTER_SP2: P%d started SP2 -> Unstoppable 4.5s", player_index);
    }
}

static void mm_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2 || !entered) return;
    if (!is_motormaster(skill_get_bot_id(player_index))) return;
    if (sp_level == 2) {
        s_mm_sp2_unstop_end[player_index] = skill_now_ms() + 4500ULL;
        skill_set_unstoppable(player_index, 4500);
        skill_apply_buff_dur(player_index, "motormaster_sp2_unstoppable", 4.5f);
        skill_log("MOTORMASTER_SP2: P%d entered SP2 -> Unstoppable 4.5s", player_index);
    }
}

static void mm_apply_random_ram_debuff(int target_p, const char* atk_id, const char* arm_id, const char* pwr_id) {
    int choice = (int)(skill_random_float() * 3.0f);
    if (choice < 0) choice = 0;
    if (choice > 2) choice = 2;
    if (choice == 0) {
        skill_apply_buff_dur(target_p, atk_id, 6.0f);
    } else if (choice == 1) {
        skill_apply_buff_dur(target_p, arm_id, 6.0f);
    } else {
        skill_apply_buff_dur(target_p, pwr_id, 6.0f);
    }
}

static void mm_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 1. 汽车大师作为防守方：结算攻击方身上来自汽车大师的攻击减益 (-21.6%/层)
    if (tp >= 0 && tp < 2 && is_motormaster(ctx->target_bot_id) && ap >= 0 && ap < 2) {
        int atk_debuffs = skill_count_buffs(ap, "motormaster_heavy_atk_debuff") +
                          skill_count_buffs(ap, "motormaster_sp3_atk_debuff");
        if (atk_debuffs > 0) {
            float scale = 1.0f - 0.216f * (float)atk_debuffs;
            if (scale < 0.10f) scale = 0.10f;
            ctx->modified_damage *= scale;
        }
    }

    // 2. 汽车大师作为攻击方
    if (ap >= 0 && ap < 2 && is_motormaster(ctx->attacker_bot_id)) {
        // 觉醒 公路之王：每层 +60% 近战伤害
        if (ctx->is_melee) {
            int king_stacks = skill_count_buffs(ap, "motormaster_sig_king");
            if (king_stacks > 0) {
                ctx->modified_damage *= (1.0f + 0.60f * (float)king_stacks);
            }
        }

        // 重击冲压：非格挡重击命中随机施加 3 选 1 减益 (6s)
        if (ctx->is_heavy && !ctx->is_blocked) {
            mm_apply_random_ram_debuff(
                tp,
                "motormaster_heavy_atk_debuff",
                "motormaster_heavy_armor_break",
                "motormaster_heavy_power_debuff"
            );
            skill_log("MOTORMASTER_HEAVY: P%d rammed P%d -> applied 1 random 6s debuff", ap, tp);
        }

        // SP1：末击非格挡即时扣除对手 2% 最大能量
        if (ctx->special_index == 1 && ctx->is_last_hit && !ctx->is_blocked) {
            skill_add_mana(tp, -0.06f);
            skill_apply_buff_dur(tp, "motormaster_sp1_power_burn", 0.5f);
            skill_log("MOTORMASTER_SP1: P%d power burned P%d (-2%% max mana)", ap, tp);
        }

        // SP3：末击 +150% 伤害、自伤 90% 攻击力(最低留 1 HP)、随机施加 6 层 6s 冲压减益
        if (ctx->special_index == 3 && ctx->is_last_hit) {
            ctx->modified_damage *= 2.50f;
            float cur_hp = skill_get_hp(ap);
            float self_atk = skill_get_attack(ap);
            float recoil = self_atk * 0.90f;
            if (cur_hp > 1.0f) {
                if (recoil >= cur_hp - 1.0f) {
                    recoil = cur_hp - 1.0f;
                }
                if (recoil > 0.0f) {
                    skill_deal_damage(ap, recoil);
                }
            }
            for (int k = 0; k < 6; k++) {
                mm_apply_random_ram_debuff(
                    tp,
                    "motormaster_sp3_atk_debuff",
                    "motormaster_sp3_ram_armor",
                    "motormaster_sp3_power_debuff"
                );
            }
            skill_overlay("[%s] 冲压全开！+150%%终结并施加6层减益！",
                          ap == 0 ? "汽车大师" : "敌方汽车大师");
            skill_log("MOTORMASTER_SP3: P%d last hit +150%% dmg, recoil=%.1f, applied 6 random debuffs to P%d",
                      ap, recoil, tp);
        }
    }
}

BotSkillModule g_module_motormaster = {
    .bot_prefix         = "motormaster",
    .display_name_zh    = "汽车大师",
    .on_hit_connected   = mm_hit_connected,
    .on_fight_reset     = mm_fight_reset,
    .on_simulation_tick = mm_simulation_tick,
    .on_attack_start    = mm_attack_start,
    .on_special_state   = mm_special_state,
};
