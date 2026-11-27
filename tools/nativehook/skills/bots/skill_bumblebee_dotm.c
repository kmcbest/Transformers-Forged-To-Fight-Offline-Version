#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 电影大黄蜂 (Bumblebee DOTM) 技能模块
// Bot ID: bumblebee_cin_dotm
// ===========================================================================
// 1. [2421] 被动：近战校准 (Melee Calibration, 0xe509)
//    开局自动进入近战校准模式，无倒计时，25.5% 几率规避对手近战攻击。
//    持有远程校准被近战攻击击中时，进入 1.26 秒 (1.5s 缩短 16%) 灰色近战校准倒计时，
//    结束后激活近战校准。
// 2. [2422] 被动：远程校准 (Ranged Calibration, 0xe518)
//    持有近战校准被远程攻击击中时，移除近战校准，进入 1.26 秒灰色远程校准倒计时，
//    结束后激活远程校准（25.5% 几率规避对手远程攻击）。
// 3. [2424] 被动：击倒攻击增益 (Attack Buff on Knockdown, 0xe406)
//    每击倒对手一次 (重击或非格挡 SP 末击)，获得 1 层永久 +13.5% 攻击增益，最多 15 层；
//    满 15 层后第 16+ 层变为 3.0 秒倒计时爆发增益。
// 4. [觉醒] 敏捷 (Alacrity, 0xe406)
//    a) 校准模式切换时间缩短 16% (1.5s -> 1.26s)。
//    b) 主动闪避对手近战攻击时，获得 1 层 75% 攻击增益，持续 5.0 秒 (不可叠加，可刷新)。
// 5. [SP1] 破甲 (Armor Break, 0xe516)
//    非格挡每一击 60% 概率施加 6 秒 35% 破甲，并在施加成功后移除对方全部护甲增益。
// 6. [SP2] 震击 (Shock, 0xe914)
//    非格挡最后一击施加 10 秒 80% ATK 震击；若对方身上有护甲，伤害增加 150% (200% ATK)。
// 7. [SP3] 震击 (Shock, 0xe914)
//    最后一击施加 10 秒 80% ATK 震击；若对方身上有护甲，伤害增加 100% (160% ATK)。
// ===========================================================================

#define DOTM_SWITCH_MS 1260ULL
#define DOTM_SWITCH_S  1.26f

typedef enum {
    CALIB_MODE_MELEE = 0,
    CALIB_MODE_RANGED = 1
} CalibrationMode;

static CalibrationMode s_dotm_mode[2]          = {CALIB_MODE_MELEE, CALIB_MODE_MELEE};
static CalibrationMode s_dotm_target_mode[2]   = {CALIB_MODE_MELEE, CALIB_MODE_MELEE};
static uint64_t        s_dotm_switch_end_ms[2] = {0, 0};

// 80ms 规避骰子去重缓存 [player][0=melee, 1=ranged]
static uint64_t s_dotm_evade_roll_ms[2][2]  = {{0, 0}, {0, 0}};
static int      s_dotm_evade_roll_res[2][2] = {{0, 0}, {0, 0}};

// 觉醒【敏捷】闪避近战去抖时间戳
static uint64_t s_dotm_sig_dodge_cd_ms[2] = {0, 0};

static int dotm_is_self(const char* bot_id) {
    return (bot_id && strstr(bot_id, "bumblebee_cin_dotm") != NULL);
}

static int dotm_target_has_armor(int tp) {
    return skill_has_buff(tp, "armor_up") ||
           skill_has_buff(tp, "armor_buff") ||
           skill_has_buff(tp, "block_armor") ||
           skill_has_buff(tp, "tank_armor") ||
           skill_has_buff(tp, "sw_armor") ||
           skill_has_buff(tp, "innate_armor") ||
           skill_has_buff(tp, "passive_armor") ||
           skill_has_buff(tp, "sp2_armor") ||
           skill_has_buff(tp, "sp3_armor") ||
           skill_has_buff(tp, "hit_armor") ||
           skill_has_buff(tp, "struck_armor") ||
           skill_has_buff(tp, "heavy_armor");
}

