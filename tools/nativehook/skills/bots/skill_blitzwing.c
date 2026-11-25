#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 闪电 (Blitzwing) 专属三变形态与“抑制夹钳”技能控制模块
// Bot ID: blitzwing_gs
// ===========================================================================

static int      s_blitzwing_active[2]         = {0, 0};
static int      s_blitzwing_mode[2]           = {0, 0}; // 0 = TANK (E902), 1 = JET (E184)
static uint64_t s_block_start_ms[2]           = {0, 0};
static int      s_switched_this_block[2]      = {0, 0};
static int      s_second_wind_triggered[2]    = {0, 0}; // 绝处逢生每场战斗限 1 次
static uint64_t s_last_debuff_blocked_ms[2]   = {0, 0}; // 同一次受击多层减益同免时间戳
static int      s_opening_armor_pending[2]    = {0, 0}; // 开局护甲待发放标记 (正式开战首个tick时发放)

int skill_blitzwing_get_mode(int player_index) {
    if (player_index >= 0 && player_index < 2) return s_blitzwing_mode[player_index];
    return 0;
}

// ---------------------------------------------------------------------------
// 战斗重置与初始化
// ---------------------------------------------------------------------------
static void blitzwing_on_fight_reset(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bot_id = skill_get_bot_id(player_index);
    if (bot_id && strstr(bot_id, "blitzwing") != NULL) {
        s_blitzwing_active[player_index] = 1;
        s_blitzwing_mode[player_index] = 0; // 默认坦克形态
        s_block_start_ms[player_index] = 0;
        s_switched_this_block[player_index] = 0;
        s_second_wind_triggered[player_index] = 0;
        s_last_debuff_blocked_ms[player_index] = 0;
        s_opening_armor_pending[player_index] = 1; // 标记正式开战后发放护甲

        skill_consume_buff(player_index, "blitzwing_jet_mode", 99);
        skill_consume_buff(player_index, "blitzwing_tank_mode", 99);
        skill_consume_buff(player_index, "blitzwing_tank_armor", 99);
        skill_apply_buff_dur(player_index, "blitzwing_tank_mode", -1.0f);

        skill_overlay("[%s] 登场！默认【坦克形态】(E902)", player_index == 0 ? "闪电" : "敌方闪电");
        skill_log("BLITZWING: P%d initialized in TANK MODE (opening armor queued)", player_index);
    } else {
        s_blitzwing_active[player_index] = 0;
        s_blitzwing_mode[player_index] = 0;
        s_block_start_ms[player_index] = 0;
        s_switched_this_block[player_index] = 0;
        s_second_wind_triggered[player_index] = 0;
        s_last_debuff_blocked_ms[player_index] = 0;
        s_opening_armor_pending[player_index] = 0;
    }
}

