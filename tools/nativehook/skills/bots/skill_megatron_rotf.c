#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 电影威震天 (Megatron ROTF) 底层战斗技能模块
// Bot ID: megatron_cin_rotf
// ===========================================================================

static int      s_hp_thresh_stage[2]    = {0, 0};
static int      s_sig_used[2]           = {0, 0};
static int      s_heavy_whiff_pending[2]= {0, 0};
static int      s_heavy_connected[2]    = {0, 0};
static int      s_heavy_unstop[2]       = {0, 0};
static uint64_t s_heavy_start_ms[2]     = {0, 0};

static void megatron_rotf_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_hp_thresh_stage[player_index]     = 0;
        s_sig_used[player_index]            = 0;
        s_heavy_whiff_pending[player_index] = 0;
        s_heavy_connected[player_index]     = 0;
        s_heavy_unstop[player_index]        = 0;
        s_heavy_start_ms[player_index]      = 0;
    }
}

static void megatron_rotf_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        const char* bid = skill_get_bot_id(p);
        if (!bid || strstr(bid, "megatron_cin_rotf") == NULL) continue;

        float hp_r = skill_get_hp_ratio(p);
        if (hp_r > 0.0f) {
            static const float k_thresh[3] = {0.80f, 0.60f, 0.40f};
            while (s_hp_thresh_stage[p] < 3 && hp_r <= k_thresh[s_hp_thresh_stage[p]]) {
                s_hp_thresh_stage[p]++;
                skill_set_unstoppable(p, 4000);
                skill_apply_buff_dur(p, "megatron_rotf_hp_unstoppable", 4.0f);
                skill_apply_buff_dur(p, "megatron_rotf_hp_unstoppable_vfx", 4.0f);
                skill_log("MEGATRON_ROTF: P%d HP threshold stage %d triggered -> 4s Unstoppable",
                          p, s_hp_thresh_stage[p]);
            }

            if (!s_sig_used[p] && hp_r < 0.10f) {
                s_sig_used[p] = 1;
                skill_apply_buff_dur(p, "megatron_rotf_sig_repair", 3.0f);
                skill_heal(p, skill_get_max_hp(p) * 0.30f);
                skill_overlay("[%s] 威震天万岁！修复 30%% 生命！", p == 0 ? "电影威震天" : "敌方电影威震天");
                skill_log("MEGATRON_ROTF: P%d sig repair triggered below 10%% HP", p);
            }
        }

        if (s_heavy_whiff_pending[p] && !s_heavy_connected[p] &&
            s_heavy_start_ms[p] > 0 && now_ms >= s_heavy_start_ms[p] &&
            (now_ms - s_heavy_start_ms[p] >= 600)) {
            s_heavy_whiff_pending[p] = 0;
            if (s_heavy_unstop[p]) {
                skill_apply_buff_dur(p, "megatron_rotf_heavy_whiff_atk", 10.0f);
                skill_log("MEGATRON_ROTF: P%d heavy whiff while unstoppable -> +40%% ATK (10s)", p);
            }
        }
    }
}

static void megatron_rotf_on_attack_start(int player_index, int action_type) {
    if (player_index < 0 || player_index >= 2) return;
    const char* bid = skill_get_bot_id(player_index);
    if (!bid || strstr(bid, "megatron_cin_rotf") == NULL) return;

    if (action_type == 4 || action_type == 0x100) {
        s_heavy_whiff_pending[player_index] = 1;
        s_heavy_connected[player_index]     = 0;
        s_heavy_start_ms[player_index]      = skill_now_ms();
        s_heavy_unstop[player_index]        = skill_is_unstoppable(player_index);
    }
}

static int megatron_rotf_on_test_roll(SkillTestRollContext* ctx, int* out_res) {
    (void)out_res;
    if (!ctx || !ctx->owner_bot_id || strstr(ctx->owner_bot_id, "megatron_cin_rotf") == NULL) return 0;
    if (ctx->is_heavy) {
        int charges = skill_count_buffs(ctx->target_player_index, "impair_charge");
        if (charges > 0 && ctx->p_chance) {
            *ctx->p_chance += 0.05f * (float)charges;
        }
    }
    return 0;
}

static void megatron_rotf_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx || !ctx->attacker_bot_id || strstr(ctx->attacker_bot_id, "megatron_cin_rotf") == NULL) return;
    int ap = ctx->attacker_player_index;
    int tp = ctx->target_player_index;

    if (ctx->is_heavy) {
        s_heavy_connected[ap]     = 1;
        s_heavy_whiff_pending[ap] = 0;
    }

    if (ctx->special_index == 3 && ctx->hit_index == 0) {
        for (int i = 0; i < 20; i++) {
            skill_apply_buff(tp, "megatron_rotf_hit_impair_charge");
        }
        skill_apply_buff(tp, "megatron_rotf_sp3_impair_charges");
        skill_log("MEGATRON_ROTF: P%d SP3 hit 0 applied 20 impair charges to P%d", ap, tp);
    }

    if (ctx->special_index == 3 && ctx->is_last_hit) {
        if (ctx->is_crit) {
            ctx->modified_damage *= 1.40f;
        }
        skill_apply_buff_dur(ap, "megatron_rotf_sp3_crit_damage", 2.0f);
        skill_log("MEGATRON_ROTF: P%d SP3 lastHit triggered megatron_rotf_sp3_crit_damage", ap);
    }

    if (ctx->is_heavy && ctx->is_crit) {
        int charges = skill_count_buffs(tp, "impair_charge");
        if (charges > 0) {
            ctx->modified_damage *= (1.0f + 0.02f * (float)charges);
            skill_consume_buff(tp, "impair_charge", 99);
            skill_log("MEGATRON_ROTF: P%d heavy crit consumed %d impair charges", ap, charges);
        }
    }
}

BotSkillModule g_module_megatron_rotf = {
    .bot_prefix         = "megatron_cin_rotf",
    .display_name_zh    = "电影威震天",
    .on_hit_connected   = megatron_rotf_on_hit_connected,
    .on_test_roll       = megatron_rotf_on_test_roll,
    .on_attack_start    = megatron_rotf_on_attack_start,
    .on_simulation_tick = megatron_rotf_on_simulation_tick,
    .on_fight_reset     = megatron_rotf_on_fight_reset,
};
