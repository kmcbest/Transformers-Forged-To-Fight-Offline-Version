#include "sim_bridge.h"
#include "../nativehook/skills/skill_env.h"
#include "../nativehook/skills/skill_types.h"
#include "../nativehook/skills/skill_dispatcher.h"
#include <stdio.h>
#include <string.h>
#include <stdarg.h>
#include <stdlib.h>

extern int _vsnprintf(char* str, size_t size, const char* format, va_list ap);

int vsnprintf(char* str, size_t size, const char* format, va_list ap) {
    if (!str || size == 0) return 0;
    int r = _vsnprintf(str, size, format, ap);
    str[size - 1] = '\0';
    return r;
}

int snprintf(char* str, size_t size, const char* format, ...) {
    va_list ap;
    va_start(ap, format);
    int r = vsnprintf(str, size, format, ap);
    va_end(ap);
    return r;
}


int __stdcall DllMain(void* hinstDLL, unsigned long fdwReason, void* lpvReserved) {
    (void)hinstDLL; (void)fdwReason; (void)lpvReserved;
    return 1;
}

#define MAX_BUFFS 48
#define MAX_LOG_LINES 128
#define MAX_FLOATERS 64
#define LOG_LINE_LEN 256

char g_p0_bot_id[64] = "";
char g_p1_bot_id[64] = "";


// ---------------------------------------------------------------------------
// 战斗实体模型
// ---------------------------------------------------------------------------
typedef struct {
    char mod_id[64];
    float duration_s;
    int64_t remaining_ms; // -1 表示永久 (Fused/Permanent)
    int stacks;
    uint64_t applied_ms;
    float dot_damage_per_sec;
    uint64_t next_dot_ms;
} SimBuff;

typedef struct {
    char bot_id[64];
    char name[64];
    float max_hp;
    float hp;
    float mana; // 0.0 ~ 3.0 格
    float atk;
    float crit_rate;
    float crit_damage_mult; // 默认 1.5
    float block_reduction;  // 默认 0.50

    int is_blocking;
    uint64_t block_enter_ms;
    uint64_t unstoppable_end_ms;
    uint64_t power_lock_end_ms;
    uint64_t ranged_boost_end_ms;
    float ranged_damage_bonus;

    int is_heavy;
    int in_special;
    int current_action;

    int prowl_melee_stacks;
    int prowl_charging;
    uint64_t prowl_charge_start_ms;
    int prowl_charge_stacks;
    uint64_t prowl_melee_buff_end_ms;
    uint64_t next_prowl_tick_ms;

    int buff_count;
    SimBuff buffs[MAX_BUFFS];
} SimCombatant;

typedef struct {
    int player_index;
    int type; // 0=DAMAGE, 1=CRIT, 2=HEAL, 3=MANA, 4=PURIFY, 5=ANNOUNCEMENT
    float value;
    char text[64];
} SimFloater;

static SimCombatant g_players[2];
static uint64_t g_sim_clock_ms = 1000; // 从 1000ms 起算
static int g_p1_buffs_nullified = 0;

static char g_logs[MAX_LOG_LINES][LOG_LINE_LEN];
static int g_log_head = 0;
static int g_log_count = 0;

static SimFloater g_floaters[MAX_FLOATERS];
static int g_floater_count = 0;

static char g_last_announcement[128] = "";

// ---------------------------------------------------------------------------
// 辅助日志与浮字记录
// ---------------------------------------------------------------------------
static void push_log(const char* text) {
    int idx = (g_log_head + g_log_count) % MAX_LOG_LINES;
    if (g_log_count < MAX_LOG_LINES) {
        g_log_count++;
    } else {
        g_log_head = (g_log_head + 1) % MAX_LOG_LINES;
    }
    strncpy(g_logs[idx], text, LOG_LINE_LEN - 1);
    g_logs[idx][LOG_LINE_LEN - 1] = '\0';
}

static void push_floater(int player_index, int type, float value, const char* text) {
    if (g_floater_count >= MAX_FLOATERS) return;
    SimFloater* f = &g_floaters[g_floater_count++];
    f->player_index = player_index;
    f->type = type;
    f->value = value;
    strncpy(f->text, text ? text : "", sizeof(f->text) - 1);
    f->text[sizeof(f->text) - 1] = '\0';
}

// ---------------------------------------------------------------------------
// 实现 skill_env.h 契约
// ---------------------------------------------------------------------------
void skill_log(const char* fmt, ...) {
    char buf[LOG_LINE_LEN];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    push_log(buf);
}

void skill_overlay(const char* fmt, ...) {
    char buf[128];
    va_list ap;
    va_start(ap, fmt);
    vsnprintf(buf, sizeof(buf), fmt, ap);
    va_end(ap);
    strncpy(g_last_announcement, buf, sizeof(g_last_announcement) - 1);
    push_log(buf);
    push_floater(0, 5, 0.0f, buf);
}

uint64_t skill_now_ms(void) {
    return g_sim_clock_ms;
}

float skill_random_float(void) {
    return ((float)rand()) / (float)RAND_MAX;
}

int skill_is_p0_bc(void* bc) {
    return (bc == (void*)&g_players[0]);
}

int skill_is_p0_attr(void* attr) {
    return (attr == (void*)&g_players[0]);
}

