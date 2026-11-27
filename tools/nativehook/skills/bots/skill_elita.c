#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 艾丽塔 (Elita-1) 技能模块
// Bot ID: elita_one_gs / elita_one_gs_kabam
// 职业: 战术系 (Tactician) | 阵营: 汽车人 (Autobot)
// ===========================================================================

static int s_elita_applying_counter_stun = 0;
static int s_elita_applying_atk_debuff = 0;
static uint64_t s_last_grant_attempt_ms[2] = {0, 0};
static int s_flame_50_used[2] = {0, 0};
static int s_flame_25_used[2] = {0, 0};
static int s_interrupt_used[2] = {0, 0};

static void elita_try_grant_counter_pouch(int elita_idx, const char* reason) {
    if (elita_idx < 0 || elita_idx >= 2) return;
    if (skill_has_buff(elita_idx, "elita_counter_pouch")) return;

    uint64_t now_ms = skill_now_ms();
    if (now_ms - s_last_grant_attempt_ms[elita_idx] < 350) return;
    s_last_grant_attempt_ms[elita_idx] = now_ms;

    float roll = skill_random_float();
    if (roll < 0.50f) {
        skill_apply_buff_dur(elita_idx, "elita_counter_pouch_buff", 2.0f);
        skill_overlay("[%s] 灵动反击！获得反击锦囊(2秒)！", elita_idx == 0 ? "艾丽塔" : "敌方艾丽塔");
        skill_log("ELITA_COUNTER_POUCH: P%d evaded opponent (%s), roll=%.2f < 0.50 -> gained pouch (2.0s)",
                  elita_idx, reason, roll);
    } else {
        skill_log("ELITA_COUNTER_POUCH_FAIL: P%d evaded opponent (%s), roll=%.2f >= 0.50",
                  elita_idx, reason, roll);
    }
}

// 灵动反击场景 1: 艾丽塔进入闪避瞬间检查对手进攻动作
static void elita_on_dodge_enter(int elita_idx) {
    if (elita_idx < 0 || elita_idx >= 2) return;
    const char* bid = skill_get_bot_id(elita_idx);
    if (!bid || strstr(bid, "elita") == NULL) return;

    uint64_t now_ms = skill_now_ms();
    int opp_index = 1 - elita_idx;

    uint64_t opp_dash_ms = skill_get_last_dash_ms(opp_index);
    uint64_t opp_melee_ms = skill_get_last_melee_ms(opp_index);
    int opp_attacking = skill_is_attacking(opp_index);
    int opp_melee_attacking = skill_is_melee_attacking(opp_index);

    uint64_t last_sidestep = skill_get_last_sidestep_ms(elita_idx);
    uint64_t last_backdash = skill_get_last_backdash_ms(elita_idx);
    int is_sidestep = (last_sidestep >= last_backdash && (now_ms - last_sidestep < 120));

    if (is_sidestep) {
        if (opp_dash_ms > 0 && now_ms >= opp_dash_ms && (now_ms - opp_dash_ms <= 850)) {
            elita_try_grant_counter_pouch(elita_idx, "reactive sidestep vs opponent dash");
        }
    } else {
        if ((opp_melee_ms > 0 && now_ms >= opp_melee_ms && (now_ms - opp_melee_ms <= 650)) ||
            opp_melee_attacking || opp_attacking) {
            elita_try_grant_counter_pouch(elita_idx, "reactive backdash vs opponent melee");
        }
    }
}

