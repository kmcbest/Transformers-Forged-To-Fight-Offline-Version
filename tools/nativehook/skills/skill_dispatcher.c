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
extern BotSkillModule g_module_megatronus;
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
extern BotSkillModule g_module_sideswipe_cin;
extern BotSkillModule g_module_necrotronus;
extern BotSkillModule g_module_motormaster;
extern BotSkillModule g_module_elita;
extern BotSkillModule g_module_dirge;
extern BotSkillModule g_module_dinobot;
extern BotSkillModule g_module_drift;
extern BotSkillModule g_module_bludgeon;
extern BotSkillModule g_module_blitzwing;
extern BotSkillModule g_module_blackout;
extern BotSkillModule g_module_optimus_g1;
extern BotSkillModule g_module_ultramagnus;
extern BotSkillModule g_module_ironhide;
extern BotSkillModule g_module_mixmaster;
extern BotSkillModule g_module_waspinator;
extern BotSkillModule g_module_ramjet;
extern BotSkillModule g_module_megatron_rotf;
extern BotSkillModule g_module_acidstorm;
extern BotSkillModule g_module_bitstream;
extern BotSkillModule g_module_hotlink;
extern BotSkillModule g_module_ionstorm;
extern BotSkillModule g_module_novastorm;
extern BotSkillModule g_module_skywarp;
extern BotSkillModule g_module_sunstorm;
extern BotSkillModule g_module_starscream;
extern BotSkillModule g_module_bumblebee_g1;
extern BotSkillModule g_module_chromia;
extern BotSkillModule g_module_cliffjumper;
extern BotSkillModule g_module_optimus_sg;
extern BotSkillModule g_module_ratchet;
extern BotSkillModule g_module_rodimus;
extern BotSkillModule g_module_sunstreaker;
extern BotSkillModule g_module_barricade;
extern BotSkillModule g_module_blaster;
extern BotSkillModule g_module_breakdown;
extern BotSkillModule g_module_dragstrip;
extern BotSkillModule g_module_galvatron;
extern BotSkillModule g_module_grindor;
extern BotSkillModule g_module_shockwave;
extern BotSkillModule g_module_soundwave;
extern BotSkillModule g_module_swindle;

static const BotSkillModule* s_registry[] = {
    &g_module_arcee,
    &g_module_rhinox,
    &g_module_wheeljack,
    &g_module_prowl,
    &g_module_optimus_mv,
    &g_module_optimus_g1,
    &g_module_ultramagnus,
    &g_module_ironhide,
    &g_module_mixmaster,
    &g_module_waspinator,
    &g_module_ramjet,
    &g_module_megatron_rotf,
    &g_module_acidstorm,
    &g_module_bitstream,
    &g_module_hotlink,
    &g_module_ionstorm,
    &g_module_novastorm,
    &g_module_skywarp,
    &g_module_sunstorm,
    &g_module_starscream,
    &g_module_bumblebee_g1,
    &g_module_chromia,
    &g_module_cliffjumper,
    &g_module_optimus_sg,
    &g_module_ratchet,
    &g_module_rodimus,
    &g_module_sunstreaker,
    &g_module_barricade,
    &g_module_blaster,
    &g_module_breakdown,
    &g_module_dragstrip,
    &g_module_galvatron,
    &g_module_grindor,
    &g_module_shockwave,
    &g_module_soundwave,
    &g_module_swindle,
    &g_module_bumblebee_dotm,
    &g_module_scorponok,
    &g_module_hotrod,
    &g_module_megatronus,
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
    &g_module_sideswipe_cin,
    &g_module_necrotronus,
    &g_module_motormaster,
    &g_module_elita,
    &g_module_dirge,
    &g_module_dinobot,
    &g_module_drift,
    &g_module_bludgeon,
    &g_module_blitzwing,
    &g_module_blackout,
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
    const BotSkillModule* best = NULL;
    size_t best_len = 0;
    for (int i = 0; s_registry[i] != NULL; i++) {
        if (s_registry[i]->bot_prefix && strstr(bot_id, s_registry[i]->bot_prefix) != NULL) {
            size_t len = strlen(s_registry[i]->bot_prefix);
            if (len > best_len) {
                best_len = len;
                best = s_registry[i];
            }
        }
    }
    return best;
}