int skill_obj_ok(void* ptr) {
    return ptr != NULL;
}

int skill_get_p1_buffs_nullified(void) {
    return g_p1_buffs_nullified;
}

void skill_set_p1_buffs_nullified(int val) {
    g_p1_buffs_nullified = val;
}

void skill_set_ranged_boost(int player_index, uint64_t duration_ms, float dmg_bonus, float spd_bonus) {
    if (player_index >= 0 && player_index < 2) {
        g_players[player_index].ranged_boost_end_ms = g_sim_clock_ms + duration_ms;
        g_players[player_index].ranged_damage_bonus = dmg_bonus;
    }
}

void skill_set_power_leak(int player_index, uint64_t duration_ms, float step) {
    (void)player_index; (void)duration_ms; (void)step;
}

void skill_set_power_lock(int target_player_index, uint64_t duration_ms) {
    if (target_player_index >= 0 && target_player_index < 2) {
        g_players[target_player_index].power_lock_end_ms = g_sim_clock_ms + duration_ms;
    }
}

void skill_set_unstoppable(int player_index, uint64_t duration_ms) {
    if (player_index >= 0 && player_index < 2) {
        g_players[player_index].unstoppable_end_ms = g_sim_clock_ms + duration_ms;
        push_floater(player_index, 5, 0.0f, "不可阻挡");
    }
}

int skill_is_unstoppable(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        return (g_sim_clock_ms < g_players[player_index].unstoppable_end_ms);
    }
    return 0;
}

float skill_get_hp_ratio(int player_index) {
    if (player_index >= 0 && player_index < 2 && g_players[player_index].max_hp > 0.0f) {
        return g_players[player_index].hp / g_players[player_index].max_hp;
    }
    return 1.0f;
}

void skill_heal(int player_index, float amount) {
    if (player_index >= 0 && player_index < 2 && amount > 0.0f) {
        g_players[player_index].hp += amount;
        if (g_players[player_index].hp > g_players[player_index].max_hp) {
            g_players[player_index].hp = g_players[player_index].max_hp;
        }
        push_floater(player_index, 2, amount, "吸血/回血");
    }
}

void skill_deal_damage(int target_player_index, float damage) {
    if (target_player_index >= 0 && target_player_index < 2 && damage > 0.0f) {
        g_players[target_player_index].hp -= damage;
        if (g_players[target_player_index].hp < 0.0f) {
            g_players[target_player_index].hp = 0.0f;
        }
        push_floater(target_player_index, 0, damage, "额外伤害");
    }
}

void skill_add_mana(int player_index, float norm_mana) {
    if (player_index >= 0 && player_index < 2) {
        g_players[player_index].mana += norm_mana;
        if (g_players[player_index].mana > 3.0f) g_players[player_index].mana = 3.0f;
        if (g_players[player_index].mana < 0.0f) g_players[player_index].mana = 0.0f;
        push_floater(player_index, 3, norm_mana * 100.0f, "+能量");
    }
}

SIM_API int sim_set_mana(int player_index, float mana) {
    if (player_index < 0 || player_index >= 2) return 0;
    if (mana < 0.0f) mana = 0.0f;
    if (mana > 3.0f) mana = 3.0f;
    g_players[player_index].mana = mana;
    skill_log("SIM: P%d mana set to %.2f / 3.00", player_index, mana);
    return 1;
}

uint64_t skill_get_block_enter_ms(int player_index) {
    if (player_index >= 0 && player_index < 2 && g_players[player_index].is_blocking) {
        return g_players[player_index].block_enter_ms;
    }
    return 0;
}

void skill_stun_player(int target_player_index, float duration_s) {
    if (target_player_index >= 0 && target_player_index < 2) {
        g_players[target_player_index].is_blocking = 0;
        // 若受击方尚未持有任何眩晕类 Buff (如 windblade_bleed_remote_stun)，才挂载通用 "stun" 占位
        if (!skill_has_buff(target_player_index, "stun")) {
            skill_apply_buff_dur(target_player_index, "stun", duration_s);
        }
        push_floater(target_player_index, 5, duration_s, "眩晕");
    }
}

int skill_has_buff(int player_index, const char* buff_id_substr) {
    return skill_count_buffs(player_index, buff_id_substr) > 0;
}

int skill_count_buffs(int player_index, const char* buff_id_substr) {
    if (player_index < 0 || player_index >= 2 || !buff_id_substr || !buff_id_substr[0]) return 0;
    SimCombatant* c = &g_players[player_index];
    int count = 0;
    for (int i = 0; i < c->buff_count; i++) {
        if (strstr(c->buffs[i].mod_id, buff_id_substr) != NULL) {
            count += c->buffs[i].stacks;
        }
    }
    return count;
}

void skill_apply_buff(int player_index, const char* mod_id) {
    skill_apply_buff_dur(player_index, mod_id, -1.0f);
}

void skill_apply_buff_dur(int player_index, const char* mod_id, float override_dur) {
    if (player_index < 0 || player_index >= 2 || !mod_id || !mod_id[0]) return;
    sim_inject_buff(player_index, mod_id, override_dur, 1);
}

void skill_consume_buff(int player_index, const char* mod_id, int count) {
    sim_remove_buff(player_index, mod_id, count);
}