// ---------------------------------------------------------------------------
// 连招命中与施加夹钳 (Hit Connected)
// ---------------------------------------------------------------------------
static void blitzwing_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // A. 闪电作为受击方 (Defender): 护甲减伤判定
    int def_p = ctx->target_player_index;
    if (def_p >= 0 && def_p < 2 && s_blitzwing_active[def_p]) {
        // 绝处逢生坦克护甲：降低 75% 受到伤害
        if (skill_has_buff(def_p, "blitzwing_sw_armor")) {
            ctx->modified_damage *= 0.25f;
            skill_log("BLITZWING: P%d Second Wind Armor reduced incoming dmg to 25%%", def_p);
        } else if (skill_has_buff(def_p, "blitzwing_tank_armor")) {
            // 坦克模式 20% 护甲减伤
            ctx->modified_damage *= 0.80f;
            skill_log("BLITZWING: P%d Tank Armor reduced incoming dmg to 80%%", def_p);
        }
    }

    // B. 闪电作为攻击方 (Attacker): 命中与夹钳判定
    int p = ctx->attacker_player_index;
    if (p < 0 || p >= 2 || !s_blitzwing_active[p]) return;
    int opp = ctx->target_player_index;
    if (opp < 0 || opp >= 2) return;

    // 关键门禁：对方格挡防御 (is_blocked) 时绝不施加抑制夹钳，也绝不触发命中掷骰！
    if (ctx->is_blocked) return;

    int current_mode = s_blitzwing_mode[p]; // 0=Tank, 1=Jet
    const char* clamp_id = (current_mode == 0) ? "blitzwing_clamp_tank" : "blitzwing_clamp_jet";

    // 1. 普通攻击 L4 或 M2 命中对手时 (20% 施加 4s)
    // 严格对齐既有成熟角色（震天尊 Megatronus / 滑流 Slipstream / 黄豹 Cheetor）的标准真理源：
    // 非特殊技、非重击、非远程、非防御，判定 L4 (action_type == 1, is_last_hit) 与 M2 (action_type == 2, is_last_hit)
    if (ctx->special_index == 0 && !ctx->is_heavy && !ctx->is_ranged) {
        int is_l4 = (ctx->action_type == 1 && (ctx->is_last_hit || ctx->hit_index == 3));
        int is_m2 = (ctx->action_type == 2 && (ctx->is_last_hit || ctx->hit_index == 1));

        if (is_l4 || is_m2) {
            float roll = skill_random_float();
            if (roll < 0.20f) {
                skill_apply_buff_dur(opp, clamp_id, 4.0f);
                skill_overlay("[%s] %s命中！施加【抑制夹钳】(4秒)",
                              p == 0 ? "我方" : "敌方", is_l4 ? "L4" : "M2");
                skill_log("BLITZWING: P%d landed %s on P%d -> applied 4s clamp", p, is_l4 ? "L4" : "M2", opp);
            }
        }
    }

    // 2. 重击命中 (80% 施加 4s)
    if (ctx->is_heavy && ctx->is_last_hit) {
        if (skill_random_float() < 0.80f) {
            skill_apply_buff_dur(opp, clamp_id, 4.0f);
            skill_overlay("[%s] 重击轰碎！施加【抑制夹钳】(4秒)", p == 0 ? "我方" : "敌方");
            skill_log("BLITZWING: P%d landed Heavy on P%d -> applied 4s clamp", p, opp);
        }
    }

    // 3. 特殊技 1 (SP1)
    if ((ctx->special_index == 1 || ctx->action_type == 16) && ctx->is_last_hit) {
        // 100% 施加 6s 夹钳
        skill_apply_buff_dur(opp, clamp_id, 6.0f);
        // 形态专属效果
        if (current_mode == 1) {
            skill_apply_buff_dur(opp, "blitzwing_sp1_armor_break", 7.0f); // 战机：30% 破甲 7s (E516)
            skill_overlay("[%s] SP1 空袭撕裂！施加【破甲】(E516) + 夹钳(6秒)", p == 0 ? "我方" : "敌方");
        } else {
            skill_apply_buff_dur(opp, "blitzwing_sp1_attack_debuff", 7.0f); // 坦克：30% 攻击减益 7s (E916)
            skill_overlay("[%s] SP1 重炮压制！施加【攻击减益】(E916) + 夹钳(6秒)", p == 0 ? "我方" : "敌方");
        }
    }

    // 4. 特殊技 2 (SP2)
    if (ctx->special_index == 2 || ctx->action_type == 32) {
        if (ctx->hit_index == 0) {
            if (current_mode == 1) {
                skill_apply_buff_dur(p, "blitzwing_jet_crit", 7.0f); // 战机首击：30% 暴击率 7s (E40D)
                skill_overlay("[%s] SP2 破空！获得【暴击几率】(E40D) 7秒！", p == 0 ? "我方" : "敌方");
            } else {
                skill_apply_buff_dur(p, "blitzwing_sp2_attack_buff", 7.0f); // 坦克首击：30% 攻击增益 7s (E406)
                skill_overlay("[%s] SP2 咆哮！获得【攻击增益】(E406) 7秒！", p == 0 ? "我方" : "敌方");
            }
        }
        if (ctx->is_last_hit) {
            skill_apply_buff_dur(opp, clamp_id, 8.0f); // 100% 施加 8s 夹钳
            skill_overlay("[%s] SP2 终结！施加【抑制夹钳】(8秒)", p == 0 ? "我方" : "敌方");
        }
    }

    // 5. 特殊技 3 (SP3) 技能完成后施加 5 层通用永久夹钳
    if ((ctx->special_index == 3 || ctx->action_type == 64) && ctx->is_last_hit) {
        for (int i = 0; i < 5; i++) {
            skill_apply_buff_dur(opp, "blitzwing_clamp_sp3", -1.0f);
        }
        skill_overlay("[%s] SP3 三变歼灭！对手植入 5 层【通用永久夹钳】！", p == 0 ? "我方" : "敌方");
    }
}

