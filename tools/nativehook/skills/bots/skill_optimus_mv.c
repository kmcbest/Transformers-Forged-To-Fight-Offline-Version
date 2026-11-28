#include "../skill_env.h"
#include "../skill_types.h"
#include <string.h>

/*
 * 电影擎天柱 (optimusprime_cin_tf) 战斗逻辑模块：
 * 1. 被动护甲增益：进入格挡获得 7 秒 16.5% 护甲增益（原生 ArmorUp 减伤；Sim 使用 #ifndef __ANDROID__ 对齐）
 * 2. 被动近战增益：任意非格挡攻击命中 10% 概率获/刷新 1 层 +60% 近战伤害增益（4 秒）
 * 3. 被动意志力：处于流血状态时将造成伤害 35% 转化为生命；最大仅保留 1 层流血，超出的流血当场净化并转化为 +10% 最大能量
 * 4. 觉醒 我会带上你们！：生命低于 20% 时每回合仅触发一次，获 1 层 90% 护甲增益（7秒）+ 3 层 44.4% 近战增益（7秒）
 * 5. SP1：按已损生命比例最高提升 150% 伤害（50% 体力时 +75%），非格挡命中 60% 施放 4 秒 40% 攻击流血
 * 6. SP2：前两击（hit_index < 2）非格挡每击 90% 概率施放 4 秒 40% 攻击流血
 * 7. SP3：每一击非格挡 60% 概率施放 4 秒 40% 攻击流血
 */

static int is_optimus_mv(const char* bot_id) {
    return bot_id && (strstr(bot_id, "optimusprime_cin_tf") != NULL || strstr(bot_id, "optimus_mv") != NULL);
}

static int s_opt_sig_used[2] = {0, 0};
static uint64_t s_opt_purify_pending_ms[2] = {0, 0};

static void optimus_mv_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_opt_sig_used[player_index] = 0;
        s_opt_purify_pending_ms[player_index] = 0;
    }
}

static void optimus_mv_check_excess_bleed(int p, uint64_t now_ms) {
    int bleed_cnt = skill_count_buffs(p, "bleed");
    if (bleed_cnt > 1) {
        int to_purify = bleed_cnt - 1;
        skill_consume_buff(p, "bleed", to_purify);
        skill_add_mana(p, 0.30f * (float)to_purify);
        skill_apply_buff_dur(p, "optimusprime_cin_tf_purify", 1.5f);
        skill_overlay("[%s] 意志力净化%d层流血，转化能量 +%d%%！",
                      p == 0 ? "电影擎天柱" : "敌方擎天柱", to_purify, to_purify * 10);
        skill_log("OPT_MV_WILLPOWER: P%d purified %d excess bleed -> +%.0f%% max mana",
                  p, to_purify, 10.0f * (float)to_purify);
        s_opt_purify_pending_ms[p] = 0;
        (void)now_ms;
    }
}

static void optimus_mv_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx) return;
    int tp = ctx->target_player_index;
    if (tp < 0 || tp >= 2 || !is_optimus_mv(ctx->target_bot_id)) return;
    if (ctx->modifier_id && strstr(ctx->modifier_id, "bleed") != NULL) {
        int bleed_cnt = skill_count_buffs(tp, "bleed");
        if (bleed_cnt > 1) {
            s_opt_purify_pending_ms[tp] = ctx->now_ms;
        }
    }
}

static void optimus_mv_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (!is_optimus_mv(skill_get_bot_id(p))) continue;

        if (s_opt_purify_pending_ms[p] > 0 && now_ms >= s_opt_purify_pending_ms[p]) {
            optimus_mv_check_excess_bleed(p, now_ms);
        }

        if (!s_opt_sig_used[p]) {
            float hp_r = skill_get_hp_ratio(p);
            if (hp_r > 0.0f && hp_r < 0.20f) {
                s_opt_sig_used[p] = 1;
                skill_apply_buff_dur(p, "optimusprime_cin_tf_sig_armor", 7.0f);
                for (int k = 0; k < 3; k++) {
                    skill_apply_buff_dur(p, "optimusprime_cin_tf_sig_melee", 7.0f);
                }
                skill_overlay("[%s] 我会带上你们！(护甲+90%% & 3层近战+44.4%%)",
                              p == 0 ? "电影擎天柱" : "敌方擎天柱");
                skill_log("OPT_MV_SIG: P%d HP %.1f%% < 20%% triggered sig armor(90%%) + 3x melee(44.4%%) for 7s",
                          p, hp_r * 100.0f);
            }
        }
    }
}

static void optimus_mv_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    if (!is_optimus_mv(skill_get_bot_id(player_index))) return;
    if (sp_level == 1) {
        if (entered) {
            if (skill_get_hp_ratio(player_index) < 0.999f) {
                skill_apply_buff_dur(player_index, "optimusprime_cin_tf_sp1_dmg_boost", 5.0f);
            }
        } else {
            skill_consume_buff(player_index, "optimusprime_cin_tf_sp1_dmg_boost", 1);
        }
    }
}

