#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>
#include <stdint.h>
#include <stdbool.h>

// ===========================================================================
// 眩晕 (Blackout) 专属战斗技能模块
// Bot ID: blackout_cin_tf
// 职业: 破坏分子 (Demolitions / demo) | 阵营: 霸天虎 (Decepticon)
// ===========================================================================
// 1. [被动 - 暴击几率 & 暴击伤害]
//    - 连击数每增加 5，获得 1 层 6% 暴击率与 1 层 12% 暴击伤害 (上限 99 层)。
//    - 被敌人命中打断连击时，全部移除。
// 2. [被动 - 无尽怒火] (Infinite Fury)
//    - 真实暴击率 > 100% 时点亮图标，hook_179 实时将溢出暴击率 1:1 转为暴击伤害。
//    - 暴击率回落 <= 100% 或连击打断受创时立即移除。
// 3. [特殊技 1 - 能量炮]
//    - 最后一击不可防御：最后一击时间窗内点亮浅紫色不可防御图标 (E41F)，最后一击结束立即熄灭。
//    - 技能期间提升 30% 暴击伤害 (E906)：SP1 进入激活，SP1 退出瞬间立即移除。
//    - 纯净门禁：SP1 期间严禁触发流血。
// 4. [特殊技 2 - 翼刃回旋]
//    - 技能期间提升 60% 暴击伤害：SP2 进入激活，SP2 退出瞬间立即移除。
//    - 每 1 击暴击 100% 触发可叠加流血 (3 秒 60% ATK)。
// 5. [特殊技 3 - 猎杀]
//    - 最后一击命中由 onSpecial3Hit (LastHit) 施加 1 层可叠加永久 20% 暴击抗性减益 (E409)。
// 6. [觉醒 - 追猎] (I'll Hunt You Down!)
//    - 由引擎终态结算回调 on_attack_ended 精准驱动：
//      仅普通攻击 (轻/中/重/远程, 排除 S1/S2/S3) 落空 (非Hit、非Blocked、非对波抵消、非被反射；
//      包含对手前冲/近战穿弹躲过) 时触发。
//    - 获得 1 层 60% 能量功率增益，持续 4 秒；最大 1 层，再次触发刷新倒计时。
// ===========================================================================

static int      s_blackout_combo[2]               = {0, 0};
static int      s_blackout_fury_active[2]         = {0, 0};

static int      s_blackout_active_sp[2]           = {0, 0}; // 0=无, 1=SP1, 2=SP2, 3=SP3
static int      s_blackout_sp1_window_active[2]   = {0, 0};
static int      s_blackout_sp1_unblockable_on[2]  = {0, 0};
static uint64_t s_blackout_sp1_start_ms[2]        = {0, 0};
static uint64_t s_blackout_sp1_exit_ms[2]         = {0, 0};

static void blackout_clear_sp1_unblockable(int p, const char* reason) {
    if (p < 0 || p >= 2) return;
    if (s_blackout_sp1_unblockable_on[p] || skill_has_buff(p, "blackout_sp1_unblockable")) {
        skill_consume_buff(p, "blackout_sp1_unblockable", 99);
        skill_log("BLACKOUT: P%d cleared SP1 light-purple unblockable icon (%s)", p, reason);
    }
    s_blackout_sp1_unblockable_on[p] = 0;
    s_blackout_sp1_window_active[p] = 0;
    s_blackout_sp1_start_ms[p] = 0;
    s_blackout_sp1_exit_ms[p] = 0;
}

static void blackout_show_sp1_unblockable(int p, const char* reason) {
    if (p < 0 || p >= 2) return;
    if (s_blackout_sp1_unblockable_on[p]) return;
    s_blackout_sp1_unblockable_on[p] = 1;
    skill_apply_buff_dur(p, "blackout_sp1_unblockable", 3.5f);
    skill_overlay("[%s] 能量波炮终击！不可防御！", p == 0 ? "眩晕" : "敌方眩晕");
    skill_log("BLACKOUT: P%d showed SP1 light-purple unblockable icon (%s)", p, reason);
}