int skill_fuse_target_debuffs(int target_player_index) {
    if (target_player_index < 0 || target_player_index >= 2) return 0;
    SimCombatant* c = &g_players[target_player_index];
    int fused = 0;
    for (int i = 0; i < c->buff_count; i++) {
        if (c->buffs[i].remaining_ms > 0) { // 带倒计时的减益
            c->buffs[i].remaining_ms = -1; // 转化为永久！
            fused++;
            skill_log("SIM: Debuff '%s' on P%d FUSED to PERMANENT!", c->buffs[i].mod_id, target_player_index);
        }
    }
    return fused;
}

int skill_get_prowl_melee_stacks(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        int b_stacks = skill_count_buffs(player_index, "prowl_melee_buff");
        if (b_stacks > 0) return b_stacks;
        return g_players[player_index].prowl_melee_stacks;
    }
    return 0;
}

int skill_is_heavy_attacking(int player_index) {
    if (player_index < 0 || player_index >= 2) return 0;
    return (g_players[player_index].is_heavy || g_players[player_index].current_action == 4);
}

int skill_is_special_attacking(int player_index) {
    if (player_index < 0 || player_index >= 2) return 0;
    return (g_players[player_index].in_special || g_players[player_index].current_action >= 16);
}

SIM_API int sim_set_special_attacking(int player_index, int in_special) {
    if (player_index < 0 || player_index >= 2) return 0;
    g_players[player_index].in_special = in_special ? 1 : 0;
    if (in_special && g_players[player_index].current_action < 16) {
        g_players[player_index].current_action = 16;
    } else if (!in_special && g_players[player_index].current_action >= 16) {
        g_players[player_index].current_action = 0;
    }
    return 1;
}

SIM_API int sim_set_heavy_attacking(int player_index, int is_heavy) {
    if (player_index < 0 || player_index >= 2) return 0;
    g_players[player_index].is_heavy = is_heavy ? 1 : 0;
    if (is_heavy) {
        g_players[player_index].current_action = 4;
    } else if (g_players[player_index].current_action == 4) {
        g_players[player_index].current_action = 0;
    }
    return 1;
}

// ---------------------------------------------------------------------------
// 模拟器核心控制 API
// ---------------------------------------------------------------------------
SIM_API int sim_init(const char* p0_bot_id, const char* p1_bot_id,
                     float p0_max_hp, float p1_max_hp,
                     float p0_atk, float p1_atk) {
    memset(g_players, 0, sizeof(g_players));
    g_sim_clock_ms = 1000;
    g_floater_count = 0;
    g_log_head = 0;
    g_log_count = 0;
    g_last_announcement[0] = '\0';

    strncpy(g_players[0].bot_id, p0_bot_id ? p0_bot_id : "optimusprime_cin_tf", sizeof(g_players[0].bot_id) - 1);
    strncpy(g_players[1].bot_id, p1_bot_id ? p1_bot_id : "bonecrusher_cin_rotf", sizeof(g_players[1].bot_id) - 1);
    strncpy(g_p0_bot_id, g_players[0].bot_id, sizeof(g_p0_bot_id) - 1);
    strncpy(g_p1_bot_id, g_players[1].bot_id, sizeof(g_p1_bot_id) - 1);

    g_players[0].max_hp = p0_max_hp > 0.0f ? p0_max_hp : 15000.0f;
    g_players[0].hp = g_players[0].max_hp;
    g_players[0].atk = p0_atk > 0.0f ? p0_atk : 1000.0f;
    g_players[0].crit_rate = 0.20f;
    g_players[0].crit_damage_mult = 1.50f;
    g_players[0].block_reduction = 0.50f;

    g_players[1].max_hp = p1_max_hp > 0.0f ? p1_max_hp : 15000.0f;
    g_players[1].hp = g_players[1].max_hp;
    g_players[1].atk = p1_atk > 0.0f ? p1_atk : 1000.0f;
    g_players[1].crit_rate = 0.16f;
    g_players[1].crit_damage_mult = 1.50f;
    g_players[1].block_reduction = 0.50f;

    skill_dispatcher_init(0x100000);
    skill_dispatch_fight_reset();

    skill_log("SIM_INIT: P0=%s (HP=%.0f, ATK=%.0f) vs P1=%s (HP=%.0f, ATK=%.0f)",
              g_players[0].bot_id, g_players[0].max_hp, g_players[0].atk,
              g_players[1].bot_id, g_players[1].max_hp, g_players[1].atk);
    return 1;
}

SIM_API void sim_reset(void) {
    g_players[0].hp = g_players[0].max_hp;
    g_players[0].mana = 0.0f;
    g_players[0].buff_count = 0;
    g_players[0].is_blocking = 0;
    g_players[0].is_heavy = 0;
    g_players[0].in_special = 0;
    g_players[0].current_action = 0;
    g_players[0].prowl_charging = 0;
    g_players[0].prowl_charge_stacks = 0;
    g_players[0].prowl_melee_stacks = 0;

    g_players[1].hp = g_players[1].max_hp;
    g_players[1].mana = 0.0f;
    g_players[1].buff_count = 0;
    g_players[1].is_blocking = 0;
    g_players[1].is_heavy = 0;
    g_players[1].in_special = 0;
    g_players[1].current_action = 0;
    g_players[1].prowl_charging = 0;
    g_players[1].prowl_charge_stacks = 0;
    g_players[1].prowl_melee_stacks = 0;

    g_sim_clock_ms = 1000;
    g_floater_count = 0;
    skill_dispatch_fight_reset();
    skill_log("SIM_RESET: Fight reset for both combatants.");
}

