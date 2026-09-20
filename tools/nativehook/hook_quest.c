#include "hook_quest.h"

// ============================================================================
// Matrix War (1.1.5) Helpers
// ============================================================================
static void* g_matrix_war_rodimus_hero = NULL;

static void filter_heroes_list_to_rodimus(const char* tag, void* list) {
    if (!list || !obj_ok(list)) return;
    void* items = *(void**)((char*)list + 0x10);
    int32_t size = *(int32_t*)((char*)list + 0x18);
    flog("MATRIX_WAR: %s checking list=%p items=%p size=%d", tag, list, items, size);
    if (!items || !obj_ok(items) || size <= 0) return;

    void* rodimus = NULL;
    for (int i = 0; i < size; i++) {
        void* hero = *(void**)((char*)items + 0x20 + i * sizeof(void*));
        if (!hero || !obj_ok(hero)) continue;
        char bid[80]; bid[0] = 0;
        void* s10 = *(void**)((char*)hero + 0x10);
        if (obj_ok(s10)) read_str(s10, bid, sizeof(bid));
        if (!bid[0] || strstr(bid, "rodimus") == NULL) {
            void* bp = *(void**)((char*)hero + 0x48);
            if (obj_ok(bp)) {
                void* bps = *(void**)((char*)bp + 0x10);
                if (obj_ok(bps)) read_str(bps, bid, sizeof(bid));
            }
        }
        if (!bid[0] || strstr(bid, "rodimus") == NULL) {
            void* uh = *(void**)((char*)hero + 0x18);
            if (obj_ok(uh)) {
                void* uhs = *(void**)((char*)uh + 0x10);
                if (obj_ok(uhs)) read_str(uhs, bid, sizeof(bid));
            }
        }
        if (strstr(bid, "rodimus") != NULL) {
            flog("MATRIX_WAR: Found Rodimus Prime at index %d ('%s') hero=%p", i, bid, hero);
            rodimus = hero;
            break;
        }
    }
    if (rodimus) {
        g_matrix_war_rodimus_hero = rodimus;
        for (int i = 0; i < size; i++) {
            *(void**)((char*)items + 0x20 + i * sizeof(void*)) = rodimus;
        }
        *(int32_t*)((char*)list + 0x18) = 1;
        *(int32_t*)((char*)list + 0x1C) += 1;
        flog("MATRIX_WAR: %s restricted list to 1 (Rodimus) successfully!", tag);
    } else if (g_matrix_war_rodimus_hero) {
        for (int i = 0; i < size; i++) {
            *(void**)((char*)items + 0x20 + i * sizeof(void*)) = g_matrix_war_rodimus_hero;
        }
        *(int32_t*)((char*)list + 0x18) = 1;
        *(int32_t*)((char*)list + 0x1C) += 1;
        flog("MATRIX_WAR: %s used cached Rodimus hero to restrict list!", tag);
    } else {
        flog("MATRIX_WAR: %s WARNING: Rodimus NOT found in %d heroes of list %p!", tag, size, list);
    }
}

// ============================================================================
// Hook: PrefightScreenData.SetCurrentHero (Slot 157 @ 0x0E3D8CC)
//
// C# Signature: void SetCurrentHero(PrefightScreenData this, HeroData hero)
// Register mapping:
//   x0: this (PrefightScreenData*)
//   x1: hero (HeroData*)
// Return: void
// Description:
//   Updates the currently selected player hero in the pre-battle matchup screen.
//   Must forward cleanly to original so _currentHeroIndex is updated.
// ============================================================================
void* hook_PrefightScreenData_SetCurrentHero(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    return H[157].orig ? H[157].orig(a0, a1, a2, a3, a4, a5, a6, a7) : NULL;
}

// ============================================================================
// Hook: TeamData.IsKnockedOut (Slot 158 @ 0x10E1E54)
//
// C# Signature: bool IsKnockedOut(TeamData this, int slot)
// Register mapping:
//   x0: this (TeamData*)
//   w1: slot (int32_t, 0-4)
// Return:
//   w0: int32_t (1 if Knocked Out / dead, 0 if Alive)
// Description:
//   Queried by EditTeamScreenPresentation and PrefightScreen to determine if a
//   squad member should display the red KO badge and be disabled from combat.
// ============================================================================
int32_t hook_TeamData_IsKnockedOut(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    int slot = (int)(intptr_t)a1;
    if (!tftf_quest_is_leisure() && slot >= 0 && slot < 5) {
        float ratio = tftf_quest_get_hero_hp_ratio(slot);
        int is_ko = (ratio <= 0.001f) ? 1 : 0;
        static int s_log_hp158 = 0;
        if (s_log_hp158++ < 20) {
            flog("TEAMDATA_IS_KO (0x10E1E54): slot=%d ratio=%.2f -> is_ko=%d", slot, ratio, is_ko);
        }
        return is_ko;
    }
    typedef int32_t (*fn_orig)(void*, void*, void*, void*, void*, void*, void*, void*);
    return H[158].orig ? ((fn_orig)H[158].orig)(self, a1, a2, a3, a4, a5, a6, a7) : 0;
}