// 触发觉醒技“追猎” (普通攻击落空获得 1 层 60% 能量功率增益，持续 3 秒；最大 1 层，再次触发刷新倒计时)
void blackout_trigger_hunt_if_ready(int blackout_p, const char* reason) {
    if (blackout_p < 0 || blackout_p >= 2) return;
    const char* bid = skill_get_bot_id(blackout_p);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    // 刷新或施加 3 秒 60% 能量功率增益 (最大 1 层，再次触发刷新倒计时)
    if (skill_has_buff(blackout_p, "blackout_sig_whiff_power_gain")) {
        skill_consume_buff(blackout_p, "blackout_sig_whiff_power_gain", 1);
        skill_log("BLACKOUT: P%d Hunt refreshed 3.0s countdown (%s)", blackout_p, reason);
    } else {
        skill_log("BLACKOUT: P%d Hunt gained +60%% power rate buff 3.0s (%s)", blackout_p, reason);
    }

    skill_apply_buff_dur(blackout_p, "blackout_sig_whiff_power_gain", 3.0f);
    skill_overlay("[%s] 追猎！获得60%%能量功率增益 (3秒)！", blackout_p == 0 ? "眩晕" : "敌方眩晕");
}

// 战斗重置
static void blackout_on_fight_reset(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    s_blackout_combo[player_index] = 0;
    s_blackout_fury_active[player_index] = 0;
    s_blackout_active_sp[player_index] = 0;
    s_blackout_sp1_window_active[player_index] = 0;
    s_blackout_sp1_unblockable_on[player_index] = 0;
    s_blackout_sp1_start_ms[player_index] = 0;
    s_blackout_sp1_exit_ms[player_index] = 0;
    if (skill_has_buff(player_index, "blackout_sp1_special_damage")) {
        skill_consume_buff(player_index, "blackout_sp1_special_damage", 99);
    }
    if (skill_has_buff(player_index, "blackout_sp1_crit_damage")) {
        skill_consume_buff(player_index, "blackout_sp1_crit_damage", 99);
    }
    skill_log("BLACKOUT: P%d reset combat state", player_index);
}

// 同步【无尽怒火】图标状态：真实暴击率 > 100% 时点亮图标，回落至 <= 100% 时移除
static void blackout_sync_infinite_fury(int p) {
    if (p < 0 || p >= 2) return;
    const char* bid = skill_get_bot_id(p);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    float total_cc = skill_get_total_crit_chance(p);
    if (total_cc > 1.0001f) {
        if (!s_blackout_fury_active[p]) {
            s_blackout_fury_active[p] = 1;
            skill_apply_buff_dur(p, "blackout_infinite_fury_crit_dmg", -1.0f);
            skill_overlay("[%s] 暴击率达%.0f%%！【无尽怒火】溢出+%.0f%%转为暴击伤害！",
                          p == 0 ? "眩晕" : "敌方眩晕", total_cc * 100.0f, (total_cc - 1.0f) * 100.0f);
            skill_log("BLACKOUT: P%d Infinite Fury ON (crit_chance=%.2f, overflow=+%.2f crit dmg)",
                      p, total_cc, total_cc - 1.0f);
        }
    } else {
        if (s_blackout_fury_active[p]) {
            s_blackout_fury_active[p] = 0;
            skill_consume_buff(p, "blackout_infinite_fury_crit_dmg", 99);
            skill_log("BLACKOUT: P%d Infinite Fury OFF (crit_chance=%.2f <= 1.00)", p, total_cc);
        }
    }
}