static void dotm_remove_all_armor_buffs(int tp) {
    skill_consume_buff(tp, "armor_up", 99);
    skill_consume_buff(tp, "armor_buff", 99);
    skill_consume_buff(tp, "block_armor", 99);
    skill_consume_buff(tp, "tank_armor", 99);
    skill_consume_buff(tp, "sw_armor", 99);
    skill_consume_buff(tp, "innate_armor", 99);
    skill_consume_buff(tp, "passive_armor", 99);
    skill_consume_buff(tp, "sp2_armor", 99);
    skill_consume_buff(tp, "sp3_armor", 99);
    skill_consume_buff(tp, "hit_armor", 99);
    skill_consume_buff(tp, "struck_armor", 99);
    skill_consume_buff(tp, "heavy_armor", 99);
    for (int i = 0; i < 32; i++) {
        if (!skill_dispel_random_buff_by_category(tp, 0, 1, NULL, 0)) {
            break;
        }
    }
}

static void dotm_grant_alacrity_atk(int bee_idx, const char* reason) {
    if (bee_idx < 0 || bee_idx >= 2) return;
    if (!dotm_is_self(skill_get_bot_id(bee_idx))) return;

    uint64_t now_ms = skill_now_ms();
    if (s_dotm_sig_dodge_cd_ms[bee_idx] > 0 && now_ms < s_dotm_sig_dodge_cd_ms[bee_idx] + 500) {
        return;
    }
    s_dotm_sig_dodge_cd_ms[bee_idx] = now_ms;

    if (skill_has_buff(bee_idx, "bumblebee_cin_dotm_sig_atk")) {
        skill_consume_buff(bee_idx, "bumblebee_cin_dotm_sig_atk", 99);
        skill_log("BUMBLEBEE_DOTM_SIG: P%d refreshed 5.0s +75%% atk buff (%s)", bee_idx, reason);
    }
    skill_apply_buff_dur(bee_idx, "bumblebee_cin_dotm_sig_atk", 5.0f);
    skill_overlay("[%s] 敏捷！闪避近战获得 +75%% 攻击增益 (5秒, 不可叠加可刷新)",
                  bee_idx == 0 ? "电影大黄蜂" : "敌方大黄蜂");
    skill_log("BUMBLEBEE_DOTM_SIG: P%d dodged melee (%s) -> +75%% atk buff (5.0s)", bee_idx, reason);
}

static void update_calibration_state(int p, uint64_t now_ms) {
    if (s_dotm_switch_end_ms[p] > 0 && now_ms >= s_dotm_switch_end_ms[p]) {
        s_dotm_mode[p] = s_dotm_target_mode[p];
        s_dotm_switch_end_ms[p] = 0;
        if (s_dotm_mode[p] == CALIB_MODE_MELEE) {
            skill_consume_buff(p, "bumblebee_cin_dotm_calib_melee_cd", 99);
            skill_apply_buff_dur(p, "bumblebee_cin_dotm_calib_melee", -1.0f);
        } else {
            skill_consume_buff(p, "bumblebee_cin_dotm_calib_ranged_cd", 99);
            skill_apply_buff_dur(p, "bumblebee_cin_dotm_calib_ranged", -1.0f);
        }
        skill_overlay("[%s] 校准完成：激活 %s 模式 (25.5%% 规避)",
                      p == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                      s_dotm_mode[p] == CALIB_MODE_MELEE ? "近战校准" : "远程校准");
        skill_log("BUMBLEBEE_DOTM: Calibration switch completed for P%d -> mode=%d", p, s_dotm_mode[p]);
    }
}

static void bumblebee_dotm_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        update_calibration_state(p, now_ms);
    }
}