// 灵动反击场景 2: 对手发起近战或前冲，艾丽塔此前刚刚主动闪避
static void elita_on_attack_start(int attacker_index, int action_type) {
    for (int elita_idx = 0; elita_idx < 2; elita_idx++) {
        if (elita_idx == attacker_index) continue;
        const char* bid = skill_get_bot_id(elita_idx);
        if (!bid || strstr(bid, "elita") == NULL) continue;

        uint64_t now_ms = skill_now_ms();
        uint64_t last_backdash = skill_get_last_backdash_ms(elita_idx);
        uint64_t last_sidestep = skill_get_last_sidestep_ms(elita_idx);

        // 对手前冲 (Dash: action_type == 2) -> 侧滑闪避
        if (action_type == 2) {
            if (last_sidestep > 0 && now_ms >= last_sidestep && (now_ms - last_sidestep <= 650)) {
                elita_try_grant_counter_pouch(elita_idx, "opponent dashed into active sidestep");
                return;
            }
        }

        // 对手近战攻击 (Light=1, Medium/Dash=2/32, Heavy=4/0x100) -> 后滑闪避
        if (action_type == 1 || action_type == 32 || action_type == 2 || action_type == 4 || action_type == 0x100) {
            if (last_backdash > 0 && now_ms >= last_backdash && (now_ms - last_backdash <= 650)) {
                elita_try_grant_counter_pouch(elita_idx, "opponent swung melee into active backdash");
                return;
            }
        }
    }
}

// 统一终态结算 (ctx->is_missed 复用瘟疫“落空”状态机):
// 1. 艾丽塔持有反击锦囊期间，自身任何攻击落空 (无论对方普通后闪/侧闪/被动规避) -> 对对手施加 50% 攻击减益 (3s)
// 2. 对手近战/前冲打空挥空 -> 艾丽塔近期侧滑/后滑闪避触发反击锦囊判定
static void elita_on_attack_ended(SkillAttackEndContext* ctx) {
    if (!ctx || !ctx->is_missed) return;

    // 分支 A: 艾丽塔进攻落空
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "elita") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;
        if (skill_has_buff(ap, "elita_counter_pouch")) {
            s_elita_applying_atk_debuff = 1;
            skill_apply_buff_dur(tp, "elita_counter_atk_debuff", 3.0f);
            s_elita_applying_atk_debuff = 0;
            skill_consume_buff(ap, "elita_counter_pouch", 99);
            skill_overlay("[%s] 攻击落空！对对手施加50%%攻击减益(3秒)！", ap == 0 ? "艾丽塔" : "敌方艾丽塔");
            skill_log("ELITA_COUNTER_MISSED: P%d attack missed P%d (al=%d flags=0x%x) with pouch -> 50%% atk debuff (3.0s)",
                      ap, tp, ctx->attack_level, ctx->flags);
        }
        return;
    }

    // 分支 B: 对手近战/前冲打空
    if (!ctx->target_bot_id || strstr(ctx->target_bot_id, "elita") == NULL) return;
    int elita_idx = ctx->target_player_index;
    int al = ctx->attack_level;
    // Light(1), Medium/Dash(2), Heavy(4)
    if ((al & (1 | 2 | 4)) == 0) return;

    uint64_t now_ms = skill_now_ms();
    uint64_t last_side = skill_get_last_sidestep_ms(elita_idx);
    uint64_t last_back = skill_get_last_backdash_ms(elita_idx);

    if (al == 2 && last_side > 0 && now_ms >= last_side && (now_ms - last_side <= 800)) {
        elita_try_grant_counter_pouch(elita_idx, "whiff dash evaded by sidestep");
    } else if (last_back > 0 && now_ms >= last_back && (now_ms - last_back <= 750)) {
        elita_try_grant_counter_pouch(elita_idx, "whiff melee evaded by backdash");
    }
}

// 艾丽塔自身 SP3 结束: 【战术封锁】封印对手全部特殊攻击 8 秒
static void elita_on_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    const char* actor_bid = skill_get_bot_id(player_index);
    if (entered == 0 && sp_level == 3 && actor_bid && strstr(actor_bid, "elita") != NULL) {
        int tp = 1 - player_index;
        skill_apply_buff_dur(tp, "elita_sp3_tactical_lockdown", 8.0f);
        skill_set_special_lock(tp, 8000);
        skill_overlay("[%s] 战术封锁！对手特殊技封印8秒！", player_index == 0 ? "艾丽塔" : "敌方艾丽塔");
        skill_log("ELITA_SP3: P%d exited SP3 -> applied 8.0s Tactical Lockdown on P%d", player_index, tp);
    }
}

