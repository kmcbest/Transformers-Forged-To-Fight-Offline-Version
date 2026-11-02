#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 艾丽塔 (Elita-1) 技能模块
// Bot ID: elita_one_gs
// 职业: 战术系 (Tactician) | 阵营: 汽车人 (Autobot)
// ===========================================================================
// 1. [被动 - 灵动反击] (Nimble Counter)
//    - 闪避对手前冲攻击或近战攻击时，有 50% 的概率得到一个反击锦囊 (持续 2.0 秒)。
//    - 双向招式因果对位判定（参考天火招架时空窗口设计，彻底去除死板距离限制）：
//      a) 针对前冲突进 (Dash) -> 我方侧滑闪避 (Sidestep)
//      b) 针对近战出招 (L1~L4 / M1~M2 / Heavy) -> 我方后滑闪避 (Backdash / Dodge)
//      c) 诱招挥空支持：我方打完5连击或拉开距离后滑/侧滑，对手随后出拳打空，100%可靠触发判定！
//    - 持有反击锦囊击中对手时，将对手眩晕 1.5 秒，并立即消耗反击锦囊。
//    - 若对手防御挡下攻击，不触发眩晕且保留锦囊；若对手处于霸体，免疫眩晕并消耗锦囊。
//    - 持有反击锦囊攻击被对手闪避时，对对手施加 1 层 50% 的攻击减益持续 3 秒，并消耗反击锦囊。
//    - 未持有反击锦囊时，绝不触发反击眩晕与攻击减益 (纯净门禁，杜绝常驻连晕)。
// ===========================================================================

static int s_elita_applying_counter_stun = 0;
static int s_elita_applying_atk_debuff = 0;
static uint64_t s_last_grant_attempt_ms[2] = {0, 0};

static void elita_try_grant_counter_pouch(int elita_idx, const char* reason) {
    if (elita_idx < 0 || elita_idx >= 2) return;
    // 已持有反击锦囊时不重复获取
    if (skill_has_buff(elita_idx, "elita_counter_pouch")) return;

    uint64_t now_ms = skill_now_ms();
    // 350ms 防抖，防止同一次攻击在多个时机重复判定
    if (now_ms - s_last_grant_attempt_ms[elita_idx] < 350) return;
    s_last_grant_attempt_ms[elita_idx] = now_ms;

    float roll = skill_random_float();
    if (roll < 0.50f) {
        skill_apply_buff_dur(elita_idx, "elita_counter_pouch_buff", 2.0f);
        skill_overlay("[%s] 灵动反击！获得反击锦囊(2秒)！", elita_idx == 0 ? "艾丽塔" : "敌方艾丽塔");
        skill_log("ELITA_COUNTER_POUCH: P%d successfully evaded opponent (%s), roll=%.2f < 0.50 -> gained counter pouch for 2.0s",
                  elita_idx, reason, roll);
    } else {
        skill_log("ELITA_COUNTER_POUCH_FAIL: P%d evaded opponent (%s) but roll (%.2f) >= 0.50", elita_idx, reason, roll);
    }
}

// 判定场景 1：艾丽塔进入闪避（侧滑或后滑）瞬间，检查对手是否正处于进攻态势
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

    // 判断刚刚进入的是侧闪还是后闪 (根据哪个时间戳在最近 120ms 内刷新)
    int is_sidestep = (last_sidestep >= last_backdash && (now_ms - last_sidestep < 120));

    if (is_sidestep) {
        // 侧滑闪避 (Sidestep) 对抗 对手前冲突进 (Dash)
        if (opp_dash_ms > 0 && now_ms >= opp_dash_ms && (now_ms - opp_dash_ms <= 850)) {
            elita_try_grant_counter_pouch(elita_idx, "reactive sidestep vs opponent dash");
        }
    } else {
        // 后滑闪避 (Backdash / Dodge) 对抗 对手近战攻击 (Melee L/M/H)
        if ((opp_melee_ms > 0 && now_ms >= opp_melee_ms && (now_ms - opp_melee_ms <= 650)) ||
            opp_melee_attacking || opp_attacking) {
            elita_try_grant_counter_pouch(elita_idx, "reactive backdash vs opponent melee");
        }
    }
}