// 必杀技状态机进出回调 (PlayerSpecialAttackState.OnEnter / OnExit & SP3_EXIT)
static void blackout_on_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    uint64_t now_ms = skill_now_ms();

    if (entered) {
        s_blackout_active_sp[player_index] = sp_level;
        if (sp_level == 1) {
            // SP1 进入：启动最后一击浅紫色图标时间窗跟踪 (ev[15]在f=15, 终击蓄力ev[18]在f=26≈867ms, 发射在f=56≈1867ms)
            blackout_clear_sp1_unblockable(player_index, "sp1_reenter");
            s_blackout_sp1_window_active[player_index] = 1;
            s_blackout_sp1_start_ms[player_index] = now_ms;
            s_blackout_sp1_exit_ms[player_index] = 0;
            if (!skill_has_buff(player_index, "blackout_sp1_special_damage")) {
                skill_apply_buff_dur(player_index, "blackout_sp1_special_damage", 3.5f);
            }
            skill_log("BLACKOUT: P%d entered SP1 (+30%% special damage active, tracking last-hit unblockable window)", player_index);
        } else if (sp_level == 2) {
            // SP2 进入：确保 +60% 暴击伤害增益已激活 (仅技能期间生效)
            if (!skill_has_buff(player_index, "blackout_sp2_crit_damage")) {
                skill_apply_buff_dur(player_index, "blackout_sp2_crit_damage", 4.0f);
            }
            skill_log("BLACKOUT: P%d entered SP2 (+60%% crit damage active)", player_index);
        } else if (sp_level == 3) {
            // SP3 进入：准备终击暴击率提升 (+50%, 2s)
            if (!skill_has_buff(player_index, "blackout_sp3_last_crit_rate")) {
                skill_apply_buff_dur(player_index, "blackout_sp3_last_crit_rate", 4.0f);
            }
            skill_log("BLACKOUT: P%d entered SP3 (+50%% crit rate active)", player_index);
        }
    } else {
        if (s_blackout_active_sp[player_index] == sp_level) {
            s_blackout_active_sp[player_index] = 0;
        }
        if (sp_level == 1) {
            // SP1 动画退出：终击能量炮投射物可能仍在飞行，记录退出时间，等终击结算回调立即熄灭或兜底 1.2s 熄灭
            s_blackout_sp1_exit_ms[player_index] = now_ms;
            if (skill_has_buff(player_index, "blackout_sp1_special_damage")) {
                skill_consume_buff(player_index, "blackout_sp1_special_damage", 99);
                skill_log("BLACKOUT: P%d exited SP1 -> removed SP1 +30%% special damage buff", player_index);
            }
            if (skill_has_buff(player_index, "blackout_sp1_crit_damage")) {
                skill_consume_buff(player_index, "blackout_sp1_crit_damage", 99);
            }
            skill_log("BLACKOUT: P%d exited SP1 state (waiting for last-hit projectile resolution)", player_index);
        } else if (sp_level == 2) {
            // SP2 退出：立即移除 +60% 暴击伤害增益，严格限定在技能期间
            if (skill_has_buff(player_index, "blackout_sp2_crit_damage")) {
                skill_consume_buff(player_index, "blackout_sp2_crit_damage", 99);
                skill_log("BLACKOUT: P%d exited SP2 -> removed SP2 +60%% crit damage buff", player_index);
            }
        } else if (sp_level == 3) {
            if (skill_has_buff(player_index, "blackout_sp3_last_crit_rate")) {
                skill_consume_buff(player_index, "blackout_sp3_last_crit_rate", 99);
            }
        }
    }
}

