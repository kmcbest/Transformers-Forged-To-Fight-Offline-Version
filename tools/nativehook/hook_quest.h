#ifndef HOOK_QUEST_H
#define HOOK_QUEST_H

#include "hook_common.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// Quest & Team Health Management Module
//
// Responsibilities:
// 1. Intercepting TeamData HP and Knockout queries for non-leisure quests.
// 2. Ensuring residual HP and KO statuses persist between fights.
// 3. Matrix War (1.1.5) squad filtering and restriction to Rodimus Prime.
// 4. Custom Act and Quest poster/tile texture path mappings.
// ============================================================================

// Hook handlers
void* hook_PrefightScreenData_SetCurrentHero(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
int32_t hook_TeamData_IsKnockedOut(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
float hook_TeamData_GetHP(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_ActPanel_get_panelDisplayNameText(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_SelectQuestTile_SetTexturePath(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_TeamSelectModel_get_Team(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_EditTeamModel_InitHeroes(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
float hook_PrefightScreenData_GetEnemyNormalizedHealth(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

#ifdef __cplusplus
}
#endif

#endif // HOOK_QUEST_H