SIM_API int sim_inject_buff(int target_idx, const char* mod_id, float duration_s, int stacks) {
    if (target_idx < 0 || target_idx >= 2 || !mod_id || !mod_id[0]) return 0;
    SimCombatant* c = &g_players[target_idx];

    // 若即将施加具体角色专属的官方眩晕 Buff (例如 windblade_bleed_remote_stun 或 windblade_sp3_stun)，自动清理通用的 "stun" 占位 Buff，避免双重图标
    if (strstr(mod_id, "stun") != NULL && strcmp(mod_id, "stun") != 0) {
        for (int i = 0; i < c->buff_count; i++) {
            if (strcmp(c->buffs[i].mod_id, "stun") == 0) {
                for (int j = i; j < c->buff_count - 1; j++) {
                    c->buffs[j] = c->buffs[j + 1];
                }
                c->buff_count--;
                break;
            }
        }
    }

    // 检查是否已有相同 mod_id
    for (int i = 0; i < c->buff_count; i++) {
        if (strcmp(c->buffs[i].mod_id, mod_id) == 0) {
            c->buffs[i].stacks += stacks;
            if (duration_s > 0.0f) {
                c->buffs[i].duration_s = duration_s;
                c->buffs[i].remaining_ms = (int64_t)(duration_s * 1000.0f);
            }
            skill_log("SIM: Buff '%s' on P%d refreshed/stacked -> x%d", mod_id, target_idx, c->buffs[i].stacks);
            goto notify;
        }
    }

    if (c->buff_count < MAX_BUFFS) {
        SimBuff* b = &c->buffs[c->buff_count++];
        strncpy(b->mod_id, mod_id, sizeof(b->mod_id) - 1);
        b->duration_s = duration_s;
        b->remaining_ms = (duration_s > 0.0f) ? (int64_t)(duration_s * 1000.0f) : -1;
        b->stacks = (stacks > 0) ? stacks : 1;
        b->applied_ms = g_sim_clock_ms;
        b->dot_damage_per_sec = 0.0f;

        // 如果是流血、震击、灼烧等 DOT，设置每秒伤害
        if (strstr(mod_id, "bleed") != NULL) {
            b->dot_damage_per_sec = g_players[1 - target_idx].atk * 0.40f;
            b->next_dot_ms = g_sim_clock_ms + 1000;
        } else if (strstr(mod_id, "shock") != NULL) {
            b->dot_damage_per_sec = g_players[1 - target_idx].atk * 0.50f;
            b->next_dot_ms = g_sim_clock_ms + 500;
        }
        skill_log("SIM: Buff '%s' applied to P%d (dur=%.1fs, stacks=%d)", mod_id, target_idx, duration_s, b->stacks);
    }

notify:
    // 通知技能模块
    {
        SkillBuffAppliedContext app_ctx = {
            .buffs_controller = (void*)c,
            .applicant = (void*)&g_players[1 - target_idx],
            .stat_modifier = NULL,
            .modifier_id = mod_id,
            .target_bot_id = c->bot_id,
            .target_player_index = target_idx,
            .attacker_player_index = 1 - target_idx,
            .override_duration = duration_s,
            .now_ms = g_sim_clock_ms
        };
        skill_dispatch_buff_applied(&app_ctx);
    }
    return 1;
}

SIM_API int sim_remove_buff(int target_idx, const char* mod_id, int count) {
    if (target_idx < 0 || target_idx >= 2 || !mod_id || !mod_id[0]) return 0;
    SimCombatant* c = &g_players[target_idx];
    for (int i = 0; i < c->buff_count; i++) {
        if (strstr(c->buffs[i].mod_id, mod_id) != NULL) {
            if (count > 0 && c->buffs[i].stacks > count) {
                c->buffs[i].stacks -= count;
                skill_log("SIM: Consumed %d stack(s) of '%s' on P%d, left %d", count, mod_id, target_idx, c->buffs[i].stacks);
            } else {
                skill_log("SIM: Removed '%s' from P%d", c->buffs[i].mod_id, target_idx);
                for (int j = i; j < c->buff_count - 1; j++) {
                    c->buffs[j] = c->buffs[j + 1];
                }
                c->buff_count--;
            }
            return 1;
        }
    }
    return 0;
}

SIM_API void sim_set_block(int player_idx, int is_blocking) {
    if (player_idx < 0 || player_idx >= 2) return;
    g_players[player_idx].is_blocking = is_blocking;
    if (is_blocking) {
        g_players[player_idx].block_enter_ms = g_sim_clock_ms;
        skill_dispatch_block_state(player_idx, 1);
        skill_log("SIM: P%d ENTERED block stance", player_idx);
    } else {
        skill_dispatch_block_state(player_idx, 0);
        skill_log("SIM: P%d EXITED block stance", player_idx);
    }
}