// 判定场景 2：对手出招瞬间，检查艾丽塔是否刚刚做出了对应闪避（诱招打空 / 5连击后撤打空）
static void elita_on_attack_start(int attacker_index, int action_type) {
    for (int elita_idx = 0; elita_idx < 2; elita_idx++) {
        if (elita_idx == attacker_index) continue;
        const char* bid = skill_get_bot_id(elita_idx);
        if (!bid || strstr(bid, "elita") == NULL) continue;

        uint64_t now_ms = skill_now_ms();
        uint64_t last_backdash = skill_get_last_backdash_ms(elita_idx);
        uint64_t last_sidestep = skill_get_last_sidestep_ms(elita_idx);

        // 分支 A: 对手发起前冲 (Dash: action_type == 32 或 2) -> 艾丽塔在最近 650ms 内侧滑闪避
        if (action_type == 32 || action_type == 2) {
            if (last_sidestep > 0 && now_ms >= last_sidestep && (now_ms - last_sidestep <= 650)) {
                elita_try_grant_counter_pouch(elita_idx, "opponent dashed into active sidestep");
                return;
            }
        }

        // 分支 B: 对手发起近战攻击 (普攻轻击 1、中击 32/2、重击 4/0x100) -> 艾丽塔在最近 650ms 内后滑闪避
        if (action_type == 1 || action_type == 32 || action_type == 2 || action_type == 4 || action_type == 0x100) {
            if (last_backdash > 0 && now_ms >= last_backdash && (now_ms - last_backdash <= 650)) {
                elita_try_grant_counter_pouch(elita_idx, "opponent swung melee into active backdash");
                return;
            }
        }
    }
}

static void elita_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    // 艾丽塔作为攻击方 (Attacker)
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "elita") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // 攻击被对方格挡挡住，不算“击中对手”！不触发眩晕，不消耗锦囊！
        if (ctx->is_blocked || (ctx->hit_flags & 4) != 0) {
            skill_log("ELITA_HIT_BLOCKED: P%d hit P%d but was blocked (flags=0x%x) -> stun suppressed, pouch preserved",
                      ap, tp, ctx->hit_flags);
            return;
        }

        // 唯有持有【反击锦囊】且【真正击中对手 (Hit)】时才触发眩晕
        if (skill_has_buff(ap, "elita_counter_pouch")) {
            // 检查对手是否处于霸体
            if (skill_is_unstoppable(tp)) {
                skill_log("ELITA_STUN_IMMUNE: Target P%d is Unstoppable, stun resisted", tp);
                skill_overlay("[%s] 目标处于霸体状态！抵抗眩晕！", ap == 0 ? "艾丽塔" : "敌方艾丽塔");
            } else {
                // 施加 1.5 秒反击眩晕
                s_elita_applying_counter_stun = 1;
                skill_apply_buff_dur(tp, "elita_counter_stun", 1.5f);
                skill_stun_player(tp, 1.5f);
                s_elita_applying_counter_stun = 0;
                skill_overlay("[%s] 反击眩晕！目标眩晕1.5秒！", ap == 0 ? "艾丽塔" : "敌方艾丽塔");
                skill_log("ELITA_STUN: P%d hit P%d cleanly with counter pouch -> stunned for 1.5s", ap, tp);
            }

            // 立即消耗反击锦囊，防止连招后续攻击无限连晕
            skill_consume_buff(ap, "elita_counter_pouch", 99);
        }
    }
}

static int elita_on_buff_gated(SkillBuffGateContext* ctx) {
    if (!ctx->modifier_id || !ctx->modifier_id[0]) return 0;

    // 针对反击眩晕和攻击减益实施铁律门禁：未持锦囊绝不允许施加
    if (strstr(ctx->modifier_id, "elita_counter_stun") != NULL) {
        if (s_elita_applying_counter_stun) {
            ctx->allow_application = true;
            return 1;
        }
        int ap = ctx->attacker_player_index;
        if (skill_has_buff(ap, "elita_counter_pouch")) {
            ctx->allow_application = true;
            return 1;
        }
        // 彻底压制！绝不允许无锦囊时击晕
        ctx->allow_application = false;
        return 1;
    }

    if (strstr(ctx->modifier_id, "elita_counter_atk_debuff") != NULL) {
        if (s_elita_applying_atk_debuff) {
            ctx->allow_application = true;
            return 1;
        }
        int ap = ctx->attacker_player_index;
        if (skill_has_buff(ap, "elita_counter_pouch")) {
            ctx->allow_application = true;
            return 1;
        }
        ctx->allow_application = false;
        return 1;
    }

    return 0;
}

static void elita_on_fight_reset(int player_index) {
    (void)player_index;
    s_elita_applying_counter_stun = 0;
    s_elita_applying_atk_debuff = 0;
    s_last_grant_attempt_ms[0] = 0;
    s_last_grant_attempt_ms[1] = 0;
}

BotSkillModule g_module_elita = {
    .bot_prefix         = "elita",
    .on_hit_connected   = elita_on_hit_connected,
    .on_attack_start    = elita_on_attack_start,
    .on_dodge_enter     = elita_on_dodge_enter,
    .on_evade_check     = NULL,
    .on_buff_gated      = elita_on_buff_gated,
    .on_buff_applied    = NULL,
    .on_hitreact_enter  = NULL,
    .on_fight_reset     = elita_on_fight_reset,
};
