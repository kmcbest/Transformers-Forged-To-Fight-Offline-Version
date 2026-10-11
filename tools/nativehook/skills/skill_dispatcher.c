#include "skill_dispatcher.h"
#include <string.h>
#include <stdio.h>
#include <android/log.h>

#define DISP_LOG(...) __android_log_print(ANDROID_LOG_INFO, "SKILL_DISP", __VA_ARGS__)

// 注册的角色模块 extern 声明
extern BotSkillModule g_module_arcee;
extern BotSkillModule g_module_rhinox;
extern BotSkillModule g_module_wheeljack;
extern BotSkillModule g_module_prowl;
extern BotSkillModule g_module_optimus_mv;
extern BotSkillModule g_module_bumblebee_dotm;

static const BotSkillModule* s_registry[] = {
    &g_module_arcee,
    &g_module_rhinox,
    &g_module_wheeljack,
    &g_module_prowl,
    &g_module_optimus_mv,
    &g_module_bumblebee_dotm,
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
