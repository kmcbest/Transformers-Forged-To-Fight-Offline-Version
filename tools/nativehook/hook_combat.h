#ifndef HOOK_COMBAT_H
#define HOOK_COMBAT_H

#include "hook_common.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Combat State & Controllers
// ============================================================================

extern void* g_p0_controller;
extern void* g_p1_controller;
extern char g_p0_bot_id[80];
extern char g_p1_bot_id[80];
extern void* g_p0_combat_character;
extern void* g_p1_combat_character;
extern volatile float g_p0_max_hp;
extern volatile float g_p1_max_hp;
extern volatile float g_p0_last_hp;
extern volatile float g_p1_last_hp;
extern int g_last_enemy_pi;

// Combat helpers
void reset_player_attack_chain(void* pc);
void hook_combat_process_touch(uintptr_t pressed, uintptr_t unpressed);
int calc_enemy_rating(const char* bid, int rank, int level);

// ============================================================================
// Combat Hook Handlers
// ============================================================================

// Slot 56 (0xDAB16C): PlayerAttributes.Init -> stats, tags, HP initialization
void* hook_PlayerAttributes_Init(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 57 (0x12A9D94): HashSet<T>..ctor -> null collection fallback
void* hook_HashSet_ctor(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 58 (0xD35130): PlayerInput.QueuedAction.SetAction -> input buffer window
void* hook_PlayerInput_QueuedAction_SetAction(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 138 (0xEA023C): PropData.SetActiveInternal -> prop state mirror onto GameObjects
void* hook_PropData_SetActiveInternal(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 139 (0x100A76C): MoveSet.GetMove -> resolve absent SP3 move
void* hook_MoveSet_GetMove(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 140 (0xDE7CF4): Simulation.RegisterComponents -> clear combat combo state
void* hook_Simulation_RegisterComponents(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 141 (0x117A67C): PlayerController.Transform -> latch cinematic transform
void* hook_PlayerController_Transform(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 142 (0x1174038): PlayerCinematicSpecialAttackState.OnEnter -> apply SP3 alt form
void* hook_PlayerCinematicSpecialAttackState_OnEnter(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 143 (0x1174484): PlayerCinematicSpecialAttackState.OnExit -> restore robot form
void* hook_PlayerCinematicSpecialAttackState_OnExit(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 145 (0xDE8750): Simulation.FixedUpdate -> combat state pump (idle reset, block timer, damage reactions)
void* hook_Simulation_FixedUpdate(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 146 (0xDB1D30): AIController.Simulate -> AI ranged attacks
void hook_AIController_Simulate(void* self, float dT, void* method);

// Slot 153 (0x1174300): PlayerController.SpecialAttack -> special attack execution
void* hook_PlayerController_SpecialAttack(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 154 (0x1179AF4): PlayerController.Action -> combo chain progression & quality gates
void* hook_PlayerController_Action(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 155 (0x0E34640): PlayerSpecialAttackState.OnExit -> attack chain reset on special end
void* hook_PlayerSpecialAttackState_OnExit(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 156 (0x0DADA6C): PlayerAttributes.RollForCriticalHit -> critical hit roll
void* hook_PlayerAttributes_RollForCriticalHit(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 160 (0x0D32A00): PlayerBlockState.OnEnter -> arm guard hold timer
void* hook_PlayerBlockState_OnEnter(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 163 (0x11794A4): PlayerController.AddMana -> mana gain rate scaling
void* hook_PlayerController_AddMana(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 165 (0x0D34E6C): PlayerDodgeState.OnEnter -> reset attack chain on back-swipe
void* hook_PlayerDodgeState_OnEnter(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 168 (0x1173FA4): PlayerController.GetAvailableSpecialTier -> swipe special tier override
void* hook_PlayerController_GetAvailableSpecialTier(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 169 (0xFF05C8): HudSpecialMeter.OnSpecialButtonPressed -> gesture recognition
void* hook_HudSpecialMeter_OnSpecialButtonPressed(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 171 (0x1173848): BLOCKENTER2 -> active guard entry
void* hook_PlayerBlockState_OnEnter2(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 172 (0x117E4AC): DODGEENTER2 -> active dodge entry
void* hook_PlayerDodgeState_OnEnter2(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

// Slot 177 (0x0DAD5A4): PlayerAttributes.ApplyDamage -> Starscream's Picnic ranged-only damage filter
float hook_PlayerAttributes_ApplyDamage(void* self, float damage, void* a1, int32_t a2, void* a3, int32_t a4, int32_t a5, float s1, float s2);

#ifdef __cplusplus
}
#endif

#endif // HOOK_COMBAT_H
