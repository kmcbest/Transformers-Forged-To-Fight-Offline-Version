#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdio.h>

// ===========================================================================
// 暗天陨 / 黑暗擎天柱 (Nemesis Prime Voyager 2015) 技能模块
// Bot ID: nemesisprime_gs_voyager2015
// ===========================================================================
// 1. [3209] 被动：黑暗能量 (Dark Energy Charges)
//    50~100% 血量每 10s 1层，15~50% 每 7s 1层，<15% 每 5s 1层，最多 10 层。
//    开局紫色 (#D204F6) 倒计时图标 (\uE407)，走完获得紫色 (\uE90A) 层数图标，满 10 层消失，少于 10 层恢复。
// 2. [3217] 被动：亚空间脉冲克隆体 (Subspace Impulse Cloner)
//    对手获得近战或护甲增益时 25% + 5%/层 概率在自身复制相同增益（同强度同时间）。
// 3. [3218] 被动：重击驱散 (Heavy Nullify)
//    重击命中时随机驱散对手 1 个近战或护甲增益（无则不驱散）；每层黑暗能量重击伤害 +5%。
// 4. [3221] 觉醒：赝品领导模块 (Artificial Matrix)
//    所有特殊技实际造成伤害的 25% 转化为自身生命值（每段独立结算并显现绿色 E503）。
// 5. [SP1] 黑暗能量斩 (Dark Energon Chop)
//    末击 30% + 3%/层 概率将自身所有减益按原强度原时间复制到对手身上；技能结束获 2 层黑暗能量。
// 6. [SP2] 邪恶之斧 · 驱散 (Axe of Evil / Nullify)
//    每击分别 50% + 5%/层 概率驱散对手近战增益（施加4s 5%近战减益）与护甲增益（施加4s 5%破甲），
//    每驱散 1 个增益消耗 3 层黑暗能量。
// 7. [SP3] 不可防御 (No Matter the Obstacle)
//    技能结束后基础攻击不可防御 7s + 0.5s/层，消耗全部黑暗能量。
// ===========================================================================

static int      s_nemesis_active[2]             = {0, 0};
static int      s_nemesis_dark_stacks[2]        = {0, 0};
static uint64_t s_last_dark_charge_ms[2]        = {0, 0};
static uint64_t s_current_dark_interval_ms[2]   = {10000, 10000};
static int      s_nemesis_cloning[2]            = {0, 0};
static int      s_nemesis_adding_stack[2]       = {0, 0};

static float get_nemesis_cd_seconds(int p, uint64_t* out_interval_ms) {
    float hp_ratio = skill_get_hp_ratio(p);
    if (hp_ratio < 0.15f) {
        if (out_interval_ms) *out_interval_ms = 5000;
        return 5.0f;
    } else if (hp_ratio < 0.50f) {
        if (out_interval_ms) *out_interval_ms = 7000;
        return 7.0f;
    } else {
        if (out_interval_ms) *out_interval_ms = 10000;
        return 10.0f;
    }
}

static void nemesis_restart_cd_if_needed(int p, uint64_t now_ms) {
    if (p < 0 || p > 1 || s_nemesis_dark_stacks[p] >= 10) return;
    if (s_last_dark_charge_ms[p] == 0) {
        uint64_t next_ms = 10000;
        float dur = get_nemesis_cd_seconds(p, &next_ms);
        s_last_dark_charge_ms[p] = now_ms;
        s_current_dark_interval_ms[p] = next_ms;
        skill_apply_buff_dur(p, "nemesisprime_dark_cd", dur);
    }
}

static void nemesis_add_dark_stacks(int p, int count, uint64_t now_ms) {
    if (p < 0 || p > 1 || count <= 0) return;
    int added = 0;
    while (added < count && s_nemesis_dark_stacks[p] < 10) {
        s_nemesis_dark_stacks[p]++;
        s_nemesis_adding_stack[p] = 1;
        skill_apply_buff_dur(p, "nemesisprime_dark_energy", -1.0f);
        s_nemesis_adding_stack[p] = 0;
        added++;
    }
    if (s_nemesis_dark_stacks[p] >= 10) {
        skill_consume_buff(p, "nemesisprime_dark_cd", 99);
        s_last_dark_charge_ms[p] = 0;
    } else {
        nemesis_restart_cd_if_needed(p, now_ms);
    }
}