// 命中连接
static void blackout_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    const char* atk_id = ctx->attacker_bot_id;

    if (atk_id && strstr(atk_id, "blackout") != NULL) {
        // SP1 特殊攻击期间：提升 30% 特殊伤害
        if (ctx->special_index == 1 || ctx->action_type == 16 || skill_has_buff(ap, "blackout_sp1_special_damage")) {
            float old_dmg = ctx->modified_damage;
            ctx->modified_damage *= 1.30f;
            skill_log("BLACKOUT: SP1 Special Damage boost (+30%%) applied on P%d: %.1f -> %.1f",
                      ap, old_dmg, ctx->modified_damage);
        }

        // 连击数自增 (仅非格挡真实命中计入连击)
        if (!ctx->is_blocked) {
            s_blackout_combo[ap]++;

            // 每增加 5 连击叠加 1 层 6% 暴击率与 12% 暴击伤害
            if (s_blackout_combo[ap] % 5 == 0) {
                int stacks = s_blackout_combo[ap] / 5;
                if (stacks > 99) stacks = 99;

                skill_apply_buff_dur(ap, "blackout_combo_crit_rate", -1.0f);
                skill_apply_buff_dur(ap, "blackout_combo_crit_dmg", -1.0f);
                skill_overlay("[%s] %d 连击！暴击几率+6%%, 暴击伤害+12%% (第%d层)！",
                              ap == 0 ? "眩晕" : "敌方眩晕", s_blackout_combo[ap], stacks);
                skill_log("BLACKOUT: P%d combo reached %d -> applied crit rate & dmg layer %d",
                          ap, s_blackout_combo[ap], stacks);
            }
        }

        // SP3 最后一击：施加永久暴击抗性减益；若暴击额外施加 6s 燃烧
        if (ctx->special_index == 3 && ctx->is_last_hit) {
            skill_apply_buff_dur(tp, "blackout_sp3_crit_resist_debuff", -1.0f);
            skill_log("BLACKOUT: SP3 last hit applied crit_resist_debuff to P%d", tp);
            if (ctx->is_crit) {
                skill_apply_buff_dur(tp, "blackout_sp3_crit_burn", 6.0f);
                skill_log("BLACKOUT: SP3 last hit crit applied burn to P%d", tp);
            }
        }

        // 实时检查暴击率是否突破 100%，同步【无尽怒火】状态
        blackout_sync_infinite_fury(ap);
    }
}

// 统一单次打击事件终态结算回调 (精确落空状态机 + SP1 最后一击图标起止)
static void blackout_on_attack_ended(SkillAttackEndContext* ctx) {
    if (!ctx) return;
    if (!ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "blackout") == NULL) return;

    int ap = ctx->attacker_player_index;
    int al = ctx->attack_level;

    // 1. SP1 浅紫色不可防御图标时间窗精确驱动
    if (al == 16) {
        if (!ctx->is_last_hit) {
            // SP1 第一击 (idx=0) 结束 -> 进入最后一击不可防御阶段，立即点亮浅紫色图标
            if (s_blackout_sp1_window_active[ap]) {
                blackout_show_sp1_unblockable(ap, "sp1_hit0_ended");
            }
        } else {
            // SP1 最后一击 (idx=100, LastHit) 结算完毕 -> 立即熄灭浅紫色图标
            blackout_clear_sp1_unblockable(ap, "sp1_last_hit_ended");
        }
        return; // S 技落空绝不触发追猎
    }

    // 2. S2 / S3 落空绝不触发追猎
    if (al == 32 || al == 64) {
        return;
    }

    // 3. 觉醒技【追猎】：仅普通攻击 (轻=1, 中=2, 重=4, 远程=8) 落空时触发
    int is_normal_attack = (al == 1 || al == 2 || al == 4 || al == 8);
    if (is_normal_attack && ctx->is_missed) {
        const char* kind = (al == 8) ? "ranged missed" : (al == 4 ? "heavy missed" : "melee missed");
        blackout_trigger_hunt_if_ready(ap, kind);
    }
}

// 受创硬直：被打断连击，全部清空暴击增益；若 SP1/SP2 被打断则同步清理
static void blackout_on_hitreact_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "blackout") == NULL) return;

    if (s_blackout_sp1_unblockable_on[player_index]) {
        blackout_clear_sp1_unblockable(player_index, "hitreact_interrupted");
    }
    if (skill_has_buff(player_index, "blackout_sp1_special_damage")) {
        skill_consume_buff(player_index, "blackout_sp1_special_damage", 99);
    }
    if (skill_has_buff(player_index, "blackout_sp1_crit_damage")) {
        skill_consume_buff(player_index, "blackout_sp1_crit_damage", 99);
    }
    if (skill_has_buff(player_index, "blackout_sp2_crit_damage")) {
        skill_consume_buff(player_index, "blackout_sp2_crit_damage", 99);
    }
    s_blackout_active_sp[player_index] = 0;

    if (s_blackout_combo[player_index] > 0) {
        skill_log("BLACKOUT: P%d hit, combo reset from %d to 0", player_index, s_blackout_combo[player_index]);
        s_blackout_combo[player_index] = 0;
        s_blackout_fury_active[player_index] = 0;

        skill_consume_buff(player_index, "blackout_combo_crit_rate", 99);
        skill_consume_buff(player_index, "blackout_combo_crit_dmg", 99);
        skill_consume_buff(player_index, "blackout_infinite_fury_crit_dmg", 99);
    }
}

