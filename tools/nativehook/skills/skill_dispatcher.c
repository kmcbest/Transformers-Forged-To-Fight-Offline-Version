#include "skill_dispatcher.h"
#include "skill_env.h"
#include <string.h>
#include <stdio.h>
#ifdef __ANDROID__
#include <android/log.h>
#define DISP_LOG(...) __android_log_print(ANDROID_LOG_INFO, "SKILL_DISP", __VA_ARGS__)
#else
#define DISP_LOG(...)
#endif

// 注册的角色模块 extern 声明
extern BotSkillModule g_module_arcee;
extern BotSkillModule g_module_rhinox;
extern BotSkillModule g_module_wheeljack;
extern BotSkillModule g_module_prowl;
extern BotSkillModule g_module_optimus_mv;
extern BotSkillModule g_module_bumblebee_dotm;
extern BotSkillModule g_module_scorponok;
extern BotSkillModule g_module_hotrod;
extern BotSkillModule g_module_megatron;
extern BotSkillModule g_module_grimlock;
extern BotSkillModule g_module_thundercracker;
extern BotSkillModule g_module_cyclonus;
extern BotSkillModule g_module_nemesis;
extern BotSkillModule g_module_jetfire;
extern BotSkillModule g_module_tantrum;
extern BotSkillModule g_module_bonecrusher;
extern BotSkillModule g_module_windblade;
extern BotSkillModule g_module_kickback;
extern BotSkillModule g_module_slipstream;
extern BotSkillModule g_module_cheetor;
extern BotSkillModule g_module_sideswipe;
extern BotSkillModule g_module_necrotronus;

static const BotSkillModule* s_registry[] = {
    &g_module_arcee,
    &g_module_rhinox,
    &g_module_wheeljack,
    &g_module_prowl,
    &g_module_optimus_mv,
    &g_module_bumblebee_dotm,
    &g_module_scorponok,
    &g_module_hotrod,
    &g_module_megatron,
    &g_module_grimlock,
    &g_module_thundercracker,
    &g_module_cyclonus,
    &g_module_nemesis,
    &g_module_jetfire,
    &g_module_tantrum,
    &g_module_bonecrusher,
    &g_module_windblade,
    &g_module_kickback,
    &g_module_slipstream,
    &g_module_cheetor,
    &g_module_sideswipe,
    &g_module_necrotronus,
    NULL
};

static uintptr_t s_il2cpp_base = 0;

void skill_dispatcher_init(uintptr_t base_addr) {
    s_il2cpp_base = base_addr;
    DISP_LOG("skill_dispatcher_init with base=0x%lx", (unsigned long)base_addr);
}

void skill_dispatch_fight_reset(void) {
    DISP_LOG("skill_dispatch_fight_reset for all modules");
    for (int i = 0; s_registry[i] != NULL; i++) {
        if (s_registry[i]->on_fight_reset) {
            s_registry[i]->on_fight_reset(0);
            s_registry[i]->on_fight_reset(1);
        }
    }
}

static const BotSkillModule* find_module_by_bot(const char* bot_id) {
    if (!bot_id || !bot_id[0]) return NULL;
    for (int i = 0; s_registry[i] != NULL; i++) {
        if (s_registry[i]->bot_prefix && strstr(bot_id, s_registry[i]->bot_prefix) != NULL) {
            return s_registry[i];
        }
    }
    return NULL;
}

static const BotSkillModule* find_module_by_modifier(const char* mod_id) {
    if (!mod_id || !mod_id[0]) return NULL;
    for (int i = 0; s_registry[i] != NULL; i++) {
        if (s_registry[i]->bot_prefix && strstr(mod_id, s_registry[i]->bot_prefix) != NULL) {
            return s_registry[i];
        }
    }
    return NULL;
}

void skill_dispatch_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    const BotSkillModule* att_mod = find_module_by_bot(ctx->attacker_bot_id);
    if (att_mod && att_mod->on_hit_connected) {
        att_mod->on_hit_connected(ctx);
    }
    const BotSkillModule* tgt_mod = find_module_by_bot(ctx->target_bot_id);
    if (tgt_mod && tgt_mod != att_mod && tgt_mod->on_hit_connected) {
        tgt_mod->on_hit_connected(ctx);
    }
}

int skill_dispatch_buff_gate(SkillBuffGateContext* ctx, int* out_allowed) {
    if (!ctx || !out_allowed) return 0;
    // 优先按 modifier_id 匹配，次选按 target_bot_id
    const BotSkillModule* mod = find_module_by_modifier(ctx->modifier_id);
    if (!mod) {
        mod = find_module_by_bot(ctx->target_bot_id);
    }
    if (mod && mod->on_buff_gated) {
        int handled = mod->on_buff_gated(ctx);
        if (handled) {
            *out_allowed = ctx->allow_application ? 1 : 0;
            return 1;
        }
    }
    return 0;
}