SIM_API int sim_dodge(int player_idx, int dodge_type) {
    if (player_idx < 0 || player_idx >= 2) return 0;
    SimCombatant* c = &g_players[player_idx];

    if (dodge_type == 0) { // 0 = 后闪 (Dash Back)
        if (strstr(c->bot_id, "prowl") != NULL) {
            c->prowl_charging = 1;
            c->prowl_charge_start_ms = g_sim_clock_ms;
            c->prowl_charge_stacks = 1;
            c->next_prowl_tick_ms = g_sim_clock_ms + 500;
            sim_remove_buff(player_idx, "prowl_melee_charge", 99);
            sim_inject_buff(player_idx, "prowl_melee_charge", 6.0f, 1);
            skill_overlay("[P%d] 立即投降！(近战充能: 1/10层, 规避率: 54%%)", player_idx);
            push_floater(player_idx, 5, 0.0f, "💨 警车后闪充能 (1/10)");
        } else if (strstr(c->bot_id, "bumblebee") != NULL) {
            sim_inject_buff(player_idx, "bumblebee_dodge_evade_melee", -1.0f, 1);
            push_floater(player_idx, 5, 0.0f, "🛡️ 近战规避 (32%)");
            skill_overlay("[P%d] 小黄蜂后闪！获得常驻近战规避 (32%%)", player_idx);
        } else {
            push_floater(player_idx, 5, 0.0f, "💨 后闪 (Dash Back)");
        }

        skill_dispatch_dodge_enter(player_idx);
        skill_log("SIM: P%d performed Dash Back (后闪)", player_idx);
        return 1;
    } else if (dodge_type == 1) { // 1 = 侧闪 (Sidestep)
        if (strstr(c->bot_id, "bumblebee") != NULL) {
            int stacks = skill_count_buffs(player_idx, "bumblebee_crit_buff");
            if (stacks < 3) {
                sim_inject_buff(player_idx, "bumblebee_crit_buff", 8.0f, 1);
                stacks++;
            }
            c->crit_rate = 0.20f + 0.28f * (float)stacks;
            push_floater(player_idx, 1, 0.0f, "✨ 暴击率+28%");
            skill_overlay("[P%d] 小黄蜂侧闪！暴击增益 (层数:%d, 暴击率:%.0f%%)", player_idx, stacks, c->crit_rate * 100.0f);
        } else {
            push_floater(player_idx, 5, 0.0f, "💨 侧闪 (Sidestep)");
        }

        skill_log("SIM: P%d performed Sidestep (侧闪)", player_idx);
        return 1;
    }
    return 0;
}

SIM_API void sim_tick(uint32_t dt_ms) {
    g_sim_clock_ms += dt_ms;

    // 1. 驱动时钟到所有技能模块 (如电影擎天柱的 1s 净化定时器，威震天的 6s 充能等)
    skill_dispatch_simulation_tick(g_sim_clock_ms);

    // 2. 检查两方 Buff 倒计时与 DOT 扣血
    for (int p = 0; p < 2; p++) {
        SimCombatant* c = &g_players[p];
        for (int i = 0; i < c->buff_count; ) {
            // DOT 跳伤害
            if (c->buffs[i].dot_damage_per_sec > 0.0f && g_sim_clock_ms >= c->buffs[i].next_dot_ms) {
                float tick_dmg = c->buffs[i].dot_damage_per_sec * 0.5f; // 0.5s 一跳
                c->hp -= tick_dmg;
                if (c->hp < 0.0f) c->hp = 0.0f;
                c->buffs[i].next_dot_ms = g_sim_clock_ms + 500;
                push_floater(p, 0, tick_dmg, "DOT伤害");
            }

            // 倒计时递减
            if (c->buffs[i].remaining_ms > 0) {
                c->buffs[i].remaining_ms -= (int64_t)dt_ms;
                if (c->buffs[i].remaining_ms <= 0) {
                    skill_log("SIM: Buff '%s' on P%d EXPIRED", c->buffs[i].mod_id, p);
                    for (int j = i; j < c->buff_count - 1; j++) {
                        c->buffs[j] = c->buffs[j + 1];
                    }
                    c->buff_count--;
                    continue;
                }
            }
            i++;
        }
    }

    // 3. 警车充能递增与小黄蜂暴击 Buff 检查
    for (int p = 0; p < 2; p++) {
        SimCombatant* c = &g_players[p];
        if (c->prowl_charging) {
            if (g_sim_clock_ms >= c->next_prowl_tick_ms) {
                c->prowl_charge_stacks++;
                c->next_prowl_tick_ms = g_sim_clock_ms + 500;
                sim_remove_buff(p, "prowl_melee_charge", 99);
                sim_inject_buff(p, "prowl_melee_charge", 6.0f, c->prowl_charge_stacks);
                push_floater(p, 5, 0.0f, "充能+1");
                if (c->prowl_charge_stacks >= 10) {
                    c->prowl_charging = 0;
                    sim_remove_buff(p, "prowl_melee_charge", 99);
                    sim_inject_buff(p, "prowl_melee_buff", 6.0f, 10);
                    c->prowl_melee_stacks = 10;
                    skill_overlay("[P%d] 警车充能满10层！近战伤害+110%% (持续6秒)", p);
                    push_floater(p, 5, 0.0f, "✨ 满层近战增益 (+110%)");
                }
            }
        }
        if (strstr(c->bot_id, "bumblebee") != NULL) {
            int c_stacks = skill_count_buffs(p, "bumblebee_crit_buff");
            c->crit_rate = 0.20f + 0.28f * (float)c_stacks;
        }
    }
}


