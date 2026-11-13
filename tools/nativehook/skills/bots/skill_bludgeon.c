#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 雷震 (Bludgeon) 底层战斗技能模块
// Bot ID: bludgeon_gs_rd20
// 职业: 格斗系 (Warrior) | 阵营: 霸天虎 (Decepticon)
// ===========================================================================
// 1. [被动 - 重击启动刷新护甲]
//    - 重击启动时立即刷新雷震身上所有护甲增益 (bludgeon_crit_struck_armor) 的倒计时 (7.0秒)。
// 2. [觉醒 - 钢铠法] (Metallikato)
//    - 当雷震近战出招落空 (对手后滑/侧滑闪避挥空) 时，获得钢铠法暴伤强化 (+250% 暴伤)。
//    - 下一次暴击命中时立即消耗并造成毁天灭地的爆发伤害。
// ===========================================================================

static uint64_t s_bludgeon_last_attack_start_ms[2] = {0, 0};
static int s_bludgeon_attack_action_type[2] = {0, 0};
static int s_bludgeon_attack_connected[2] = {0, 0};

// 雷震出招回调
static void bludgeon_on_attack_start(int attacker_index, int action_type) {
    if (attacker_index < 0 || attacker_index >= 2) return;
    const char* bid = skill_get_bot_id(attacker_index);
    if (!bid || strstr(bid, "bludgeon") == NULL) return;

    uint64_t now_ms = skill_now_ms();

    // 1. 重击启动时立即刷新身上所有护甲增益倒计时
    int is_heavy = (action_type == 4 || action_type == 0x100 || action_type == 3);
    if (is_heavy) {
        if (skill_has_buff(attacker_index, "bludgeon_crit_struck_armor")) {
            skill_apply_buff_dur(attacker_index, "bludgeon_crit_struck_armor", 7.0f);
            skill_overlay("[%s] 极意霸斩！刷新护甲增益倒计时！", attacker_index == 0 ? "雷震" : "敌方雷震");
            skill_log("BLUDGEON: P%d started Heavy Attack -> refreshed armor buff duration (7.0s)", attacker_index);
        }
    }

    // 记录出招状态用于判定挥空
    s_bludgeon_last_attack_start_ms[attacker_index] = now_ms;
    s_bludgeon_attack_action_type[attacker_index] = action_type;
    s_bludgeon_attack_connected[attacker_index] = 0;
}

// 命中连接
static void bludgeon_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;

    int ap = ctx->attacker_player_index;
    const char* atk_id = ctx->attacker_bot_id;

    if (atk_id && strstr(atk_id, "bludgeon") != NULL) {
        s_bludgeon_attack_connected[ap] = 1;

        // 钢铠法消耗：下一次暴击命中时消耗 +250% 暴伤增益
        if (ctx->is_crit) {
            if (skill_has_buff(ap, "bludgeon_metallikato_crit_dmg")) {
                skill_consume_buff(ap, "bludgeon_metallikato_crit_dmg", 1);
                skill_overlay("[%s] 钢铠法爆发！+250%%暴击斩击！", ap == 0 ? "雷震" : "敌方雷震");
                skill_log("BLUDGEON: Metallikato consumed on critical hit by P%d (+250%% crit damage proc)", ap);
            }
        }
    }
}

// 对手闪避进入时，检查雷震是否正在出招挥空
static void bludgeon_on_opponent_dodge_enter(int opponent_index) {
    if (opponent_index < 0 || opponent_index >= 2) return;
    int bludgeon_p = 1 - opponent_index;
    const char* bid = skill_get_bot_id(bludgeon_p);
    if (!bid || strstr(bid, "bludgeon") == NULL) return;

    // 如果雷震已经拥有钢铠法，不重复堆叠
    if (skill_has_buff(bludgeon_p, "bludgeon_metallikato_crit_dmg")) return;

    uint64_t now_ms = skill_now_ms();
    uint64_t atk_start = s_bludgeon_last_attack_start_ms[bludgeon_p];

    // 如果雷震在最近 650ms 内发起了近战攻击且未命中 (挥空)
    if (atk_start > 0 && now_ms >= atk_start && (now_ms - atk_start <= 650)) {
        if (!s_bludgeon_attack_connected[bludgeon_p]) {
            skill_apply_buff_dur(bludgeon_p, "bludgeon_metallikato_crit_dmg", -1.0f);
            skill_overlay("[%s] 近战落空！触发【钢铠法】(+250%%下次暴伤)！", bludgeon_p == 0 ? "雷震" : "敌方雷震");
            skill_log("BLUDGEON: P%d melee attack missed (opponent dodged), granted Metallikato (+250%% crit damage)", bludgeon_p);
        }
    }
}

static void bludgeon_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_bludgeon_last_attack_start_ms[player_index] = 0;
        s_bludgeon_attack_action_type[player_index] = 0;
        s_bludgeon_attack_connected[player_index] = 0;
    }
}

BotSkillModule g_module_bludgeon = {
    .bot_prefix = "bludgeon",
    .on_hit_connected = bludgeon_on_hit_connected,
    .on_buff_gated = NULL,
    .on_buff_applied = NULL,
    .on_evade_check = NULL,
    .on_test_roll = NULL,
    .on_power_gain_rate = NULL,
    .on_reflect_proj = NULL,
    .on_projectile_speed = NULL,
    .on_fight_reset = bludgeon_on_fight_reset,
    .on_simulation_tick = NULL,
    .on_block_state = NULL,
    .on_dodge_enter = NULL,
    .on_opponent_block_state = NULL,
    .on_opponent_dodge_enter = bludgeon_on_opponent_dodge_enter,
    .on_hitreact_enter = NULL,
    .on_attack_start = bludgeon_on_attack_start,
};
