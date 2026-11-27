#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 恐龙勇士 (Dinobot BW) 底层战斗技能模块
// Bot ID: dinobot_bw_kabam
// 职业: 战术系 (Tactician) | 阵营: 巨无霸 (Maximal)
// ===========================================================================
// 1. [被动 - 护甲穿透] (Armor Piercing)
//    - 近战攻击自带 65% 护甲穿透 (ctx->is_melee)；近战暴击 100% 护甲穿透。
// 2. [被动 - 格挡反伤] (Blocking Damage)
//    - 格挡对方近战攻击时，60% 几率反向造成对手攻击力 10% 的伤害。
//    - 格挡对方前冲攻击时，100% 几率反向造成对手攻击力 20% 的伤害。
// 3. [被动 - 格挡破甲] (Blocking Armor Break)
//    - 格挡对方前冲攻击时，100% 施加 1 层 40% 破甲减益，持续 9 秒 (原生抵消 1 层护甲)。
// 4. [被动 - 即时格挡精通] (Block Proficiency)
//    - 即时格挡 (held_ms <= 380ms，对齐天火招架护盾窗口) 时降低格挡伤害 50%。
// 5. [特殊技 3 - 修复] (Cretaceous Carnage Repair)
//    - 仅 3 下咬击 (hit_index == 1, 2, 3；排除起手 hit=0 与末尾 4 段眼射激光 hit=4..7)
//      每击有 50% 概率获 4s 修复 (3% 最大生命值)。
// 6. [觉醒 - 适者生存] (Survival of the Fittest)
//    - 对手处于破甲状态并格挡恐龙勇士的任何攻击时：
//      * 有 20% 概率使恐龙勇士本次攻击不可防御 (无战斗 HUD 图标，真实破防)；
//      * 未破防而被格挡时，格挡穿透伤害提高 20%。
// ===========================================================================

#define DINOBOT_PERFECT_BLOCK_MS 380

static int      s_unblock_swing_roll[2]    = {0, 0};
static uint64_t s_unblock_swing_ms[2]      = {0, 0};
static int      s_unblock_broke_guard[2]   = {0, 0};
static int      s_unblock_announced[2]     = {0, 0};

static int dinobot_is_self(const char* bot_id) {
    return (bot_id && strstr(bot_id, "dinobot") != NULL);
}

static int dinobot_has_armor_break(int target_player_index) {
    return skill_has_buff(target_player_index, "armor_break") ||
           skill_has_buff(target_player_index, "dinobot_dash_block_break") ||
           skill_has_buff(target_player_index, "dinobot_sp1_armor_break");
}

static void dinobot_on_fight_reset(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    s_unblock_swing_roll[player_index] = 0;
    s_unblock_swing_ms[player_index] = 0;
    s_unblock_broke_guard[player_index] = 0;
    s_unblock_announced[player_index] = 0;
}

static void dinobot_on_attack_start(int player_index, int action_type) {
    (void)action_type;
    if (player_index < 0 || player_index >= 2) return;
    if (!dinobot_is_self(skill_get_bot_id(player_index))) return;

    uint64_t now_ms = skill_now_ms();
    // 防止 SP 启动同帧连续两次派发 (0x200+idx 与 sp_action) 重复掷骰子
    if (s_unblock_swing_ms[player_index] > 0 && now_ms >= s_unblock_swing_ms[player_index] &&
        (now_ms - s_unblock_swing_ms[player_index] < 60)) {
        return;
    }
    float roll = skill_random_float();
    s_unblock_swing_roll[player_index] = (roll < 0.20f) ? 1 : 0;
    s_unblock_swing_ms[player_index] = now_ms;
    s_unblock_broke_guard[player_index] = 0;
    s_unblock_announced[player_index] = 0;
}

static void dinobot_on_attack_ended(SkillAttackEndContext* ctx) {
    if (!ctx || !dinobot_is_self(ctx->attacker_bot_id)) return;
    if (ctx->is_last_hit || (ctx->attack_level & (1 | 2 | 4 | 8)) != 0) {
        int ap = ctx->attacker_player_index;
        if (ap >= 0 && ap < 2) {
            s_unblock_swing_roll[ap] = 0;
            s_unblock_broke_guard[ap] = 0;
            s_unblock_announced[ap] = 0;
        }
    }
}