static void bumblebee_dotm_on_dodge_enter(int bee_idx) {
    if (bee_idx < 0 || bee_idx >= 2) return;
    if (!dotm_is_self(skill_get_bot_id(bee_idx))) return;

    uint64_t now_ms = skill_now_ms();
    int opp_idx = 1 - bee_idx;
    uint64_t opp_dash_ms = skill_get_last_dash_ms(opp_idx);
    uint64_t opp_melee_ms = skill_get_last_melee_ms(opp_idx);

    uint64_t last_side = skill_get_last_sidestep_ms(bee_idx);
    uint64_t last_back = skill_get_last_backdash_ms(bee_idx);
    int is_sidestep = (last_side > last_back && (now_ms - last_side < 120));

    if (is_sidestep) {
        if (opp_dash_ms > 0 && now_ms >= opp_dash_ms && (now_ms - opp_dash_ms <= 850)) {
            dotm_grant_alacrity_atk(bee_idx, "sidestep vs opponent dash");
        }
    } else {
        if ((opp_melee_ms > 0 && now_ms >= opp_melee_ms && (now_ms - opp_melee_ms <= 650)) ||
            skill_is_melee_attacking(opp_idx)) {
            dotm_grant_alacrity_atk(bee_idx, "dodge vs active melee attack");
        }
    }
}

static void bumblebee_dotm_on_attack_start(int attacker_index, int action_type) {
    for (int bee_idx = 0; bee_idx < 2; bee_idx++) {
        if (bee_idx == attacker_index) continue;
        if (!dotm_is_self(skill_get_bot_id(bee_idx))) continue;

        uint64_t now_ms = skill_now_ms();
        uint64_t last_back = skill_get_last_backdash_ms(bee_idx);
        uint64_t last_side = skill_get_last_sidestep_ms(bee_idx);

        if (action_type == 2 && last_side > 0 && now_ms >= last_side && (now_ms - last_side <= 650)) {
            dotm_grant_alacrity_atk(bee_idx, "opponent dashed into active sidestep");
            return;
        }
        if (action_type == 1 || action_type == 2 || action_type == 32 || action_type == 4 || action_type == 0x100) {
            if (last_back > 0 && now_ms >= last_back && (now_ms - last_back <= 650)) {
                dotm_grant_alacrity_atk(bee_idx, "opponent swung melee into active dodge");
                return;
            }
        }
    }
}

static void bumblebee_dotm_on_attack_ended(SkillAttackEndContext* ctx) {
    if (!ctx || !ctx->is_missed) return;
    if (!dotm_is_self(ctx->target_bot_id)) return;

    int bee_idx = ctx->target_player_index;
    int al = ctx->attack_level;
    // 仅近战攻击 (轻=1, 中/前冲=2, 重击=4) 落空，且最近存在主动闪避/侧闪才计入“闪避近战攻击”
    if ((al & (1 | 2 | 4)) == 0) return;

    uint64_t now_ms = skill_now_ms();
    uint64_t last_back = skill_get_last_backdash_ms(bee_idx);
    uint64_t last_side = skill_get_last_sidestep_ms(bee_idx);

    if (al == 2 && last_side > 0 && now_ms >= last_side && (now_ms - last_side <= 800)) {
        dotm_grant_alacrity_atk(bee_idx, "whiff dash evaded by sidestep");
    } else if (last_back > 0 && now_ms >= last_back && (now_ms - last_back <= 750)) {
        dotm_grant_alacrity_atk(bee_idx, "whiff melee evaded by dodge");
    }
}

