/*
 * TFTF Combat System Golden Reference / 真理源备份
 * =======================================================
 * 文件名: tools/nativehook/combat_truth_backup.c
 * 作用: 本文件完整备份了 tools/nativehook/hook.c 中所有决定战斗手感、
 *       输入手势分发、连招状态机、受击中断与空等超时的核心代码。
 * 
 * 任何后续对 hook.c 战斗逻辑的变更，必须对照本真理源进行复核；
 * 若因意外修改导致手感劣化或 bug 重现，可直接参考本文件进行无损复原。
 * 对应说明文档: re_notes/combat_truth_source.md
 */

#ifndef COMBAT_TRUTH_BACKUP_H
#define COMBAT_TRUTH_BACKUP_H

#include <stdint.h>
#include <string.h>

/* ========================================================
 * 1. 核心状态变量与宏定义
 * ======================================================== */
static void* g_p0_controller = NULL;
static volatile uint64_t g_p0_block_enter_ms = 0;
static volatile int g_p0_block_reset_done = 0;
static volatile int g_p0_after_heavy = 0;
static volatile int g_p0_combo_ended = 0;
static volatile uint64_t g_p0_last_attack_ms = 0;
#define COMBO_IDLE_RESET_MS 900

/* ========================================================
 * 2. 攻击链安全重置函数 (严禁修改 _lastHitResult)
 * ======================================================== */
static void truth_reset_player_attack_chain(void* pc) {
    if (!obj_ok(pc)) return;
    int32_t p_idx = *(int32_t*)((uintptr_t)pc + 0xF4);
    if (p_idx != 0) return; // 本地玩家 P0 独占
    g_p0_controller = pc;
    g_p0_last_attack_ms = 0;                 // 空等计时器在下一次有效出招时重新启动
    *(uint32_t*)((uintptr_t)pc + 0x1c0) = 0; // _lightAttackIndex = 0
    *(uint32_t*)((uintptr_t)pc + 0x1c4) = 0; // _mediumAttackIndex = 0
    *(uint32_t*)((uintptr_t)pc + 0x1c8) = 0; // _rangedAttackIndex = 0
    // 【铁律】：绝对不能把 _lastHitResult.Flags 清零！
    // 否则会破坏 Arcee 等角色多段中击（M2）的命中传递，导致第二段击空！
    flog("RESET_ATTACK_CHAIN on p0 pc=%p (caller=%p)", pc, __builtin_return_address(0));
}

/* ========================================================
 * 3. hook_145 (Simulation.FixedUpdate @ 0xDE8750) 核心战斗时序
 * ======================================================== */
void truth_combat_fixed_update(void) {
    // GATE-04: 900ms 空等超时清链
    // 当角色停顿不攻击、或被击倒在地超过 900ms 时，自动重置攻击链为 L1/M1
    if (g_p0_last_attack_ms && obj_ok(g_p0_controller)) {
        uint64_t idle = propgo_now_ms() - g_p0_last_attack_ms;
        if (idle >= COMBO_IDLE_RESET_MS) {
            g_p0_last_attack_ms = 0;
            flog("COMBAT_IDLE: %llu ms without an attack (>= %d ms window) -> reset attack chain to L1",
                 (unsigned long long)idle, COMBO_IDLE_RESET_MS);
            reset_player_attack_chain(g_p0_controller);
            g_p0_combo_ended = 0;
            g_p0_after_heavy = 0;
        }
    }

    // GATE-05: 格挡长按（>=200ms）清链，短按（<200ms）保留连招
    if (g_p0_block_enter_ms > 0 && !g_p0_block_reset_done && g_p0_controller) {
        uint64_t held = propgo_now_ms() - g_p0_block_enter_ms;
        if (held >= 200) {
            g_p0_block_reset_done = 1;
            flog("BLOCK_HELD: P0 held guard stance for %llu ms >= 200ms -> attack chain reset to L1",
                 (unsigned long long)held);
            reset_player_attack_chain(g_p0_controller);
        }
    }

    // GATE-03: 受创扣血清链（非格挡削血）
    if (g_p0_combat_character && obj_ok(g_p0_combat_character)) {
        typedef float (*fn_get_hp)(void*, void*);
        fn_get_hp get_hp = (fn_get_hp)(g_base + 0xDAC6CC); // get_Health
        float cur_hp = get_hp(g_p0_combat_character, NULL);
        if (g_p0_last_hp >= 0.0f && cur_hp < g_p0_last_hp - 0.01f) {
            if (g_p0_block_enter_ms == 0) {
                flog("COMBAT_GATE: P0 took unblocked damage (%.1f -> %.1f) -> hit reaction resets attack chain",
                     g_p0_last_hp, cur_hp);
                if (g_p0_controller) {
                    reset_player_attack_chain(g_p0_controller);
                    g_p0_combo_ended = 0;
                    g_p0_after_heavy = 0;
                    COMBAT_ASSERT(*(uint32_t*)((uintptr_t)g_p0_controller + 0x1c0) == 0 &&
                                  *(uint32_t*)((uintptr_t)g_p0_controller + 0x1c4) == 0,
                                  "GATE-03", "Combo chain must be reset after hit reaction");
                }
            } else {
                flog("COMBAT_GATE: P0 took block chip damage (%.1f -> %.1f) while guarding -> combo chain preserved",
                     g_p0_last_hp, cur_hp);
            }
        }
        g_p0_last_hp = cur_hp;
    }
}