static int dinobot_on_unblockable_check(int attacker_player_index, int* out_unblockable) {
    if (attacker_player_index < 0 || attacker_player_index >= 2 || !out_unblockable) return 0;
    if (!dinobot_is_self(skill_get_bot_id(attacker_player_index))) return 0;
    // 重击本身原生破防，不消耗或归功于觉醒“适者生存”
    if (skill_is_heavy_attacking(attacker_player_index)) return 0;

    int opp = 1 - attacker_player_index;
    if (!dinobot_has_armor_break(opp)) return 0;
    if (skill_get_block_enter_ms(opp) == 0) return 0;

    uint64_t now_ms = skill_now_ms();
    if (s_unblock_swing_ms[attacker_player_index] == 0 || now_ms < s_unblock_swing_ms[attacker_player_index] ||
        (now_ms - s_unblock_swing_ms[attacker_player_index] > 2500)) {
        // 兜底：若连段后续未经过 on_attack_start 重新触发，按 300ms 短窗单次检定
        float roll = skill_random_float();
        s_unblock_swing_roll[attacker_player_index] = (roll < 0.20f) ? 1 : 0;
        s_unblock_swing_ms[attacker_player_index] = now_ms;
        s_unblock_broke_guard[attacker_player_index] = 0;
        s_unblock_announced[attacker_player_index] = 0;
    }

    if (s_unblock_swing_roll[attacker_player_index] == 1) {
        s_unblock_broke_guard[attacker_player_index] = 1;
        *out_unblockable = 1;
        return 1;
    }
    return 0;
}

