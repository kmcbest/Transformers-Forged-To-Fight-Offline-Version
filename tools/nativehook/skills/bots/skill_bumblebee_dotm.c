#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 电影大黄蜂 (Bumblebee DOTM) 技能模块
// Bot ID: bumblebee_cin_dotm
// ===========================================================================
// 1. [2421] 被动：近战校准 (Melee Calibration, 0xe509)
//    开局自动进入近战校准模式，无倒计时，25.5% 几率闪避对手基础近战攻击。
//    若受到远程攻击击中，近战校准消失，进入 1.5 秒灰色远程校准倒计时，结束后激活远程校准。
// 2. [2422] 被动：远程校准 (Ranged Calibration, 0xe518)
//    拥有远程校准时，无倒计时，25.5% 几率闪避对手基础远程攻击。
//    若受到近战攻击击中，远程校准消失，进入 1.5 秒灰色近战校准倒计时，结束后激活近战校准。
// 3. [2424] 被动：击倒攻击增益 (Knockdown Attack Buff, 0xe406)
//    每次击倒对手 (Heavy 或 SP 最终击)，永久获得 1 层攻击增益 (+13.5% 攻击力)。
//    永久增益最多 15 层；第 16 层带有 3.0 秒倒计时，超时后消失。
// ===========================================================================

typedef enum {
    CALIB_MODE_MELEE = 0,
    CALIB_MODE_RANGED = 1
} CalibrationMode;

static CalibrationMode s_dotm_mode[2]              = {CALIB_MODE_MELEE, CALIB_MODE_MELEE};
static CalibrationMode s_dotm_target_mode[2]       = {CALIB_MODE_MELEE, CALIB_MODE_MELEE};
static uint64_t        s_dotm_switch_end_ms[2]     = {0, 0};

// 击倒攻击增益层数与第16层计时器
static int             s_dotm_kd_stacks[2]         = {0, 0};
static uint64_t        s_dotm_stack16_expire_ms[2] = {0, 0};

static void update_calibration_state(int p, uint64_t now_ms) {
    if (s_dotm_switch_end_ms[p] > 0 && now_ms >= s_dotm_switch_end_ms[p]) {
        s_dotm_mode[p] = s_dotm_target_mode[p];
        s_dotm_switch_end_ms[p] = 0;
        if (s_dotm_mode[p] == CALIB_MODE_MELEE) {
            skill_consume_buff(p, "bumblebee_cin_dotm_calib_melee_cd", 1);
            skill_apply_buff_dur(p, "bumblebee_cin_dotm_calib_melee", -1.0f);
        } else {
            skill_consume_buff(p, "bumblebee_cin_dotm_calib_ranged_cd", 1);
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

static void bumblebee_dotm_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // -----------------------------------------------------------------------
    // A. 电影大黄蜂作为受击方 (Target) -> 触发校准模式切换
    // -----------------------------------------------------------------------
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "bumblebee_cin_dotm") != NULL) {
        int tp = ctx->target_player_index;
        update_calibration_state(tp, now_ms);

        // 如果不在切换倒计时中，触发 1.5s 灰色倒计时切换
        if (s_dotm_switch_end_ms[tp] == 0) {
            if (s_dotm_mode[tp] == CALIB_MODE_MELEE && ctx->is_ranged) {
                // 近战模式下被远程击中 -> 移除近战规避，开启 1.5s 灰色远程规避倒计时
                skill_consume_buff(tp, "bumblebee_cin_dotm_calib_melee", 1);
                skill_apply_buff_dur(tp, "bumblebee_cin_dotm_calib_ranged_cd", 1.5f);
                s_dotm_switch_end_ms[tp] = now_ms + 1500;
                s_dotm_target_mode[tp] = CALIB_MODE_RANGED;
                skill_overlay("[%s] 受到远程射击，远程校准倒计时 (1.5s)...", tp == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM: P%d Melee calibration broken by ranged hit, switching to Ranged (1.5s)", tp);
            } else if (s_dotm_mode[tp] == CALIB_MODE_RANGED && !ctx->is_ranged) {
                // 远程模式下被近战击中 -> 移除远程规避，开启 1.5s 灰色近战规避倒计时
                skill_consume_buff(tp, "bumblebee_cin_dotm_calib_ranged", 1);
                skill_apply_buff_dur(tp, "bumblebee_cin_dotm_calib_melee_cd", 1.5f);
                s_dotm_switch_end_ms[tp] = now_ms + 1500;
                s_dotm_target_mode[tp] = CALIB_MODE_MELEE;
                skill_overlay("[%s] 受到近战打击，近战校准倒计时 (1.5s)...", tp == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM: P%d Ranged calibration broken by melee hit, switching to Melee (1.5s)", tp);
            }
        }
    }

    // -----------------------------------------------------------------------
    // B. 电影大黄蜂作为攻击方 (Attacker) -> 应用击倒攻击增益加成 (+13.5% per stack)
    // -----------------------------------------------------------------------
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "bumblebee_cin_dotm") != NULL) {
        int ap = ctx->attacker_player_index;
        float boost = 1.0f;
        if (s_dotm_stack16_expire_ms[ap] > 0 && now_ms < s_dotm_stack16_expire_ms[ap]) {
            // 第 16 层爆发增益 (+216.0% 攻击加成)
            boost = 1.0f + (0.135f * 16.0f);
        } else if (s_dotm_kd_stacks[ap] > 0) {
            // 常驻击倒增益 (+13.5% 每层，最多15层)
            boost = 1.0f + (0.135f * (float)s_dotm_kd_stacks[ap]);
        }
        if (boost > 1.0f) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= boost;
            skill_log("BUMBLEBEE_DOTM: Damage boosted x%.3f (%.1f -> %.1f, stacks=%d, s16=%d) on P%d",
                      boost, old_dmg, ctx->modified_damage, s_dotm_kd_stacks[ap],
                      (s_dotm_stack16_expire_ms[ap] > 0 && now_ms < s_dotm_stack16_expire_ms[ap]), ap);
        }
    }
}