static void bumblebee_dotm_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // -----------------------------------------------------------------------
    // A. 电影大黄蜂作为受击方 (Target) -> 仅非格挡真实命中时触发校准模式切换
    // -----------------------------------------------------------------------
    if (dotm_is_self(ctx->target_bot_id) && !ctx->is_blocked) {
        int tp = ctx->target_player_index;
        update_calibration_state(tp, now_ms);

        if (s_dotm_switch_end_ms[tp] == 0) {
            if (s_dotm_mode[tp] == CALIB_MODE_MELEE && ctx->is_ranged) {
                skill_consume_buff(tp, "bumblebee_cin_dotm_calib_melee", 99);
                skill_apply_buff_dur(tp, "bumblebee_cin_dotm_calib_ranged_cd", DOTM_SWITCH_S);
                s_dotm_switch_end_ms[tp] = now_ms + DOTM_SWITCH_MS;
                s_dotm_target_mode[tp] = CALIB_MODE_RANGED;
                skill_overlay("[%s] 受到远程射击，远程校准倒计时 (1.26s)...",
                              tp == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM: P%d Melee calibration broken by ranged hit, switching to Ranged (%.2fs)",
                          tp, DOTM_SWITCH_S);
            } else if (s_dotm_mode[tp] == CALIB_MODE_RANGED && ctx->is_melee) {
                skill_consume_buff(tp, "bumblebee_cin_dotm_calib_ranged", 99);
                skill_apply_buff_dur(tp, "bumblebee_cin_dotm_calib_melee_cd", DOTM_SWITCH_S);
                s_dotm_switch_end_ms[tp] = now_ms + DOTM_SWITCH_MS;
                s_dotm_target_mode[tp] = CALIB_MODE_MELEE;
                skill_overlay("[%s] 受到近战打击，近战校准倒计时 (1.26s)...",
                              tp == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM: P%d Ranged calibration broken by melee hit, switching to Melee (%.2fs)",
                          tp, DOTM_SWITCH_S);
            }
        }
    }

    // -----------------------------------------------------------------------
    // B. 电影大黄蜂作为攻击方 (Attacker)
    // -----------------------------------------------------------------------
    if (dotm_is_self(ctx->attacker_bot_id)) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 1. 实时读取场上有效攻击增益层数并计算倍率
        //    (C# AttributeDefs 不自动结算 attack_buff，必须由此处统一计算，消除静态计数器漂移)
        int kd_stacks    = skill_count_buffs(ap, "bumblebee_cin_dotm_knockdown_atk");
        int burst_stacks = skill_count_buffs(ap, "bumblebee_cin_dotm_burst_atk");
        int sig_stacks   = skill_count_buffs(ap, "bumblebee_cin_dotm_sig_atk");
        if (sig_stacks > 1) sig_stacks = 1; // 敏捷 +75% 攻击增益严格限 1 层（可刷新）

        float total_atk_bonus = 0.135f * (float)(kd_stacks + burst_stacks) + 0.75f * (float)sig_stacks;
        if (total_atk_bonus > 0.0f) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= (1.0f + total_atk_bonus);
            skill_log("BUMBLEBEE_DOTM: Damage boosted x%.3f (%.1f -> %.1f, kd=%d burst=%d sig=%d) on P%d",
                      1.0f + total_atk_bonus, old_dmg, ctx->modified_damage, kd_stacks, burst_stacks, sig_stacks, ap);
        }

        // 后续触发效果均要求未被格挡
        if (ctx->is_blocked) return;

        int sp = ctx->special_index;
        if (sp == 0) {
            if (ctx->action_type == 16) sp = 1;
            else if (ctx->action_type == 32) sp = 2;
            else if (ctx->action_type == 64) sp = 3;
        }

        // 2. SP1: 每一击 60% 概率施加 35% 破甲 (6秒)，并在施加成功后移除对方所有护甲增益
        if (sp == 1) {
            float roll = skill_random_float();
            if (roll < 0.60f) {
                skill_apply_buff_dur(tp, "bumblebee_cin_dotm_sp1_armor_break", 6.0f);
                skill_overlay("[%s] SP1 速踢破甲！移除护甲并施加 35%% 破甲 (6秒)",
                              ap == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM_SP1: P%d hit=%d roll=%.3f < 0.60 -> applied armor break (6.0s) to P%d",
                          ap, ctx->hit_index, roll, tp);
            } else {
                skill_log("BUMBLEBEE_DOTM_SP1: P%d hit=%d roll=%.3f >= 0.60 -> armor break missed",
                          ap, ctx->hit_index, roll);
            }
        }

        // 3. SP2 / SP3 末击震击 (检测施加震击前目标是否持有护甲)
        if (ctx->is_last_hit && (sp == 2 || sp == 3)) {
            int opp_armored = dotm_target_has_armor(tp);
            if (sp == 2) {
                const char* mod_id = opp_armored ? "bumblebee_cin_dotm_sp2_shock_armored"
                                                 : "bumblebee_cin_dotm_sp2_shock";
                skill_apply_buff_dur(tp, mod_id, 10.0f);
                skill_overlay("[%s] SP2 漏洞射击！%s (10秒)",
                              ap == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                              opp_armored ? "对手有护甲！震击伤害+150%%" : "施加 80%% 震击");
                skill_log("BUMBLEBEE_DOTM_SP2: P%d lastHit -> %s (opp_armored=%d) on P%d",
                          ap, mod_id, opp_armored, tp);
            } else {
                const char* mod_id = opp_armored ? "bumblebee_cin_dotm_sp3_shock_armored"
                                                 : "bumblebee_cin_dotm_sp3_shock";
                skill_apply_buff_dur(tp, mod_id, 10.0f);
                skill_overlay("[%s] SP3 炮弹冲击波！%s (10秒)",
                              ap == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                              opp_armored ? "对手有护甲！震击伤害+100%%" : "施加 80%% 震击");
                skill_log("BUMBLEBEE_DOTM_SP3: P%d lastHit -> %s (opp_armored=%d) on P%d",
                          ap, mod_id, opp_armored, tp);
            }
        }

        // 4. 被动：击倒攻击增益 (重击或非格挡 SP 末击，且目标未因不可阻挡免疫倒地)
        if (ctx->is_last_hit && (ctx->is_heavy || sp > 0)) {
            int can_kd = (sp == 3) || !skill_is_unstoppable(tp);
            if (can_kd) {
                if (kd_stacks < 15) {
                    skill_apply_buff_dur(ap, "bumblebee_cin_dotm_knockdown_atk", -1.0f);
                    skill_overlay("[%s] 击倒对手！获得攻击增益第 %d 层 (+%.1f%%)",
                                  ap == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                                  kd_stacks + 1, (kd_stacks + 1) * 13.5f);
                    skill_log("BUMBLEBEE_DOTM: Knockdown atk buff applied to P%d! stacks=%d->%d",
                              ap, kd_stacks, kd_stacks + 1);
                } else {
                    skill_apply_buff_dur(ap, "bumblebee_cin_dotm_burst_atk", 3.0f);
                    skill_overlay("[%s] 击倒满溢！第 %d 层爆发增益 (3秒倒计时)",
                                  ap == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                                  kd_stacks + burst_stacks + 1);
                    skill_log("BUMBLEBEE_DOTM: P%d at 15 perm stacks, applied 3.0s burst_atk (burst_stacks=%d->%d)",
                              ap, burst_stacks, burst_stacks + 1);
                }
            }
        }
    }
}