// ---------------------------------------------------------------------------
// 辅助判定: 是否属于战斗减益 (Debuff)
// ---------------------------------------------------------------------------
static int skill_is_debuff_modifier(const char* mod_id, void* stat_modifier) {
    if (!mod_id || !mod_id[0]) return 0;
    // 1. IL2CPP BCGStatModifier ModType 属性直接核验 (实机运行时最权威真理源)
    if (stat_modifier && skill_obj_ok(stat_modifier)) {
        void* bcg_sm = *(void**)((char*)stat_modifier + 0x18);
        if (bcg_sm && skill_obj_ok(bcg_sm)) {
            int32_t mt = *(int32_t*)((char*)bcg_sm + 0x4C);
            if (mt == 2 || mt == 16) return 1; // 2=debuff, 16=passive_debuff
            if (mt == 1 || mt == 8) return 0;  // 1=buff, 8=passive_buff
        }
    }
    // 2. 全库官方减益关键词详尽匹配 (支持模拟器与无反射环境)
    if (strstr(mod_id, "debuff") != NULL ||
        strstr(mod_id, "bleed") != NULL ||
        strstr(mod_id, "break") != NULL ||
        strstr(mod_id, "shock") != NULL ||
        strstr(mod_id, "burn") != NULL ||
        strstr(mod_id, "acid") != NULL ||
        strstr(mod_id, "leak") != NULL ||
        strstr(mod_id, "drain") != NULL ||
        strstr(mod_id, "steal") != NULL ||
        strstr(mod_id, "poison") != NULL ||
        strstr(mod_id, "corrosion") != NULL ||
        strstr(mod_id, "rust") != NULL ||
        strstr(mod_id, "rot") != NULL ||
        strstr(mod_id, "wither") != NULL ||
        strstr(mod_id, "stun") != NULL ||
        strstr(mod_id, "daze") != NULL ||
        strstr(mod_id, "freeze") != NULL ||
        strstr(mod_id, "chill") != NULL ||
        strstr(mod_id, "frost") != NULL ||
        strstr(mod_id, "slow") != NULL ||
        strstr(mod_id, "decel") != NULL ||
        strstr(mod_id, "fear") != NULL ||
        strstr(mod_id, "weakness") != NULL ||
        strstr(mod_id, "exhaust") != NULL ||
        strstr(mod_id, "fatigue") != NULL ||
        strstr(mod_id, "stagger") != NULL ||
        strstr(mod_id, "wound") != NULL ||
        strstr(mod_id, "glass_gas") != NULL ||
        strstr(mod_id, "anti_evade") != NULL ||
        strstr(mod_id, "heal_block") != NULL ||
        strstr(mod_id, "repair_block") != NULL ||
        strstr(mod_id, "confuse") != NULL) {
        return 1;
    }
    return 0;
}

