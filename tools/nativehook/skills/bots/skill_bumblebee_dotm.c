#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 电影大黄蜂 (Bumblebee DOTM) 技能模块
// Bot ID: bumblebee_cin_dotm
// ===========================================================================
// 1. [2421] 被动：近战校准 (Melee Calibration, 0xe509)
//    开局自动进入近战校准模式，无倒计时，25.5% 几率闪避对手基础近战攻击。
//    若受到远程攻击击中，近战校准消失，进入 1.5 秒灰色切换倒计时，结束后激活远程校准。
// 2. [2422] 被动：远程校准 (Ranged Calibration, 0xe518)
//    拥有远程校准时，无倒计时，25.5% 几率闪避对手基础远程攻击。
//    若受到近战攻击击中，远程校准消失，进入 1.5 秒灰色切换倒计时，结束后激活近战校准。
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
        skill_overlay("[%s] 校准完成：激活 %s 模式 (25.5%% 规避)",
                      p == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                      s_dotm_mode[p] == CALIB_MODE_MELEE ? "近战校准" : "远程校准");
        skill_log("BUMBLEBEE_DOTM: Calibration switch completed for P%d -> mode=%d", p, s_dotm_mode[p]);
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

        // 如果在切换倒计时中，保持冷却状态
        if (s_dotm_switch_end_ms[tp] == 0) {
            if (s_dotm_mode[tp] == CALIB_MODE_MELEE && ctx->is_ranged) {
                // 近战模式下被远程击中 -> 开启 1.5s 切换到远程模式
                s_dotm_switch_end_ms[tp] = now_ms + 1500;
                s_dotm_target_mode[tp] = CALIB_MODE_RANGED;
                skill_overlay("[%s] 受到远程射击，校准切换中 (1.5s)...", tp == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM: P%d Melee calibration broken by ranged hit, switching to Ranged (1.5s)", tp);
            } else if (s_dotm_mode[tp] == CALIB_MODE_RANGED && !ctx->is_ranged) {
                // 远程模式下被近战击中 -> 开启 1.5s 切换到近战模式
                s_dotm_switch_end_ms[tp] = now_ms + 1500;
                s_dotm_target_mode[tp] = CALIB_MODE_MELEE;
                skill_overlay("[%s] 受到近战打击，校准切换中 (1.5s)...", tp == 0 ? "电影大黄蜂" : "敌方大黄蜂");
                skill_log("BUMBLEBEE_DOTM: P%d Ranged calibration broken by melee hit, switching to Melee (1.5s)", tp);
            }
        }
    }

    // -----------------------------------------------------------------------
    // B. 电影大黄蜂作为攻击方 (Attacker) -> 伤害加成与击倒叠层
    // -----------------------------------------------------------------------
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "bumblebee_cin_dotm") != NULL) {
        int ap = ctx->attacker_player_index;

        // 检查第 16 层倒计时
        if (s_dotm_kd_stacks[ap] >= 16) {
            if (now_ms >= s_dotm_stack16_expire_ms[ap]) {
                s_dotm_kd_stacks[ap] = 15;
                s_dotm_stack16_expire_ms[ap] = 0;
            }
        }

        // 应用攻击增益加成 (+13.5% 每层)
        int effective_stacks = s_dotm_kd_stacks[ap];
        if (effective_stacks > 0) {
            float atk_mult = 1.0f + (0.135f * effective_stacks);
            ctx->modified_damage *= atk_mult;
        }

        // 击倒判定 (SP 最终击或重击)
        int is_kd = ctx->is_last_hit && (ctx->special_index > 0);
        if (is_kd) {
            if (s_dotm_kd_stacks[ap] < 15) {
                s_dotm_kd_stacks[ap]++;
                skill_overlay("[%s] 击倒对手！获得攻击增益第 %d 层 (+%.1f%%)",
                              ap == 0 ? "电影大黄蜂" : "敌方大黄蜂",
                              s_dotm_kd_stacks[ap], s_dotm_kd_stacks[ap] * 13.5f);
            } else if (s_dotm_kd_stacks[ap] == 15) {
                // 激活第 16 层 (3.0s 倒计时)
                s_dotm_kd_stacks[ap] = 16;
                s_dotm_stack16_expire_ms[ap] = now_ms + 3000;
                skill_overlay("[%s] 击倒满溢！第 16 层爆发增益 (+216.0%%, 3s)",
                              ap == 0 ? "电影大黄蜂" : "敌方大黄蜂");
            } else if (s_dotm_kd_stacks[ap] >= 16) {
                // 刷新第 16 层时间
                s_dotm_stack16_expire_ms[ap] = now_ms + 3000;
            }
            skill_log("BUMBLEBEE_DOTM: Knockdown triggered by P%d! current stacks=%d", ap, s_dotm_kd_stacks[ap]);
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
    .bot_prefix = "bumblebee_cin_dotm",
    .on_hit_connected = bumblebee_dotm_on_hit_connected,
    .on_buff_gated = NULL,
    .on_buff_applied = NULL,
    .on_evade_check = bumblebee_dotm_on_evade_check,
    .on_test_roll = NULL,
    .on_fight_reset = bumblebee_dotm_on_fight_reset
};