static int bumblebee_dotm_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !ctx->bot_id || !out_evade) return 0;
    if (!dotm_is_self(ctx->bot_id)) return 0;

    int p = ctx->player_index;
    if (p < 0 || p > 1) return 0;

    uint64_t now_ms = skill_now_ms();
    update_calibration_state(p, now_ms);

    // 灰色切换倒计时期间不生效规避
    if (s_dotm_switch_end_ms[p] > 0 && now_ms < s_dotm_switch_end_ms[p]) {
        *out_evade = 0;
        return 1;
    }

    int r = ctx->is_ranged ? 1 : 0;
    int match_mode = (!r && s_dotm_mode[p] == CALIB_MODE_MELEE) ||
                     (r && s_dotm_mode[p] == CALIB_MODE_RANGED);
    if (!match_mode) {
        *out_evade = 0;
        return 1;
    }

    // 80ms 同击判定去重缓存，确保真实概率严格等于 25.5%
    if (s_dotm_evade_roll_ms[p][r] > 0 && now_ms >= s_dotm_evade_roll_ms[p][r] &&
        (now_ms - s_dotm_evade_roll_ms[p][r]) < 80) {
        *out_evade = s_dotm_evade_roll_res[p][r];
        return 1;
    }

    float roll = skill_random_float();
    const float CALIB_EVADE_CHANCE = 0.255f;
    int passed = (roll < CALIB_EVADE_CHANCE) ? 1 : 0;
    s_dotm_evade_roll_ms[p][r] = now_ms;
    s_dotm_evade_roll_res[p][r] = passed;

    if (passed) {
        skill_overlay("[%s] %s闪避成功！(25.5%% 几率通过)",
                      p == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                      r ? "远程校准" : "近战校准");
        skill_log("BUMBLEBEE_DOTM: %s Evade PASS roll=%.3f < 0.255 for P%d",
                  r ? "Ranged" : "Melee", roll, p);
    } else {
        skill_log("BUMBLEBEE_DOTM: %s Evade MISSED roll=%.3f >= 0.255 for P%d",
                  r ? "Ranged" : "Melee", roll, p);
    }

    *out_evade = passed;
    return 1;
}