SIM_API int sim_attack_start(int attacker_idx, int action_type) {
    if (attacker_idx < 0 || attacker_idx >= 2) return 0;
    SimCombatant* atker = &g_players[attacker_idx];
    atker->current_action = action_type;
    atker->is_heavy = (action_type == 4);
    atker->in_special = (action_type >= 16);
    skill_dispatch_attack_start(attacker_idx, action_type);
    skill_log("SIM_ATTACK_START: P%d started action %d (%s)", attacker_idx, action_type, atker->bot_id);
    return 1;
}

SIM_API int sim_attack(int attacker_idx, int action_type, int hit_index,
                       int is_last_hit, int is_blocked) {
    if (attacker_idx < 0 || attacker_idx >= 2) return 0;
    int target_idx = 1 - attacker_idx;
    SimCombatant* atker = &g_players[attacker_idx];
    SimCombatant* victim = &g_players[target_idx];

    // 若警车正在充能，攻击会打断充能并将其转化为对应层数的橙色近战增益
    if (atker->prowl_charging) {
        int st = atker->prowl_charge_stacks;
        if (st < 1) st = 1;
        if (st > 10) st = 10;
        atker->prowl_charging = 0;
        sim_remove_buff(attacker_idx, "prowl_melee_charge", 99);
        sim_inject_buff(attacker_idx, "prowl_melee_buff", 6.0f, st);
        atker->prowl_melee_stacks = st;
        skill_overlay("[P%d] 警车出手！%d层充能转化为近战增益(+%d%%, 6秒)", attacker_idx, st, st * 11);
        push_floater(attacker_idx, 5, 0.0f, "✨ 近战增益激活");
    }

    int sp_idx = 0;
    if (action_type == 16) sp_idx = 1;
    else if (action_type == 32) sp_idx = 2;
    else if (action_type == 64) sp_idx = 3;

    int is_heavy = (action_type == 4);
    int is_ranged = (action_type == 8);

    atker->current_action = action_type;
    atker->is_heavy = is_heavy;
    atker->in_special = (sp_idx > 0);

    if (is_heavy && !atker->is_heavy) {
        skill_dispatch_attack_start(attacker_idx, 4);
    }

    // 远程攻击闪避/穿透判定 (Evade / Penetration Check)
    int out_evade = 0;
    SkillEvadeContext evade_ctx = {
        .entity_attr = (void*)victim,
        .bot_id = victim->bot_id,
        .player_index = target_idx,
        .is_ranged = (bool)is_ranged,
        .original_evade_result = 0,
        .base_chance = 0.0f,
        .modified_chance = 0.0f,
        .force_guaranteed = false
    };

    int penetrated = 0;
    if (is_ranged && (skill_is_heavy_attacking(target_idx) || skill_has_buff(target_idx, "windblade_heavy_range_immune"))) {
        penetrated = 1;
    }

    if (penetrated || (skill_dispatch_evade_check(&evade_ctx, &out_evade) && out_evade)) {
        skill_log("SIM_ATTACK: P%d attack was EVADED/PENETRATED by P%d (%s)!", attacker_idx, target_idx, victim->bot_id);
        if (strstr(victim->bot_id, "windblade") != NULL && is_ranged) {
            push_floater(target_idx, 4, 0.0f, "💨 穿透规避");
        } else {
            push_floater(target_idx, 4, 0.0f, "规避");
        }
        if (is_last_hit) {
            atker->current_action = 0;
            atker->is_heavy = 0;
            atker->in_special = 0;
        }
        return 0;
    }

    // 基础伤害计算
    float base_dmg = atker->atk;
    if (action_type == 1) base_dmg *= 0.25f;       // 轻击
    else if (action_type == 2) base_dmg *= 0.40f;  // 中击
    else if (action_type == 4) base_dmg *= 1.00f;  // 重击
    else if (action_type == 8) base_dmg *= 0.35f;  // 远程射击 (Ranged)
    else if (sp_idx == 1) base_dmg *= 1.80f;       // SP1
    else if (sp_idx == 2) base_dmg *= 2.80f;       // SP2
    else if (sp_idx == 3) base_dmg *= 4.50f;       // SP3

    // 暴击率构成计算 (Crit Rate Breakdown & Roll Dice)
    float base_crit = atker->crit_rate;
    float blade_crit = 0.0f;
    float resolution_crit = 0.0f;
    bool is_windblade = (strstr(atker->bot_id, "windblade") != NULL);
    bool is_thundercracker = (strstr(atker->bot_id, "thundercracker") != NULL);

    if (is_windblade) {
        // [2907] 剑刃攻击暴击率 +25% (近战或 SP1/SP2，远程射击不享受)
        bool is_blade_attack = (!is_ranged) || (sp_idx == 1) || (sp_idx == 2);
        if (is_blade_attack) {
            blade_crit = 0.25f;
        }
        // [2908] 决心觉醒机制: 按敌方已损生命值百分比最高 +25%
        float opp_max_hp = (victim->max_hp > 0.0f) ? victim->max_hp : 1.0f;
        float opp_lost_ratio = 1.0f - (victim->hp / opp_max_hp);
        if (opp_lost_ratio < 0.0f) opp_lost_ratio = 0.0f;
        if (opp_lost_ratio > 1.0f) opp_lost_ratio = 1.0f;
        resolution_crit = 0.25f * opp_lost_ratio;
    }

    float total_crit_rate = base_crit + blade_crit + resolution_crit;
    if (is_thundercracker && !is_ranged && sp_idx == 0) {
        total_crit_rate = 0.0f; // 惊天雷近战 0 暴击
    }
    if (total_crit_rate < 0.0f) total_crit_rate = 0.0f;
    if (total_crit_rate > 1.0f) total_crit_rate = 1.0f;

    // 暴击检定 (Roll Dice)
    float roll = skill_random_float();
    float roll_pct = roll * 100.0f;
    float crit_rate_pct = total_crit_rate * 100.0f;
    int is_crit = (roll < total_crit_rate);

    if (is_crit) {
        base_dmg *= atker->crit_damage_mult;
        if (blade_crit > 0.0f || resolution_crit > 0.0f) {
            skill_log("ROLL_DICE_PASS: [%s] 暴击检定 PASS! (Roll: %.1f%% < %.1f%% [基础%.1f%% + 剑刃%.1f%% + 决心%.1f%%])",
                      atker->bot_id, roll_pct, crit_rate_pct,
                      base_crit * 100.0f, blade_crit * 100.0f, resolution_crit * 100.0f);
        } else {
            skill_log("ROLL_DICE_PASS: [%s] 暴击检定 PASS! (Roll: %.1f%% < %.1f%% [基础%.1f%%])",
                      atker->bot_id, roll_pct, crit_rate_pct, base_crit * 100.0f);
        }
    } else {
        if (blade_crit > 0.0f || resolution_crit > 0.0f) {
            skill_log("ROLL_DICE_FAIL: [%s] 暴击检定 FAIL (Roll: %.1f%% >= %.1f%% [基础%.1f%% + 剑刃%.1f%% + 决心%.1f%%])",
                      atker->bot_id, roll_pct, crit_rate_pct,
                      base_crit * 100.0f, blade_crit * 100.0f, resolution_crit * 100.0f);
        } else {
            skill_log("ROLL_DICE_FAIL: [%s] 暴击检定 FAIL (Roll: %.1f%% >= %.1f%% [基础%.1f%%])",
                      atker->bot_id, roll_pct, crit_rate_pct, base_crit * 100.0f);
        }
    }

    // 命中上下文构建并派发给解耦技能系统 (skill_optimus_mv, skill_megatron, etc.)
    SkillHitContext hit_ctx = {
        .attacker_entity = (void*)atker,
        .target_entity = (void*)victim,
        .attacker_bot_id = atker->bot_id,
        .target_bot_id = victim->bot_id,
        .attacker_player_index = attacker_idx,
        .target_player_index = target_idx,
        .special_index = sp_idx,
        .hit_index = hit_index,
        .is_last_hit = (bool)is_last_hit,
        .is_ranged = (bool)is_ranged,
        .is_heavy = (bool)is_heavy,
        .is_crit = (bool)is_crit,
        .is_blocked = (bool)is_blocked,
        .base_damage = base_dmg,
        .modified_damage = base_dmg,
        .hit_flags = 0x2180 | (is_last_hit ? 0x80 : 0) | (is_crit ? 32 : 0) | (is_blocked ? 4 : 1)
    };

    skill_dispatch_hit_connected(&hit_ctx);

    float final_dmg = hit_ctx.modified_damage;
    if (is_blocked && !is_heavy) {
        final_dmg *= (1.0f - victim->block_reduction);
    }

    victim->hp -= final_dmg;
    if (victim->hp < 0.0f) victim->hp = 0.0f;

    // 攻击方回气结算 (对齐 hook_197 官方原版基准: 1格=300点)
    if (sp_idx == 0) {
        float atk_gain = 0.05f; // 轻击 15点 = 0.05格
        if (action_type == 1) atk_gain = 0.05f;        // 轻击 15点 = 0.05格
        else if (action_type == 2) atk_gain = 0.10f;   // 中击 30点 = 0.10格
        else if (action_type == 4) atk_gain = 0.20f;   // 重击 60点 = 0.20格
        else if (action_type == 8) atk_gain = 0.05f;   // 远程 15点 = 0.05格

        if (is_blocked) {
            atk_gain *= 0.5f; // 攻击被格挡时获取减半
        }
        if (skill_has_buff(attacker_idx, "power_lock")) {
            atk_gain = 0.0f; // 能量锁定禁止回气
        }
        if (skill_has_buff(attacker_idx, "power")) {
            atk_gain *= 1.5f; // 能量获取增益
        }
        atker->mana += atk_gain;
        if (atker->mana > 3.0f) atker->mana = 3.0f;
    } else {
        // 扣除释放 SP 消耗的能量
        atker->mana -= (float)sp_idx;
        if (atker->mana < 0.0f) atker->mana = 0.0f;
    }

    // 受击方防守加气结算 (对齐 hook_198 官方原版基准: 基础比进攻方多 20%，即 1.2 倍速)
    float def_gain = 0.06f;
    if (sp_idx == 1) {
        def_gain = 0.20f; // SP1 受击 60点 = 0.20格
    } else if (sp_idx == 2) {
        def_gain = 0.40f; // SP2 受击 120点 = 0.40格
    } else if (sp_idx == 3) {
        def_gain = 0.50f; // SP3 受击 150点 = 0.50格
    } else {
        if (action_type == 1) def_gain = 0.06f;        // 轻击受击 18点 = 0.06格 (15 * 1.2)
        else if (action_type == 2) def_gain = 0.12f;   // 中击受击 36点 = 0.12格 (30 * 1.2)
        else if (action_type == 4) def_gain = 0.24f;   // 重击受击 72点 = 0.24格 (60 * 1.2)
        else if (action_type == 8) def_gain = 0.06f;   // 远程受击 18点 = 0.06格 (15 * 1.2)
    }
    // 受击方若被格挡不扣减回气
    if (skill_has_buff(target_idx, "power_lock")) {
        def_gain = 0.0f;
    }
    if (skill_has_buff(target_idx, "power")) {
        def_gain *= 1.5f;
    }
    victim->mana += def_gain;
    if (victim->mana > 3.0f) victim->mana = 3.0f;

    // 推送战斗浮字
    bool effective_crit = hit_ctx.is_crit;
    push_floater(target_idx, effective_crit ? 1 : 0, final_dmg, effective_crit ? "暴击" : (is_blocked ? "格挡" : "命中"));

    skill_log("SIM_ATTACK: P%d [act=%d sp=%d heavy=%d last=%d] -> P%d: dmg=%.1f (crit=%d, crit_rate=%.1f%%, blk=%d, hp_left=%.0f)",
              attacker_idx, action_type, sp_idx, is_heavy, is_last_hit,
              target_idx, final_dmg, effective_crit, crit_rate_pct, is_blocked, victim->hp);

    if (is_last_hit) {
        atker->current_action = 0;
        atker->is_heavy = 0;
        atker->in_special = 0;
    }

    return (int)final_dmg;
}