static const BotSkillModule* find_module_by_modifier(const char* mod_id) {
    if (!mod_id || !mod_id[0]) return NULL;
    const BotSkillModule* best = NULL;
    size_t best_len = 0;
    for (int i = 0; s_registry[i] != NULL; i++) {
        if (s_registry[i]->bot_prefix && strstr(mod_id, s_registry[i]->bot_prefix) != NULL) {
            size_t len = strlen(s_registry[i]->bot_prefix);
            if (len > best_len) {
                best_len = len;
                best = s_registry[i];
            }
        }
    }
    return best;
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

    // 通用被动护甲减伤托底 (对未定义独立模块的角色生效，如 G1 擎天柱、原始擎天柱、铁皮等)：
    if (!tgt_mod && ctx->target_player_index >= 0 && ctx->target_player_index < 2) {
        int tp = ctx->target_player_index;
        if (skill_has_buff(tp, "block_armor") || skill_has_buff(tp, "armor_up") || skill_has_buff(tp, "buff_armor")) {
            ctx->modified_damage *= (1.0f - 0.165f); // 降低 16.5% 伤害
        }
    }

    // 通用被动近战加攻托底 (对未定义独立模块的角色生效)：
    if (!att_mod && ctx->attacker_player_index >= 0 && ctx->attacker_player_index < 2 && !ctx->is_ranged) {
        int ap = ctx->attacker_player_index;
        if (skill_has_buff(ap, "melee_buff")) {
            ctx->modified_damage *= 1.50f; // 标准近战增益 +50%
        } else if (skill_has_buff(ap, "atk_buff") || skill_has_buff(ap, "attack_buff") || skill_has_buff(ap, "attack_boost")) {
            ctx->modified_damage *= 1.20f; // 标准攻击力增益 +20%
        }
    }
}