static void nemesis_consume_dark_stacks(int p, int count, uint64_t now_ms) {
    if (p < 0 || p > 1 || count <= 0 || s_nemesis_dark_stacks[p] <= 0) return;
    int actual = (count >= s_nemesis_dark_stacks[p]) ? s_nemesis_dark_stacks[p] : count;
    s_nemesis_dark_stacks[p] -= actual;
    skill_consume_buff(p, "nemesisprime_dark_energy", actual);
    nemesis_restart_cd_if_needed(p, now_ms);
}

static int nemesis_is_opponent_melee_or_armor_buff(const char* mod_id, void* stat_modifier) {
    if (!mod_id || !mod_id[0]) return 0;
    if (strstr(mod_id, "nemesisprime_") != NULL) return 0;
    if (strstr(mod_id, "debuff") != NULL || strstr(mod_id, "break") != NULL ||
        strstr(mod_id, "pierce") != NULL || strstr(mod_id, "evade") != NULL ||
        strstr(mod_id, "resist") != NULL || strstr(mod_id, "gp_") != NULL) {
        return 0;
    }
    if (stat_modifier && skill_obj_ok(stat_modifier)) {
        void* bcg_sm = *(void**)((char*)stat_modifier + 0x18);
        if (bcg_sm && skill_obj_ok(bcg_sm)) {
            int32_t mt = *(int32_t*)((char*)bcg_sm + 0x4C);
            if (mt == 2 || mt == 16) return 0;
        }
    }
    int is_armor = strstr(mod_id, "armor_up") != NULL || strstr(mod_id, "armor_buff") != NULL ||
                   strstr(mod_id, "block_armor") != NULL || strstr(mod_id, "_armor") != NULL;
    int is_melee = strstr(mod_id, "melee_buff") != NULL || strstr(mod_id, "melee_bonus") != NULL ||
                   (strstr(mod_id, "melee") != NULL && (strstr(mod_id, "buff") != NULL || strstr(mod_id, "boost") != NULL));
    return is_armor || is_melee;
}

static void nemesis_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (s_nemesis_active[p] && s_nemesis_dark_stacks[p] < 10 && s_last_dark_charge_ms[p] > 0) {
            // 若战斗中血量降档（如 <50% 或 <15%），实时缩短当前充能周期阈值
            uint64_t target_ms = 10000;
            get_nemesis_cd_seconds(p, &target_ms);
            if (target_ms < s_current_dark_interval_ms[p]) {
                s_current_dark_interval_ms[p] = target_ms;
            }
            if (now_ms >= s_last_dark_charge_ms[p] &&
                now_ms - s_last_dark_charge_ms[p] >= s_current_dark_interval_ms[p]) {
                s_nemesis_dark_stacks[p]++;
                skill_consume_buff(p, "nemesisprime_dark_cd", 99);
                s_nemesis_adding_stack[p] = 1;
                skill_apply_buff_dur(p, "nemesisprime_dark_energy", -1.0f);
                s_nemesis_adding_stack[p] = 0;
                skill_overlay("[%s] 黑暗能量充能 (%d/10)",
                              p == 0 ? "暗天陨" : "敌方暗天陨", s_nemesis_dark_stacks[p]);
                skill_log("NEMESIS: P%d gained Dark Energy stack %d/10", p, s_nemesis_dark_stacks[p]);

                if (s_nemesis_dark_stacks[p] < 10) {
                    uint64_t next_ms = 10000;
                    float dur = get_nemesis_cd_seconds(p, &next_ms);
                    s_last_dark_charge_ms[p] = now_ms;
                    s_current_dark_interval_ms[p] = next_ms;
                    skill_apply_buff_dur(p, "nemesisprime_dark_cd", dur);
                } else {
                    s_last_dark_charge_ms[p] = 0;
                    skill_log("NEMESIS: P%d Dark Energy reached 10/10, countdown hidden", p);
                }
            }
        }
    }
}

