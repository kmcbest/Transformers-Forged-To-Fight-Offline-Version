#include "hook_ui.h"

// ============================================================================
// Faction Resolution Helpers
// ============================================================================

uint16_t faction_icon_code(const char* faction) {
    if (!faction || !*faction) return 0;
    if (!strcmp(faction, "autobot"))    return 0xE134;  // Autobot
    if (!strcmp(faction, "decepticon")) return 0xE135;  // Decepticon
    if (!strcmp(faction, "maximal"))    return 0xE160;  // Maximal
    if (!strcmp(faction, "predacon"))   return 0xE161;  // Predacon
    return 0;
}

const char* faction_icon_glyph(const char* faction) {
    switch (faction_icon_code(faction)) {
        case 0xE134: return "\uE134";   // EE 84 B4
        case 0xE135: return "\uE135";   // EE 84 B5
        case 0xE160: return "\uE160";   // EE 85 A0
        case 0xE161: return "\uE161";   // EE 85 A1
    }
    return NULL;
}

const char* hero_faction_str(void* hero_data) {
    static char buf[24];
    buf[0] = 0;
    if (!obj_ok(hero_data)) return NULL;
    void* bp = *(void**)((char*)hero_data + 0x48);
    if (obj_ok(bp)) {
        void* a = *(void**)((char*)bp + 0x70);
        if (read_str(a, buf, sizeof buf) && buf[0]) return buf;
    }
    void* f = ((void*(*)(void*,void*))(g_base + 0xE8D8A0))(hero_data, NULL);
    if (read_str(f, buf, sizeof buf) && buf[0]) return buf;
    return NULL;
}

// ============================================================================
// Card Portrait Decorator
//
// Hardened against non-HeroPortrait objects (such as HeroPortraitOverlay)
// to prevent heap corruption and segfaults.
// ============================================================================