static int bumblebee_dotm_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !ctx->bot_id || !out_evade) return 0;

    // 匹配电影大黄蜂
    if (strstr(ctx->bot_id, "bumblebee_cin_dotm") == NULL) {
        return 0; // 非电影大黄蜂，不接管
    }

    int p = ctx->player_index;
    uint64_t now_ms = skill_now_ms();
    update_calibration_state(p, now_ms);

    // 处于切换倒计时中，灰色状态不生效闪避
    if (s_dotm_switch_end_ms[p] > 0 && now_ms < s_dotm_switch_end_ms[p]) {
        *out_evade = 0;
        return 1; // 已处理，返回 0
    }

    float roll = skill_random_float();
    const float CALIB_EVADE_CHANCE = 0.255f; // 25.5% 规避几率

    if (!ctx->is_ranged) {
        // [2421] 近战规避检定
        if (s_dotm_mode[p] == CALIB_MODE_MELEE) {
            if (roll < CALIB_EVADE_CHANCE) {
                *out_evade = 1;
                skill_overlay("[%s] 近战校准闪避成功！(25.5%% 几率通过)", p == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM: Melee Evade PASS roll=%.3f < 0.255 for P%d", roll, p);
            } else {
                *out_evade = 0;
                skill_log("BUMBLEBEE_DOTM: Melee Evade MISSED roll=%.3f >= 0.255 for P%d", roll, p);
            }
            return 1; // 已处理
        }
    } else {
        // [2422] 远程规避检定
        if (s_dotm_mode[p] == CALIB_MODE_RANGED) {
            if (roll < CALIB_EVADE_CHANCE) {
                *out_evade = 1;
                skill_overlay("[%s] 远程校准闪避成功！(25.5%% 几率通过)", p == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM: Ranged Evade PASS roll=%.3f < 0.255 for P%d", roll, p);
            } else {
                *out_evade = 0;
                skill_log("BUMBLEBEE_DOTM: Ranged Evade MISSED roll=%.3f >= 0.255 for P%d", roll, p);
            }
            return 1; // 已处理
        }
    }

    *out_evade = 0;
    return 1; // 电影大黄蜂规避检定已接管
}

static int bumblebee_dotm_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id) return 0;

    // 1. 击倒攻击增益: 仅重击或 SP 最终击 (造成对手击倒) 施加
    if (strstr(ctx->modifier_id, "bumblebee_cin_dotm_knockdown_atk") != NULL) {
        int is_kd_hit = ctx->current_hit_is_last && (ctx->is_heavy || ctx->current_special_index > 0);
        if (!is_kd_hit) {
            skill_log("BUMBLEBEE_DOTM: Suppressed knockdown atk buff on non-kd hit (hit=%d, last=%d, heavy=%d, sp=%d)",
                      ctx->last_hit_index, ctx->current_hit_is_last, ctx->is_heavy, ctx->current_special_index);
            ctx->allow_application = false;
            return 1;
        }

        int ap = ctx->target_player_index; // 增益施加给大黄蜂自身
        if (s_dotm_kd_stacks[ap] >= 15) {
            // 已满 15 层常驻增益，阻止继续堆叠永久 buff，转为施加/刷新第 16 层 3 秒倒计时爆发增益
            ctx->allow_application = false;
            skill_apply_buff_dur(ap, "bumblebee_cin_dotm_burst_atk", 3.0f);
            s_dotm_stack16_expire_ms[ap] = skill_now_ms() + 3000;
            skill_overlay("[%s] 击倒满溢！第 16 层爆发增益 (+216.0%%, 3秒倒计时)",
                          ap == 0 ? "电影大黄蜂" : "敌方大黄蜂");
            skill_log("BUMBLEBEE_DOTM: P%d at 15 stacks, applied 16th burst atk buff (3s)", ap);
            return 1;
        }

        ctx->allow_application = true;
        return 1;
    }

    // 2. SP2 震击: 仅最后一击施加
    if (strstr(ctx->modifier_id, "bumblebee_cin_dotm_sp2_shock") != NULL) {
        if (!ctx->current_hit_is_last) {
            skill_log("BUMBLEBEE_DOTM: Suppressed SP2 shock on non-last hit (hit=%d)", ctx->last_hit_index);
            ctx->allow_application = false;
            return 1;
        }
        ctx->allow_application = true;
        return 1;
    }

    // 3. SP3 震击: 仅最后一击施加
    if (strstr(ctx->modifier_id, "bumblebee_cin_dotm_sp3_shock") != NULL) {
        if (!ctx->current_hit_is_last) {
            skill_log("BUMBLEBEE_DOTM: Suppressed SP3 shock on non-last hit (hit=%d)", ctx->last_hit_index);
            ctx->allow_application = false;
            return 1;
        }
        ctx->allow_application = true;
        return 1;
    }

    return 0;
}

