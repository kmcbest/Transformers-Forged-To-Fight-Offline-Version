#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 艾丽塔 (Elita-1) 技能模块
// Bot ID: elita_one_gs
// 职业: 战术系 (Tactician) | 阵营: 汽车人 (Autobot)
// ===========================================================================
// 1. [被动 - 灵动反击]
//    - 闪避对手前冲攻击或近战攻击时，有 50% 的概率得到一个反击锦囊 (持续 1.0 秒)。
//    - 持有反击锦囊击中对手时，将对手眩晕 1.5 秒，并立即消耗反击锦囊。
//    - 持有反击锦囊攻击被对手闪避时，对对手施加 1 层 50% 的攻击减益持续 3 秒，并消耗反击锦囊。
//    - 未持有反击锦囊时，绝不触发反击眩晕与攻击减益 (纯净门禁，杜绝常驻连晕)。
// ===========================================================================

static void elita_on_dodge_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "elita") == NULL) return;

    int opp_index = 1 - player_index;
    uint64_t now_ms = skill_now_ms();
    uint64_t opp_dash_ms = skill_get_last_dash_ms(opp_index);
    uint64_t opp_melee_ms = skill_get_last_melee_ms(opp_index);

    int is_dash_evade = (opp_dash_ms > 0 && now_ms >= opp_dash_ms && (now_ms - opp_dash_ms <= 600));
    int is_melee_evade = (opp_melee_ms > 0 && now_ms >= opp_melee_ms && (now_ms - opp_melee_ms <= 600));

    if (is_dash_evade || is_melee_evade) {
        float roll = skill_random_float();
        if (roll < 0.50f) {
            skill_apply_buff_dur(player_index, "elita_counter_pouch_buff", 1.0f);
            skill_overlay("[%s] 灵动反击！获得反击锦囊(1秒)！", player_index == 0 ? "艾丽塔" : "敌方艾丽塔");
            skill_log("ELITA_COUNTER_POUCH: P%d evaded opponent %s (dt=%llu), gained counter pouch for 1.0s",
                      player_index, is_dash_evade ? "dash" : "melee",
                      (unsigned long long)(now_ms - (is_dash_evade ? opp_dash_ms : opp_melee_ms)));
        } else {
            skill_log("ELITA_COUNTER_POUCH_FAIL: P%d evaded %s but roll (%.2f) >= 0.50",
                      player_index, is_dash_evade ? "dash" : "melee", roll);
        }
    }
}

static void elita_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // 艾丽塔作为攻击方 (Attacker)
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "elita") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 唯有持有【反击锦囊】命中对手时才触发眩晕
        if (skill_has_buff(ap, "elita_counter_pouch")) {
            // 立即消耗反击锦囊，防止连招后续攻击无限连晕
            skill_consume_buff(ap, "elita_counter_pouch", 99);

            // 施加 1.5 秒反击眩晕
            skill_stun_player(tp, 1.5f);
            skill_apply_buff_dur(tp, "elita_counter_stun", 1.5f);
            skill_overlay("[%s] 反击眩晕！目标眩晕1.5秒！", ap == 0 ? "艾丽塔" : "敌方艾丽塔");
            skill_log("ELITA_STUN: P%d hit P%d with counter pouch -> stunned for 1.5s", ap, tp);
        }
    }
}

static int elita_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    // 针对反击眩晕和攻击减益实施铁律门禁：未持锦囊绝不允许施加
    if (strstr(ctx->modifier_id, "elita_counter_stun") != NULL ||
        strstr(ctx->modifier_id, "elita_counter_atk_debuff") != NULL) {
        int ap = ctx->attacker_player_index;
        if (skill_has_buff(ap, "elita_counter_pouch")) {
            skill_consume_buff(ap, "elita_counter_pouch", 99);
            ctx->allow_application = true;
            return 1;
        } else {
            // 彻底压制！绝不允许无锦囊时击晕
            ctx->allow_application = false;
            return 1;
        }
    }

    return 0;
}

static void elita_on_fight_reset(int player_index) {
    (void)player_index;
}

BotSkillModule g_module_elita = {
    .bot_prefix         = "elita",
    .on_hit_connected   = elita_on_hit_connected,
    .on_attack_start    = NULL,
    .on_dodge_enter     = elita_on_dodge_enter,
    .on_evade_check     = NULL,
    .on_buff_gated      = elita_on_buff_gated,
    .on_buff_applied    = NULL,
    .on_hitreact_enter  = NULL,
    .on_fight_reset     = elita_on_fight_reset,
};