// ---------------------------------------------------------------------------
// 状态导出为 JSON
// ---------------------------------------------------------------------------
SIM_API int sim_get_state_json(char* out_buf, int max_len) {
    if (!out_buf || max_len <= 0) return 0;

    int offset = 0;
    offset += snprintf(out_buf + offset, max_len - offset,
                       "{\"clock_ms\":%llu,\"announcement\":\"%s\",\"p0\":{\"bot_id\":\"%s\",\"hp\":%.1f,\"max_hp\":%.1f,\"mana\":%.2f,\"is_blocking\":%d,\"buffs\":[",
                       (unsigned long long)g_sim_clock_ms, g_last_announcement,
                       g_players[0].bot_id, g_players[0].hp, g_players[0].max_hp, g_players[0].mana, g_players[0].is_blocking);

    for (int i = 0; i < g_players[0].buff_count && offset < max_len - 128; i++) {
        SimBuff* b = &g_players[0].buffs[i];
        offset += snprintf(out_buf + offset, max_len - offset,
                           "%s{\"id\":\"%s\",\"rem_ms\":%lld,\"stacks\":%d}",
                           (i > 0 ? "," : ""), b->mod_id, (long long)b->remaining_ms, b->stacks);
    }

    offset += snprintf(out_buf + offset, max_len - offset,
                       "]},\"p1\":{\"bot_id\":\"%s\",\"hp\":%.1f,\"max_hp\":%.1f,\"mana\":%.2f,\"is_blocking\":%d,\"buffs\":[",
                       g_players[1].bot_id, g_players[1].hp, g_players[1].max_hp, g_players[1].mana, g_players[1].is_blocking);

    for (int i = 0; i < g_players[1].buff_count && offset < max_len - 128; i++) {
        SimBuff* b = &g_players[1].buffs[i];
        offset += snprintf(out_buf + offset, max_len - offset,
                           "%s{\"id\":\"%s\",\"rem_ms\":%lld,\"stacks\":%d}",
                           (i > 0 ? "," : ""), b->mod_id, (long long)b->remaining_ms, b->stacks);
    }

    offset += snprintf(out_buf + offset, max_len - offset, "]}}");
    return offset;
}