// ============================================================================
// Hook: TeamData.GetHP (Slot 159 @ 0x10E1AE4)
//
// C# Signature: float GetHP(TeamData this, int slot)
// Register mapping:
//   x0: this (TeamData*)
//   w1: slot (int32_t, 0-4)
// Return:
//   s0: float (residual health ratio, 0.0f to 1.0f)
// Description:
//   Returns the surviving health ratio for the squad slot in non-leisure quests.
// ============================================================================
float hook_TeamData_GetHP(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    int slot = (int)(intptr_t)a1;
    if (!tftf_quest_is_leisure() && slot >= 0 && slot < 5) {
        float ratio = tftf_quest_get_hero_hp_ratio(slot);
        if (ratio > 1.0f) ratio = 1.0f;
        if (ratio < 0.0f) ratio = 0.0f;
        static int s_log_hp159 = 0;
        if (s_log_hp159++ < 20) {
            flog("TEAMDATA_GET_HP (0x10E1AE4): slot=%d -> ratio=%.2f", slot, ratio);
        }
        return ratio;
    }
    typedef float (*fn_orig)(void*, void*, void*, void*, void*, void*, void*, void*);
    return H[159].orig ? ((fn_orig)H[159].orig)(self, a1, a2, a3, a4, a5, a6, a7) : 1.0f;
}

// ============================================================================
// Hook: ActPanel.get_panelDisplayNameText (Slot 166 @ 0x00C2BE04)
//
// C# Signature: string get_panelDisplayNameText(ActPanel this)
// Register mapping:
//   x0: this (ActPanel*)
// Return:
//   x0: Il2CppString* ("重生" / "Revived")
// Description:
//   Renames the custom campaign act header on the Quest Selection screen.
// ============================================================================
void* hook_ActPanel_get_panelDisplayNameText(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    extern int g_is_chinese_lang;
    if (g_strnew && obj_ok(a0)) {
        uintptr_t actData = *(uintptr_t*)((char*)a0 + 0x220);
        int actIdx = *(int*)((char*)a0 + 0x228);
        const char* name = g_is_chinese_lang ? "重生" : "Revived";
        static int logged_act_name = 0;
        if (logged_act_name < 5) {
            flog("ACT_NAME: ActPanel %p (actIdx=%d actData=%p) returning %s", a0, actIdx, (void*)actData, name);
            logged_act_name++;
        }
        return g_strnew(name);
    }
    return H[166].orig ? H[166].orig(a0, a1, a2, a3, a4, a5, a6, a7) : NULL;
}