/* ========================================================
 * 4. hook_153 (PlayerController.SpecialAttack @ 0x1174300)
 * ======================================================== */
void* truth_hook_153(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7){
    int index = (int)(intptr_t)a1;
    flog("SPECIAL_ATTACK index=%d called on controller=%p (p0=%p, is_p0=%d)",
         index, self, g_p0_controller, (self == g_p0_controller));
    if (self == g_p0_controller || (obj_ok(self) && *(int32_t*)((uintptr_t)self + 0xF4) == 0)) {
        g_intended_special_tier = 0;
        reset_player_attack_chain(self);
        g_p0_combo_ended = 0;
        g_p0_after_heavy = 0;
    }
    void* r = H[153].orig(self, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        ensure_p0_power_rounding(self);
    });
    return r;
}

/* ========================================================
 * 5. hook_154 (PlayerController.Action @ 0x1179AF4)
 * ======================================================== */
void* truth_hook_154(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7){
    int action = (int)(intptr_t)a1;
    uint32_t pre_l = 0, pre_m = 0;
    int did_reset = 0;
    PROTECT({
        if (obj_ok(self) && *(int32_t*)((uintptr_t)self + 0xF4) == 0) {
            g_p0_controller = self;
            pre_l = *(uint32_t*)((uintptr_t)self + 0x1c0);
            pre_m = *(uint32_t*)((uintptr_t)self + 0x1c4);

            flog("ACTION pre act=%d l=%u m=%u r=%u", action, pre_l, pre_m,
                 *(uint32_t*)((uintptr_t)self + 0x1c8));

            if (action == 2) {
                // Action 2 = Block / Guard stance
                g_p0_block_enter_ms = 0;
                g_p0_block_reset_done = 0;
            }
            if (action == 8 || action == 64 || action == 128 || (action & 192)) {
                // 8 = Dodge (后划), 64 (0x40) = SidestepLeft (上划侧闪), 128 (0x80) = SidestepRight (下划侧闪)
                // 侧闪与后避必须立刻清空攻击索引，确保侧闪避开后首招严格从 L1 / 前冲 M1 起手！
                g_p0_block_enter_ms = 0;
                g_p0_block_reset_done = 0;
                flog("PLAYER_ACTION dodge/sidestep (action=%d) on P0: reset attack chain", action);
                reset_player_attack_chain(self);
                did_reset = 1;
                g_p0_combo_ended = 0;
                g_p0_after_heavy = 0;
            }
            if (action == 0x100) {
                // 0x100 = HeavyAttack (长按重击起手)
                g_p0_block_enter_ms = 0;
                g_p0_block_reset_done = 0;
                g_p0_after_heavy = 1;
                flog("PLAYER_ACTION heavy (action=0x100) on P0: reset attack chain and arm after_heavy flag");
                reset_player_attack_chain(self);
                did_reset = 1;
                COMBAT_ASSERT(*(uint32_t*)((uintptr_t)self + 0x1c4) == 0, "GATE-07",
                              "Medium index must be 0 after heavy attack so the next swipe is M1, got %u",
                              *(uint32_t*)((uintptr_t)self + 0x1c4));
            }
            if (action == 1 || action == 4 || action == 32) {
                // 普攻 / 冲刺消费逻辑
                if (g_p0_after_heavy) {
                    flog("COMBAT_GATE: attack following heavy attack (action=%d) -> reset attack chain to L1/M1", action);
                    reset_player_attack_chain(self);
                    did_reset = 1;
                    g_p0_after_heavy = 0;
                    g_p0_combo_ended = 0;
                    pre_l = *(uint32_t*)((uintptr_t)self + 0x1c0);
                    pre_m = *(uint32_t*)((uintptr_t)self + 0x1c4);
                    COMBAT_ASSERT(pre_l == 0, "GATE-02", "Light index must be 0 after heavy attack, got %u", pre_l);
                } else if ((action == 1 || action == 4) && (g_p0_combo_ended || pre_m >= 2 || pre_l >= 4)) {
                    flog("COMBAT_GATE: combo ender reached (ended_flag=%d, pre_m=%u, pre_l=%u, action=%d) -> reset chain",
                         g_p0_combo_ended, pre_m, pre_l, action);
                    reset_player_attack_chain(self);
                    did_reset = 1;
                    g_p0_combo_ended = 0;
                    pre_l = *(uint32_t*)((uintptr_t)self + 0x1c0);
                    pre_m = *(uint32_t*)((uintptr_t)self + 0x1c4);
                    COMBAT_ASSERT(pre_l == 0 && pre_m == 0, "GATE-01", "Attack after combo ender must start at index 0");
                }
            }
            if (action == 4 || action == 1 || action == 32 || action == 0x100) {
                // ReleaseBlock (4) 或攻击操作：短按松开（<200ms）取消格挡计时，保留连击链
                if (g_p0_block_enter_ms > 0) {
                    uint64_t held = propgo_now_ms() - g_p0_block_enter_ms;
                    g_p0_block_enter_ms = 0;
                    if (!g_p0_block_reset_done) {
                        flog("PLAYER_ACTION abort block (action=%d) on P0: held for %llu ms (< 200ms) -> combo chain preserved",
                             action, (unsigned long long)held);
                    }
                }
            }
            if (action == 0x200) {
                // SpecialAttack 按键按下
                if (!g_sp_dispatching_internal && g_sp_touch_tracking) {
                    flog("PLAYER_ACTION 0x200: suppressed premature touch-down special on P0 (tracking gesture)");
                    return (void*)1;
                }
                flog("PLAYER_ACTION 0x200: executing on P0 (intended_tier=%d, internal=%d)",
                     g_intended_special_tier, g_sp_dispatching_internal);
                reset_player_attack_chain(self);
                did_reset = 1;
                g_p0_combo_ended = 0;
                g_p0_after_heavy = 0;
            }
        }
    });

    if (action >= 1 && action <= 32) {
        flog("PLAYER_ACTION action=%d on controller=%p (p0=%p, is_p0=%d)",
             action, self, g_p0_controller, (self == g_p0_controller));
    }
    void* r = H[154].orig(self, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        int action_ok = ((uintptr_t)r != 0);
        if (obj_ok(self) && *(int32_t*)((uintptr_t)self + 0xF4) == 0) {
            uint32_t post_l = *(uint32_t*)((uintptr_t)self + 0x1c0);
            uint32_t post_m = *(uint32_t*)((uintptr_t)self + 0x1c4);
            flog("ACTION post act=%d l=%u m=%u r=%u ended=%d heavy=%d", action, post_l, post_m,
                 *(uint32_t*)((uintptr_t)self + 0x1c8), g_p0_combo_ended, g_p0_after_heavy);

            // 仅在原生引擎真正成功执行攻击动作时刷新时间戳；
            // 角色在受创倒地状态时点按的无效 Tap (action_ok==0) 不会推迟时间戳，确保 900ms 超时生效
            if (action_ok && (action == 1 || action == 32 || action == 0x100)) {
                g_p0_last_attack_ms = propgo_now_ms();
            }

            // 仅在真实确认终结时立起 g_p0_combo_ended
            if (!did_reset && (post_l >= 4 || post_m >= 2 || post_l < pre_l || post_m < pre_m)) {
                g_p0_combo_ended = 1;
                flog("COMBAT_GATE: combo ender CONFIRMED (action=%d, pre l=%u m=%u -> post l=%u m=%u) -> g_p0_combo_ended = 1",
                     action, pre_l, pre_m, post_l, post_m);
            }
        }
    });
    return r;
}

/* ========================================================
 * 6. hook_155 (PlayerSpecialAttackState.OnExit @ 0x0E34640)
 * ======================================================== */
void* truth_hook_155(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* pc = fld_p(a0, 0x18);
    void* r = H[155].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        void* target = (obj_ok(pc) && *(int32_t*)((uintptr_t)pc + 0xF4) == 0) ? pc
                     : (obj_ok(g_p0_controller) ? g_p0_controller : NULL);
        if (target) {
            flog("SPECIAL_EXIT (0x0E34640) on P0 (target=%p): attack chain reset", target);
            reset_player_attack_chain(target);
            ensure_p0_power_rounding(target);
            g_p0_combo_ended = 0;
            g_p0_after_heavy = 0;
        }
    });
    return r;
}

#endif /* COMBAT_TRUTH_BACKUP_H */
