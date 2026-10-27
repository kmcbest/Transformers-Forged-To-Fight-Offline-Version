#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 钢锁 (Grimlock MP-08) 技能模块
// Bot ID: grimlock_gs_mp08
// ===========================================================================
// 1. [2532] 被动：受击近战增益 (Melee Buff on Struck) +25%
// 2. [2534] 招牌：恐龙之怒 (Dino Rage - 延时净化与近战狂暴 +30%/层)
// 3. [2542] 被动：重击燃烧 (Heavy Burn)
// 4. [2543] 被动：重击不可阻挡 (Heavy Unstoppable)
// 5. [2544] SP1：近战增益 (SP1 Melee Buff) +40%
// 6. [2545] SP1：燃烧 (SP1 Burn)
// 7. [2546] SP2：近战增益 (SP2 Melee Buff) +60%
//
// 核心机制：恐龙之怒 (Dino Rage)
// 受到伤害类减益 (流血/燃烧/震击) 后 1.0 秒净化该减益，并有 30% 概率激活 +30% 近战增益。
// ===========================================================================

static uint64_t s_rage_pending_purify_ms[2] = {0, 0};
static int      s_rage_melee_stacks[2]      = {0, 0};

static void grimlock_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 检查延时净化到期
    for (int p = 0; p < 2; p++) {
        if (s_rage_pending_purify_ms[p] > 0 && now_ms >= s_rage_pending_purify_ms[p]) {
            s_rage_pending_purify_ms[p] = 0;
            // 掷骰 30% 几率激活近战狂暴
            int roll = (int)(now_ms % 100);
            if (roll < 30) {
                s_rage_melee_stacks[p]++;
                skill_overlay("[%s] 恐龙之怒触发！净化伤害减益并激活 +30%% 近战狂暴！",
                              p == 0 ? "钢锁" : "敌方钢锁");
                skill_log("GRIMLOCK: Dino Rage purified debuff on P%d, gained melee boost stack %d",
                          p, s_rage_melee_stacks[p]);
            } else {
                skill_overlay("[%s] 恐龙之怒触发！成功净化伤害减益！",
                              p == 0 ? "钢锁" : "敌方钢锁");
                skill_log("GRIMLOCK: Dino Rage purified debuff on P%d", p);
            }
        }
    }

    // 钢锁作为攻击方：应用恐龙之怒及各项近战增益加成 (受击近战+25%、SP1+40%、SP2+60%、怒气+30%/层)
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "grimlock") != NULL) {
        int ap = ctx->attacker_player_index;
        if (!ctx->is_ranged) {
            float boost = 1.0f;
            if (s_rage_melee_stacks[ap] > 0) {
                boost += 0.30f * (float)s_rage_melee_stacks[ap];
            }
            if (skill_has_buff(ap, "grimlock_takehit_melee_buff")) {
                boost += 0.25f;
            }
            if (skill_has_buff(ap, "grimlock_sp1_melee_buff")) {
                boost += 0.40f;
            }
            if (skill_has_buff(ap, "grimlock_sp2_melee_buff")) {
                boost += 0.60f;
            }
            if (boost > 1.0f) {
                float old_dmg = ctx->modified_damage;
                ctx->modified_damage *= boost;
                skill_log("GRIMLOCK: Melee damage boosted x%.2f (%.1f -> %.1f) on P%d",
                          boost, old_dmg, ctx->modified_damage, ap);
            }
        }
    }
}

static void grimlock_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    uint64_t now_ms = skill_now_ms();

    // 若钢锁受到伤害类 Debuff (bleed, burn, shock):
    int tp = ctx->target_player_index;
    if (strstr(ctx->modifier_id, "bleed") != NULL ||
        strstr(ctx->modifier_id, "burn") != NULL ||
        strstr(ctx->modifier_id, "shock") != NULL) {
        // 设置 1.0 秒后延时净化
        s_rage_pending_purify_ms[tp] = now_ms + 1000;
        skill_overlay("[%s] 受到伤害减益！恐龙之怒准备中 (1.0s 后净化)...",
                      tp == 0 ? "钢锁" : "敌方钢锁");
        skill_log("GRIMLOCK: Damaging debuff [%s] detected on P%d, scheduled Dino Rage purify in 1000ms",
                  ctx->modifier_id, tp);
    }
}

static void grimlock_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_rage_pending_purify_ms[player_index] = 0;
        s_rage_melee_stacks[player_index] = 0;
    }
}

BotSkillModule g_module_grimlock = {
    .bot_prefix       = "grimlock",
    .on_hit_connected = grimlock_on_hit_connected,
    .on_buff_gated    = NULL,
    .on_buff_applied  = grimlock_on_buff_applied,
    .on_evade_check   = NULL,
    .on_test_roll     = NULL,
    .on_fight_reset   = grimlock_on_fight_reset,
};