void skill_dispatch_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx) return;
    const BotSkillModule* mod = find_module_by_modifier(ctx->modifier_id);
    if (mod && mod->on_buff_applied) {
        mod->on_buff_applied(ctx);
    }
    const BotSkillModule* tgt_mod = find_module_by_bot(ctx->target_bot_id);
    if (tgt_mod && tgt_mod != mod && tgt_mod->on_buff_applied) {
        tgt_mod->on_buff_applied(ctx);
    }
}


int skill_dispatch_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    const BotSkillModule* mod = find_module_by_bot(ctx->bot_id);
    if (mod && mod->on_evade_check) {
        return mod->on_evade_check(ctx, out_evade);
    }
    return 0;
}

int skill_dispatch_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !out_res) return 0;
    const BotSkillModule* mod = find_module_by_modifier(ctx->modifier_id);
    if (!mod) {
        mod = find_module_by_bot(ctx->owner_bot_id);
    }
    if (mod && mod->on_test_roll) {
        return mod->on_test_roll(ctx, out_res);
    }
    return 0;
}

extern char g_p0_bot_id[80];
extern char g_p1_bot_id[80];

float skill_dispatch_power_gain_rate_mod(int player_index) {
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_power_gain_rate) {
        float mult = 1.0f;
        if (mod->on_power_gain_rate(player_index, &mult)) {
            return mult;
        }
    }
    return 1.0f;
}

int skill_dispatch_reflect_proj(int player_index, float* out_reflect_mod) {
    if (player_index < 0 || player_index >= 2 || !out_reflect_mod) return 0;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_reflect_proj) {
        return mod->on_reflect_proj(player_index, out_reflect_mod);
    }
    return 0;
}

void skill_dispatch_simulation_tick(uint64_t now_ms) {
    for (int i = 0; s_registry[i] != NULL; i++) {
        if (s_registry[i]->on_simulation_tick) {
            s_registry[i]->on_simulation_tick(now_ms);
        }
    }
}

void skill_dispatch_block_state(int player_index, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_block_state) {
        mod->on_block_state(player_index, entered);
    }
}

void skill_dispatch_dodge_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_dodge_enter) {
        mod->on_dodge_enter(player_index);
    }
}

void skill_dispatch_hitreact_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_hitreact_enter) {
        mod->on_hitreact_enter(player_index);
    }
}

void skill_dispatch_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;

    // 释放S技：打断充能与逆火反噬检测
    if (action_type >= 16 || action_type == 0x200) {
        if (skill_prowl_is_charging(player_index)) {
            skill_prowl_finish_charge(player_index, "special attack start");
        }

        // 规则 3: 逆火反噬机制 (Backfire: 有逆火减益的角色，放SP技会受到逆火伤害)
        if (skill_has_buff(player_index, "slipstream_backfire")) {
            // 滑流逆火：反噬承受滑流 80% 攻击力伤害
            float dmg = 2306.0f * 0.80f;
            skill_deal_damage(player_index, dmg);
            skill_consume_buff(player_index, "slipstream_backfire", 99);
            skill_overlay("[%s] 遭受能量逆火反噬！承受 %.0f 点反噬伤害！", player_index == 0 ? "我方" : "敌方", dmg);
            skill_log("BACKFIRE: P%d cast SP under Slipstream Backfire! Suffered %.1f damage", player_index, dmg);
        }
        if (skill_has_buff(player_index, "scorponok_venom_backfire")) {
            // 巨蝎逆火：反噬承受巨蝎 153% 攻击力伤害
            float dmg = 3000.0f * 1.53f;
            skill_deal_damage(player_index, dmg);
            skill_consume_buff(player_index, "scorponok_venom_backfire", 99);
            skill_overlay("[%s] 遭受巨蝎毒液逆火反噬！承受 %.0f 点反噬伤害！", player_index == 0 ? "我方" : "敌方", dmg);
            skill_log("BACKFIRE: P%d cast SP under Scorponok Backfire! Suffered %.1f damage", player_index, dmg);
        }
    }

    const BotSkillModule* mod0 = find_module_by_bot(g_p0_bot_id);
    if (mod0 && mod0->on_attack_start) {
        mod0->on_attack_start(player_index, action_type);
    }
    const BotSkillModule* mod1 = find_module_by_bot(g_p1_bot_id);
    if (mod1 && mod1 != mod0 && mod1->on_attack_start) {
        mod1->on_attack_start(player_index, action_type);
    }
}