// ---------------------------------------------------------------------------
// 辅助判定: 是否属于正向增益 (Buff)
// ---------------------------------------------------------------------------
static int skill_is_buff_modifier(const char* mod_id, void* stat_modifier) {
    if (!mod_id || !mod_id[0]) return 0;
    // 减益互斥关键词优先排除 (例如 armor_break 含有 armor，但属于减益)
    if (strstr(mod_id, "debuff") != NULL ||
        strstr(mod_id, "break") != NULL ||
        strstr(mod_id, "leak") != NULL ||
        strstr(mod_id, "drain") != NULL ||
        strstr(mod_id, "steal") != NULL) {
        return 0;
    }
    if (stat_modifier && skill_obj_ok(stat_modifier)) {
        void* bcg_sm = *(void**)((char*)stat_modifier + 0x18);
        if (bcg_sm && skill_obj_ok(bcg_sm)) {
            int32_t mt = *(int32_t*)((char*)bcg_sm + 0x4C);
            if (mt == 1 || mt == 8) return 1; // 1=buff, 8=passive_buff
            if (mt == 2 || mt == 16) return 0; // 2=debuff, 16=passive_debuff
        }
    }
    if (strstr(mod_id, "buff") != NULL ||
        strstr(mod_id, "crit") != NULL ||
        strstr(mod_id, "evade") != NULL ||
        strstr(mod_id, "armor") != NULL ||
        strstr(mod_id, "power") != NULL ||
        strstr(mod_id, "shield") != NULL ||
        strstr(mod_id, "regen") != NULL ||
        strstr(mod_id, "heal") != NULL ||
        strstr(mod_id, "fury") != NULL ||
        strstr(mod_id, "precision") != NULL ||
        strstr(mod_id, "cruelty") != NULL ||
        strstr(mod_id, "unstoppable") != NULL ||
        strstr(mod_id, "unblockable") != NULL ||
        strstr(mod_id, "focus") != NULL ||
        strstr(mod_id, "boost") != NULL ||
        strstr(mod_id, "certainty") != NULL ||
        strstr(mod_id, "surge") != NULL ||
        strstr(mod_id, "piercing") != NULL) {
        return 1;
    }
    return 0;
}