void apply_hero_portrait_deco(void* hp) {
    if (!hp || !obj_ok(hp)) return;
    char hp_cname[64];
    if (!il2cpp_object_class(hp, hp_cname, sizeof(hp_cname)) || strcmp(hp_cname, "HeroPortrait") != 0) return;

    PROTECT({
        void* (*comp_get_go)(void*, void*) = (void*(*)(void*, void*))(g_base + 0x1B4BD28);
        void (*go_set_active)(void*, int, void*) = (void(*)(void*, int, void*))(g_base + 0x1B50CA8);
        void (*set_sprite_name)(void*, void*, void*) = (void(*)(void*, void*, void*))(g_base + 0x1E61320);

        // 1. Explicitly ensure progress bar (+0x210) is INACTIVE
        void* pbar = *(void**)((char*)hp + 0x210);
        if (pbar && obj_ok(pbar)) {
            void* pgo = comp_get_go(pbar, NULL);
            if (pgo && obj_ok(pgo)) go_set_active(pgo, 0, NULL);
        }

        // 2. Inspect hero_data (+0xE0)
        void* hero_data = *(void**)((char*)hp + 0xE0);
        if (!hero_data || !obj_ok(hero_data)) return;

        if (tftf_is_matrix_war_active()) {
            char bid_check[80]; bid_check[0] = 0;
            void* bid_str = *(void**)((char*)hero_data + 0x10);
            if (obj_ok(bid_str)) read_str(bid_str, bid_check, sizeof(bid_check));
            if (!bid_check[0] || strstr(bid_check, "rodimus") == NULL) {
                void* bp_chk = *(void**)((char*)hero_data + 0x48);
                if (obj_ok(bp_chk)) {
                    void* bps = *(void**)((char*)bp_chk + 0x10);
                    if (obj_ok(bps)) read_str(bps, bid_check, sizeof(bid_check));
                }
            }
            if (strstr(bid_check, "rodimus") == NULL) {
                void* hp_go = comp_get_go(hp, NULL);
                if (hp_go && obj_ok(hp_go)) {
                    go_set_active(hp_go, 0, NULL);
                    return;
                }
            }
        }

        // Ensure mUserOwned is 1 so any internal getters treat it as owned
        *(uint8_t*)((char*)hero_data + 0x68) = 1;

        // Ensure isRendering is 1
        *(uint8_t*)((char*)hp + 0xFA) = 1;

        // 3. Resolve rarity from blueprint (+0x48)
        int rarity = 5;
        void* bp = *(void**)((char*)hero_data + 0x48);
        if (!bp || !obj_ok(bp)) {
            void* bid = *(void**)((char*)hero_data + 0x10);
            if (bid && obj_ok(bid)) {
                bp = ((void*(*)(void*, void*))(g_base + 0xC1B364))(bid, NULL);
                if (bp && obj_ok(bp)) *(void**)((char*)hero_data + 0x48) = bp;
            }
        }
        if (bp && obj_ok(bp)) {
            int r = *(int*)((char*)bp + 0x64);
            if (r >= 1 && r <= 5) rarity = r;
        }

        // 4. Set rarity frame (HeroPortrait.SetRarityFrame @ 0xE91768)
        ((void(*)(void*, int, void*))(g_base + 0xE91768))(hp, rarity, NULL);

        if (!tftf_quest_is_leisure()) {
            char h_bid[80]; h_bid[0] = 0;
            void* bid_str = *(void**)((char*)hero_data + 0x10);
            if (obj_ok(bid_str)) read_str(bid_str, h_bid, sizeof(h_bid));
            if (!h_bid[0] && bp && obj_ok(bp)) {
                void* bps = *(void**)((char*)bp + 0x10);
                if (obj_ok(bps)) read_str(bps, h_bid, sizeof(h_bid));
            }
            if (h_bid[0]) {
                float h_ratio = tftf_quest_get_hero_hp_ratio_by_bid(h_bid);
                if (h_ratio <= 0.001f) {
                    *(uint8_t*)((char*)hp + 0x110) = 1; // _isClickDisabled
                    *(uint8_t*)((char*)hp + 0x111) = 1; // _isDragDisabled
                    *(uint8_t*)((char*)hp + 0x112) = 0; // _isKnockedOut (0 = dead)
                    *(float*)((char*)hp + 0x1c8) = 0.0f; // _healthPercentage
                    void* ko_tab = *(void**)((char*)hp + 0x178); // _knockedOutTab
                    if (obj_ok(ko_tab)) {
                        void* kogo = comp_get_go(ko_tab, NULL);
                        if (kogo && obj_ok(kogo)) go_set_active(kogo, 1, NULL);
                    }
                    void* act_tab = *(void**)((char*)hp + 0x180);
                    if (obj_ok(act_tab)) {
                        void* actgo = comp_get_go(act_tab, NULL);
                        if (actgo && obj_ok(actgo)) go_set_active(actgo, 0, NULL);
                    }
                } else {
                    *(uint8_t*)((char*)hp + 0x110) = 0; // _isClickDisabled
                    *(uint8_t*)((char*)hp + 0x111) = 0; // _isDragDisabled
                    *(uint8_t*)((char*)hp + 0x112) = 1; // _isKnockedOut (1 = alive)
                    *(float*)((char*)hp + 0x1c8) = h_ratio; // _healthPercentage
                    void* ko_tab = *(void**)((char*)hp + 0x178); // _knockedOutTab
                    if (obj_ok(ko_tab)) {
                        void* kogo = comp_get_go(ko_tab, NULL);
                        if (kogo && obj_ok(kogo)) go_set_active(kogo, 0, NULL);
                    }
                }
            }
        }

        // 5. Activate _frame UISprite (+0x240) and _portraitTexture (+0x260)
        void* frame_sprite = *(void**)((char*)hp + 0x240);
        if (frame_sprite && obj_ok(frame_sprite)) {
            void* fgo = comp_get_go(frame_sprite, NULL);
            if (fgo && obj_ok(fgo)) go_set_active(fgo, 1, NULL);
        }
        void* frame_tex = *(void**)((char*)hp + 0x260);
        if (frame_tex && obj_ok(frame_tex)) {
            void* tgo = comp_get_go(frame_tex, NULL);
            if (tgo && obj_ok(tgo)) go_set_active(tgo, 1, NULL);
        }

        // 5b. Activate mWingWangs container (+0x1E0)
        void* wing_wangs = *(void**)((char*)hp + 0x1E0);
        if (wing_wangs && obj_ok(wing_wangs)) {
            void* wgo = comp_get_go(wing_wangs, NULL);
            if (wgo && obj_ok(wgo)) go_set_active(wgo, 1, NULL);
        }

        // 6. Iterate child widgets (+0x1D8) and update data
        void* widgets_list = *(void**)((char*)hp + 0x1D8);
        if (widgets_list && obj_ok(widgets_list)) {
            int count = *(int*)((char*)widgets_list + 0x18);
            void* items = *(void**)((char*)widgets_list + 0x10);
            if (items && count > 0 && count < 32) {
                for (int i = 0; i < count; i++) {
                    void* w = *(void**)((char*)items + 0x20 + i * 8);
                    if (w && obj_ok(w)) {
                        void* wgo = comp_get_go(w, NULL);
                        if (wgo && obj_ok(wgo)) go_set_active(wgo, 1, NULL);

                        const char* cname = "<unknown>";
                        void* klass = *(void**)w;
                        if (klass && obj_ok(klass)) {
                            cname = *(const char**)((char*)klass + 0x10);
                        }

                        // Call SetData(hero_data) via interface vtable slot 0x1C8
                        void** vtable = (void**)klass;
                        if (vtable) {
                            typedef void (*set_data_fn)(void*, void*, void*);
                            set_data_fn fn = (set_data_fn)vtable[0x1C8 / 8];
                            void* minfo = vtable[0x1D0 / 8];
                            if (fn && (uintptr_t)fn >= g_base) {
                                fn(w, hero_data, minfo);
                            }
                        }

                        // If RarityWidget, explicitly activate and configure star GameObjects!
                        if (cname && strstr(cname, "RarityWidget")) {
                            void* star_str = g_strnew ? g_strnew("Star_white") : NULL;
                            for (int arr_idx = 0; arr_idx < 2; arr_idx++) {
                                void* stars_arr = *(void**)((char*)w + 0x20 + arr_idx * 8);
                                if (stars_arr && obj_ok(stars_arr)) {
                                    int n_stars = *(int*)((char*)stars_arr + 0x18);
                                    if (n_stars > 0 && n_stars <= 10) {
                                        for (int s = 0; s < n_stars; s++) {
                                            void* star_sp = *(void**)((char*)stars_arr + 0x20 + s * 8);
                                            if (star_sp && obj_ok(star_sp)) {
                                                void* sgo = comp_get_go(star_sp, NULL);
                                                if (sgo && obj_ok(sgo)) {
                                                    go_set_active(sgo, (s < rarity) ? 1 : 0, NULL);
                                                }
                                                if (s < rarity && star_str) {
                                                    set_sprite_name(star_sp, star_str, NULL);
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                            // Reposition aligners
                            void* aligner1 = *(void**)((char*)w + 0x40);
                            if (aligner1 && obj_ok(aligner1)) {
                                void* ago1 = comp_get_go(aligner1, NULL);
                                if (ago1 && obj_ok(ago1)) go_set_active(ago1, 1, NULL);
                                ((void(*)(void*, void*))(g_base + 0x1517F60))(aligner1, NULL);
                            }
                            void* aligner2 = *(void**)((char*)w + 0x48);
                            if (aligner2 && obj_ok(aligner2)) {
                                void* ago2 = comp_get_go(aligner2, NULL);
                                if (ago2 && obj_ok(ago2)) go_set_active(ago2, 1, NULL);
                                ((void(*)(void*, void*))(g_base + 0x1517F60))(aligner2, NULL);
                            }
                        }

                        // If RatingWidget, activate FactionLabel and paint the faction glyph ourselves.
                        if (cname && strstr(cname, "RatingWidget")) {
                            void* flabel = *(void**)((char*)w + 0x30);
                            if (flabel && obj_ok(flabel)) {
                                void* fgo = comp_get_go(flabel, NULL);
                                if (fgo && obj_ok(fgo)) go_set_active(fgo, 1, NULL);
                                char bid[80]; bid[0] = 0;
                                void* bstr = *(void**)((char*)hero_data + 0x10);
                                if (obj_ok(bstr)) read_str(bstr, bid, sizeof bid);
                                const char* faction = hero_faction_str(hero_data);
                                const char* glyph = faction_icon_glyph(faction);
                                char lcn[40]; lcn[0] = 0;
                                {   // diagnostic: what really sits at widget+0x30?
                                    void* fk = *(void**)flabel;
                                    if (obj_ok(fk)) {
                                        const char* n = *(const char**)((char*)fk + 0x10);
                                        if ((uintptr_t)n >= 0x100000) {
                                            int k = 0;
                                            for (; k < 39; k++) { char ch = n[k]; if (!ch || ch < 0x20 || ch >= 0x7f) break; lcn[k] = ch; }
                                            lcn[k] = 0;
                                        }
                                    }
                                }
                                if (glyph && g_strnew) {
                                    void* icon_str = g_strnew(glyph);
                                    if (icon_str) {
                                        ((void(*)(void*, void*, void*))(g_base + 0xDE127C))(flabel, icon_str, NULL);
                                        flog("RATEWGT %s faction='%s' glyph=U+%04X label=%p(%s) written",
                                             bid[0] ? bid : "?", faction ? faction : "<null>",
                                             (unsigned)faction_icon_code(faction), flabel, lcn);
                                    }
                                } else {
                                    int attr_raw = 0;
                                    void* bp2 = *(void**)((char*)hero_data + 0x48);
                                    if (obj_ok(bp2)) attr_raw = *(int*)((char*)bp2 + 0x70);
                                    flog("RATEWGT %s faction='%s' attr_raw=%d label=%p(%s) -> NO glyph, badge blank",
                                         bid[0] ? bid : "?", faction ? faction : "<null>", attr_raw, flabel, lcn);
                                }
                            }
                            void* r_align = *(void**)((char*)w + 0x38);
                            if (r_align && obj_ok(r_align)) {
                                void* ago = comp_get_go(r_align, NULL);
                                if (ago && obj_ok(ago)) go_set_active(ago, 1, NULL);
                                ((void(*)(void*, void*))(g_base + 0xDDE398))(r_align, NULL);
                            }
                        }
                    }
                }
            }
        }
    });
}

// ============================================================================
// Hook: HeroPortrait.RefreshFromData (Slot 33 @ 0x0E8DF9C)
//
// C# Signature: void RefreshFromData(HeroPortrait this)
// Register mapping:
//   x0: this (HeroPortrait*)
// Return: void
// Description:
//   Refreshes portrait display from HeroData. Validates object class to safely
//   ignore HeroPortraitOverlay and avoid null dereferences on empty slots.
// ============================================================================
void* hook_HeroPortrait_RefreshFromData(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (!a0 || !obj_ok(a0)) return NULL;

    char cname[64];
    if (!il2cpp_object_class(a0, cname, sizeof(cname)) || strcmp(cname, "HeroPortrait") != 0) {
        return H[33].orig ? H[33].orig(a0, a1, a2, a3, a4, a5, a6, a7) : NULL;
    }

    // Check hero_data (+0xE0)
    void* hero_data = *(void**)((char*)a0 + 0xE0);
    if (!hero_data || !obj_ok(hero_data)) {
        return NULL;
    }

    // Ensure blueprint (+0x48) is resolved before orig
    void* bp = *(void**)((char*)hero_data + 0x48);
    if (!bp || !obj_ok(bp)) {
        void* bid = *(void**)((char*)hero_data + 0x10);
        if (bid && obj_ok(bid)) {
            bp = ((void*(*)(void*, void*))(g_base + 0xC1B364))(bid, NULL);
            if (bp) *(void**)((char*)hero_data + 0x48) = bp;
        }
    }

    // In Matrix War, ensure non-Rodimus cards are hidden
    if (tftf_is_matrix_war_active()) {
        char bid[80]; bid[0] = 0;
        void* s10 = *(void**)((char*)hero_data + 0x10);
        if (obj_ok(s10)) read_str(s10, bid, sizeof(bid));
        if (!bid[0] || strstr(bid, "rodimus") == NULL) {
            if (bp && obj_ok(bp)) {
                void* bps = *(void**)((char*)bp + 0x10);
                if (obj_ok(bps)) read_str(bps, bid, sizeof(bid));
            }
        }
        if (strstr(bid, "rodimus") == NULL) {
            void* (*comp_get_go)(void*, void*) = (void*(*)(void*, void*))(g_base + 0x1B4BD28);
            void (*go_set_active)(void*, int, void*) = (void(*)(void*, int, void*))(g_base + 0x1B50CA8);
            void* go = comp_get_go(a0, NULL);
            if (go && obj_ok(go)) go_set_active(go, 0, NULL);
            return NULL;
        }
    }

    void* r = H[33].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    apply_hero_portrait_deco(a0);
    return r;
}

// ============================================================================
// Hook: HeroPortrait.SetEnabledItems (Slot 35 @ 0x0E8002C)
// ============================================================================
void* hook_HeroPortrait_SetEnabledItems(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = H[35].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    apply_hero_portrait_deco(a0);
    return r;
}

// ============================================================================
// Hook: HeroPortrait.LoadTexture (Slot 44 @ 0x0E910DC)
// ============================================================================
void* hook_HeroPortrait_LoadTexture(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    PROTECT( char b[300]; if(read_str(a1,b,sizeof b)) flog("TEXPATH %s", b); else flog("TEXPATH <null/empty>"); );
    return H[44].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// ============================================================================
// Hook: HeroPortrait.set_baseTexturePath (Slot 50 @ 0x0E85F70)
// ============================================================================
void* hook_HeroPortrait_set_baseTexturePath(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    PROTECT({
        char b[300] = {0};
        int ok = read_str(a1, b, sizeof b);
        if (!ok || b[0] == '\0') {
            if (g_strnew) {
                a1 = g_strnew("questboard/poster_special_act");
                flog("SETPATH <null/empty> -> redirected to questboard/poster_special_act for %p", a0);
            }
        } else {
            flog("SETPATH %s", b);
        }
    });
    return H[50].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// ============================================================================
// Hook: HeroPortrait.OnHeroTextureLoaded (Slot 46 @ 0x0E916B4)
// ============================================================================
void* hook_HeroPortrait_OnHeroTextureLoaded(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    PROTECT( uintptr_t hp=(uintptr_t)a0; int before=-1; char b[300]; b[0]=0;
        if(hp>=0x100000 && !(hp&7)){ before=*(unsigned char*)(hp+0x140);
            uintptr_t tex=*(uintptr_t*)(hp+0x260);
            if(tex>=0x100000 && !(tex&7)){ void* pth=*(void**)(tex+0x290); if(!read_str(pth,b,sizeof b)) strcpy(b,"<empty>"); } }
        flog("TEXDONE fired loadedWas=%d basePath=%s", before, b); );
    void* r = H[46].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT( uintptr_t hp=(uintptr_t)a0; int after=-1; if(hp>=0x100000 && !(hp&7)) after=*(unsigned char*)(hp+0x140);
        flog("TEXDONE loadedNow=%d", after); );
    apply_hero_portrait_deco(a0);
    return r;
}

// ============================================================================
// Hook: HeroPortrait.get_healthPercentage (Slot 167 @ 0x0E8F33C)
//
// C# Signature: float get_healthPercentage(HeroPortrait this)
// Return:
//   s0: float (health percentage, 0.0f to 1.0f)
// ============================================================================
float hook_HeroPortrait_get_healthPercentage(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (!tftf_quest_is_leisure()) {
        char bid[80]; bid[0] = 0;
        if (self && obj_ok(self)) {
            void* hero_data = *(void**)((char*)self + 0xE0);
            if (hero_data && obj_ok(hero_data)) {
                void* s10 = *(void**)((char*)hero_data + 0x10);
                if (obj_ok(s10)) read_str(s10, bid, sizeof(bid));
                if (!bid[0]) {
                    void* bp = *(void**)((char*)hero_data + 0x48);
                    if (obj_ok(bp)) {
                        void* bps = *(void**)((char*)bp + 0x10);
                        if (obj_ok(bps)) read_str(bps, bid, sizeof(bid));
                    }
                }
            }
        }
        float ratio = 1.0f;
        if (bid[0]) {
            ratio = tftf_quest_get_hero_hp_ratio_by_bid(bid);
        } else {
            ratio = tftf_quest_get_hero_hp_ratio(0);
        }
        if (ratio > 1.0f) ratio = 1.0f;
        if (ratio < 0.0f) ratio = 0.0f;
        static int s_log_hp167 = 0;
        if (s_log_hp167++ < 20) {
            flog("PORTRAIT_GET_HP (0x0E8F33C): hero='%s' -> ratio=%.2f", bid[0] ? bid : "?", ratio);
        }
        return ratio;
    }
    typedef float (*fn_orig)(void*, void*, void*, void*, void*, void*, void*, void*);
    return H[167].orig ? ((fn_orig)H[167].orig)(self, a1, a2, a3, a4, a5, a6, a7) : 1.0f;
}

// ============================================================================
// Blueprint Map Asset ID Map & Resolver (Slot 161 @ 0xC16688)
// ============================================================================
struct ArtBaseMap { const char* bid; const char* art; };
static const struct ArtBaseMap ART_BASE_MAP[] = {
    { "acidstorm_gs_leader2015", "acidstorm" },
    { "arcee_gs_deluxe2014", "arcee_gs" },
    { "barricade_cin_dotm", "barri_c" },
    { "bitstream_gs_leader2015", "bitstream" },
    { "blaster_gs_leader2016", "blastr_gs" },
    { "bludgeon_gs_rd20", "bludge_gs" },
    { "bonecrusher_cin_rotf", "bonec_c" },
    { "breakdown_gs", "breakdown" },
    { "breakdown", "breakdown" },
    { "bumblebee_cin_dotm", "bumbl_c" },
    { "bumblebee_gs_kabam", "bumbl_gs" },
    { "cheetor_bw_transmetal", "cheetor_bw" },
    { "chromia_gs_kabam", "chromia_gs" },
    { "cyclonus_gs_voyager2015", "cyclonus_gs" },
    { "deadend_gs_deluxe2015", "deadend_gs" },
    { "dinobot_bw_deluxe", "dinob_bw" },
    { "dirge_gs_deluxe2008", "dirge_gs" },
    { "dragstrip_gs_deluxe2016", "dragstrip" },
    { "dragstrip_gs", "dragstrip" },
    { "dragstrip", "dragstrip" },
    { "drift_cin_aoe", "drift_c" },
    { "drift_gs_kabam", "drift_gs" },
    { "fte_grimlock_cin_aoe", "grimlock_c" },
    { "fte_megatron_cin_dotm", "megatron_c_dotm" },
    { "fte_mixmaster_cin_rotf", "mixm_c" },
    { "fte_optimusprime_cin_aoe", "optimus_c" },
    { "fte_stars_gs_t3", "stars_gs" },
    { "galvatron_gs_voyager2016", "galva_gs" },
    { "grimlock_gs_deluxe2014", "grim_gs" },
    { "grindor_cin_rotf", "blackout_c" },
    { "hotlink_gs_leader2015", "hotlink" },
    { "hotrod_cin_tlk", "hotrod_c" },
    { "hound_cin_aoe", "hound_c" },
    { "ionstorm_gs_leader2015", "ionstorm" },
    { "ironhide_cin_dotm", "iron_c" },
    { "ironhide_gs_deluxe2015", "iron_gs" },
    { "jazz_cin_tf", "jazz_c" },
    { "jetfire_gs_leader2014", "jetfire_gs" },
    { "kickback_gs_deluxe2012", "kickb_gs" },
    { "lifeline_gs_deluxe2014", "lifeline" },
    { "lockdown_cin_aoe", "lockd_c" },
    { "megatron_cin_rotf", "megatron_c_rotf" },
    { "megatron_gs_leader2015", "megatron_gs" },
    { "megatronus_gs_kabam", "megatro_gs" },
    { "mirage_gs_deluxe2015", "mirage_gs" },
    { "mixmaster_cin_rotf", "mixm_c" },
    { "mods_amalgamousfocus_01", "amalgamousfocus" },
    { "mods_amalgamousfocus_02", "amalgamousfocus" },
    { "mods_amalgamousfocus_03", "amalgamousfocus" },
    { "mods_amalgamousfocus_04", "amalgamousfocus" },
    { "mods_amalgamousfocus_05", "amalgamousfocus" },
    { "mods_amalgamousfocus_06", "amalgamousfocus" },
    { "mods_antiarmorcharge", "antiarmorcharge" },
    { "mods_autofire", "autofire" },
    { "mods_base_laserbeam_01", "laserbeam" },
    { "mods_base_missiles_01", "missiles" },
    { "mods_base_railgun_01", "railgun" },
    { "mods_base_sonicblast_01", "sonicblast" },
    { "mods_bleedmodule", "bleedmodule" },
    { "mods_cleansemodule", "cleansemodule" },
    { "mods_countermeasure_01", "countermeasure" },
    { "mods_critmodule", "critmodule" },
    { "mods_damageburst", "damageburst" },
    { "mods_defensemodule", "defensemodule" },
    { "mods_emfield_01", "emfield" },
    { "mods_energonharvester_01", "energonharvester" },
    { "mods_harmaccelerator_01", "harmaccelerator" },
    { "mods_healingmodule", "healingmodule" },
    { "mods_laserbeam_01", "laserbeam" },
    { "mods_multiprocessor_01", "multiprocessor" },
    { "mods_nanites_01", "nanites" },
    { "mods_paralyzer_01", "paralyzer" },
    { "mods_powergainmodule", "powergainmodule" },
    { "mods_powershield_01", "powershield" },
    { "mods_precisionmodule", "precisionmodule" },
    { "mods_reinforcedarmor", "reinforcedarmor" },
    { "mods_repairmodule", "repairmodule" },
    { "mods_repulsor_01", "repulsor" },
    { "mods_resistancemodule", "resistancemodule" },
    { "mods_resourcemodule", "resourcemodule" },
    { "mods_revivemodule", "revivemodule" },
    { "mods_securitymodule", "securitymodule" },
    { "mods_shieldgenerator_01", "shieldgenerator" },
    { "mods_shockmodule", "shockmodule" },
    { "mods_specialistprotocol", "specialistprotocol" },
    { "mods_speedmodule", "speedmodule" },
    { "mods_stunmodule", "stunmodule" },
    { "mods_tacticianstrick_01", "tacticianstrick" },
    { "mods_tacticianstrick_02", "tacticianstrick" },
    { "mods_techconsole_01", "techconsole" },
    { "mods_warriorscall", "warriorscall" },
    { "motormaster_gs_voyager2015", "motorm_gs" },
    { "necrotronus_gs_kabam", "necrotro_gs" },
    { "nemesisprime_gs_voyager2015", "nemesis_p" },
    { "novastorm_gs_leader2015", "novastorm" },
    { "optimusprimal_bw_mp32", "oprimal_bw" },
    { "optimusprime_cin_tf", "optimus_c_tf" },
    { "optimusprime_sg_voyager2015", "optimus_sg" },
    { "prowl_gs_deluxe2016", "prowl_gs" },
    { "ramjet_gs_deluxe2008", "ramjet_gs" },
    { "ratchet_gs_kabam", "ratch_gs" },
    { "relic_alliance_victory", "relic_ave_t4" },
    { "relic_allspark", "allspark" },
    { "relic_ancient_tablet", "ancient_tablet" },
    { "relic_ancienthead", "ancienthead" },
    { "relic_blaster", "relic_blaster_t4" },
    { "relic_bumblebee", "relic_bumblebee_t4" },
    { "relic_cheetor", "relic_cheetor_t4" },
    { "relic_cloaking_field", "cloaking_field" },
    { "relic_covenant_primus", "covenant_primus" },
    { "relic_dark_energon_crystal", "dark_energon_crystal" },
    { "relic_fallen_titan_hand", "fallen_titan_hand" },
    { "relic_galvatron", "relic_galvatron_t4" },
    { "relic_goldendisk", "goldendisk" },
    { "relic_hound", "relic_hound_t4" },
    { "relic_immobilizer", "immobilizer" },
    { "relic_jazz", "relic_jazz_t4" },
    { "relic_kickback", "relic_kickback_t4" },
    { "relic_matrix_of_leadership", "matrix_of_leadership" },
    { "relic_megatron", "relic_megatron_t4" },
    { "relic_optimus_primal", "relic_optimus_primal_t4" },
    { "relic_origin_matrix", "origin_matrix" },
    { "relic_raid_champion", "relic_raid_t4" },
    { "relic_shattered_disk", "shattered_disk_t4" },
    { "relic_solus_forge", "solus_forge" },
    { "relic_stasis_generator", "stasis_generator" },
    { "relic_statue_hotrod", "statue_hotrod" },
    { "relic_statue_megatron", "statue_megatron" },
    { "relic_statue_op", "statue_op_c" },
    { "relic_statue_solus", "statue_solus_g" },
    { "relic_unstable_energon_crystal", "unstable_energon_crystal" },
    { "rhinox_gs_voyager2014", "rhino_bw" },
    { "rodimusprime_gs_mp09", "rodimus_gs" },
    { "scorponok_bw_kabam", "scorponok_bw" },
    { "sharkticon_gs_brawler", "npc_shark_braw" },
    { "sharkticon_gs_demolition", "npc_shark_demo" },
    { "sharkticon_gs_kabam", "npc_shark_gold" },
    { "sharkticon_gs_scout", "npc_shark_scou" },
    { "sharkticon_gs_tactician", "npc_shark_tact" },
    { "sharkticon_gs_tech", "npc_shark_tech" },
    { "sharkticon_gs_warrior", "npc_shark_warr" },
    { "shockwave_gs", "shock_c" },
    { "sideswipe_gs", "sides_gs" },
    { "skywarp_gs_leader2015", "skywarp_gs" },
    { "slipstream_gs", "slipstream_gs" },
    { "soundblaster_gs_mp13b", "soundblast_gs" },
    { "soundwave_gs", "sound_gs" },
    { "starsaber_gs_leader2014", "starsaber" },
    { "sunstorm_gs_leader2015", "sunstorm" },
    { "sunstreaker_gs_deluxe2008", "sunstreak_gs" },
    { "tantrum_gs_kabam", "tantrum_gs" },
    { "thrust_gs_deluxe2008", "thrust" },
    { "thundercracker_gs_leader2015", "thunder_gs" },
    { "ultramagnus_gs_leader", "ultram_gs" },
    { "ultramagnus_sg_leader", "ultram_sg" },
    { "ultramagnus_sg", "ultram_sg" },
    { "waspinator_gs_deluxe", "wasp_bw" },
    { "wheeljack_gs_mp20", "wheelj_gs" },
    { "wildrider_gs_deluxe2016", "wildrider" },
    { "wildrider_gs", "wildrider" },
    { "wildrider", "wildrider" },
    { "windblade_gs", "windb_gs" },
};
#define NUM_ART_BASE_MAP (int)(sizeof(ART_BASE_MAP)/sizeof(ART_BASE_MAP[0]))

static const char* resolve_art_base(const char* bid) {
    if (!bid || !*bid) return bid;
    for (int i = 0; i < NUM_ART_BASE_MAP; i++) {
        if (strcmp(ART_BASE_MAP[i].bid, bid) == 0) {
            return ART_BASE_MAP[i].art;
        }
    }
    return bid;
}

void* hook_BCGBlueprintBase_get_MapAssetID(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = H[161].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    if (!g_strnew) return r;
    char id[80]; id[0] = 0;
    if (r && read_str(r, id, sizeof(id)) && id[0]) {
        const char* art = resolve_art_base(id);
        if (art && strcmp(art, id) != 0) {
            LOG("GET_MAP_ASSET_ID(str): %s -> %s", id, art);
            return g_strnew(art);
        }
        return r;
    }
    if (obj_ok(a0)) {
        void* ch = *(void**)((char*)a0 + 0x28);
        if (ch && read_str(ch, id, sizeof(id)) && id[0]) {
            const char* art = resolve_art_base(id);
            if (art) {
                LOG("GET_MAP_ASSET_ID(ch): %s -> %s", id, art);
                return g_strnew(art);
            }
        }
        void* bid = *(void**)((char*)a0 + 0x10);
        if (bid && read_str(bid, id, sizeof(id)) && id[0]) {
            const char* art = resolve_art_base(id);
            if (art) {
                LOG("GET_MAP_ASSET_ID(id): %s -> %s", id, art);
                return g_strnew(art);
            }
        }
    }
    return r;
}

// ============================================================================
// Hook: BCGHelper.GetTopHeroId (Slot 164 @ 0xC1F2B8)
//
// Description:
//   Returns the current squad leader (team[0]) for the commander portrait button.
// ============================================================================
void* hook_BCGHelper_GetTopHeroId(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* leader_str = NULL;
    PROTECT({
        Team current_team;
        if (tftf_get_current_team(&current_team) && current_team.count > 0 && current_team.bid[0][0]) {
            const char* leader_bid = current_team.bid[0];
            leader_str = g_strnew ? g_strnew(leader_bid) : NULL;
            if (leader_str) {
                flog("GET_TOP_HERO_ID intercepted -> returning squad leader '%s'", leader_bid);
            }
        }
    });
    if (leader_str) {
        return leader_str;
    }
    return H[164].orig ? H[164].orig(a0, a1, a2, a3, a4, a5, a6, a7) : NULL;
}

// ============================================================================
// Hook: TransformersTopBarPresentation.OnHardCurrencyClick (Slot 173 @ 0x141CD54)
// ============================================================================
void* hook_TransformersTopBarPresentation_OnHardCurrencyClick(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    flog("ONHCCLICK: hard currency clicked (this=%p, go=%p) -> redirecting to OnResourceClick", a0, a1);
    if (g_base) {
        typedef void* (*OnResourceClick_fn)(void*, void*, void*);
        return ((OnResourceClick_fn)(g_base + 0x141F8F8))(a0, a1, a2);
    }
    return NULL;
}

// ============================================================================
// Hook: PayoutsModel.GetDefaultTabId (Slot 174 @ 0x0DA0720)
// ============================================================================
void* hook_PayoutsModel_GetDefaultTabId(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (!a1 || !obj_ok(a1)) {
        flog("GETDEFTAB: null tabs -> return NULL");
        return NULL;
    }
    int len = *(int*)((uintptr_t)a1 + 0x18);
    if (len <= 0) {
        flog("GETDEFTAB: empty tabs array (len=%d) -> return NULL", len);
        return NULL;
    }
    return H[174].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}