static void nemesis_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    uint64_t now_ms = skill_now_ms();

    // A. 对手持有暗天陨 SP2 施加的 5% 可叠加近战减益 (-5% / 层)
    if (ap >= 0 && ap < 2 && !ctx->is_ranged && ctx->special_index == 0) {
        int m_debuffs = skill_count_buffs(ap, "nemesisprime_sp2_melee_debuff");
        if (m_debuffs > 0) {
            float mult = 1.0f - 0.05f * (float)m_debuffs;
            if (mult < 0.10f) mult = 0.10f;
            ctx->modified_damage *= mult;
            skill_log("NEMESIS_SP2: P%d melee weakened by %dx melee_debuff (-%.0f%% -> dmg=%.1f)",
                      ap, m_debuffs, (1.0f - mult) * 100.0f, ctx->modified_damage);
        }
    }

    // B. 暗天陨作为攻击方 (Attacker):
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "nemesisprime") != NULL) {
        if (ap < 0 || ap > 1 || tp < 0 || tp > 1) return;

        // 1. [3218] 重击：每层黑暗能量重击伤害 +5%
        if (ctx->is_heavy && s_nemesis_dark_stacks[ap] > 0) {
            float boost = 1.0f + (0.05f * (float)s_nemesis_dark_stacks[ap]);
            ctx->modified_damage *= boost;
            skill_overlay("[%s] %d 层黑暗能量加持！重击增伤 %.0f%%！",
                          ap == 0 ? "暗天陨" : "敌方暗天陨",
                          s_nemesis_dark_stacks[ap], (boost - 1.0f) * 100.0f);
            skill_log("NEMESIS_HEAVY: P%d %d dark stacks -> heavy dmg +%.0f%% (%.1f)",
                      ap, s_nemesis_dark_stacks[ap], (boost - 1.0f) * 100.0f, ctx->modified_damage);
        }

        // 2. [3221] 觉醒：赝品领导模块 (每击将实际特技伤害的 25% 转为自身生命值 + 绿色 E503)
        if (ctx->special_index > 0 || ctx->action_type == 16 || ctx->action_type == 32 || ctx->action_type == 64) {
            float lifesteal_amount = ctx->modified_damage * 0.25f;
            if (lifesteal_amount > 0.0f) {
                skill_heal(ap, lifesteal_amount);
                skill_apply_buff_dur(ap, "nemesisprime_matrix_lifesteal", 1.0f);
                skill_overlay("[%s] 赝品领导模块吸血！(+%.0f HP)",
                              ap == 0 ? "暗天陨" : "敌方暗天陨", lifesteal_amount);
                skill_log("NEMESIS_MATRIX: P%d SP%d hit lifesteal +%.1f HP (25%% of %.1f)",
                          ap, ctx->special_index, lifesteal_amount, ctx->modified_damage);
            }
        }

        if (ctx->is_blocked) return;

        if (ctx->special_index == 0 && skill_has_buff(ap, "nemesisprime_sp3_unblockable")) {
            skill_log("NEMESIS_SP3: P%d basic attack (al=%d) pierced guard cleanly (unblockable blk=0)", ap, ctx->action_type);
        }

        // 3. [3218] 重击驱散：随机驱散对手 1 个近战或护甲增益（无则不驱散）
        if (ctx->is_heavy && ctx->is_last_hit) {
            char removed_id[64] = {0};
            if (skill_dispel_random_buff_by_category(tp, 1, 1, removed_id, sizeof(removed_id))) {
                skill_apply_buff_dur(tp, "nemesisprime_heavy_dispel", 0.8f);
                skill_overlay("[%s] 重击驱散！移除对手 [%s]！",
                              ap == 0 ? "暗天陨" : "敌方暗天陨", removed_id);
                skill_log("NEMESIS_HEAVY_DISPEL: P%d dispelled '%s' from P%d", ap, removed_id, tp);
            } else {
                skill_log("NEMESIS_HEAVY_DISPEL: P%d heavy hit, P%d had no melee/armor buff to dispel", ap, tp);
            }
        }

        // 4. SP1 黑暗能量斩：末击 30% + 3%/层 概率把自身全部减益按原强度原时间复制给对手
        if ((ctx->special_index == 1 || ctx->action_type == 16) && ctx->is_last_hit) {
            float copy_chance = 0.30f + 0.03f * (float)s_nemesis_dark_stacks[ap];
            float r = skill_random_float();
            if (r < copy_chance) {
                int copied = skill_copy_self_debuffs_to_opponent(ap, tp);
                if (copied > 0) {
                    skill_apply_buff_dur(tp, "nemesisprime_sp1_clone_debuff", 1.2f);
                    skill_overlay("[%s] 黑暗能量斩！复制 %d 个减益至对手！",
                                  ap == 0 ? "暗天陨" : "敌方暗天陨", copied);
                }
                skill_log("NEMESIS_SP1: P%d lastHit cloned %d debuffs to P%d (roll=%.3f<%.2f)",
                          ap, copied, tp, r, copy_chance);
            } else {
                skill_log("NEMESIS_SP1: P%d lastHit clone missed (roll=%.3f>=%.2f)", ap, r, copy_chance);
            }
        }

        // 5. SP2 邪恶之斧：每击独立 50%+5%/层 驱散近战增益(->4s 5%近战减益)与护甲增益(->4s 5%破甲)，每驱散1个消耗3层黑暗能量
        if (ctx->special_index == 2 || ctx->action_type == 32) {
            float base_chance = 0.50f + 0.05f * (float)s_nemesis_dark_stacks[ap];
            char removed_id[64] = {0};

            // 分支 5a: 驱散近战增益 -> 5% 近战减益 4s
            if (skill_random_float() < base_chance) {
                if (skill_dispel_random_buff_by_category(tp, 1, 0, removed_id, sizeof(removed_id))) {
                    skill_apply_buff_dur(tp, "nemesisprime_sp2_melee_debuff", 4.0f);
                    nemesis_consume_dark_stacks(ap, 3, now_ms);
                    skill_overlay("[%s] 邪恶之斧驱散近战 [%s] -> 施加5%%近战减益(4s)！",
                                  ap == 0 ? "暗天陨" : "敌方暗天陨", removed_id);
                    skill_log("NEMESIS_SP2: P%d hit%d dispelled melee '%s' -> melee_debuff(5%%,4s), stacks=%d",
                              ap, ctx->hit_index, removed_id, s_nemesis_dark_stacks[ap]);
                }
            }

            // 分支 5b: 驱散护甲增益 -> 5% 破甲 4s
            float armor_chance = 0.50f + 0.05f * (float)s_nemesis_dark_stacks[ap];
            if (skill_random_float() < armor_chance) {
                if (skill_dispel_random_buff_by_category(tp, 0, 1, removed_id, sizeof(removed_id))) {
                    skill_apply_buff_dur(tp, "nemesisprime_sp2_armor_break", 4.0f);
                    nemesis_consume_dark_stacks(ap, 3, now_ms);
                    skill_overlay("[%s] 邪恶之斧驱散护甲 [%s] -> 施加5%%破甲(4s)！",
                                  ap == 0 ? "暗天陨" : "敌方暗天陨", removed_id);
                    skill_log("NEMESIS_SP2: P%d hit%d dispelled armor '%s' -> armor_break(5%%,4s), stacks=%d",
                              ap, ctx->hit_index, removed_id, s_nemesis_dark_stacks[ap]);
                }
            }
        }
    }
}