// 修饰器过滤门禁：严格杜绝 SP1 误触发流血 (使用本机精确 s_blackout_active_sp，绝不误伤 SP2)
static int blackout_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    int ap = ctx->attacker_player_index;
    if (ap < 0 || ap >= 2) return 0;
    const char* atk_id = skill_get_bot_id(ap);
    if (!atk_id || strstr(atk_id, "blackout") == NULL) return 0;

    if (s_blackout_active_sp[ap] == 1) {
        if (strstr(ctx->modifier_id, "bleed") != NULL) {
            skill_log("BLACKOUT_GATE: suppressed bleed modifier during SP1 (mod=%s)", ctx->modifier_id);
            ctx->allow_application = false;
            return 1;
        }
    }

    // SP3 暴击抗性减益：严格限定最后一击命中方可施加
    if (strstr(ctx->modifier_id, "blackout_sp3_crit_resist_debuff") != NULL) {
        if (!ctx->current_hit_is_last) {
            skill_log("BLACKOUT_GATE: suppressed crit resist debuff on non-last hit (mod=%s)", ctx->modifier_id);
            ctx->allow_application = false;
            return 1;
        }
    }

    return 0;
}

// 周期同步：1) 精准驱动 SP1 最后一击浅紫色图标时间窗；2) 同步【无尽怒火】100% 暴击率阈值
static uint64_t s_blackout_last_fury_sync_ms = 0;
static void blackout_on_simulation_tick(uint64_t now_ms) {
    // A. SP1 最后一击时间窗 (每帧轻量检查)
    for (int p = 0; p < 2; p++) {
        if (s_blackout_sp1_window_active[p]) {
            // 如果第一击未触发或时间已到蓄力起手 (f=26 ≈ 800ms)，点亮浅紫色不可防御图标
            if (!s_blackout_sp1_unblockable_on[p] &&
                s_blackout_sp1_start_ms[p] > 0 &&
                now_ms >= s_blackout_sp1_start_ms[p] + 800) {
                blackout_show_sp1_unblockable(p, "sp1_charge_window_800ms");
            }
            // 安全兜底：SP1 退出超过 1200ms 或总时长超 3500ms 自动熄灭
            if (s_blackout_sp1_exit_ms[p] > 0 && now_ms >= s_blackout_sp1_exit_ms[p] + 1200) {
                blackout_clear_sp1_unblockable(p, "sp1_exit_timeout");
            } else if (s_blackout_sp1_start_ms[p] > 0 && now_ms >= s_blackout_sp1_start_ms[p] + 3500) {
                blackout_clear_sp1_unblockable(p, "sp1_max_timeout");
            }
        }
    }

    // B. 每 250ms 同步一次【无尽怒火】
    if (now_ms < s_blackout_last_fury_sync_ms + 250) return;
    s_blackout_last_fury_sync_ms = now_ms;
    for (int p = 0; p < 2; p++) {
        blackout_sync_infinite_fury(p);
    }
}

BotSkillModule g_module_blackout = {
    .bot_prefix              = "blackout",
    .on_hit_connected        = blackout_on_hit_connected,
    .on_buff_gated           = blackout_on_buff_gated,
    .on_buff_applied         = NULL,
    .on_evade_check          = NULL,
    .on_test_roll            = NULL,
    .on_power_gain_rate      = NULL,
    .on_reflect_proj         = NULL,
    .on_projectile_speed     = NULL,
    .on_fight_reset          = blackout_on_fight_reset,
    .on_simulation_tick      = blackout_on_simulation_tick,
    .on_block_state          = NULL,
    .on_dodge_enter          = NULL,
    .on_opponent_block_state = NULL,
    .on_opponent_dodge_enter = NULL,
    .on_hitreact_enter       = blackout_on_hitreact_enter,
    .on_attack_start         = NULL,
    .on_attack_ended         = blackout_on_attack_ended,
    .on_special_state        = blackout_on_special_state,
};