// 对手释放 SP1/SP2: 艾丽塔 HP<=25% 时【抵抗军之火】概率打断并眩晕 1.5s (斗士系 70%, 非斗士 40%, 每局1次)
static void elita_on_opponent_special_state(int opponent_player_index, int sp_level, int entered) {
    if (entered != 1 || (sp_level != 1 && sp_level != 2)) return;
    if (opponent_player_index < 0 || opponent_player_index >= 2) return;
    int elita_idx = 1 - opponent_player_index;
    const char* elita_bid = skill_get_bot_id(elita_idx);
    if (!elita_bid || strstr(elita_bid, "elita") == NULL || s_interrupt_used[elita_idx]) return;

    float hp_r = skill_get_hp_ratio(elita_idx);
    if (hp_r > 0.0f && hp_r <= 0.25f) {
        int opp_is_braw = ((skill_get_bot_class(opponent_player_index) & BOT_CLASS_BRAW) != 0);
        float chance = opp_is_braw ? 0.70f : 0.40f;
        float roll = skill_random_float();
        if (roll < chance) {
            s_interrupt_used[elita_idx] = 1;
            skill_apply_buff_dur(opponent_player_index,
                opp_is_braw ? "elita_sig_flame_interrupt_stun_braw" : "elita_sig_flame_interrupt_stun",
                1.5f);
            skill_interrupt_special(opponent_player_index, 1.5f);
            skill_overlay("[%s] 抵抗军之火！打断 SP%d 并眩晕 1.5 秒！",
                          elita_idx == 0 ? "艾丽塔" : "敌方艾丽塔", sp_level);
            skill_log("ELITA_INTERRUPT: P%d interrupted P%d SP%d (braw=%d, roll=%.2f < %.2f)",
                      elita_idx, opponent_player_index, sp_level, opp_is_braw, roll, chance);
        } else {
            skill_log("ELITA_INTERRUPT_FAIL: P%d vs P%d SP%d (braw=%d, roll=%.2f >= %.2f)",
                      elita_idx, opponent_player_index, sp_level, opp_is_braw, roll, chance);
        }
    }
}

static void elita_on_simulation_tick(uint64_t now_ms) {
    (void)now_ms;
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "elita") == NULL) continue;

        float hp_r = skill_get_hp_ratio(p);
        if (hp_r <= 0.0f) continue;
        if (!s_flame_50_used[p] && hp_r <= 0.50f) {
            s_flame_50_used[p] = 1;
            skill_apply_buff_dur(p, "elita_sig_flame_atk_50", 6.0f);
            skill_apply_buff_dur(p, "elita_sig_flame_crit_50", 6.0f);
            skill_log("ELITA_FLAME_50: P%d HP<=50%% -> ATK+50%% & Crit+50%% (6s)", p);
        }
        if (!s_flame_25_used[p] && hp_r <= 0.25f) {
            s_flame_25_used[p] = 1;
            skill_apply_buff_dur(p, "elita_sig_flame_armor_25", 6.0f);
            skill_log("ELITA_FLAME_25: P%d HP<=25%% -> Armor+90%% (6s)", p);
        }
    }
}

// 纯净只读规避查询 (禁止在 get_EvadeMelee 内修改状态机或 Buff!)
static int elita_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade || !ctx->bot_id || strstr(ctx->bot_id, "elita") == NULL) return 0;
    if (!ctx->is_ranged && skill_is_unstoppable(1 - ctx->player_index)) {
        *out_evade = 1;
        return 1;
    }
    return 0;
}

static void elita_on_evade_triggered(int evader_player_index, int is_ranged) {
    const char* evader_id = skill_get_bot_id(evader_player_index);
    int opp_idx = 1 - evader_player_index;

    // 1. 艾丽塔战术洞察规避不可阻挡对手的近战攻击 -> 弹出绿字“规避”并立即获得 3 秒近战增益 (+30%)
    if (!is_ranged && evader_id && strstr(evader_id, "elita") != NULL && skill_is_unstoppable(opp_idx)) {
        skill_apply_buff_dur(evader_player_index, "gp_evade_callout", 1.0f);
        skill_apply_buff_dur(evader_player_index, "elita_tactical_insight_melee_buff", 3.0f);
        skill_overlay("[%s] 战术洞察规避霸体！近战增益+30%%(3秒)", evader_player_index == 0 ? "艾丽塔" : "敌方艾丽塔");
        skill_log("ELITA_INSIGHT: P%d evaded unstoppable melee -> green evade callout + 30%% melee buff (3.0s)", evader_player_index);
    }
}