SIM_API int sim_pop_logs(char* out_buf, int max_len) {
    if (!out_buf || max_len <= 0) return 0;
    out_buf[0] = '[';
    int offset = 1;

    for (int i = 0; i < g_log_count && offset < max_len - 100; i++) {
        int idx = (g_log_head + i) % MAX_LOG_LINES;
        offset += snprintf(out_buf + offset, max_len - offset,
                           "%s\"%s\"", (i > 0 ? "," : ""), g_logs[idx]);
    }
    offset += snprintf(out_buf + offset, max_len - offset, "]");
    g_log_count = 0; // 清空已读取日志
    return offset;
}

SIM_API int sim_pop_floaters(char* out_buf, int max_len) {
    if (!out_buf || max_len <= 0) return 0;
    out_buf[0] = '[';
    int offset = 1;

    for (int i = 0; i < g_floater_count && offset < max_len - 100; i++) {
        SimFloater* f = &g_floaters[i];
        offset += snprintf(out_buf + offset, max_len - offset,
                           "%s{\"pidx\":%d,\"type\":%d,\"val\":%.1f,\"text\":\"%s\"}",
                           (i > 0 ? "," : ""), f->player_index, f->type, f->value, f->text);
    }
    offset += snprintf(out_buf + offset, max_len - offset, "]");
    g_floater_count = 0; // 清空浮字
    return offset;
}