static void dinobot_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;
    uint64_t now_ms = skill_now_ms();

    // -----------------------------------------------------------------------
    // A) 恐龙勇士作为格挡防守方 (受击): 即时格挡精通、格挡反伤、格挡前冲破甲
    // -----------------------------------------------------------------------
    if (dinobot_is_self(ctx->target_bot_id) && ctx->is_blocked) {
        uint64_t block_start = skill_get_block_enter_ms(tp);
        uint64_t held_ms = (block_start > 0 && now_ms >= block_start) ? (now_ms - block_start) : 999999;

        // 1. 即时格挡精通：380ms 内即时格挡降低格挡伤害 50% (与天火招架窗口同步)
        if (held_ms <= DINOBOT_PERFECT_BLOCK_MS) {
            ctx->modified_damage *= 0.50f;
            skill_overlay("[%s] 即时格挡！格挡伤害降低50%%！", tp == 0 ? "恐龙勇士" : "敌方恐龙勇士");
            skill_log("DINOBOT_WELL_TIMED_BLOCK: P%d well-timed block (held=%llu ms <= %d), blocked dmg -50%%",
                      tp, (unsigned long long)held_ms, DINOBOT_PERFECT_BLOCK_MS);
        }

        // 2. 格挡前冲 / 格挡近战判定
        //    注意严禁把真机 Special2 (action_type == 32) 或连招中击误判为前冲攻击
#ifdef __ANDROID__
        int is_dash = (ctx->special_index == 0 && skill_is_dash_attacking(ap));
#else
        int is_dash = (!ctx->is_ranged && ctx->special_index == 0 && ctx->action_type == 32);
#endif
        if (is_dash) {
            // 格挡前冲攻击：100% 施加 1 层 40% 破甲 9 秒 (原生抵消 1 层护甲)
            skill_apply_buff_dur(ap, "dinobot_dash_block_break", 9.0f);
            // 格挡前冲攻击：100% 概率反向造成对手 20% 攻击力伤害
            float opp_atk = skill_get_attack(ap);
            if (opp_atk <= 0.0f) opp_atk = 3000.0f;
            float reflect_dmg = opp_atk * 0.20f;
            skill_deal_damage(ap, reflect_dmg);
            skill_overlay("[%s] 格挡前冲！反弹20%%伤害并施加破甲！", tp == 0 ? "恐龙勇士" : "敌方恐龙勇士");
            skill_log("DINOBOT_DASH_BLOCK: P%d blocked Dash attack from P%d -> 40%% Armor Break (9s) + reflect %.1f",
                      tp, ap, reflect_dmg);
        } else if (ctx->is_melee) {
            // 格挡常规近战攻击 (L/M/H, 排除 SP 与远程)：60% 概率反向造成对手 10% 攻击力伤害
            float roll = skill_random_float();
            if (roll < 0.60f) {
                float opp_atk = skill_get_attack(ap);
                if (opp_atk <= 0.0f) opp_atk = 3000.0f;
                float reflect_dmg = opp_atk * 0.10f;
                skill_deal_damage(ap, reflect_dmg);
                skill_overlay("[%s] 格挡反伤！反弹10%%近战伤害！", tp == 0 ? "恐龙勇士" : "敌方恐龙勇士");
                skill_log("DINOBOT_MELEE_BLOCK: P%d blocked Melee attack from P%d (roll=%.2f < 0.60) -> reflect %.1f",
                          tp, ap, roll, reflect_dmg);
            } else {
                skill_log("DINOBOT_MELEE_BLOCK_MISS: P%d blocked Melee from P%d (roll=%.2f >= 0.60)",
                          tp, ap, roll);
            }
        }
    }

    // -----------------------------------------------------------------------
    // B) 恐龙勇士作为进攻方 (Attacker): 护甲穿透、SP3 中段修复、适者生存
    // -----------------------------------------------------------------------
    if (dinobot_is_self(ctx->attacker_bot_id)) {
        // 1. [被动 - 护甲穿透]: 仅近战攻击 (65%), 近战暴击 (100%)
        if (ctx->is_melee) {
            float pierce = ctx->is_crit ? 1.00f : 0.65f;
            if (ctx->armor_penetration < pierce) {
                ctx->armor_penetration = pierce;
            }
            skill_log("DINOBOT_ARMOR_PIERCE: P%d melee hit (crit=%d) -> armor_penetration=%.2f",
                      ap, ctx->is_crit ? 1 : 0, ctx->armor_penetration);
        }

        // 2. [SP3 - 修复]: 仅咬击段 (hit_index == 1, 2, 3) 每击 50% 概率 4s 修复 3% 最大生命值
        //    SP3 实机 8 段结构: hit=0(起手) | hit=1,2,3(咬击x3) | hit=4..7(眼射激光x4)
        if (ctx->special_index == 3 && !ctx->is_blocked) {
            if (ctx->hit_index >= 1 && ctx->hit_index <= 3) {
                float roll = skill_random_float();
                if (roll < 0.50f) {
                    skill_apply_buff_dur(ap, "dinobot_sp3_repair", 4.0f);
                    skill_log("DINOBOT_SP3_REPAIR: P%d bite hit=%d gained 4s repair (roll=%.2f < 0.50)",
                              ap, ctx->hit_index, roll);
                } else {
                    skill_log("DINOBOT_SP3_REPAIR_MISS: P%d bite hit=%d roll=%.2f >= 0.50",
                              ap, ctx->hit_index, roll);
                }
            } else {
                skill_log("DINOBOT_SP3_REPAIR_SKIP: P%d skipped non-bite hit (hit=%d last=%d)",
                          ap, ctx->hit_index, ctx->is_last_hit ? 1 : 0);
            }
        }

        // 3. [觉醒 - 适者生存]: 对手破甲状态下格挡 -> 20% 真实不可防御(成功破防我方弹出“适者生存”) / 否则格挡伤害提高 20%
        int opp_has_armor_break = dinobot_has_armor_break(tp);
        if (opp_has_armor_break) {
            if (ctx->is_blocked) {
                ctx->modified_damage *= 1.20f;
                skill_log("DINOBOT_SIG_BLOCK_DMG: P%d blocked dmg +20%% vs Armor-Broken P%d (dmg=%.1f)",
                          ap, tp, ctx->modified_damage);
            } else if (ap >= 0 && ap < 2 && !ctx->is_heavy &&
                       s_unblock_broke_guard[ap] == 1 && !s_unblock_announced[ap]) {
                s_unblock_announced[ap] = 1;
                s_unblock_broke_guard[ap] = 0;
                skill_apply_buff_dur(ap, "dinobot_sig_callout", 0.8f);
                skill_overlay("[%s] 适者生存！不可防御破防！", ap == 0 ? "恐龙勇士" : "敌方恐龙勇士");
                skill_log("DINOBOT_SIG_UNBLOCKABLE: P%d landed unblockable hit on Armor-Broken P%d (sp=%d hit=%d blk=0)",
                          ap, tp, ctx->special_index, ctx->hit_index);
            }
        }
    }
}

BotSkillModule g_module_dinobot = {
    .bot_prefix           = "dinobot",
    .display_name_zh      = "恐龙勇士",
    .on_hit_connected     = dinobot_on_hit_connected,
    .on_fight_reset       = dinobot_on_fight_reset,
    .on_attack_start      = dinobot_on_attack_start,
    .on_attack_ended      = dinobot_on_attack_ended,
    .on_unblockable_check = dinobot_on_unblockable_check,
};