static void elita_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // 防守方收益: 若对手持有艾丽塔施加的 50% 攻击减益，削弱其本次伤害 50%
    if (ctx->target_bot_id && strstr(ctx->target_bot_id, "elita") != NULL) {
        if (skill_has_buff(ctx->attacker_player_index, "elita_counter_atk_debuff")) {
            ctx->modified_damage *= 0.50f;
            skill_log("ELITA_WEAKEN: P%d attack under 50%% atk debuff -> dmg=%.1f",
                      ctx->attacker_player_index, ctx->modified_damage);
        }
    }

    // 艾丽塔作为攻击方 (Attacker)
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "elita") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 1. 关节狙击: 远程攻击 100% 护甲穿透；命中或被防均有 70% 概率刷新对手全部减益
        if (ctx->is_ranged) {
            ctx->armor_penetration = 1.0f;
            float roll = skill_random_float();
            if (roll < 0.70f) {
                if (skill_refresh_target_debuffs(tp) > 0) {
                    skill_apply_buff_dur(tp, "elita_joint_aim_refresh", 0.5f);
                    skill_overlay("[%s] 关节狙击！刷新对手减益！", ap == 0 ? "艾丽塔" : "敌方艾丽塔");
                }
                skill_log("ELITA_JOINT_AIM: P%d ranged (blk=%d) refreshed P%d debuffs (roll=%.2f < 0.70)",
                          ap, ctx->is_blocked ? 1 : 0, tp, roll);
            }
        }

        // 2. 战术洞察近战增益 (+30% 仅对近战)
        if (ctx->is_melee && skill_has_buff(ap, "elita_tactical_insight_melee_buff")) {
            ctx->modified_damage *= 1.30f;
            skill_log("ELITA_INSIGHT_DMG: P%d melee boosted +30%% -> %.1f", ap, ctx->modified_damage);
        }

        // 格挡门禁: 被对方格挡挡住时不触发眩晕、不消耗锦囊、不触发 SP 收招减益，但前面远程刷新已结算
        if (ctx->is_blocked || (ctx->hit_flags & HIT_FLAG_BLOCKED) != 0) {
            skill_log("ELITA_HIT_BLOCKED: P%d -> P%d blocked (flags=0x%x)", ap, tp, ctx->hit_flags);
            return;
        }

        // 3. 持有【反击锦囊】且真正击中对手 -> 眩晕 1.5 秒并消耗锦囊
        if (skill_has_buff(ap, "elita_counter_pouch")) {
            if (skill_is_unstoppable(tp)) {
                skill_log("ELITA_STUN_IMMUNE: Target P%d is Unstoppable, stun resisted", tp);
                skill_overlay("[%s] 目标处于霸体状态！抵抗眩晕！", ap == 0 ? "艾丽塔" : "敌方艾丽塔");
            } else {
                s_elita_applying_counter_stun = 1;
                skill_apply_buff_dur(tp, "elita_counter_stun", 1.5f);
                skill_stun_player(tp, 1.5f);
                s_elita_applying_counter_stun = 0;
                skill_overlay("[%s] 反击眩晕！目标眩晕1.5秒！", ap == 0 ? "艾丽塔" : "敌方艾丽塔");
                skill_log("ELITA_STUN: P%d hit P%d cleanly with counter pouch -> stunned 1.5s", ap, tp);
            }
            skill_consume_buff(ap, "elita_counter_pouch", 99);
        }

        // 4. SP1 最后一击: 100% 破甲 (普通 35% / 斗士 50%, 7s) + 满能量燃烧 (扣 5% = 0.15 格)
        if (ctx->special_index == 1 && ctx->is_last_hit) {
            if ((skill_get_bot_class(tp) & BOT_CLASS_BRAW) != 0) {
                skill_apply_buff_dur(tp, "elita_sp1_armor_break_braw", 7.0f);
                skill_log("ELITA_SP1: Last hit vs brawler P%d -> 50%% armor break (7s)", tp);
            } else {
                skill_apply_buff_dur(tp, "elita_sp1_armor_break", 7.0f);
                skill_log("ELITA_SP1: Last hit vs P%d -> 35%% armor break (7s)", tp);
            }
            if (skill_get_mana(tp) >= 2.999f) {
                skill_add_mana(tp, -0.15f);
                skill_apply_buff_dur(tp, "elita_sp1_power_burn", 0.5f);
                skill_overlay("[%s] 能量燃烧！扣除满能量 5%%！", ap == 0 ? "艾丽塔" : "敌方艾丽塔");
                skill_log("ELITA_SP1: Last hit burned 5%% max power from full P%d", tp);
            }
        }

        // 5. SP2 最后一击: 100% 震击 (100% ATK, 10s)
        if (ctx->special_index == 2 && ctx->is_last_hit) {
            skill_apply_buff_dur(tp, "elita_sp2_shock", 10.0f);
            skill_log("ELITA_SP2: Last hit inflicted Shock (10s) on P%d", tp);
        }

        // 6. SP3 最后一击: 流血 (120% ATK, 6s)
        if (ctx->special_index == 3 && ctx->is_last_hit) {
            skill_apply_buff_dur(tp, "elita_sp3_bleed", 6.0f);
            skill_log("ELITA_SP3: Last hit inflicted Bleed (6s) on P%d", tp);
        }

        // 7. 领袖威仪: 处于 DOT 状态时每次击中对手加速 DOT 倒计时 20% (skill_accelerate_dots 直接按 Buff._buffType 检索全部 dmg_* / acid)
        int acc = skill_accelerate_dots(ap, 0.20f);
        if (acc > 0) {
            skill_apply_buff_dur(ap, "elita_commanders_presence", 0.5f);
        }
    }
}