static void optimus_mv_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    // 1. 电影擎天柱受击：桌面 Sim 兜底计算被动/觉醒护甲减伤（Android 由 IL2CPP 原生 GetArmorDR 结算）
    if (tp >= 0 && tp < 2 && is_optimus_mv(ctx->target_bot_id)) {
#ifndef __ANDROID__
        float dr = 0.0f;
        if (skill_has_buff(tp, "optimusprime_cin_tf_block_armor")) dr += 0.165f;
        if (skill_has_buff(tp, "optimusprime_cin_tf_sig_armor"))   dr += 0.90f;
        if (dr > 0.0f) {
            if (dr > 0.95f) dr = 0.95f;
            float apen = ctx->armor_penetration;
            if (apen < 0.0f) apen = 0.0f;
            if (apen > 1.0f) apen = 1.0f;
            ctx->modified_damage *= (1.0f - dr * (1.0f - apen));
        }
#endif
    }

    // 2. 电影擎天柱进攻
    if (ap >= 0 && ap < 2 && is_optimus_mv(ctx->attacker_bot_id)) {
        // 近战攻击加成 (被动近战 +60% + 觉醒 +44.4% * 层数)
        if (ctx->is_melee) {
            float bonus = 0.0f;
            if (skill_has_buff(ap, "optimusprime_cin_tf_melee_buff")) {
                bonus += 0.60f;
            }
            int sig_stacks = skill_count_buffs(ap, "optimusprime_cin_tf_sig_melee");
            if (sig_stacks > 0) {
                bonus += 0.444f * (float)sig_stacks;
            }
            if (bonus > 0.0f) {
                ctx->modified_damage *= (1.0f + bonus);
            }
        }

        // SP1 伤害增益：已损生命值越多伤害越高，最高 +150%
        if (ctx->special_index == 1) {
            float hp_r = skill_get_hp_ratio(ap);
            if (hp_r < 0.0f) hp_r = 0.0f;
            if (hp_r > 1.0f) hp_r = 1.0f;
            float sp1_bonus = (1.0f - hp_r) * 1.50f;
            if (sp1_bonus > 0.0f) {
                ctx->modified_damage *= (1.0f + sp1_bonus);
                skill_log("OPT_MV_SP1: P%d lost %.1f%% HP -> SP1 bonus +%.1f%%",
                          ap, (1.0f - hp_r) * 100.0f, sp1_bonus * 100.0f);
            }
        }

        // 所有非格挡攻击命中 10% 概率获得/刷新 1 层近战增益 (+60%, 4s)
        if (!ctx->is_blocked && skill_random_float() < 0.10f) {
            skill_consume_buff(ap, "optimusprime_cin_tf_melee_buff", 1);
            skill_apply_buff_dur(ap, "optimusprime_cin_tf_melee_buff", 4.0f);
            skill_log("OPT_MV_MELEE_BUFF: P%d gained/refreshed +60%% melee buff (4.0s)", ap);
        }

        // 意志力回血：若身上存在流血，将造成伤害的 35% 转化为自身生命
        int bleed_cnt = skill_count_buffs(ap, "bleed");
        if (bleed_cnt > 0 && ctx->modified_damage > 0.0f) {
            float heal_amt = ctx->modified_damage * 0.35f;
            skill_heal(ap, heal_amt);
            skill_log("OPT_MV_WILLPOWER: P%d healed %.1f (35%% of %.1f dmg) while bleeding",
                      ap, heal_amt, ctx->modified_damage);
            if (bleed_cnt > 1) {
                optimus_mv_check_excess_bleed(ap, skill_now_ms());
            }
        }

        // SP 流血触发 (未格挡生效)
        if (!ctx->is_blocked) {
            if (ctx->special_index == 1 && skill_random_float() < 0.60f) {
                skill_apply_buff_dur(tp, "optimusprime_cin_tf_sp1_bleed", 4.0f);
            } else if (ctx->special_index == 2 && ctx->hit_index < 2 && skill_random_float() < 0.90f) {
                skill_apply_buff_dur(tp, "optimusprime_cin_tf_sp2_bleed", 4.0f);
            } else if (ctx->special_index == 3 && skill_random_float() < 0.60f) {
                skill_apply_buff_dur(tp, "optimusprime_cin_tf_sp3_bleed", 4.0f);
            }
        }
    }
}

BotSkillModule g_module_optimus_mv = {
    .bot_prefix          = "optimusprime_cin_tf",
    .display_name_zh     = "电影擎天柱",
    .on_hit_connected    = optimus_mv_hit_connected,
    .on_buff_applied     = optimus_mv_buff_applied,
    .on_fight_reset      = optimus_mv_fight_reset,
    .on_simulation_tick  = optimus_mv_simulation_tick,
    .on_special_state    = optimus_mv_special_state,
};