static void bumblebee_dotm_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    if (strstr(ctx->modifier_id, "bumblebee_cin_dotm_knockdown_atk") != NULL) {
        int ap = ctx->target_player_index; // 增益施加给大黄蜂自身
        if (s_dotm_kd_stacks[ap] < 15) {
            s_dotm_kd_stacks[ap]++;
            skill_overlay("[%s] 击倒对手！获得攻击增益第 %d 层 (+%.1f%%)",
                          ap == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                          s_dotm_kd_stacks[ap], s_dotm_kd_stacks[ap] * 13.5f);
            skill_log("BUMBLEBEE_DOTM: Knockdown atk buff applied to P%d! current stacks=%d", ap, s_dotm_kd_stacks[ap]);
        }
    }
}

static void bumblebee_dotm_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_dotm_mode[player_index]              = CALIB_MODE_MELEE; // 开局默认近战模式
        s_dotm_target_mode[player_index]       = CALIB_MODE_MELEE;
        s_dotm_switch_end_ms[player_index]     = 0;
        s_dotm_kd_stacks[player_index]         = 0;
        s_dotm_stack16_expire_ms[player_index] = 0;
    }
}

BotSkillModule g_module_bumblebee_dotm = {
    .bot_prefix         = "bumblebee_cin_dotm",
    .on_hit_connected   = bumblebee_dotm_on_hit_connected,
    .on_buff_gated      = bumblebee_dotm_on_buff_gated,
    .on_buff_applied    = bumblebee_dotm_on_buff_applied,
    .on_evade_check     = bumblebee_dotm_on_evade_check,
    .on_test_roll       = NULL,
    .on_fight_reset     = bumblebee_dotm_on_fight_reset,
    .on_simulation_tick = bumblebee_dotm_on_simulation_tick,
};