static int elita_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    if (strstr(ctx->modifier_id, "elita_counter_stun") != NULL) {
        if (s_elita_applying_counter_stun || skill_has_buff(ctx->attacker_player_index, "elita_counter_pouch")) {
            ctx->allow_application = true;
            return 1;
        }
        ctx->allow_application = false;
        return 1;
    }

    if (strstr(ctx->modifier_id, "elita_counter_atk_debuff") != NULL) {
        if (s_elita_applying_atk_debuff || skill_has_buff(ctx->attacker_player_index, "elita_counter_pouch")) {
            ctx->allow_application = true;
            return 1;
        }
        ctx->allow_application = false;
        return 1;
    }

    return 0;
}

static int elita_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !ctx->modifier_id || !out_res) return 0;

    if (strstr(ctx->modifier_id, "elita_counter_stun") != NULL ||
        strstr(ctx->modifier_id, "elita_counter_atk_debuff") != NULL) {
        if (!skill_has_buff(ctx->owner_player_index, "elita_counter_pouch")) {
            *out_res = 0;
            return 1;
        }
    }
    return 0;
}

static void elita_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_last_grant_attempt_ms[player_index] = 0;
        s_flame_50_used[player_index] = 0;
        s_flame_25_used[player_index] = 0;
        s_interrupt_used[player_index] = 0;
    }
    s_elita_applying_counter_stun = 0;
    s_elita_applying_atk_debuff = 0;
}

BotSkillModule g_module_elita = {
    .bot_prefix         = "elita",
    .display_name_zh    = "艾丽塔",
    .on_hit_connected   = elita_on_hit_connected,
    .on_attack_start    = elita_on_attack_start,
    .on_attack_ended    = elita_on_attack_ended,
    .on_special_state   = elita_on_special_state,
    .on_opponent_special_state = elita_on_opponent_special_state,
    .on_dodge_enter     = elita_on_dodge_enter,
    .on_evade_check     = elita_on_evade_check,
    .on_evade_triggered = elita_on_evade_triggered,
    .on_test_roll       = elita_on_test_roll,
    .on_buff_gated      = elita_on_buff_gated,
    .on_simulation_tick = elita_on_simulation_tick,
    .on_fight_reset     = elita_on_fight_reset,
};