// ============================================================================
// Hook: SelectQuestTile.SetTexturePath (Slot 170 @ 0x11CFCAC)
//
// C# Signature: void SetTexturePath(SelectQuestTile this, string path, ...)
// Register mapping:
//   x0: this (SelectQuestTile*)
//   x1: path (Il2CppString*)
// Return: void
// Description:
//   Redirects quest node cover icons to custom poster textures for chapters
//   1.1.1 through 1.1.7.
// ============================================================================
void* hook_SelectQuestTile_SetTexturePath(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    PROTECT({
        if (obj_ok(a0)) {
            void* summary = *(void**)((char*)a0 + 0xB0);
            if (obj_ok(summary)) {
                void* qid_str = *(void**)((char*)summary + 0x20);
                char qid[32];
                if (read_str(qid_str, qid, sizeof(qid))) {
                    char orig_path[128] = "<null>";
                    if (a1 && obj_ok(a1)) read_str(a1, orig_path, sizeof(orig_path));
                    if (strcmp(qid, "1.1.1") == 0) {
                        if (g_strnew) {
                            a1 = g_strnew("questboard/portrait_arrival_quest");
                            a2 = (void*)0;
                            static int logged_111 = 0;
                            if (logged_111 < 5) {
                                flog("QUEST_ICON: tile %p (1.1.1, orig='%s') redirected to questboard/portrait_arrival_quest", a0, orig_path);
                                logged_111++;
                            }
                        }
                    } else if (strcmp(qid, "1.1.2") == 0) {
                        if (g_strnew) {
                            a1 = g_strnew("questboard/portrait_karmasix_quest");
                            a2 = (void*)0;
                            static int logged_112 = 0;
                            if (logged_112 < 5) {
                                flog("QUEST_ICON: tile %p (1.1.2, orig='%s') redirected to questboard/portrait_karmasix_quest", a0, orig_path);
                                logged_112++;
                            }
                        }
                    } else if (strcmp(qid, "1.1.3") == 0) {
                        if (g_strnew) {
                            a1 = g_strnew("questboard/portrait_menasor_quest");
                            a2 = (void*)0;
                        }
                    } else if (strcmp(qid, "1.1.4") == 0) {
                        if (g_strnew) {
                            a1 = g_strnew("questboard/portrait_supreme_optimus_quest");
                            a2 = (void*)0;
                        }
                    } else if (strcmp(qid, "1.1.5") == 0) {
                        if (g_strnew) {
                            a1 = g_strnew("portraits/portrait_matrix_war_small");
                            a2 = (void*)0;
                        }
                    } else if (strcmp(qid, "1.1.6") == 0) {
                        if (g_strnew) {
                            a1 = g_strnew("questboard/portrait_fembots_quest");
                            a2 = (void*)0;
                        }
                    } else if (strcmp(qid, "1.1.7") == 0) {
                        if (g_strnew) {
                            a1 = g_strnew("portraits/portrait_picnic_small");
                            a2 = (void*)0;
                        }
                    }
                }
            }
        }
    });
    return H[170].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// ============================================================================
// Hook: TeamSelectModel.get_Team (Slot 175 @ 0xF9A7F8)
//
// C# Signature: TeamData get_Team(TeamSelectModel this)
// Description:
//   In Matrix War (1.1.5), clears the squad on initial entry so that only
//   Rodimus Prime can be selected into the team.
// ============================================================================
void* hook_TeamSelectModel_get_Team(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (tftf_is_matrix_war_active() && tftf_matrix_war_should_empty_team()) {
        flog("MATRIX_WAR: TeamSelectModel.get_Team -> returning NULL to clear squad on entry!");
        return NULL;
    }
    return H[175].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// ============================================================================
// Hook: EditTeamModel.InitHeroes (Slot 176 @ 0xB16C54)
//
// C# Signature: void InitHeroes(EditTeamModel this, TeamData data)
// Description:
//   Restricts the editable hero pool to Rodimus Prime only during Matrix War.
// ============================================================================
void* hook_EditTeamModel_InitHeroes(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (tftf_is_matrix_war_active()) {
        PROTECT({
            flog("MATRIX_WAR: hook_176 InitHeroes pre model=%p data=%p", a0, a1);
            if (a1 && obj_ok(a1)) {
                filter_heroes_list_to_rodimus("pre data+0x60", *(void**)((char*)a1 + 0x60));
            }
        });
    }

    void* res = H[176].orig(a0, a1, a2, a3, a4, a5, a6, a7);

    if (tftf_is_matrix_war_active()) {
        PROTECT({
            flog("MATRIX_WAR: hook_176 InitHeroes post model=%p", a0);
            if (a0 && obj_ok(a0)) {
                filter_heroes_list_to_rodimus("post model+0x20", *(void**)((char*)a0 + 0x20));
            }
        });
    }
    return res;
}

// ============================================================================
// Hook: PrefightScreenData.GetEnemyNormalizedHealth (Slot 178 @ 0x0E3D688)
//
// C# Signature: float GetEnemyNormalizedHealth(PrefightScreenData this)
// Return:
//   s0: float (residual enemy health ratio, 0.05f to 1.0f)
// Description:
//   Provides the surviving enemy health ratio across continuous quest fights.
// ============================================================================
float hook_PrefightScreenData_GetEnemyNormalizedHealth(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (!tftf_quest_is_leisure() && tftf_quest_has_pending_enemy()) {
        float ratio = tftf_quest_get_pending_enemy_hp_ratio();
        if (ratio > 1.0f) ratio = 1.0f;
        if (ratio < 0.05f) ratio = 0.05f;
        static int s_log_hp178 = 0;
        if (s_log_hp178++ < 20) {
            flog("PFS_ENEMY_HP (0x0E3D688): returning pending ratio=%.2f", ratio);
        }
        return ratio;
    }
    typedef float (*fn_orig)(void*, void*, void*, void*, void*, void*, void*, void*);
    return H[178].orig ? ((fn_orig)H[178].orig)(self, a1, a2, a3, a4, a5, a6, a7) : 1.0f;
}