static void nemesis_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;

    int tp = ctx->target_player_index;
    if (tp < 0 || tp > 1) return;

    // 1. 黑暗能量倒计时启动 / 外部同步层数
    if (strstr(ctx->modifier_id, "nemesisprime_dark_cd") != NULL) {
        s_nemesis_active[tp] = 1;
        if (s_last_dark_charge_ms[tp] == 0) {
            uint64_t next_ms = 10000;
            float dur = get_nemesis_cd_seconds(tp, &next_ms);
            s_last_dark_charge_ms[tp] = skill_now_ms();
            s_current_dark_interval_ms[tp] = next_ms;
            skill_log("NEMESIS: Initial Dark Energy CD (%.1fs) started on P%d", dur, tp);
        }
        return;
    }
    if (strcmp(ctx->modifier_id, "nemesisprime_dark_energy") == 0) {
        s_nemesis_active[tp] = 1;
        if (!s_nemesis_adding_stack[tp] && s_nemesis_dark_stacks[tp] < 10) {
            s_nemesis_dark_stacks[tp]++;
            if (s_nemesis_dark_stacks[tp] >= 10) {
                skill_consume_buff(tp, "nemesisprime_dark_cd", 99);
                s_last_dark_charge_ms[tp] = 0;
            }
        }
        return;
    }
}

// 2. [3217] 亚空间脉冲克隆体：对手获得近战或护甲增益时，25% + 5%/层 复制同强度同时间增益至暗天陨
static void nemesis_on_opponent_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    int tp = ctx->target_player_index;
    if (tp < 0 || tp > 1) return;
    int opp_nemesis = 1 - tp;
    const char* nem_bid = skill_get_bot_id(opp_nemesis);
    if (!nem_bid || strstr(nem_bid, "nemesisprime") == NULL || s_nemesis_cloning[opp_nemesis]) {
        return;
    }
    if (nemesis_is_opponent_melee_or_armor_buff(ctx->modifier_id, ctx->stat_modifier)) {
        float clone_chance = 0.25f + 0.05f * (float)s_nemesis_dark_stacks[opp_nemesis];
        float r = skill_random_float();
        if (r < clone_chance) {
            s_nemesis_cloning[opp_nemesis] = 1;
            int ok = skill_clone_buff_from_opponent(opp_nemesis, tp, ctx->modifier_id);
            s_nemesis_cloning[opp_nemesis] = 0;
            if (ok) {
                skill_apply_buff_dur(opp_nemesis, "nemesisprime_subspace_cloner", 1.2f);
                skill_overlay("[%s] 亚空间脉冲克隆！复制了对手的 [%s]！",
                              opp_nemesis == 0 ? "暗天陨" : "敌方暗天陨", ctx->modifier_id);
                skill_log("NEMESIS_CLONER: P%d cloned '%s' from P%d (roll=%.3f<%.2f)",
                          opp_nemesis, ctx->modifier_id, tp, r, clone_chance);
            }
        } else {
            skill_log("NEMESIS_CLONER: P%d missed clone '%s' (roll=%.3f>=%.2f)",
                      opp_nemesis, ctx->modifier_id, r, clone_chance);
        }
    }
}