// ---------------------------------------------------------------------------
// 抑制夹钳核心拦截门禁 (Buff Gate: 抵消增益 / 抵消减益)
// ---------------------------------------------------------------------------
static int blitzwing_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx || !ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    // 豁免黑名单校验
    if (strstr(ctx->modifier_id, "relic") != NULL ||
        strstr(ctx->modifier_id, "charge") != NULL ||
        strstr(ctx->modifier_id, "stance") != NULL ||
        strstr(ctx->modifier_id, "blitzwing_") != NULL) {
        return 0; // 核心机制不予抵消
    }

    uint64_t now_ms = skill_now_ms();

    // 遍历在场双方，定位哪一方是闪电
    for (int p = 0; p < 2; p++) {
        if (!s_blitzwing_active[p]) continue;
        int opp = (p == 0) ? 1 : 0;

        // -------------------------------------------------------------------
        // 场景 A: 对方要获得正向增益 (Target == Opponent, Modifier == Buff)
        // -------------------------------------------------------------------
        if (ctx->target_player_index == opp) {
            if (skill_is_buff_modifier(ctx->modifier_id, ctx->stat_modifier)) {
                // 优先检查是否有坦克夹钳
                if (skill_has_buff(opp, "blitzwing_clamp_tank")) {
                    skill_consume_buff(opp, "blitzwing_clamp_tank", 1);
                    ctx->allow_application = false;
                    skill_overlay("[增益阻塞] 抑制夹钳抵消了对手的 %s！", ctx->modifier_id);
                    skill_log("BLITZWING_CLAMP: blocked opponent buff '%s' via tank clamp", ctx->modifier_id);
                    return 1;
                }
                // 次选检查 SP3 通用永久夹钳
                if (skill_has_buff(opp, "blitzwing_clamp_sp3")) {
                    skill_consume_buff(opp, "blitzwing_clamp_sp3", 1);
                    ctx->allow_application = false;
                    skill_overlay("[双重阻塞] 通用夹钳抵消了对手的 %s！", ctx->modifier_id);
                    skill_log("BLITZWING_CLAMP: blocked opponent buff '%s' via SP3 clamp", ctx->modifier_id);
                    return 1;
                }
            }
        }

        // -------------------------------------------------------------------
        // 场景 B: 对方要向闪电施加负面减益 (Target == Blitzwing, Modifier == Debuff)
        // -------------------------------------------------------------------
        if (ctx->target_player_index == p) {
            if (skill_is_debuff_modifier(ctx->modifier_id, ctx->stat_modifier)) {
                // 同一次攻击多层减益同免时间窗 (200ms)
                if (now_ms - s_last_debuff_blocked_ms[p] < 200) {
                    ctx->allow_application = false;
                    skill_log("BLITZWING_CLAMP: batch blocked debuff '%s'", ctx->modifier_id);
                    return 1;
                }

                if (skill_has_buff(opp, "blitzwing_clamp_jet")) {
                    skill_consume_buff(opp, "blitzwing_clamp_jet", 1);
                    s_last_debuff_blocked_ms[p] = now_ms;
                    ctx->allow_application = false;
                    skill_overlay("[减益阻塞] 战机夹钳抵消了受到的 %s！", ctx->modifier_id);
                    skill_log("BLITZWING_CLAMP: blocked incoming debuff '%s' via jet clamp", ctx->modifier_id);
                    return 1;
                }

                if (skill_has_buff(opp, "blitzwing_clamp_sp3")) {
                    skill_consume_buff(opp, "blitzwing_clamp_sp3", 1);
                    s_last_debuff_blocked_ms[p] = now_ms;
                    ctx->allow_application = false;
                    skill_overlay("[双重阻塞] 通用夹钳抵消了受到的 %s！", ctx->modifier_id);
                    skill_log("BLITZWING_CLAMP: blocked incoming debuff '%s' via SP3 clamp", ctx->modifier_id);
                    return 1;
                }
            }
        }
    }

    return 0;
}

