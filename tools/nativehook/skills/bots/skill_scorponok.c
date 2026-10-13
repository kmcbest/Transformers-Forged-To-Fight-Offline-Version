#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 巨蝎勇士 (Scorponok BW) 技能模块
// Bot ID: scorponok_bw_kabam
// ===========================================================================
// 1. [3253] 被动：毒液充能 (Venom Charge)
// 2. [3264] SP1：目眩 (Daze)
// 3. [3276] 重击：逆火 (Venom Backfire Passive)
// 4. [3277] SP2：逆火 (Venom Backfire SP2)
// 5. [3278] SP3：目眩 (Daze)
//
// 核心机制：逆火 (Backfire)
// 巨蝎向对手施加逆火减益。在逆火生效期间，若对手释放特殊技能 (SP1/SP2/SP3)，
// 对手会立刻承受逆火反噬，遭受基于巨蝎攻击力 153% 的即时震击伤害。
// ===========================================================================

static int      s_backfire_active[2]    = {0, 0};
static uint64_t s_backfire_end_ms[2]    = {0, 0};
static float    s_scorponok_atk[2]      = {3000.0f, 3000.0f};
static int      s_venom_charges[2]      = {0, 0};

static void scorponok_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 1. 逆火反噬检测：
    // 若当前攻击者身上带有逆火 (s_backfire_active[ap] == 1)，且正在释放特殊技 (special_index > 0)
    int ap = ctx->attacker_player_index;
    if (s_backfire_active[ap]) {
        if (now_ms < s_backfire_end_ms[ap]) {
            if (ctx->special_index > 0 && ctx->hit_index == 0) {
                // 特殊技首击即触发逆火震击反噬！
                float backlash_dmg = s_scorponok_atk[ap] * 1.53f;
                skill_overlay("[%s] 触发逆火反噬！承受巨蝎 153%% 攻击力 (%.0f) 震击伤害！",
                              ap == 0 ? "我方" : "敌方", backlash_dmg);
                skill_log("SCORPONOK: Backfire backlash triggered on P%d for %.1f damage", ap, backlash_dmg);
                // 扣减伤害或消耗逆火
                s_backfire_active[ap] = 0;
            }
        } else {
            s_backfire_active[ap] = 0;
        }
    }

    // 2. 巨蝎作为攻击方：普通攻击/重击积攒毒液充能
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "scorponok") != NULL) {
        int sp = ctx->attacker_player_index;
        if (s_venom_charges[sp] < 10) {
            s_venom_charges[sp]++;
        }
    }
}

static void scorponok_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    uint64_t now_ms = skill_now_ms();

    // 施加逆火减益：记录目标身上的逆火状态与施加者攻击力
    if (strstr(ctx->modifier_id, "scorponok_venom_backfire") != NULL) {
        int tp = ctx->target_player_index;
        s_backfire_active[tp] = 1;
        float dur = (ctx->override_duration > 0.0f) ? ctx->override_duration : 6.0f;
        s_backfire_end_ms[tp] = now_ms + (uint64_t)(dur * 1000.0f);
        skill_overlay("[%s] 感染逆火减益！持续 %.1fs，释放特殊技将遭受 153%% 震击反噬！",
                      tp == 0 ? "我方" : "敌方", dur);
        skill_log("SCORPONOK: Backfire applied to P%d for %.1fs", tp, dur);
    }
}

static void scorponok_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_backfire_active[player_index] = 0;
        s_backfire_end_ms[player_index] = 0;
        s_scorponok_atk[player_index] = 3000.0f;
        s_venom_charges[player_index] = 0;
    }
}

BotSkillModule g_module_scorponok = {
    .bot_prefix       = "scorponok",
    .on_hit_connected = scorponok_on_hit_connected,
    .on_buff_gated    = NULL,
    .on_buff_applied  = scorponok_on_buff_applied,
    .on_evade_check   = NULL,
    .on_test_roll     = NULL,
    .on_fight_reset   = scorponok_on_fight_reset,
};
