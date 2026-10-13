#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 热破 (Hot Rod TLK) 技能模块
// Bot ID: hotrod_cin_tlk
// ===========================================================================
// 1. [3086] 重击：眩晕 (Heavy Stun)
// 2. [3089] 远程减速：能量获取率减益 (Deceleration Power Gain Rate Debuff)
// 3. [3099] SP2：减速时间场 (SP2 Deceleration Bubble)
// 4. [3100] SP3：超载减速 (SP3 Deceleration Bubble)
//
// 核心机制：减速 (Deceleration - 克制规避)
// 当对手受到减速效果时，其时间流速被阻滞，绝对禁止闪避 (近战规避/远程规避均归零)。
// ===========================================================================

static int      s_decel_active[2] = {0, 0};
static uint64_t s_decel_end_ms[2] = {0, 0};

static void hotrod_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;
    uint64_t now_ms = skill_now_ms();

    // 减速 Debuff 激活检测
    if (strstr(ctx->modifier_id, "decel") != NULL ||
        strstr(ctx->modifier_id, "hotrod_sp2_deceleration") != NULL ||
        strstr(ctx->modifier_id, "hotrod_sp3_deceleration") != NULL) {
        int tp = ctx->target_player_index;
        s_decel_active[tp] = 1;
        float dur = (ctx->override_duration > 0.0f) ? ctx->override_duration : 6.0f;
        s_decel_end_ms[tp] = now_ms + (uint64_t)(dur * 1000.0f);
        skill_overlay("[%s] 陷入热破时间减速场！规避能力彻底封锁 (持续 %.1fs)",
                      tp == 0 ? "我方" : "敌方", dur);
        skill_log("HOTROD: Deceleration applied to P%d for %.1fs, evasion disabled", tp, dur);
    }
}

static int hotrod_on_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    uint64_t now_ms = skill_now_ms();

    int p = ctx->player_index;
    if (s_decel_active[p]) {
        if (now_ms < s_decel_end_ms[p]) {
            // 减速压制：强行判定闪避失败！
            *out_evade = 0;
            skill_overlay("[%s] 减速压制！禁止闪避！", p == 0 ? "我方" : "敌方");
            skill_log("HOTROD: Evade denied on P%d due to active deceleration bubble", p);
            return 1; // 已接管并覆盖判定
        } else {
            s_decel_active[p] = 0;
        }
    }
    return 0;
}

static void hotrod_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_decel_active[player_index] = 0;
        s_decel_end_ms[player_index] = 0;
    }
}

BotSkillModule g_module_hotrod = {
    .bot_prefix       = "hotrod",
    .on_hit_connected = NULL,
    .on_buff_gated    = NULL,
    .on_buff_applied  = hotrod_on_buff_applied,
    .on_evade_check   = hotrod_on_evade_check,
    .on_test_roll     = NULL,
    .on_fight_reset   = hotrod_on_fight_reset,
};