// ---------------------------------------------------------------------------
// 周期模拟 Tick: 1) 长按防御变形; 2) 绝处逢生引爆
// ---------------------------------------------------------------------------
static void blitzwing_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (!s_blitzwing_active[p]) continue;
        int opp = (p == 0) ? 1 : 0;

        // 0. 开局护甲：正式开战后（首个 simulation tick）再触发判定与倒计时，绝不在选人动画或倒计时阶段空转浪费
        if (s_opening_armor_pending[p]) {
            s_opening_armor_pending[p] = 0;
            if (s_blitzwing_mode[p] == 0) {
                if (skill_random_float() < 0.50f) {
                    skill_apply_buff_dur(p, "blitzwing_tank_armor", 5.0f);
                    skill_overlay("[%s] 战斗开始！获得【护甲增益】(5秒)！", p == 0 ? "闪电" : "敌方闪电");
                    skill_log("BLITZWING: P%d fight officially started in TANK MODE -> applied 5s armor buff", p);
                }
            }
        }

        // A. 持防 1.0 秒变形切换
        if (s_block_start_ms[p] > 0 && !s_switched_this_block[p]) {
            if (now_ms - s_block_start_ms[p] >= 1000) {
                s_switched_this_block[p] = 1;
                if (s_blitzwing_mode[p] == 0) {
                    s_blitzwing_mode[p] = 1; // 坦克 -> 战机
                    skill_consume_buff(p, "blitzwing_tank_mode", 99);
                    skill_apply_buff_dur(p, "blitzwing_jet_mode", -1.0f);
                    if (skill_random_float() < 0.50f) {
                        skill_apply_buff_dur(p, "blitzwing_jet_crit", 7.0f);
                    }
                    skill_overlay("[%s] 变形！切换至【战机形态】(E184)！", p == 0 ? "闪电" : "敌方闪电");
                    skill_log("BLITZWING: P%d switched to JET MODE (E184)", p);
                } else {
                    s_blitzwing_mode[p] = 0; // 战机 -> 坦克
                    skill_consume_buff(p, "blitzwing_jet_mode", 99);
                    skill_apply_buff_dur(p, "blitzwing_tank_mode", -1.0f);
                    if (skill_random_float() < 0.50f) {
                        skill_apply_buff_dur(p, "blitzwing_tank_armor", 5.0f);
                    }
                    skill_overlay("[%s] 变形！切换至【坦克形态】(E902)！", p == 0 ? "闪电" : "敌方闪电");
                    skill_log("BLITZWING: P%d switched to TANK MODE (E902)", p);
                }
            }
        }

        // B. 绝处逢生 (Second Wind) 检测: HP <= 25%
        if (!s_second_wind_triggered[p] && skill_get_hp_ratio(p) <= 0.25f && skill_get_hp_ratio(p) > 0.0f) {
            s_second_wind_triggered[p] = 1;

            // 1. 赋予自身 75% 极速增益
            if (s_blitzwing_mode[p] == 0) {
                skill_apply_buff_dur(p, "blitzwing_sw_armor", 8.0f);
            } else {
                skill_apply_buff_dur(p, "blitzwing_sw_special", 8.0f);
            }

            // 2. 引爆对手身上所有抑制夹钳
            int c_tank = skill_count_buffs(opp, "blitzwing_clamp_tank");
            int c_jet  = skill_count_buffs(opp, "blitzwing_clamp_jet");
            int c_sp3  = skill_count_buffs(opp, "blitzwing_clamp_sp3");
            int total_clamps = c_tank + c_jet + c_sp3;

            if (total_clamps > 0) {
                skill_consume_buff(opp, "blitzwing_clamp_tank", 99);
                skill_consume_buff(opp, "blitzwing_clamp_jet", 99);
                skill_consume_buff(opp, "blitzwing_clamp_sp3", 99);

                // 造成 2.5 秒强控眩晕
                skill_stun_player(opp, 2.5f);
                skill_overlay("【绝处逢生】引爆 %d 层抑制夹钳！对手眩晕 2.5 秒！", total_clamps);
                skill_log("BLITZWING_SECOND_WIND: detonated %d clamps, stunned P%d for 2.5s", total_clamps, opp);
            } else {
                skill_overlay("【绝处逢生】极限启动！获得 75%% 形态强化！");
            }
        }
    }
}

static void blitzwing_on_block_state(int player_index, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    if (!s_blitzwing_active[player_index]) return;
    if (entered) {
        s_block_start_ms[player_index] = skill_now_ms();
        s_switched_this_block[player_index] = 0;
    } else {
        s_block_start_ms[player_index] = 0;
        s_switched_this_block[player_index] = 0;
    }
}

static void blitzwing_on_hitreact_enter(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_block_start_ms[player_index] = 0;
        s_switched_this_block[player_index] = 0;
    }
}

BotSkillModule g_module_blitzwing = {
    .bot_prefix              = "blitzwing",
    .on_hit_connected        = blitzwing_on_hit_connected,
    .on_buff_gated           = blitzwing_on_buff_gated,
    .on_buff_applied         = NULL,
    .on_evade_check          = NULL,
    .on_test_roll            = NULL,
    .on_power_gain_rate      = NULL,
    .on_reflect_proj         = NULL,
    .on_projectile_speed     = NULL,
    .on_fight_reset          = blitzwing_on_fight_reset,
    .on_simulation_tick      = blitzwing_on_simulation_tick,
    .on_block_state          = blitzwing_on_block_state,
    .on_dodge_enter          = NULL,
    .on_opponent_block_state = NULL,
    .on_opponent_dodge_enter = NULL,
    .on_hitreact_enter       = blitzwing_on_hitreact_enter,
    .on_attack_start         = NULL
};