static void nemesis_on_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index > 1) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "nemesisprime") == NULL) return;
    uint64_t now_ms = skill_now_ms();

    // SP1 结束时立即获得 2 层黑暗能量充能 (上限 10)
    if (sp_level == 1 && !entered) {
        nemesis_add_dark_stacks(player_index, 2, now_ms);
        skill_overlay("[%s] 黑暗能量斩完成！获得 +2 层黑暗能量 (%d/10)！",
                      player_index == 0 ? "暗天陨" : "敌方暗天陨", s_nemesis_dark_stacks[player_index]);
        skill_log("NEMESIS_SP1: P%d SP1 ended -> gained +2 dark stacks (now %d/10)",
                  player_index, s_nemesis_dark_stacks[player_index]);
    }

    // SP3 结束：消耗全部黑暗能量，施加 7s + 0.5s/层 不可防御 (overrideDuration 直接入参确保实机精确时长)
    if (sp_level == 3 && !entered) {
        int stacks = s_nemesis_dark_stacks[player_index];
        float dur = 7.0f + (0.5f * (float)stacks);
        if (stacks > 0) {
            nemesis_consume_dark_stacks(player_index, stacks, now_ms);
        }
        skill_apply_buff_dur(player_index, "nemesisprime_sp3_unblockable", dur);
        skill_overlay("[%s] SP3消耗 %d 层黑暗能量！不可防御持续 %.1f 秒！",
                      player_index == 0 ? "暗天陨" : "敌方暗天陨", stacks, dur);
        skill_log("NEMESIS_SP3: P%d SP3 exited -> consumed %d stacks, applied unblockable (%.1fs)",
                  player_index, stacks, dur);
    }
}

static int nemesis_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    if (strcmp(ctx->modifier_id, "nemesisprime_dark_cd") == 0) {
        if (ctx->p_chance) *ctx->p_chance = 1.0f;
        if (ctx->p_roll) *ctx->p_roll = 0.0f;
        *out_res = 1; // 开局自动激活紫色 E407 倒计时图标
        return 1;
    }
    if (strcmp(ctx->modifier_id, "nemesisprime_dark_energy") == 0) {
        *out_res = 0; // 待倒计时走完后叠加
        return 1;
    }
    return 0;
}

static void nemesis_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        const char* bid = skill_get_bot_id(player_index);
        s_nemesis_active[player_index]           = (bid && strstr(bid, "nemesisprime") != NULL) ? 1 : 0;
        s_nemesis_dark_stacks[player_index]      = 0;
        s_last_dark_charge_ms[player_index]      = 0;
        s_current_dark_interval_ms[player_index] = 10000;
        s_nemesis_cloning[player_index]          = 0;
        if (s_nemesis_active[player_index]) {
            skill_consume_buff(player_index, "nemesisprime_dark_energy", 99);
            skill_consume_buff(player_index, "nemesisprime_sp3_unblockable", 99);
        }
    }
}

BotSkillModule g_module_nemesis = {
    .bot_prefix               = "nemesisprime",
    .display_name_zh          = "暗黑擎天柱",
    .on_hit_connected         = nemesis_on_hit_connected,
    .on_buff_gated            = NULL,
    .on_buff_applied          = nemesis_on_buff_applied,
    .on_opponent_buff_applied = nemesis_on_opponent_buff_applied,
    .on_special_state         = nemesis_on_special_state,
    .on_evade_check           = NULL,
    .on_test_roll             = nemesis_on_test_roll,
    .on_fight_reset           = nemesis_on_fight_reset,
    .on_simulation_tick       = nemesis_on_simulation_tick,
};
