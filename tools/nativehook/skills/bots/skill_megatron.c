#include "../skill_types.h"
#include "../skill_env.h"
#include <string.h>

// ===========================================================================
// 威震天 (Megatron Leader 2015) 技能模块
// Bot ID: megatron_gs_leader2015
// ===========================================================================
// 1. [3121] 被动：融合炮充能 (Fusion Cannon Charge)
//    - 开局显现灰色 6 秒倒计时图标 (\uE910)，每 6 秒充满 1 层紫色融合炮图标 (上限 3 层)。
//    - 满 3 层时倒计时隐藏暂停；消耗后重新开始 6 秒倒计时。
//    - 重击命中时：若拥有融合炮，增伤 30%，且消耗 1 层融合炮（过载时不消耗）。
// 2. [3129] SP2：弱化 (Weakness / Atk Debuff) 44% 10s
// 3. [3130] SP3：震击 300% 20s + 融合炮过载 (图标变绿，不带数字，本局无限使用不消耗)
// 4. [3137] SP1：破甲 38% 10s
// 5. [3138] 特色能力：减益融合 (Debuff Fusion)
//    - 仅在【拥有融合炮且重击命中】时：检查对方身上是否有带倒计时的减益。
//    - 若有，将其全部固化为永久减益，此时才显示并呼出“减益融合”！
//    - 若对方没有带倒计时的减益，则绝不显示“减益融合”。
// ===========================================================================

static int      s_megatron_active[2]         = {0, 0};
static int      s_fusion_charges[2]          = {0, 0};
static uint64_t s_last_charge_ms[2]          = {0, 0};
static int      s_fusion_overload[2]         = {0, 0};

static void megatron_on_simulation_tick(uint64_t now_ms) {
    for (int p = 0; p < 2; p++) {
        if (!s_megatron_active[p] || s_fusion_overload[p]) continue;

        // Auto charge every 6 seconds if under 3 charges
        if (s_fusion_charges[p] < 3 && s_last_charge_ms[p] > 0) {
            if (now_ms - s_last_charge_ms[p] >= 6000) {
                s_fusion_charges[p]++;
                skill_consume_buff(p, "megatron_fusion_cd", 1);
                skill_apply_buff_dur(p, "megatron_fusion_cannon", -1.0f);
                skill_overlay("[%s] 融合炮充能完成 (%d/3)",
                              p == 0 ? "威震天" : "敌方威震天", s_fusion_charges[p]);
                skill_log("MEGATRON: P%d gained Fusion Cannon stack %d/3", p, s_fusion_charges[p]);

                if (s_fusion_charges[p] < 3) {
                    s_last_charge_ms[p] = now_ms;
                    skill_apply_buff_dur(p, "megatron_fusion_cd", 6.0f);
                } else {
                    s_last_charge_ms[p] = 0; // 满 3 层时停止倒计时
                }
            }
        }
    }
}

static void megatron_on_hit_connected(SkillHitContext* ctx) {
    if (!ctx) return;
    uint64_t now_ms = skill_now_ms();

    // 威震天作为攻击方：
    if (ctx->attacker_bot_id && strstr(ctx->attacker_bot_id, "megatron") != NULL) {
        int ap = ctx->attacker_player_index;
        int tp = ctx->target_player_index;

        // SP3 激活：融合炮过载 (仅在最后一击命中且未被格挡时生效)
        if (ctx->special_index == 3 && ctx->is_last_hit && !ctx->is_blocked && !s_fusion_overload[ap]) {
            s_fusion_overload[ap] = 1;
            // 移除原有倒计时和紫色层数图标
            skill_consume_buff(ap, "megatron_fusion_cd", 1);
            skill_consume_buff(ap, "megatron_fusion_cannon", 3);
            // 显现绿色过载图标（无数字，本局无限使用不消耗）
            skill_apply_buff_dur(ap, "megatron_fusion_overload", -1.0f);
            skill_overlay("[%s] 融合炮过载！本局无限全功率重击，不消耗层数！",
                          ap == 0 ? "威震天" : "敌方威震天");
            skill_log("MEGATRON: P%d activated SP3 Fusion Cannon Overload!", ap);
        }

        // 重击命中判定 (必须未被格挡，且必须是真正的普通重击，非远程、非SP技)：
        if (ctx->is_heavy && !ctx->is_ranged && ctx->special_index == 0 && ctx->is_last_hit && !ctx->is_blocked) {
            int has_fusion = (s_fusion_overload[ap] || s_fusion_charges[ap] > 0);

            if (has_fusion) {
                // 1. 伤害增加 30%
                ctx->modified_damage *= 1.30f;

                // 2. 消耗 1 层融合炮（过载时不消耗）
                if (!s_fusion_overload[ap]) {
                    s_fusion_charges[ap]--;
                    skill_consume_buff(ap, "megatron_fusion_cannon", 1);
                    skill_log("MEGATRON: P%d consumed 1 Fusion stack, remaining %d/3",
                              ap, s_fusion_charges[ap]);

                    // 如果从满 3 层变为 2 层，或者小于 3 层且未在倒计时，重启 6 秒倒计时
                    if (s_fusion_charges[ap] < 3 && s_last_charge_ms[ap] == 0) {
                        s_last_charge_ms[ap] = now_ms;
                        skill_apply_buff_dur(ap, "megatron_fusion_cd", 6.0f);
                    }
                }

                // 3. 减益融合：仅在对方身上有带倒计时的减益时，转化为永久并显示“减益融合”
                int fused = skill_fuse_target_debuffs(tp);
                if (fused > 0) {
                    skill_apply_buff_dur(ap, "megatron_debuff_fusion", 1.5f);
                    skill_overlay("[%s] 减益融合！固化对手 %d 个减益为永久！",
                                  ap == 0 ? "威震天" : "敌方威震天", fused);
                    skill_log("MEGATRON: P%d successfully FUSED %d debuffs on P%d to permanent!",
                              ap, fused, tp);
                } else {
                    skill_log("MEGATRON: P%d heavy hit with fusion, but opponent P%d has no timed debuffs to fuse",
                              ap, tp);
                }
            }
        }
    }
}

static void megatron_on_buff_applied(SkillBuffAppliedContext* ctx) {
    if (!ctx || !ctx->modifier_id) return;

    int tp = ctx->target_player_index;
    if (strstr(ctx->modifier_id, "megatron_fusion_cd") != NULL) {
        s_megatron_active[tp] = 1;
        if (s_last_charge_ms[tp] == 0) {
            s_last_charge_ms[tp] = skill_now_ms();
            skill_log("MEGATRON: Initial 6s Fusion Cannon CD started on P%d", tp);
        }
        return;
    }
}

static void megatron_on_fight_reset(int player_index) {
    if (player_index >= 0 && player_index < 2) {
        s_megatron_active[player_index]         = 0;
        s_fusion_charges[player_index]          = 0;
        s_last_charge_ms[player_index]          = 0;
        s_fusion_overload[player_index]         = 0;
    }
}

BotSkillModule g_module_megatron = {
    .bot_prefix         = "megatron",
    .on_hit_connected   = megatron_on_hit_connected,
    .on_buff_gated      = NULL,
    .on_buff_applied    = megatron_on_buff_applied,
    .on_evade_check     = NULL,
    .on_test_roll       = NULL,
    .on_fight_reset     = megatron_on_fight_reset,
    .on_simulation_tick = megatron_on_simulation_tick,
};