static void bumblebee_dotm_on_evade_triggered(int evader_player_index, int is_ranged) {
    (void)is_ranged;
    if (evader_player_index < 0 || evader_player_index >= 2) return;
    if (!dotm_is_self(skill_get_bot_id(evader_player_index))) return;

    // 呼出绿色“规避”文字
    skill_apply_buff_dur(evader_player_index, "gp_evade_callout", 1.0f);
    skill_log("BUMBLEBEE_DOTM: P%d triggered green evade callout (ranged=%d)",
              evader_player_index, is_ranged);
}

static void bumblebee_dotm_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;

    int tp = ctx->target_player_index;
    if (tp < 0 || tp > 1) return;

    // 若通过外部注入或恢复同步校准状态，保持状态机一致
    if (strcmp(ctx->modifier_id, "bumblebee_cin_dotm_calib_ranged") == 0) {
        s_dotm_mode[tp] = CALIB_MODE_RANGED;
        s_dotm_target_mode[tp] = CALIB_MODE_RANGED;
        s_dotm_switch_end_ms[tp] = 0;
        return;
    }
    if (strcmp(ctx->modifier_id, "bumblebee_cin_dotm_calib_melee") == 0) {
        s_dotm_mode[tp] = CALIB_MODE_MELEE;
        s_dotm_target_mode[tp] = CALIB_MODE_MELEE;
        s_dotm_switch_end_ms[tp] = 0;
        return;
    }

    // SP1 破甲施加成功后，清空对方身上全部剩余护甲增益（原生 ArmorBreak_BuffEffect 仅移除 1 层）
    if (strcmp(ctx->modifier_id, "bumblebee_cin_dotm_sp1_armor_break") == 0) {
        dotm_remove_all_armor_buffs(tp);
        skill_log("BUMBLEBEE_DOTM_SP1: Cleared all remaining armor buffs on P%d", tp);
    }
}

static void bumblebee_dotm_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_dotm_mode[player_index]             = CALIB_MODE_MELEE;
        s_dotm_target_mode[player_index]      = CALIB_MODE_MELEE;
        s_dotm_switch_end_ms[player_index]    = 0;
        s_dotm_evade_roll_ms[player_index][0] = 0;
        s_dotm_evade_roll_ms[player_index][1] = 0;
        s_dotm_evade_roll_res[player_index][0] = 0;
        s_dotm_evade_roll_res[player_index][1] = 0;
        s_dotm_sig_dodge_cd_ms[player_index]  = 0;
    }
}

BotSkillModule g_module_bumblebee_dotm = {
    .bot_prefix         = "bumblebee_cin_dotm",
    .display_name_zh    = "大黄蜂",
    .on_hit_connected   = bumblebee_dotm_on_hit_connected,
    .on_buff_applied    = bumblebee_dotm_on_buff_applied,
    .on_evade_check     = bumblebee_dotm_on_evade_check,
    .on_evade_triggered = bumblebee_dotm_on_evade_triggered,
    .on_dodge_enter     = bumblebee_dotm_on_dodge_enter,
    .on_attack_start    = bumblebee_dotm_on_attack_start,
    .on_attack_ended    = bumblebee_dotm_on_attack_ended,
    .on_fight_reset     = bumblebee_dotm_on_fight_reset,
    .on_simulation_tick = bumblebee_dotm_on_simulation_tick,
};