int skill_dispatch_buff_gate(SkillBuffGateContext* ctx, int* out_allowed) {
    if (!ctx || !out_allowed) return 0;

    const BotSkillModule* mod_owner = find_module_by_modifier(ctx->modifier_id);
    const BotSkillModule* mod_target = ctx->target_bot_id ? find_module_by_bot(ctx->target_bot_id) : NULL;
    if (!mod_target && ctx->target_player_index >= 0 && ctx->target_player_index < 2) {
        mod_target = find_module_by_bot(skill_get_bot_id(ctx->target_player_index));
    }
    const BotSkillModule* mod_attacker = (ctx->attacker_player_index >= 0 && ctx->attacker_player_index < 2) ?
                                         find_module_by_bot(skill_get_bot_id(ctx->attacker_player_index)) : NULL;

    // 1. 优先由 Modifier 属主模块进行门禁判定 (如阿尔茜踢击门禁、千斤顶终段门禁)
    if (mod_owner && mod_owner->on_buff_gated) {
        if (mod_owner->on_buff_gated(ctx)) {
            *out_allowed = ctx->allow_application ? 1 : 0;
            return 1;
        }
    }

    // 2. 目标受体模块判定 (如闪电被施加减益时通过战机夹钳反制拦截、黄豹被施加燃烧/流失时免疫)
    if (mod_target && mod_target != mod_owner && mod_target->on_buff_gated) {
        if (mod_target->on_buff_gated(ctx)) {
            *out_allowed = ctx->allow_application ? 1 : 0;
            return 1;
        }
    }

    // 3. 施加方/对手模块判定 (如对手尝试获得增益时通过坦克夹钳拦截)
    if (mod_attacker && mod_attacker != mod_owner && mod_attacker != mod_target && mod_attacker->on_buff_gated) {
        if (mod_attacker->on_buff_gated(ctx)) {
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
    if (ctx->target_player_index >= 0 && ctx->target_player_index < 2) {
        const char* opp_id = skill_get_bot_id(1 - ctx->target_player_index);
        const BotSkillModule* opp_mod = find_module_by_bot(opp_id);
        if (opp_mod && opp_mod->on_opponent_buff_applied) {
            opp_mod->on_opponent_buff_applied(ctx);
        }
    }
}


int skill_dispatch_evade_check(SkillEvadeContext* ctx, int* out_evade) {
    if (!ctx || !out_evade) return 0;
    int attacker_idx = (ctx->player_index == 0) ? 1 : 0;
    const BotSkillModule* att_mod = find_module_by_bot(skill_get_bot_id(attacker_idx));
    if (att_mod && att_mod->on_anti_evade_check) {
        if (att_mod->on_anti_evade_check(attacker_idx, ctx)) {
            *out_evade = 0;
            return 1;
        }
    }
    const BotSkillModule* mod = find_module_by_bot(ctx->bot_id);
    if (mod && mod->on_evade_check) {
        return mod->on_evade_check(ctx, out_evade);
    }
    return 0;
}

int skill_dispatch_test_roll(SkillTestRollContext* ctx, int* out_res) {
    if (!ctx || !out_res) return 0;
    const BotSkillModule* mod = find_module_by_bot(ctx->owner_bot_id);
    if (!mod) {
        mod = find_module_by_modifier(ctx->modifier_id);
    }
    if (mod && mod->on_test_roll) {
        return mod->on_test_roll(ctx, out_res);
    }
    return 0;
}

void skill_dispatch_test_roll_post(SkillTestRollContext* ctx, int roll_result) {
    if (!ctx) return;
    const BotSkillModule* mod = find_module_by_bot(ctx->owner_bot_id);
    if (!mod) {
        mod = find_module_by_modifier(ctx->modifier_id);
    }
    if (mod && mod->on_test_roll_post) {
        mod->on_test_roll_post(ctx, roll_result);
    }
}

void skill_dispatch_hit_begin(void) {
    for (int i = 0; s_registry[i] != NULL; i++) {
        if (s_registry[i]->on_hit_begin) {
            s_registry[i]->on_hit_begin();
        }
    }
}

void skill_dispatch_evade_triggered(int evader_player_index, int is_ranged) {
    if (evader_player_index < 0 || evader_player_index >= 2) return;
    int opp_idx = 1 - evader_player_index;
    const char* opp_bot = skill_get_bot_id(opp_idx);
    const BotSkillModule* opp_mod = find_module_by_bot(opp_bot);
    if (opp_mod && opp_mod->on_evade_triggered) {
        opp_mod->on_evade_triggered(evader_player_index, is_ranged);
    }
    const char* self_bot = skill_get_bot_id(evader_player_index);
    const BotSkillModule* self_mod = find_module_by_bot(self_bot);
    if (self_mod && self_mod != opp_mod && self_mod->on_evade_triggered) {
        self_mod->on_evade_triggered(evader_player_index, is_ranged);
    }
}

const char* skill_dispatch_get_display_name(const char* bot_id) {
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->display_name_zh && mod->display_name_zh[0]) {
        return mod->display_name_zh;
    }
    return (bot_id && bot_id[0]) ? bot_id : "英雄";
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

float skill_dispatch_projectile_speed(int player_index, int is_heavy) {
    if (player_index < 0 || player_index >= 2) return 1.0f;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_projectile_speed) {
        float mult = 1.0f;
        if (mod->on_projectile_speed(player_index, is_heavy, &mult)) {
            return mult;
        }
    }
    return 1.0f;
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
    const char* opp_bot_id = (player_index == 0) ? g_p1_bot_id : g_p0_bot_id;
    const BotSkillModule* opp_mod = find_module_by_bot(opp_bot_id);
    if (opp_mod && opp_mod->on_opponent_block_state) {
        opp_mod->on_opponent_block_state(player_index, entered);
    }
}

void skill_dispatch_dodge_enter(int player_index) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_dodge_enter) {
        mod->on_dodge_enter(player_index);
    }
    const char* opp_bot_id = (player_index == 0) ? g_p1_bot_id : g_p0_bot_id;
    const BotSkillModule* opp_mod = find_module_by_bot(opp_bot_id);
    if (opp_mod && opp_mod->on_opponent_dodge_enter) {
        opp_mod->on_opponent_dodge_enter(player_index);
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

    // 释放S技：打断充能与逆火反噬检测 (仅限特殊技 16, 32, 64, 0x200，绝不包含重击 4 / 0x100)
    int is_special = (action_type == 16 || action_type == 32 || action_type == 64 || action_type == 0x200);
    if (is_special && action_type != 4 && action_type != 0x100) {
        if (skill_prowl_is_charging(player_index)) {
            skill_prowl_finish_charge(player_index, "special attack start");
        }

        // 规则 3: 逆火反噬机制 (Backfire: 有逆火减益的角色，放SP技会受到逆火伤害)
        if (skill_has_buff(player_index, "slipstream_backfire")) {
            // 滑流逆火：反噬承受施加者 100% 攻击力伤害
            float atk = skill_get_attack(1 - player_index);
            if (atk <= 0.0f) atk = 2306.0f;
            float dmg = atk * 1.0f;
            skill_deal_damage(player_index, dmg);
            skill_consume_buff(player_index, "slipstream_backfire", 99);
            skill_overlay("[%s] 遭受能量逆火反噬！承受 %.0f 点反噬伤害！", player_index == 0 ? "我方" : "敌方", dmg);
            skill_log("BACKFIRE: P%d cast SP under Slipstream Backfire! Suffered %.1f damage (atk=%.1f)", player_index, dmg, atk);
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

void skill_dispatch_attack_ended(SkillAttackEndContext* ctx) {
    if (!ctx) return;

    // 统一“落空”标准判定：
    // 1. 绝非命中 (Hit)、非格挡 (Blocked)、非对波抵消 (Cancelled)、非被反射 (Reflected)
    // 2. 带有 Missed / Evaded / Avoided / Invulnerable 之一
    uint32_t f = ctx->flags;
    bool excluded = (f & (HIT_FLAG_HIT | HIT_FLAG_BLOCKED | HIT_FLAG_CANCELLED | HIT_FLAG_REFLECTED)) != 0;
    bool miss_bit = (f & (HIT_FLAG_MISSED | HIT_FLAG_EVADED | HIT_FLAG_AVOIDED | HIT_FLAG_INVULNERABLE)) != 0;
    ctx->is_missed = (!excluded && miss_bit);
    ctx->is_last_hit = ((f & HIT_FLAG_LAST_HIT) != 0);

    const BotSkillModule* att_mod = find_module_by_bot(ctx->attacker_bot_id);
    if (att_mod && att_mod->on_attack_ended) {
        att_mod->on_attack_ended(ctx);
    }
    const BotSkillModule* tgt_mod = find_module_by_bot(ctx->target_bot_id);
    if (tgt_mod && tgt_mod != att_mod && tgt_mod->on_attack_ended) {
        tgt_mod->on_attack_ended(ctx);
    }
}

void skill_dispatch_special_state(int player_index, int sp_level, int entered) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_special_state) {
        mod->on_special_state(player_index, sp_level, entered);
    }
    const char* opp_id = (player_index == 0) ? g_p1_bot_id : g_p0_bot_id;
    const BotSkillModule* opp_mod = find_module_by_bot(opp_id);
    if (opp_mod && opp_mod->on_opponent_special_state) {
        opp_mod->on_opponent_special_state(player_index, sp_level, entered);
    }
}

float skill_dispatch_crit_chance_mod(int player_index, int atk_level) {
    if (player_index < 0 || player_index >= 2) return 0.0f;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_crit_chance_mod) {
        float bonus = 0.0f;
        if (mod->on_crit_chance_mod(player_index, atk_level, &bonus)) {
            return bonus;
        }
    }
    return 0.0f;
}

void skill_dispatch_crit_rolled(int player_index, int atk_level, int is_last_hit, int is_crit) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_crit_rolled) {
        mod->on_crit_rolled(player_index, atk_level, is_last_hit, is_crit);
    }
}

int skill_dispatch_ranged_pierce_check(int player_index, int atk_level) {
    if (player_index < 0 || player_index >= 2) return 0;
    const char* bot_id = (player_index == 0) ? g_p0_bot_id : g_p1_bot_id;
    const BotSkillModule* mod = find_module_by_bot(bot_id);
    if (mod && mod->on_ranged_pierce_check) {
        return mod->on_ranged_pierce_check(player_index, atk_level);
    }
    return 0;
}
