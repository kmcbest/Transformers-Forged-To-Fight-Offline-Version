#ifndef HOOK_UI_H
#define HOOK_UI_H

#include "hook_common.h"

#ifdef __cplusplus
extern "C" {
#endif

// ============================================================================
// UI & Portrait Decoration Module
//
// Responsibilities:
// 1. HeroPortrait decoration: rarity frame, stars, faction badge glyph, KO tabs.
// 2. Ensuring HeroPortraitOverlay does not crash via type checking.
// 3. TopBar resource click redirection and map asset ID resolution.
// ============================================================================

// Faction resolution
uint16_t faction_icon_code(const char* faction);
const char* faction_icon_glyph(const char* faction);
const char* hero_faction_str(void* hero_data);

// Portrait decorator
void apply_hero_portrait_deco(void* hp);

// Hook handlers
void* hook_HeroPortrait_RefreshFromData(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_HeroPortrait_SetEnabledItems(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_HeroPortrait_OnHeroTextureLoaded(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
float hook_HeroPortrait_get_healthPercentage(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_BCGBlueprintBase_get_MapAssetID(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_BCGHelper_GetTopHeroId(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_TransformersTopBarPresentation_OnHardCurrencyClick(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);
void* hook_PayoutsModel_GetDefaultTabId(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7);

#ifdef __cplusplus
}
#endif

#endif // HOOK_UI_H
