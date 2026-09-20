#include "hook_combat.h"
#include "bot_info.h"

// ============================================================================
// Combat State Variables & Controllers
// ============================================================================

void* g_p0_controller = NULL;
void* g_p1_controller = NULL;
char g_p0_bot_id[80] = {0};
char g_p1_bot_id[80] = {0};
static volatile uint64_t g_p0_block_enter_ms = 0;
static volatile int g_p0_block_reset_done = 0;
static volatile int g_p0_after_heavy = 0;
static volatile int g_p0_combo_ended = 0;
void* g_p0_combat_character = NULL;
void* g_p1_combat_character = NULL;
volatile float g_p0_max_hp = 50000.0f;
volatile float g_p1_max_hp = 50000.0f;
volatile float g_p0_last_hp = -1.0f;
volatile float g_p1_last_hp = -1.0f;

// Timestamp of the last P0 attack action (1 / 4 / 32). GATE-04: clears chain after idle window
static volatile uint64_t g_p0_last_attack_ms = 0;
#define COMBO_IDLE_RESET_MS 900

int g_last_enemy_pi = 3000;
static float g_last_enemy_hp = 50000.0f;
static float g_last_enemy_atk = 2500.0f;

static float g_combat_enemy_mana_gain = 0.5f;
static float g_combat_player_mana_gain = 1.0f;

static int g_propgoact_lines = 0;
static int g_sp3move_lines = 0;
static int g_sp3cand_dumped = 0;
static int g_sp3cand_lines = 0;

// Input buffer window fallback for hook_58
#define SETACT_FALLBACK_WINDOW 0.2f
static inline float game_clock(void) {
    if (!g_base) return -1.0f;
    typedef float (*fn_time)(void);
    return ((fn_time)(g_base + 0x1B86184))(); // UnityEngine.Time.get_time
}

// ============================================================================
// Vector3 & Touch Helpers
// ============================================================================

typedef struct {
    float x;
    float y;
    float z;
} Vector3_t;

static volatile int g_intended_special_tier = 0;
static volatile uint64_t g_intended_special_time_ms = 0;
static volatile int g_sp_touch_tracking = 0;
static float g_sp_touch_start_x = 0.0f;
static float g_sp_touch_start_y = 0.0f;
static uint64_t g_sp_touch_start_ms = 0;
static volatile int g_sp_btn_pressed_fired = 0;
static volatile int g_sp_dispatching_internal = 0;

static inline Vector3_t unity_get_mouse_position(void) {
    typedef Vector3_t (*fn_mouse_pos)(void);
    return ((fn_mouse_pos)(g_base + 0x21BC1D4))();
}

static inline int unity_get_screen_width(void) {
    typedef int (*fn_screen_dim)(void);
    return ((fn_screen_dim)(g_base + 0x16AFBF8))();
}

static inline int unity_get_screen_height(void) {
    typedef int (*fn_screen_dim)(void);
    return ((fn_screen_dim)(g_base + 0x16AFC2C))();
}

static inline int power_meter_can_use_special(void* power_meter, int tier) {
    if (!obj_ok(power_meter)) return 0;
    typedef int (*fn_can_use_sp)(void*, int, void*);
    return ((fn_can_use_sp)(g_base + 0xDACE1C))(power_meter, tier, NULL);
}

static inline void trigger_special_action(void* controller) {
    if (!obj_ok(controller)) return;
    g_sp_dispatching_internal = 1;
    H[154].orig(controller, (void*)(intptr_t)0x200, NULL, NULL, NULL, NULL, NULL, NULL);
    g_sp_dispatching_internal = 0;
}

static inline void ensure_p0_power_rounding(void* pc) {
    if (!obj_ok(pc)) return;
    if (pc != g_p0_controller && *(int32_t*)((uintptr_t)pc + 0xF4) != 0) return;
    void* pm = *(void**)((char*)pc + 0x80);
    if (!obj_ok(pm)) return;
    void* fm = *(void**)((char*)pm + 0x70);
    if (!obj_ok(fm)) return;
    typedef float (*fn_get_cur)(void*, void*);
    typedef void (*fn_set_cur)(void*, float, void*);
    fn_get_cur get_cur = (fn_get_cur)(g_base + 0xE2FF20);
    fn_set_cur set_cur = (fn_set_cur)(g_base + 0xE2FF70);
    float cur = get_cur(fm, NULL);
    if (cur >= 0.32f && cur <= 0.3339f) {
        set_cur(fm, 0.34f, NULL);
        flog("POWER_ROUNDING: cur=%.5f -> boosted to 0.34f (SP1 full green)", cur);
    } else if (cur >= 0.65f && cur <= 0.6675f) {
        set_cur(fm, 0.67f, NULL);
        flog("POWER_ROUNDING: cur=%.5f -> boosted to 0.67f (SP2 full green)", cur);
    }
}

void hook_combat_process_touch(uintptr_t pressed, uintptr_t unpressed) {
    if (obj_ok(g_p0_controller) && tftf_get_enable_swipe_specials()) {
        PROTECT({
            Vector3_t mpos = unity_get_mouse_position();
            int sw = unity_get_screen_width();
            int sh = unity_get_screen_height();
            if (sw <= 0) sw = 1920;
            if (sh <= 0) sh = 1080;

            if (pressed) {
                if (mpos.x >= 0 && mpos.x <= 0.28f * (float)sw && mpos.y >= 0 && mpos.y <= 0.35f * (float)sh) {
                    g_sp_touch_tracking = 1;
                    g_sp_touch_start_x = mpos.x;
                    g_sp_touch_start_y = mpos.y;
                    g_sp_touch_start_ms = propgo_now_ms();
                    g_sp_btn_pressed_fired = 0;
                    flog("SP_TOUCH DOWN at (%.1f, %.1f) [screen %dx%d]", mpos.x, mpos.y, sw, sh);
                } else {
                    g_sp_touch_tracking = 0;
                }
            } else if (g_sp_touch_tracking) {
                uint64_t elapsed = propgo_now_ms() - g_sp_touch_start_ms;
                float dx = mpos.x - g_sp_touch_start_x;
                float dy = mpos.y - g_sp_touch_start_y;

                if (dx > 35.0f && dx > fabsf(dy)) {
                    flog("SP_GESTURE: SWIPE RIGHT (SP1) dx=%.1f dy=%.1f elapsed=%llu ms",
                         dx, dy, (unsigned long long)elapsed);
                    g_intended_special_tier = 1;
                    g_intended_special_time_ms = propgo_now_ms();
                    g_sp_touch_tracking = 0;
                    trigger_special_action(g_p0_controller);
                } else if (dy > 35.0f && dy > fabsf(dx)) {
                    flog("SP_GESTURE: SWIPE UP (SP2) dx=%.1f dy=%.1f elapsed=%llu ms",
                         dx, dy, (unsigned long long)elapsed);
                    g_intended_special_tier = 2;
                    g_intended_special_time_ms = propgo_now_ms();
                    g_sp_touch_tracking = 0;
                    trigger_special_action(g_p0_controller);
                } else if (unpressed) {
                    flog("SP_GESTURE: TAP RELEASE (MAX SP) dx=%.1f dy=%.1f elapsed=%llu ms",
                         dx, dy, (unsigned long long)elapsed);
                    g_intended_special_tier = 0;
                    g_intended_special_time_ms = propgo_now_ms();
                    g_sp_touch_tracking = 0;
                    trigger_special_action(g_p0_controller);
                } else if (elapsed > 350) {
                    flog("SP_GESTURE: HOLD TIMEOUT (MAX SP) dx=%.1f dy=%.1f elapsed=%llu ms",
                         dx, dy, (unsigned long long)elapsed);
                    g_intended_special_tier = 0;
                    g_intended_special_time_ms = propgo_now_ms();
                    g_sp_touch_tracking = 0;
                    trigger_special_action(g_p0_controller);
                }
            }
        });
    }
}

// ============================================================================
// Attack Chain Management & Reset
// ============================================================================

void reset_player_attack_chain(void* pc) {
    if (!obj_ok(pc)) return;
    int32_t p_idx = *(int32_t*)((uintptr_t)pc + 0xF4);
    if (p_idx != 0) return; // local player P0 only
    g_p0_controller = pc;
    g_p0_last_attack_ms = 0;                 // the idle window restarts from the next attack
    *(uint32_t*)((uintptr_t)pc + 0x1c0) = 0; // _lightAttackIndex = 0
    *(uint32_t*)((uintptr_t)pc + 0x1c4) = 0; // _mediumAttackIndex = 0
    *(uint32_t*)((uintptr_t)pc + 0x1c8) = 0; // _rangedAttackIndex = 0
    flog("RESET_ATTACK_CHAIN on p0 pc=%p (caller=%p)", pc, __builtin_return_address(0));
}

// ============================================================================
// SP3 Cinematic Engine & Prop Mirroring
// ============================================================================

#define SP3_MAX_INTERVALS 4
typedef struct {
    int count;
    int on_ms[SP3_MAX_INTERVALS];
    int off_ms[SP3_MAX_INTERVALS];
} SP3ActiveTiming;

static SP3ActiveTiming g_current_sp3_timing = {
    .count = 1,
    .on_ms = {1000},
    .off_ms = {2500}
};

#define SP3_MAX_PROPS 8
typedef struct {
    char name[32];
    int count;
    int on_ms[SP3_MAX_INTERVALS];
    int off_ms[SP3_MAX_INTERVALS];
    void* prop_ptr;
    int is_active;
} SP3PropTiming;

static int g_sp3_prop_timing_count = 0;
static SP3PropTiming g_sp3_prop_timings[SP3_MAX_PROPS];

static void* g_sp3_xf[4];
static void* g_sp3_xf_props[8];
static int g_sp3_xf_capture_props = 0;
static uint64_t g_sp3_xf_since_ms = 0;
static int g_sp3_anim_played = 0;
static int g_sp3_xf_timeout_logged = 0;
static int g_sp3_beat_du_ms = 800;
static int g_sp3_alt_on_ms  = 1000;
static int g_sp3_alt_off_ms = 2500;
static int g_sp3_beat_form = -1;
static int g_sp3_beat_ticks = 0;
static int g_sp3_beat_lines = 0;
static int g_propgoinv_lines = 0;
static int g_sp3xhold_lines = 0;

static void sp3_xf_props_clear(void) {
    for (int i = 0; i < 8; i++) g_sp3_xf_props[i] = NULL;
}

static int sp3_xf_props_has(void* prop) {
    if (!prop) return 0;
    for (int i = 0; i < 8; i++) if (g_sp3_xf_props[i] == prop) return 1;
    return 0;
}

static void sp3_xf_props_add(void* prop) {
    if (!prop || sp3_xf_props_has(prop)) return;
    for (int i = 0; i < 8; i++) if (!g_sp3_xf_props[i]) { g_sp3_xf_props[i] = prop; return; }
}

static int sp3_xf_any(void) {
    for (int i = 0; i < 4; i++) if (g_sp3_xf[i]) return 1;
    return 0;
}

static int sp3_xf_has(void* pc) {
    if (!pc) return 0;
    for (int i = 0; i < 4; i++) if (g_sp3_xf[i] == pc) return 1;
    return 0;
}

static void sp3_xf_add(void* pc) {
    if (!pc) return;
    if (sp3_xf_has(pc)) return;
    for (int i = 0; i < 4; i++) if (!g_sp3_xf[i]) {
        g_sp3_xf[i] = pc;
        g_sp3_xf_since_ms = propgo_now_ms();
        g_sp3_xf_timeout_logged = 0;
        return;
    }
}

static void sp3_xf_remove(void* pc) {
    if (!pc) return;
    for (int i = 0; i < 4; i++) if (g_sp3_xf[i] == pc) g_sp3_xf[i] = NULL;
    if (!sp3_xf_any()) {
        sp3_xf_props_clear();
        g_sp3_xf_since_ms = 0;
        g_sp3_anim_played = 0;
        g_sp3_xf_capture_props = 0;
        g_sp3_beat_form = -1;
    }
}

static void sp3_xf_clear(void) {
    for (int i = 0; i < 4; i++) g_sp3_xf[i] = NULL;
    sp3_xf_props_clear();
    g_sp3_prop_timing_count = 0;
    g_sp3_xf_capture_props = 0;
    g_sp3_xf_since_ms = 0;
    g_sp3_anim_played = 0;
    g_sp3_xf_timeout_logged = 0;
    g_sp3_beat_form = -1;
}

typedef void (*propgo_set_bool_t)(void*,int,void*);
static int sp3_prop_mirror(void* prop, int on) {
    int applied = 0;
    void* arr = *(void**)((char*)prop + 0x70);
    if (obj_ok(arr)) {
        int n = *(int32_t*)((char*)arr + 0x18);
        if (n > 0 && n <= 256) for (int i = 0; i < n; i++) {
            void* rr = *(void**)((char*)arr + 0x20 + 8 * i);
            if (obj_ok(rr)) {
                void* go = ((fn8)(g_base + 0x1B4BD28))(rr, NULL, NULL, NULL, NULL, NULL, NULL, NULL);
                if (obj_ok(go)) {
                    ((propgo_set_bool_t)(g_base + 0x1B50CA8))(go, on, NULL);
                    applied++;
                }
            }
        }
    }
    return applied;
}

static void sp3_set_default_timing(void) {
    g_current_sp3_timing.count = 1;
    g_current_sp3_timing.on_ms[0] = 1000;
    g_current_sp3_timing.off_ms[0] = 2500;
    g_sp3_alt_on_ms = 1000;
    g_sp3_alt_off_ms = 2500;
    g_sp3_prop_timing_count = 0;
    memset(g_sp3_prop_timings, 0, sizeof(g_sp3_prop_timings));
}

static int sp3_parse_intervals_from_json(const char* json_str, const char* bot_id) {
    if (!json_str || !bot_id || !bot_id[0]) return 0;

    const char* p = NULL;
    char search_id[80];
    strncpy(search_id, bot_id, sizeof(search_id) - 1);
    search_id[sizeof(search_id) - 1] = 0;

    while (search_id[0]) {
        char quoted[96];
        snprintf(quoted, sizeof(quoted), "\"%s\"", search_id);
        p = strstr(json_str, quoted);
        if (p) break;
        p = strstr(json_str, search_id);
        if (p) break;

        char* last_under = strrchr(search_id, '_');
        if (last_under) {
            *last_under = 0;
        } else {
            break;
        }
    }

    if (!p) {
        p = strstr(json_str, "\"_default\"");
        if (!p) p = strstr(json_str, "_default");
    }
    if (!p) return 0;

    const char* block_start = strchr(p, '{');
    if (!block_start) return 0;

    const char* cur_b = block_start + 1;
    int brace_depth = 1;
    const char* block_end = NULL;
    while (*cur_b && brace_depth > 0) {
        if (*cur_b == '{') brace_depth++;
        else if (*cur_b == '}') {
            brace_depth--;
            if (brace_depth == 0) {
                block_end = cur_b;
                break;
            }
        }
        cur_b++;
    }
    if (!block_end) return 0;

    const char* inv = strstr(block_start, "\"intervals\"");
    if (!inv || inv > block_end) return 0;

    const char* arr_start = strchr(inv, '[');
    if (!arr_start || arr_start > block_end) return 0;

    const char* inv_cur = arr_start + 1;
    int inv_arr_depth = 1;
    const char* outer_inv_end = NULL;
    while (*inv_cur && inv_cur < block_end && inv_arr_depth > 0) {
        if (*inv_cur == '[') inv_arr_depth++;
        else if (*inv_cur == ']') {
            inv_arr_depth--;
            if (inv_arr_depth == 0) { outer_inv_end = inv_cur; break; }
        }
        inv_cur++;
    }

    int count = 0;
    const char* cur = arr_start + 1;
    while (outer_inv_end && cur < outer_inv_end && count < SP3_MAX_INTERVALS) {
        const char* sub_start = strchr(cur, '[');
        if (!sub_start || sub_start > outer_inv_end) break;
        int on_val = 0, off_val = 0;
        if (sscanf(sub_start + 1, "%d , %d", &on_val, &off_val) == 2 ||
            sscanf(sub_start + 1, "%d ,%d", &on_val, &off_val) == 2 ||
            sscanf(sub_start + 1, "%d,%d", &on_val, &off_val) == 2) {
            g_current_sp3_timing.on_ms[count] = on_val;
            g_current_sp3_timing.off_ms[count] = off_val;
            count++;
        }
        const char* sub_end = strchr(sub_start, ']');
        if (!sub_end || sub_end > outer_inv_end) break;
        cur = sub_end + 1;
    }

    if (count > 0) {
        g_current_sp3_timing.count = count;
        g_sp3_alt_on_ms = g_current_sp3_timing.on_ms[0];
        g_sp3_alt_off_ms = g_current_sp3_timing.off_ms[0];
    } else {
        return 0;
    }

    g_sp3_prop_timing_count = 0;
    const char* props_kw = strstr(block_start, "\"props\"");
    if (props_kw && props_kw < block_end) {
        const char* p_obj_start = strchr(props_kw, '{');
        if (p_obj_start && p_obj_start < block_end) {
            const char* cur_pb = p_obj_start + 1;
            int p_depth = 1;
            const char* p_obj_end = NULL;
            while (*cur_pb && cur_pb < block_end && p_depth > 0) {
                if (*cur_pb == '{') p_depth++;
                else if (*cur_pb == '}') {
                    p_depth--;
                    if (p_depth == 0) { p_obj_end = cur_pb; break; }
                }
                cur_pb++;
            }
            if (p_obj_end) {
                const char* cur_p = p_obj_start + 1;
                while (cur_p < p_obj_end && g_sp3_prop_timing_count < SP3_MAX_PROPS) {
                    const char* q1 = strchr(cur_p, '\"');
                    if (!q1 || q1 >= p_obj_end) break;
                    const char* q2 = strchr(q1 + 1, '\"');
                    if (!q2 || q2 >= p_obj_end) break;
                    size_t nlen = (size_t)(q2 - (q1 + 1));
                    if (nlen > 0 && nlen < 32) {
                        char pname[32];
                        memcpy(pname, q1 + 1, nlen);
                        pname[nlen] = 0;

                        const char* colon = strchr(q2, ':');
                        if (!colon || colon >= p_obj_end) break;
                        const char* arr_open = strchr(colon, '[');
                        if (!arr_open || arr_open >= p_obj_end) break;

                        const char* scur = arr_open + 1;
                        int arr_depth = 1;
                        const char* outer_arr_end = NULL;
                        while (*scur && scur < p_obj_end && arr_depth > 0) {
                            if (*scur == '[') arr_depth++;
                            else if (*scur == ']') {
                                arr_depth--;
                                if (arr_depth == 0) { outer_arr_end = scur; break; }
                            }
                            scur++;
                        }

                        int p_cnt = 0;
                        int p_on[SP3_MAX_INTERVALS];
                        int p_off[SP3_MAX_INTERVALS];
                        const char* pcur = arr_open + 1;
                        while (outer_arr_end && pcur < outer_arr_end && p_cnt < SP3_MAX_INTERVALS) {
                            const char* ssub = strchr(pcur, '[');
                            if (!ssub || ssub >= outer_arr_end) break;
                            int on_v = 0, off_v = 0;
                            if (sscanf(ssub + 1, "%d , %d", &on_v, &off_v) == 2 ||
                                sscanf(ssub + 1, "%d ,%d", &on_v, &off_v) == 2 ||
                                sscanf(ssub + 1, "%d,%d", &on_v, &off_v) == 2) {
                                if (on_v > 0 || off_v > 0) {
                                    p_on[p_cnt] = on_v;
                                    p_off[p_cnt] = off_v;
                                    p_cnt++;
                                }
                            }
                            const char* ssub_end = strchr(ssub, ']');
                            if (!ssub_end || ssub_end > outer_arr_end) break;
                            pcur = ssub_end + 1;
                        }

                        if (p_cnt > 0) {
                            SP3PropTiming* pt = &g_sp3_prop_timings[g_sp3_prop_timing_count++];
                            strncpy(pt->name, pname, sizeof(pt->name) - 1);
                            pt->name[sizeof(pt->name) - 1] = 0;
                            pt->count = p_cnt;
                            for (int k = 0; k < p_cnt; k++) {
                                pt->on_ms[k] = p_on[k];
                                pt->off_ms[k] = p_off[k];
                            }
                            pt->prop_ptr = NULL;
                            pt->is_active = 0;
                            flog("SP3WEAPON_CFG name=%s active_intervals=%d on0=%d off0=%d",
                                 pt->name, pt->count, pt->on_ms[0], pt->off_ms[0]);
                        } else {
                            SP3PropTiming* pt = &g_sp3_prop_timings[g_sp3_prop_timing_count++];
                            strncpy(pt->name, pname, sizeof(pt->name) - 1);
                            pt->name[sizeof(pt->name) - 1] = 0;
                            pt->count = 0;
                            pt->prop_ptr = NULL;
                            pt->is_active = 0;
                            flog("SP3WEAPON_CFG name=%s force_hidden", pt->name);
                        }

                        if (outer_arr_end) cur_p = outer_arr_end + 1;
                        else cur_p = q2 + 1;
                    } else {
                        cur_p = q2 + 1;
                    }
                }
            }
        }
    }

    flog("SP3CFG bot=%s intervals=%d on0=%d off0=%d weapon_props=%d",
         bot_id, g_current_sp3_timing.count, g_sp3_alt_on_ms, g_sp3_alt_off_ms, g_sp3_prop_timing_count);
    return 1;
}

static void sp3_load_timing_for_character(const char* bot_id) {
    sp3_set_default_timing();
    if (!bot_id || !bot_id[0]) return;

    const char* hot_paths[] = {
        "/data/data/com.kabam.bigrobot/files/sp3_timings.json",
        "/sdcard/Android/media/com.kabam.bigrobot/sp3_timings.json",
        "/sdcard/Download/sp3_timings.json",
        "/storage/emulated/0/Download/sp3_timings.json",
        "/data/local/tmp/sp3_timings.json"
    };

    for (size_t hi = 0; hi < sizeof(hot_paths)/sizeof(hot_paths[0]); hi++) {
        FILE* fp = fopen(hot_paths[hi], "rb");
        if (fp) {
            fseek(fp, 0, SEEK_END);
            long len = ftell(fp);
            fseek(fp, 0, SEEK_SET);
            if (len > 10 && len < 262144) {
                char* buf = (char*)malloc(len + 1);
                if (buf) {
                    size_t read_bytes = fread(buf, 1, len, fp);
                    buf[read_bytes] = 0;
                    if (sp3_parse_intervals_from_json(buf, bot_id)) {
                        flog("SP3CFG loaded from %s for %s", hot_paths[hi], bot_id);
                        free(buf);
                        fclose(fp);
                        return;
                    }
                    free(buf);
                }
            }
            fclose(fp);
        }
    }

    // 2. Try loading from APK in-app Payload @sp3_timings
    size_t payload_len = 0;
    const unsigned char* pdata = tftf_payload_lookup("@sp3_timings", &payload_len);
    if (pdata && payload_len > 10) {
        char* pbuf = (char*)malloc(payload_len + 1);
        if (pbuf) {
            memcpy(pbuf, pdata, payload_len);
            pbuf[payload_len] = 0;
            if (sp3_parse_intervals_from_json(pbuf, bot_id)) {
                flog("SP3TIMING: loaded from @sp3_timings payload for %s (intervals=%d on0=%d off0=%d)",
                     bot_id, g_current_sp3_timing.count, g_current_sp3_timing.on_ms[0], g_current_sp3_timing.off_ms[0]);
                free(pbuf);
                return;
            }
            free(pbuf);
        }
    }

    // 3. Built-in C fallback table
    if (strstr(bot_id, "optimusprime")) {
        g_current_sp3_timing.count = 1;
        g_current_sp3_timing.on_ms[0] = 1150;
        g_current_sp3_timing.off_ms[0] = 3200;
    } else if (strstr(bot_id, "starscream")) {
        g_current_sp3_timing.count = 1;
        g_current_sp3_timing.on_ms[0] = 850;
        g_current_sp3_timing.off_ms[0] = 2650;
    } else if (strstr(bot_id, "bumblebee")) {
        g_current_sp3_timing.count = 1;
        g_current_sp3_timing.on_ms[0] = 1300;
        g_current_sp3_timing.off_ms[0] = 2900;
    } else if (strstr(bot_id, "motormaster")) {
        g_current_sp3_timing.count = 2;
        g_current_sp3_timing.on_ms[0] = 566;   g_current_sp3_timing.off_ms[0] = 2766;
        g_current_sp3_timing.on_ms[1] = 4000;  g_current_sp3_timing.off_ms[1] = 4966;
    } else if (strstr(bot_id, "tantrum")) {
        g_current_sp3_timing.count = 1;
        g_current_sp3_timing.on_ms[0] = 933;   g_current_sp3_timing.off_ms[0] = 4933;
    } else if (strstr(bot_id, "cyclonus")) {
        g_current_sp3_timing.count = 1;
        g_current_sp3_timing.on_ms[0] = 1100;  g_current_sp3_timing.off_ms[0] = 2500;
    } else if (strstr(bot_id, "mirage")) {
        g_current_sp3_timing.count = 1;
        g_current_sp3_timing.on_ms[0] = 1166;  g_current_sp3_timing.off_ms[0] = 2700;
    }
    g_sp3_alt_on_ms = g_current_sp3_timing.on_ms[0];
    g_sp3_alt_off_ms = g_current_sp3_timing.off_ms[0];
    flog("SP3TIMING: used fallback for %s: count=%d on0=%d off0=%d",
         bot_id, g_current_sp3_timing.count, g_current_sp3_timing.on_ms[0], g_current_sp3_timing.off_ms[0]);
}

static int sp3_beat_form_at(uint64_t elapsed_ms) {
    for (int i = 0; i < g_current_sp3_timing.count; i++) {
        if (elapsed_ms >= (uint64_t)g_current_sp3_timing.on_ms[i] &&
            elapsed_ms < (uint64_t)g_current_sp3_timing.off_ms[i]) {
            return 1;
        }
    }
    return 0;
}

static void sp3_beat_apply(int alt) {
    PROTECT({
        for (int i = 0; i < 8; i++) {
            void* prop = g_sp3_xf_props[i];
            if (!obj_ok(prop)) continue;
            char name[64];
            name[0] = 0;
            void* str_obj = *(void**)((char*)prop + 0x10);
            if (!obj_ok(str_obj)) continue;
            read_str(str_obj, name, sizeof name);
            int want;
            if (!strcmp(name, "transformed")) want = alt;
            else if (!strcmp(name, "character_model")) want = !alt;
            else continue;
            ((void(*)(void*,int,void*,void*,void*,void*,void*,void*))H[138].orig)
                (prop, want, NULL, NULL, NULL, NULL, NULL, NULL);
            int n = sp3_prop_mirror(prop, want);
            flog("SP3BEAT_PROP name=%s want=%d n=%d pgo=%p", name, want, n, *(void**)((char*)prop + 0x60));
            if (!g_sp3_anim_played && alt && want && !strcmp(name, "transformed") && g_strnew) {
                void* st = g_strnew("SpecialAttack03");
                if (st) ((void(*)(void*,void*,void*))(g_base + 0xEA05B4))(prop, st, NULL);
                void* st2 = g_strnew("Base.SpecialAttack03");
                if (st2) ((void(*)(void*,void*,void*))(g_base + 0xEA05B4))(prop, st2, NULL);
                g_sp3_anim_played = 1;
            }
        }
    });
    if (g_sp3_beat_lines < 40) {
        g_sp3_beat_lines++;
        flog("SP3BEAT apply alt=%d on=%d off=%d tms=%llu", alt, g_sp3_alt_on_ms,
             g_sp3_alt_off_ms, (unsigned long long)propgo_now_ms());
    }
}

static void sp3_beat_pump(void) {
    if (!g_sp3_xf_since_ms) return;
    uint64_t now = propgo_now_ms();
    uint64_t elapsed = now - g_sp3_xf_since_ms;
    if (elapsed > 12000u) return;
    g_sp3_beat_ticks++;
    int want = sp3_beat_form_at(elapsed);
    if (want != g_sp3_beat_form) {
        g_sp3_beat_form = want;
        sp3_beat_apply(want);
    }
    for (int i = 0; i < g_sp3_prop_timing_count; i++) {
        SP3PropTiming* pt = &g_sp3_prop_timings[i];
        if (!obj_ok(pt->prop_ptr)) continue;
        int prop_want = 0;
        for (int k = 0; k < pt->count; k++) {
            if (elapsed >= (uint64_t)pt->on_ms[k] && elapsed < (uint64_t)pt->off_ms[k]) {
                prop_want = 1;
                break;
            }
        }
        if (prop_want != pt->is_active) {
            pt->is_active = prop_want;
            ((void(*)(void*,int,void*,void*,void*,void*,void*,void*))H[138].orig)
                (pt->prop_ptr, prop_want, NULL, NULL, NULL, NULL, NULL, NULL);
            sp3_prop_mirror(pt->prop_ptr, prop_want);
            flog("SP3WEAPON_BEAT prop=%s want=%d elapsed=%llu", pt->name, prop_want, (unsigned long long)elapsed);
        }
    }
}

static int sp3move_events_xform(void* move, int* nev) {
    if (nev) *nev = -1;
    if (!obj_ok(move)) return 0;
    void* events = fld_p(move, 0x28);
    int n = list_count(events);
    void* items = fld_p(events, 0x10);
    if (nev) *nev = n;
    if (!obj_ok(items) || n <= 0) return 0;
    int alen = *(int32_t*)((char*)items + 0x18);
    if (alen < 0 || alen > 256 || n > alen || n > 256) return 0;
    for (int i = 0; i < n; i++) {
        void* event = *(void**)((char*)items + 0x20 + 8 * i);
        if (!obj_ok(event)) continue;
        char cls[64];
        il2cpp_object_class(event, cls, sizeof cls);
        if (!strcmp(cls, "TransformMoveEvent")) return 1;
    }
    return 0;
}

static int sp3_ci_has(const char* hay, const char* needle) {
    if (!hay || !needle) return 0;
    if (!*needle) return 1;
    for (; *hay; hay++) {
        const char* h = hay;
        const char* n = needle;
        while (*h && *n) {
            char hc = *h, nc = *n;
            if (hc >= 'A' && hc <= 'Z') hc = (char)(hc - 'A' + 'a');
            if (nc >= 'A' && nc <= 'Z') nc = (char)(nc - 'A' + 'a');
            if (hc != nc) break;
            h++; n++;
        }
        if (!*n) return 1;
    }
    return 0;
}

static int sp3_is_excluded(const char* name, const char* anim) {
    static const char* words[] = {"hitreaction","hit_reaction","flinch","stagger","knock","stun","dizzy",
                                  "getup","idle","block","parry","death","victory","entrance","taunt",
                                  "intro","outro","respawn"};
    for (unsigned int i = 0; i < sizeof(words)/sizeof(words[0]); i++)
        if (sp3_ci_has(name, words[i]) || sp3_ci_has(anim, words[i])) return 1;
    return 0;
}

static void sp3_beat_capture(void* move) {
    void* events = fld_p(move, 0x28);
    int n = list_count(events);
    void* items = fld_p(events, 0x10);
    if (!obj_ok(items) || n <= 0) return;
    int alen = *(int32_t*)((char*)items + 0x18);
    if (alen < 0 || alen > 256 || n > alen || n > 256) return;
    for (int i = 0; i < n; i++) {
        void* event = *(void**)((char*)items + 0x20 + 8 * i);
        if (!obj_ok(event)) continue;
        char cls[64];
        cls[0] = 0;
        il2cpp_object_class(event, cls, sizeof cls);
        if (strcmp(cls, "TransformMoveEvent")) continue;
        float du = *(float*)((char*)event + 0x58);
        int du_ms = (int)(du * 1000.0f);
        if (du_ms < 400) du_ms = 400;
        if (du_ms > 3000) du_ms = 3000;
        g_sp3_beat_du_ms = du_ms;
        if (g_sp3_beat_lines < 40) {
            g_sp3_beat_lines++;
            flog("SP3BEAT src du=%d tms=%llu", du_ms, (unsigned long long)propgo_now_ms());
        }
        return;
    }
}

#ifndef TFTF_ENABLE_MAX_POWER_TEST
#define TFTF_ENABLE_MAX_POWER_TEST 0
#endif

static void give_p0_max_power(void) {
#if TFTF_ENABLE_MAX_POWER_TEST
    if (sp3_xf_any()) return;
    if (!g_p0_controller || !obj_ok(g_p0_controller)) return;
    PROTECT({
        void* c80 = *(void**)((char*)g_p0_controller + 0x80);
        if (obj_ok(c80)) {
            void* spec = *(void**)((char*)c80 + 0x70);
            if (obj_ok(spec) && g_base) {
                ((void(*)(void*, float, void*))(g_base + 0xE2FE60))(spec, 99999.0f, NULL);
            }
        }
    });
#endif
}

// ============================================================================
// Enemy Stats Calculation & Tuning
// ============================================================================

static void calc_enemy_stats_all(const char* bid, int rank, int level, float* out_hp, float* out_atk, int* out_pi) {
    int hp = 42000, atk = 2300, rating = 44300;
    if (bid && *bid) {
        for (int i = 0; i < NUM_ENEMY_STATS; i++) {
            if (strcmp(ENEMY_STATS[i].id, bid) == 0) {
                hp = ENEMY_STATS[i].hp;
                atk = ENEMY_STATS[i].atk;
                rating = ENEMY_STATS[i].rating;
                break;
            }
        }
    }
    if (out_hp) *out_hp = (float)hp;
    if (out_atk) *out_atk = (float)atk;
    if (out_pi) *out_pi = rating;
}

int calc_enemy_rating(const char* bid, int rank, int level) {
    int pi = 0;
    calc_enemy_stats_all(bid, rank, level, NULL, NULL, &pi);
    return pi;
}

static void load_combat_tuning_config(void) {
    const char* hot_paths[] = {
        "/data/data/com.kabam.bigrobot/files/sp3_timings.json",
        "/sdcard/Android/media/com.kabam.bigrobot/sp3_timings.json",
        "/sdcard/Download/sp3_timings.json",
        "/storage/emulated/0/Download/sp3_timings.json",
        "/data/local/tmp/sp3_timings.json"
    };
    for (size_t hi = 0; hi < sizeof(hot_paths)/sizeof(hot_paths[0]); hi++) {
        FILE* fp = fopen(hot_paths[hi], "rb");
        if (fp) {
            fseek(fp, 0, SEEK_END);
            long len = ftell(fp);
            fseek(fp, 0, SEEK_SET);
            if (len > 10 && len < 262144) {
                char* buf = (char*)malloc(len + 1);
                if (buf) {
                    size_t read_bytes = fread(buf, 1, len, fp);
                    buf[read_bytes] = 0;
                    const char* p_enemy = strstr(buf, "\"enemy_mana_gain\"");
                    if (p_enemy) {
                        const char* colon = strchr(p_enemy, ':');
                        if (colon) {
                            float val = 0.5f;
                            if (sscanf(colon + 1, "%f", &val) == 1 && val >= 0.0f && val <= 10.0f) {
                                g_combat_enemy_mana_gain = val;
                            }
                        }
                    }
                    const char* p_player = strstr(buf, "\"player_mana_gain\"");
                    if (p_player) {
                        const char* colon = strchr(p_player, ':');
                        if (colon) {
                            float val = 1.0f;
                            if (sscanf(colon + 1, "%f", &val) == 1 && val >= 0.0f && val <= 10.0f) {
                                g_combat_player_mana_gain = val;
                            }
                        }
                    }
                    free(buf);
                }
            }
            fclose(fp);
            return;
        }
    }
}

// ============================================================================
// Hook Handlers Implementation
// ============================================================================

// Slot 56: PlayerAttributes.Init
void* hook_PlayerAttributes_Init(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    PROTECT({
        ensure_empty_tags();
        uintptr_t fd = (uintptr_t)a3;
        uintptr_t ofd = (uintptr_t)a4;
        void* bp1 = (fd >= 0x100000 && !(fd & 7)) ? *(void**)(fd + 0x40) : 0;
        void* bp2 = (ofd >= 0x100000 && !(ofd & 7)) ? *(void**)(ofd + 0x40) : 0;
        void* t1a = (bp1 && ((uintptr_t)bp1 >= 0x100000) && !((uintptr_t)bp1 & 7)) ? *(void**)((uintptr_t)bp1 + 0xB8) : (void*)-1;
        void* t2a = (bp2 && ((uintptr_t)bp2 >= 0x100000) && !((uintptr_t)bp2 & 7)) ? *(void**)((uintptr_t)bp2 + 0xB8) : (void*)-1;
        fix_blueprint_tags(bp1);
        fix_blueprint_tags(bp2);
        void* t1b = (bp1 && ((uintptr_t)bp1 >= 0x100000) && !((uintptr_t)bp1 & 7)) ? *(void**)((uintptr_t)bp1 + 0xB8) : (void*)-1;
        void* t2b = (bp2 && ((uintptr_t)bp2 >= 0x100000) && !((uintptr_t)bp2 & 7)) ? *(void**)((uintptr_t)bp2 + 0xB8) : (void*)-1;
        char id1[80]; char id2[80]; id1[0] = id2[0] = 0;
        if (!read_str(fld_p(bp1, 0x10), id1, sizeof id1)) strcpy(id1, "<null>");
        if (!read_str(fld_p(bp2, 0x10), id2, sizeof id2)) strcpy(id2, "<null>");
        void* at1 = fld_p((void*)fd, 0x30); void* at2 = fld_p((void*)ofd, 0x30);
        void* ch1 = fld_p((void*)fd, 0x38); void* ch2 = fld_p((void*)ofd, 0x38);
        int player_idx = obj_ok(a1) ? *(int32_t*)((uintptr_t)a1 + 0xF4) : -1;
        if (player_idx == 0 || g_p0_controller == NULL) {
            g_p0_controller = a1;
            strncpy(g_p0_bot_id, id1, sizeof(g_p0_bot_id) - 1);
            g_p0_bot_id[sizeof(g_p0_bot_id) - 1] = 0;
            if (id2[0] && strcmp(id2, "<null>") != 0 && !g_p1_bot_id[0]) {
                strncpy(g_p1_bot_id, id2, sizeof(g_p1_bot_id) - 1);
                g_p1_bot_id[sizeof(g_p1_bot_id) - 1] = 0;
            }
        } else {
            g_p1_controller = a1;
            strncpy(g_p1_bot_id, id1, sizeof(g_p1_bot_id) - 1);
            g_p1_bot_id[sizeof(g_p1_bot_id) - 1] = 0;
        }
        load_combat_tuning_config();
        int32_t cur_hp = (at1 && obj_ok(at1)) ? *(int32_t*)((char*)at1 + 0x2C) : 0;
        if (player_idx == 1 || (player_idx != 0 && cur_hp <= 0)) {
            float hp_f = 50000.0f;
            float atk_f = 2500.0f;
            int pi = 3000;
            calc_enemy_stats_all(id1, 5, 50, &hp_f, &atk_f, &pi);
            if (g_current_is_10x_challenge) {
                float mult = tftf_get_challenge_hp_multiplier();
                if (mult <= 0.05f) mult = 1.0f;
                float atk_mult = (mult <= 1.5f) ? 0.8f : ((mult >= 9.0f) ? 1.25f : 1.0f);
                hp_f *= mult;
                atk_f *= atk_mult;
                pi = (int)(hp_f + atk_f) / 20;
            }
            float enemy_hp_ratio = 1.0f;
            if (!tftf_quest_is_leisure() && tftf_quest_has_pending_enemy()) {
                enemy_hp_ratio = tftf_quest_get_pending_enemy_hp_ratio();
                if (enemy_hp_ratio < 0.05f) enemy_hp_ratio = 0.05f;
                if (enemy_hp_ratio > 1.0f) enemy_hp_ratio = 1.0f;
            }
            int32_t hp = (int32_t)hp_f;
            int32_t atk = (int32_t)atk_f;
            g_last_enemy_pi = pi;
            g_last_enemy_hp = hp_f;
            g_last_enemy_atk = atk_f;
            if (at1 && obj_ok(at1)) {
                *(int32_t*)((char*)at1 + 0x28) = 3;     // SpecialAttackCount
                *(int32_t*)((char*)at1 + 0x2C) = hp;    // HPMax
                *(int32_t*)((char*)at1 + 0x30) = hp;    // HPMaxBase
                *(float*)  ((char*)at1 + 0x34) = enemy_hp_ratio; // HP (normalized)
                *(int32_t*)((char*)at1 + 0x38) = atk;   // Attack
                *(int32_t*)((char*)at1 + 0x3C) = atk;   // AttackBase
                *(float*)  ((char*)at1 + 0x40) = 0.0f;  // Armor
                *(float*)  ((char*)at1 + 0x44) = 0.5f;  // CritChance
                *(float*)  ((char*)at1 + 0x48) = 1.5f;  // CritDamage
                *(float*)  ((char*)at1 + 0x50) = 0.5f;  // BlockProficiency
                *(float*)  ((char*)at1 + 0x54) = g_combat_enemy_mana_gain;
                *(int32_t*)((char*)at1 + 0x58) = 0;     // ManaStart
            }
            if (at2 && obj_ok(at2)) {
                *(int32_t*)((char*)at2 + 0x58) = 0;
                *(float*)  ((char*)at2 + 0x44) = 0.5f;
                *(float*)  ((char*)at2 + 0x54) = g_combat_player_mana_gain;
            }
            if (ch1 && obj_ok(ch1)) {
                *(int32_t*)((char*)ch1 + 0x28) = 3;     // NumSpecials
                *(int32_t*)((char*)ch1 + 0x2C) = hp;
                *(int32_t*)((char*)ch1 + 0x30) = hp;
                *(float*)  ((char*)ch1 + 0x34) = enemy_hp_ratio;
                *(int32_t*)((char*)ch1 + 0x38) = atk;
                *(int32_t*)((char*)ch1 + 0x3C) = atk;
                *(float*)  ((char*)ch1 + 0x58) = 1.0f;
            }
            LOG("FIXFIGHT_STATS: player=%d bp=%s filled hp=%d (ratio=%.2f) atk=%d pi=%d enemy_mana_gain=%.2f challenge_mult=%.1f",
                 player_idx, id1, hp, enemy_hp_ratio, atk, pi, g_combat_enemy_mana_gain, tftf_get_challenge_hp_multiplier());
        } else if (player_idx == 0) {
            if (at1 && obj_ok(at1)) {
                *(float*)((char*)at1 + 0x44) = 0.5f;                      // Player 0 CritChance
                *(float*)((char*)at1 + 0x48) = 1.5f;                      // Player 0 CritDamage
                const char* cur_qid = tftf_quest_get_current_qid();
                int is_fembots = (cur_qid && strcmp(cur_qid, "1.1.6") == 0);
                if (is_fembots) {
                    *(float*)  ((char*)at1 + 0x54) = 0.0f;
                    *(int32_t*)((char*)at1 + 0x58) = 0;
                    *(int32_t*)((char*)at1 + 0x28) = 0;
                    flog("FIXFIGHT: Fembots (1.1.6) disabled player special attacks and mana gain!");
                } else {
                    *(float*)((char*)at1 + 0x54) = g_combat_player_mana_gain;
                }
                if (!tftf_quest_is_leisure()) {
                    float hp_ratio = tftf_quest_get_hero_hp_ratio_by_bid(id1);
                    if (hp_ratio > 1.0f) hp_ratio = 1.0f;
                    if (hp_ratio <= 0.0f) hp_ratio = 0.0f;
                    *(float*)((char*)at1 + 0x34) = hp_ratio;
                    if (hp_ratio <= 0.0f) {
                        *(int32_t*)((char*)at1 + 0x2C) = 0;
                    }
                } else {
                    float cur_norm_hp = *(float*)((char*)at1 + 0x34);
                    if (cur_norm_hp <= 0.0f || cur_hp <= 0) {
                        flog("FIXFIGHT: reviving Player 0 HP from %f (max=%d) to 1.0f", cur_norm_hp, cur_hp);
                        *(float*)((char*)at1 + 0x34) = 1.0f;
                        if (cur_hp <= 0) {
                            *(int32_t*)((char*)at1 + 0x2C) = 50000;
                            *(int32_t*)((char*)at1 + 0x30) = 50000;
                        }
                    }
                }
                float bp = *(float*)((char*)at1 + 0x50);
                if (bp <= 0.0f || bp > 1.0f) {
                    *(float*)((char*)at1 + 0x50) = 0.5f;
                }
            }
            if (at2 && obj_ok(at2)) {
                *(float*)((char*)at2 + 0x44) = 1.0f;
                *(float*)((char*)at2 + 0x54) = g_combat_enemy_mana_gain;
            }
            if (ch1 && obj_ok(ch1)) {
                const char* cur_qid = tftf_quest_get_current_qid();
                int is_fembots = (cur_qid && strcmp(cur_qid, "1.1.6") == 0);
                if (is_fembots) {
                    *(int32_t*)((char*)ch1 + 0x28) = 0;
                }
                if (!tftf_quest_is_leisure()) {
                    float hp_ratio = tftf_quest_get_hero_hp_ratio_by_bid(id1);
                    if (hp_ratio > 1.0f) hp_ratio = 1.0f;
                    if (hp_ratio <= 0.0f) hp_ratio = 0.0f;
                    *(float*)((char*)ch1 + 0x34) = hp_ratio;
                } else {
                    if (*(float*)((char*)ch1 + 0x34) <= 0.0f) {
                        *(float*)((char*)ch1 + 0x34) = 1.0f;
                    }
                }
                *(float*)((char*)ch1 + 0x58) = 1.0f;
            }
            LOG("FIXFIGHT_STATS: player=0 bp=%s set crit_chance=%.2f at1=%p at2=%p",
                id1, at1 ? *(float*)((char*)at1 + 0x44) : -1.0f, at1, at2);
        }
        flog("FIXFIGHT player=%d bp1=%s msa=%d attr.specials=%d tags:%p->%p  bp2=%s msa=%d attr.specials=%d tags:%p->%p",
             player_idx, id1, obj_ok(bp1)?*(int32_t*)((uintptr_t)bp1+0xAC):-1,
             obj_ok(at1)?*(int32_t*)((uintptr_t)at1+0x28):-1, t1a, t1b, id2,
             obj_ok(bp2)?*(int32_t*)((uintptr_t)bp2+0xAC):-1, obj_ok(at2)?*(int32_t*)((uintptr_t)at2+0x28):-1, t2a, t2b);
    });
    void* r = H[56].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        if (a0 && obj_ok(a0)) {
            int player_idx = obj_ok(a1) ? *(int32_t*)((uintptr_t)a1 + 0xF4) : -1;
            if (player_idx == 0) {
                const char* cur_qid = tftf_quest_get_current_qid();
                int is_fembots = (cur_qid && strcmp(cur_qid, "1.1.6") == 0);
                if (is_fembots) {
                    typedef void (*fn_set_mana)(void*, float, void*);
                    fn_set_mana set_mana = (fn_set_mana)(g_base + 0xDAC774);
                    set_mana(a0, 0.0f, NULL);
                }
                g_p0_combat_character = a0;
                typedef float (*fn_get_max)(void*, void*);
                fn_get_max get_max = (fn_get_max)(g_base + 0xDAC698);
                float max_val = get_max(a0, NULL);
                if (max_val > 0.0f) g_p0_max_hp = max_val;

                if (!tftf_quest_is_leisure()) {
                    float hp_ratio = tftf_quest_get_hero_hp_ratio_by_bid(g_p0_bot_id);
                    if (hp_ratio > 1.0f) hp_ratio = 1.0f;
                    if (hp_ratio <= 0.0f) hp_ratio = 0.0f;
                    typedef void (*fn_set_norm)(void*, float, void*);
                    fn_set_norm set_norm = (fn_set_norm)(g_base + 0xDAC720);
                    set_norm(a0, hp_ratio, NULL);
                    typedef float (*fn_get_hp)(void*, void*);
                    fn_get_hp get_hp = (fn_get_hp)(g_base + 0xDAC6CC);
                    g_p0_last_hp = get_hp(a0, NULL);
                    flog("FIXFIGHT: Player 0 '%s' combat HP initialized to %.1f / %.1f (ratio=%.2f)",
                         g_p0_bot_id, g_p0_last_hp, g_p0_max_hp, hp_ratio);
                } else {
                    typedef float (*fn_get_hp)(void*, void*);
                    fn_get_hp get_hp = (fn_get_hp)(g_base + 0xDAC6CC);
                    float cur_hp_val = get_hp(a0, NULL);
                    if (cur_hp_val <= 0.0f) {
                        typedef void (*fn_set_norm)(void*, float, void*);
                        fn_set_norm set_norm = (fn_set_norm)(g_base + 0xDAC720);
                        set_norm(a0, 1.0f, NULL);
                        cur_hp_val = get_hp(a0, NULL);
                    }
                    g_p0_last_hp = cur_hp_val;
                }
            } else if (player_idx == 1) {
                g_p1_combat_character = a0;
                typedef float (*fn_get_max)(void*, void*);
                fn_get_max get_max = (fn_get_max)(g_base + 0xDAC698);
                float max_val = get_max(a0, NULL);
                if (max_val > 0.0f) g_p1_max_hp = max_val;

                if (!tftf_quest_is_leisure() && tftf_quest_has_pending_enemy()) {
                    float enemy_hp_ratio = tftf_quest_get_pending_enemy_hp_ratio();
                    if (enemy_hp_ratio < 0.05f) enemy_hp_ratio = 0.05f;
                    if (enemy_hp_ratio > 1.0f) enemy_hp_ratio = 1.0f;
                    typedef void (*fn_set_norm)(void*, float, void*);
                    fn_set_norm set_norm = (fn_set_norm)(g_base + 0xDAC720);
                    set_norm(a0, enemy_hp_ratio, NULL);
                    typedef float (*fn_get_hp)(void*, void*);
                    fn_get_hp get_hp = (fn_get_hp)(g_base + 0xDAC6CC);
                    g_p1_last_hp = get_hp(a0, NULL);
                    flog("FIXFIGHT: Enemy '%s' combat HP initialized to %.1f / %.1f (ratio=%.2f)",
                         g_p1_bot_id, g_p1_last_hp, g_p1_max_hp, enemy_hp_ratio);
                } else {
                    typedef float (*fn_get_hp)(void*, void*);
                    fn_get_hp get_hp = (fn_get_hp)(g_base + 0xDAC6CC);
                    g_p1_last_hp = get_hp(a0, NULL);
                }
            }
        }
    });
    return r;
}

// Slot 57: HashSet<T>..ctor
static int g_fixhs_logged = 0;
void* hook_HashSet_ctor(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (a1 == NULL) {
        PROTECT(
            ensure_empty_tags();
            if (!g_fixhs_logged) {
                g_fixhs_logged = 1;
                flog("FIXHS null-collection -> empty (empty=%p)", g_empty_tags);
            }
        );
        if (g_empty_tags) a1 = g_empty_tags;
    }
    return H[57].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// Slot 58: PlayerInput.QueuedAction.SetAction
void* hook_PlayerInput_QueuedAction_SetAction(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = H[58].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        uintptr_t q = (uintptr_t)a0;
        float clk = game_clock();
        if (q >= 0x100000 && !(q & 7) && clk >= 0) {
            float ts = *(float*)(q + 0x14);
            static int diagnostics = 0;
            if (ts - clk > 0.01f) {
                if (diagnostics < 4) { diagnostics++; flog("SETACTFIX config window=%.3f (kept)", ts - clk); }
            } else {
                *(float*)(q + 0x14) = clk + SETACT_FALLBACK_WINDOW;
                if (diagnostics < 4) { diagnostics++; flog("SETACTFIX no config window, fallback=%.3f", (float)SETACT_FALLBACK_WINDOW); }
            }
        }
    });
    return r;
}

// Slot 138: PropData.SetActiveInternal
void* hook_PropData_SetActiveInternal(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    char name[64]; name[0] = 0;
    int propgo_special = 0;
    int req = (intptr_t)a1 ? 1 : 0;
    PROTECT({
        if (obj_ok(a0)) read_str(*(void**)((char*)a0 + 0x10), name, sizeof name);
        if (!strcmp(name, "character_model") || !strcmp(name, "transformed")) {
            propgo_special = 1;
            if (g_sp3_xf_capture_props) sp3_xf_props_add(a0);
            if (sp3_xf_props_has(a0) && g_sp3_xf_since_ms) {
                uint64_t now = propgo_now_ms();
                if (now - g_sp3_xf_since_ms > 12000u) {
                    if (!g_sp3_xf_timeout_logged) {
                        g_sp3_xf_timeout_logged = 1;
                        flog("SP3XFIX timeout tms=%llu", (unsigned long long)now);
                    }
                    sp3_xf_clear();
                } else {
                    int alt = sp3_beat_form_at(now - g_sp3_xf_since_ms);
                    int forced = !strcmp(name, "transformed") ? alt : !alt;
                    if (req != forced) {
                        if (g_propgoinv_lines < 500) {
                            g_propgoinv_lines++;
                            flog("PROPGOINV prop=%s req=%d forced=%d tms=%llu", name, req, forced, (unsigned long long)now);
                        }
                        a1 = (void*)(intptr_t)forced;
                    }
                }
            }
        }
    });
    void* r = H[138].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        int on = (intptr_t)a1 ? 1 : 0;
        int applied = sp3_prop_mirror(a0, on);
        if (applied > 0 && g_propgoact_lines < 500) {
            g_propgoact_lines++;
            flog("PROPGOACT prop=%s on=%d n=%d tms=%llu", name, on, applied, (unsigned long long)propgo_now_ms());
        }
        if (propgo_special) {
            if (on && !g_sp3_anim_played && g_sp3_xf_since_ms && sp3_xf_props_has(a0)
                    && !strcmp(name, "transformed") && g_strnew) {
                void* st = g_strnew("SpecialAttack03");
                if (st) {
                    g_sp3_anim_played = 1;
                    ((void(*)(void*,void*,void*))(g_base + 0xEA05B4))(a0, st, NULL);
                    void* st2 = g_strnew("Base.SpecialAttack03");
                    if (st2) ((void(*)(void*,void*,void*))(g_base + 0xEA05B4))(a0, st2, NULL);
                    flog("SP3ANIM prop=%s state=SpecialAttack03 anim=%p tms=%llu",
                         name, fld_p(a0, 0x68), (unsigned long long)propgo_now_ms());
                }
            }
        }
    });
    return r;
}

// Slot 139: MoveSet.GetMove
void* hook_MoveSet_GetMove(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = H[139].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    if (r) return r;
    PROTECT({
        int32_t hash = (int32_t)(intptr_t)a1;
        if (hash == -1919714467 || hash == -2049617737) {
            void* moves = fld_p(a0, 0x18);
            void* items = fld_p(moves, 0x10);
            int n = list_count(moves);
            if (obj_ok(items) && n > 0) {
                int alen = *(int32_t*)((char*)items + 0x18);
                if (alen >= 0 && alen <= 256 && n <= alen && n <= 256) {
                    void* chosen = NULL; int rank = 0; int nev = -1; int xform = 0;
                    if (!g_sp3cand_dumped) {
                        g_sp3cand_dumped = 1;
                        for (int i = 0; i < n; i++) {
                            void* move = *(void**)((char*)items + 0x20 + 8 * i);
                            if (!obj_ok(move)) continue;
                            char name[96]; char anim[96]; name[0] = anim[0] = 0;
                            read_str(fld_p(move, 0x10), name, sizeof name);
                            read_str(fld_p(move, 0x18), anim, sizeof anim);
                            int this_nev = -1;
                            int this_xform = sp3move_events_xform(move, &this_nev);
                            if ((this_xform || !strncmp(anim, "Base.Special", 12)) && g_sp3cand_lines < 40) {
                                g_sp3cand_lines++;
                                flog("SP3CAND i=%d name=%s anim=%s nev=%d xform=%d excl=%d tms=%llu", i, name, anim,
                                     this_nev, this_xform, sp3_is_excluded(name, anim), (unsigned long long)propgo_now_ms());
                            }
                        }
                    }
                    for (int want = 1; want <= 5 && !chosen; want++) {
                        for (int i = 0; i < n; i++) {
                            void* move = *(void**)((char*)items + 0x20 + 8 * i);
                            if (!obj_ok(move)) continue;
                            char name[96]; char anim[96]; name[0] = anim[0] = 0;
                            read_str(fld_p(move, 0x10), name, sizeof name);
                            read_str(fld_p(move, 0x18), anim, sizeof anim);
                            int this_nev = -1;
                            if (!sp3move_events_xform(move, &this_nev)) continue;
                            if (sp3_is_excluded(name, anim)) continue;
                            int match = (want == 1 && !strcmp(anim, "Base.SpecialAttack02")) ||
                                        (want == 2 && !strcmp(anim, "Base.SpecialAttack01")) ||
                                        (want == 3 && !strcmp(anim, "Base.HeavyAttack")) ||
                                        (want == 4 && !strncmp(anim, "Base.SpecialAttack", 18)) ||
                                        (want == 5 && (sp3_ci_has(name, "heavy") || sp3_ci_has(anim, "heavy") ||
                                                       sp3_ci_has(name, "medium") || sp3_ci_has(anim, "medium") ||
                                                       sp3_ci_has(name, "light") || sp3_ci_has(anim, "light") ||
                                                       sp3_ci_has(name, "combo") || sp3_ci_has(anim, "combo") ||
                                                       sp3_ci_has(name, "attack") || sp3_ci_has(anim, "attack")));
                            if (match) { chosen = move; rank = want; nev = this_nev; xform = 1; break; }
                        }
                    }
                    if (!chosen) {
                        int best_nev = -1;
                        for (int i = 0; i < n; i++) {
                            void* move = *(void**)((char*)items + 0x20 + 8 * i);
                            if (!obj_ok(move)) continue;
                            char name[96]; char anim[96]; name[0] = anim[0] = 0;
                            read_str(fld_p(move, 0x10), name, sizeof name);
                            read_str(fld_p(move, 0x18), anim, sizeof anim);
                            int this_nev = -1;
                            if (!sp3move_events_xform(move, &this_nev) || sp3_is_excluded(name, anim)) continue;
                            if (this_nev > best_nev) { chosen = move; rank = 6; nev = this_nev; xform = 1; best_nev = this_nev; }
                        }
                    }
                    for (int want = 7; want <= 8 && !chosen; want++) {
                        const char* target = (want == 7) ? "Base.SpecialAttack02" : "Base.SpecialAttack01";
                        for (int i = 0; i < n; i++) {
                            void* move = *(void**)((char*)items + 0x20 + 8 * i);
                            if (!obj_ok(move)) continue;
                            char name[96]; char anim[96]; name[0] = anim[0] = 0;
                            read_str(fld_p(move, 0x10), name, sizeof name);
                            read_str(fld_p(move, 0x18), anim, sizeof anim);
                            if (!sp3_is_excluded(name, anim) && !strcmp(anim, target)) {
                                chosen = move; rank = want; nev = -1; xform = sp3move_events_xform(move, &nev); break;
                            }
                        }
                    }
                    char name[96]; char anim[96]; name[0] = anim[0] = 0;
                    if (chosen) {
                        read_str(fld_p(chosen, 0x10), name, sizeof name);
                        read_str(fld_p(chosen, 0x18), anim, sizeof anim);
                        r = chosen;
                    } else {
                        strcpy(name, "none"); strcpy(anim, "none");
                    }
                    if (g_sp3move_lines < 20) {
                        g_sp3move_lines++;
                        flog("SP3MOVE hash=%d rank=%d name=%s anim=%s nev=%d xform=%d tms=%llu", hash, rank,
                             name, anim, nev, xform, (unsigned long long)propgo_now_ms());
                    }
                    if (chosen) sp3_beat_capture(chosen);
                }
            }
        }
    });
    return r;
}

// Slot 140: Simulation.RegisterComponents
void* hook_Simulation_RegisterComponents(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    flog("COMBAT_START: Simulation.RegisterComponents -> all P0 combo state cleared");
    sp3_xf_clear();
    g_p0_controller = NULL;
    g_p1_controller = NULL;
    g_intended_special_tier = 0;
    g_sp_touch_tracking = 0;
    g_p0_block_enter_ms = 0;
    g_p0_block_reset_done = 0;
    g_p0_after_heavy = 0;
    g_p0_combo_ended = 0;
    g_p0_last_attack_ms = 0;
    return H[140].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// Slot 141: PlayerController.Transform
void* hook_PlayerController_Transform(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    PROTECT({
        if (sp3_xf_has(a0) && !(uintptr_t)a1) {
            if (g_sp3xhold_lines < 200) {
                g_sp3xhold_lines++;
                flog("SP3XHOLD pc=%p tms=%llu", a0, (unsigned long long)propgo_now_ms());
            }
            a1 = (void*)1;
        }
    });
    return H[141].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// Slot 142: PlayerCinematicSpecialAttackState.OnEnter
void* hook_PlayerCinematicSpecialAttackState_OnEnter(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = H[142].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        void* pc = fld_p(a0, 0x18);
        if (obj_ok(pc)) {
            if (pc == g_p0_controller) {
                g_intended_special_tier = 0;
            }
            const char* current_bot_id = (pc == g_p0_controller) ? g_p0_bot_id : g_p1_bot_id;
            if (!current_bot_id || !current_bot_id[0]) {
                if (g_p0_bot_id[0]) current_bot_id = g_p0_bot_id;
                else if (g_p1_bot_id[0]) current_bot_id = g_p1_bot_id;
            }
            flog("SP3XFIX enter pc=%p bot_id=%s tms=%llu", pc, current_bot_id ? current_bot_id : "unknown",
                 (unsigned long long)propgo_now_ms());

            sp3_load_timing_for_character(current_bot_id);

            sp3_xf_add(pc);
            g_sp3_beat_form = 0;
            g_sp3_beat_ticks = 0;
            g_sp3_anim_played = 0;
            g_sp3_beat_lines = 0;
            g_propgoact_lines = 0;
            g_propgoinv_lines = 0;
            flog("SP3SCHED intervals=%d on0=%d off0=%d tms=%llu", g_current_sp3_timing.count,
                 g_sp3_alt_on_ms, g_sp3_alt_off_ms, (unsigned long long)propgo_now_ms());

            sp3_xf_props_clear();
            void* cpm = *(void**)((char*)pc + 0x90);
            if (obj_ok(cpm) && g_strnew) {
                void* prop_trans = ((void*(*)(void*,void*,void*))(g_base + 0xEA16C0))(cpm, g_strnew("transformed"), NULL);
                void* prop_char  = ((void*(*)(void*,void*,void*))(g_base + 0xEA16C0))(cpm, g_strnew("character_model"), NULL);
                if (prop_trans) sp3_xf_props_add(prop_trans);
                if (prop_char)  sp3_xf_props_add(prop_char);
                flog("SP3PROPS cpm=%p trans=%p char=%p", cpm, prop_trans, prop_char);

                for (int pi = 0; pi < g_sp3_prop_timing_count; pi++) {
                    void* p = ((void*(*)(void*,void*,void*))(g_base + 0xEA16C0))(cpm, g_strnew(g_sp3_prop_timings[pi].name), NULL);
                    g_sp3_prop_timings[pi].prop_ptr = p;
                    g_sp3_prop_timings[pi].is_active = 0;
                    if (p) {
                        ((void(*)(void*,int,void*,void*,void*,void*,void*,void*))H[138].orig)
                            (p, 0, NULL, NULL, NULL, NULL, NULL, NULL);
                        sp3_prop_mirror(p, 0);
                        flog("SP3WEAPON_INIT name=%s ptr=%p", g_sp3_prop_timings[pi].name, p);
                    }
                }
            }

            g_sp3_xf_capture_props = 1;
            ((void(*)(void*,int,void*))(g_base + 0x117A67C))(pc, 1, NULL);
            g_sp3_xf_capture_props = 0;
            sp3_beat_apply(0);
            if (g_strnew) {
                for (int pi = 0; pi < 8; pi++) {
                    void* p = g_sp3_xf_props[pi];
                    if (!obj_ok(p)) continue;
                    char pname[64]; pname[0] = 0;
                    void* strobj = *(void**)((char*)p + 0x10);
                    if (!obj_ok(strobj)) continue;
                    read_str(strobj, pname, sizeof pname);
                    if (!strcmp(pname, "transformed")) {
                        void* st = g_strnew("SpecialAttack03");
                        void* st2 = g_strnew("Base.SpecialAttack03");
                        if (st)  ((void(*)(void*,void*,void*))(g_base + 0xEA05B4))(p, st, NULL);
                        if (st2) ((void(*)(void*,void*,void*))(g_base + 0xEA05B4))(p, st2, NULL);
                        g_sp3_anim_played = 1;
                        flog("SP3ANIM_START prop=transformed anim=%p tms=%llu",
                             fld_p(p, 0x68), (unsigned long long)propgo_now_ms());
                    }
                }
            }
        }
    });
    return r;
}

// Slot 143: PlayerCinematicSpecialAttackState.OnExit
void* hook_PlayerCinematicSpecialAttackState_OnExit(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* pc = fld_p(a0, 0x18);
    sp3_beat_apply(0);
    for (int i = 0; i < g_sp3_prop_timing_count; i++) {
        SP3PropTiming* pt = &g_sp3_prop_timings[i];
        if (obj_ok(pt->prop_ptr)) {
            ((void(*)(void*,int,void*,void*,void*,void*,void*,void*))H[138].orig)
                (pt->prop_ptr, 0, NULL, NULL, NULL, NULL, NULL, NULL);
            sp3_prop_mirror(pt->prop_ptr, 0);
            pt->prop_ptr = NULL;
            pt->is_active = 0;
        }
    }
    g_sp3_prop_timing_count = 0;
    sp3_xf_remove(pc);
    sp3_xf_props_clear();
    g_sp3_beat_form = -1;
    g_sp3_anim_played = 0;
    void* r = H[143].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        if (obj_ok(pc)) {
            flog("SP3XFIX exit pc=%p pump=%d tms=%llu", pc, g_sp3_beat_ticks, (unsigned long long)propgo_now_ms());
            ((void(*)(void*,int,void*))(g_base + 0x117A67C))(pc, 0, NULL);
            reset_player_attack_chain(pc);
        }
    });
    return r;
}

// Slot 145: Simulation.FixedUpdate
void* hook_Simulation_FixedUpdate(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = H[145].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        sp3_beat_pump();
        give_p0_max_power();
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
        if (g_p0_block_enter_ms > 0 && !g_p0_block_reset_done && g_p0_controller) {
            uint64_t held = propgo_now_ms() - g_p0_block_enter_ms;
            if (held >= 200) {
                g_p0_block_reset_done = 1;
                flog("BLOCK_HELD: P0 held guard stance for %llu ms >= 200ms -> attack chain reset to L1", (unsigned long long)held);
                reset_player_attack_chain(g_p0_controller);
            }
        }
        if (g_p0_combat_character && obj_ok(g_p0_combat_character)) {
            typedef float (*fn_get_hp)(void*, void*);
            fn_get_hp get_hp = (fn_get_hp)(g_base + 0xDAC6CC);
            float cur_hp = get_hp(g_p0_combat_character, NULL);
            if (g_p0_last_hp >= 0.0f && cur_hp < g_p0_last_hp - 0.01f) {
                flog("COMBAT_GATE: P0 took damage (%.1f -> %.1f) -> hit reaction resets attack chain",
                     g_p0_last_hp, cur_hp);
                if (g_p0_controller) {
                    reset_player_attack_chain(g_p0_controller);
                    g_p0_combo_ended = 0;
                    g_p0_after_heavy = 0;
                    COMBAT_ASSERT(*(uint32_t*)((uintptr_t)g_p0_controller + 0x1c0) == 0 &&
                                  *(uint32_t*)((uintptr_t)g_p0_controller + 0x1c4) == 0,
                                  "GATE-03", "Combo chain must be reset after hit reaction");
                }
            }
            g_p0_last_hp = cur_hp;
        }
        if (g_p1_combat_character && obj_ok(g_p1_combat_character)) {
            typedef float (*fn_get_hp)(void*, void*);
            fn_get_hp get_hp = (fn_get_hp)(g_base + 0xDAC6CC);
            float cur_hp = get_hp(g_p1_combat_character, NULL);
            g_p1_last_hp = cur_hp;
        }
    });
    return r;
}

// Slot 146: AIController.Simulate
void hook_AIController_Simulate(void* self, float dT, void* method) {
    if (H[146].orig) {
        ((fn_ai_simulate)H[146].orig)(self, dT, method);
    }
    PROTECT({
        if (!self || !obj_ok(self)) return;
        typedef int (*fn_can_shoot)(void*);
        fn_can_shoot can_shoot = (fn_can_shoot)(g_base + 0xDB31A8);
        if (can_shoot && can_shoot(self)) {
            typedef int (*fn_try_exec)(void*, int);
            fn_try_exec try_exec = (fn_try_exec)(g_base + 0xDB237C);
            if (try_exec) {
                int ok = try_exec(self, 1);
                static int ai_atk_logged = 0;
                if (ok && ai_atk_logged < 15) {
                    ai_atk_logged++;
                    flog("AIRANGE: triggered ranged attack action=1 on %p", self);
                }
            }
        }
    });
}

// Slot 153: PlayerController.SpecialAttack
void* hook_PlayerController_SpecialAttack(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    int index = (int)(intptr_t)a1;
    flog("SPECIAL_ATTACK index=%d called on controller=%p (p0=%p, is_p0=%d)",
         index, self, g_p0_controller, (self == g_p0_controller));
    if (self == g_p0_controller) {
        g_intended_special_tier = 0;
    }
    void* r = H[153].orig(self, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        ensure_p0_power_rounding(self);
    });
    return r;
}

// Slot 154: PlayerController.Action
void* hook_PlayerController_Action(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
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
                g_p0_block_enter_ms = 0;
                g_p0_block_reset_done = 0;
            }
            if (action == 0x100 || action == 8) {
                g_p0_block_enter_ms = 0;
                g_p0_block_reset_done = 0;
                if (action == 0x100) g_p0_after_heavy = 1;
                flog("PLAYER_ACTION heavy/ender (action=%d) on P0: reset attack chain and arm after_heavy flag", action);
                reset_player_attack_chain(self);
                did_reset = 1;
                COMBAT_ASSERT(*(uint32_t*)((uintptr_t)self + 0x1c4) == 0, "GATE-07",
                              "Medium index must be 0 after heavy attack so the next swipe is M1, got %u",
                              *(uint32_t*)((uintptr_t)self + 0x1c4));
            }
            if (action == 1 || action == 4 || action == 32) {
                if (g_p0_after_heavy) {
                    flog("COMBAT_GATE: attack following heavy attack (action=%d) -> reset attack chain to L1/M1", action);
                    reset_player_attack_chain(self);
                    did_reset = 1;
                    g_p0_after_heavy = 0;
                    pre_l = *(uint32_t*)((uintptr_t)self + 0x1c0);
                    pre_m = *(uint32_t*)((uintptr_t)self + 0x1c4);
                    COMBAT_ASSERT(pre_l == 0, "GATE-02", "Light index must be 0 after heavy attack, got %u", pre_l);
                } else if (g_p0_combo_ended || pre_m >= 2 || pre_l >= 4) {
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
            if (action == 0x80 || action == 1 || action == 4 || action == 0x100) {
                if (g_p0_block_enter_ms > 0) {
                    uint64_t held = propgo_now_ms() - g_p0_block_enter_ms;
                    g_p0_block_enter_ms = 0;
                    if (!g_p0_block_reset_done) {
                        flog("PLAYER_ACTION action=%d: held block for %llu ms (< 200ms) -> tap ignored, attack chain NOT reset",
                             action, (unsigned long long)held);
                    }
                }
            }
            if (action == 0x200) {
                if (!g_sp_dispatching_internal && g_sp_touch_tracking) {
                    flog("PLAYER_ACTION 0x200: suppressed premature touch-down special on P0 (tracking gesture)");
                    return (void*)1;
                }
                flog("PLAYER_ACTION 0x200: executing on P0 (intended_tier=%d, internal=%d)",
                     g_intended_special_tier, g_sp_dispatching_internal);
            }
            if (action == 1 || action == 4 || action == 32) g_p0_last_attack_ms = propgo_now_ms();
        }
    });
    if (action >= 1 && action <= 10) {
        flog("PLAYER_ACTION action=%d on controller=%p (p0=%p, is_p0=%d)",
             action, self, g_p0_controller, (self == g_p0_controller));
    }
    void* r = H[154].orig(self, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        if (obj_ok(self) && *(int32_t*)((uintptr_t)self + 0xF4) == 0) {
            uint32_t post_l = *(uint32_t*)((uintptr_t)self + 0x1c0);
            uint32_t post_m = *(uint32_t*)((uintptr_t)self + 0x1c4);
            flog("ACTION post act=%d l=%u m=%u r=%u ended=%d heavy=%d", action, post_l, post_m,
                 *(uint32_t*)((uintptr_t)self + 0x1c8), g_p0_combo_ended, g_p0_after_heavy);
            if (!did_reset && (post_l >= 4 || post_m >= 2 || post_l < pre_l || post_m < pre_m)) {
                g_p0_combo_ended = 1;
                flog("COMBAT_GATE: combo ender CONFIRMED (action=%d, pre l=%u m=%u -> post l=%u m=%u) -> g_p0_combo_ended = 1",
                     action, pre_l, pre_m, post_l, post_m);
            }
        }
    });
    return r;
}

// Slot 155: PlayerSpecialAttackState.OnExit
void* hook_PlayerSpecialAttackState_OnExit(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* pc = fld_p(a0, 0x18);
    void* r = H[155].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        if (obj_ok(pc) && *(int32_t*)((uintptr_t)pc + 0xF4) == 0) {
            flog("SPEXIT (0x0E34640) on P0: special attack ended -> resetting attack chain to L1/M1");
            reset_player_attack_chain(pc);
            g_p0_combo_ended = 0;
            g_p0_after_heavy = 0;
        }
    });
    return r;
}

// Slot 156: PlayerAttributes.RollForCriticalHit
void* hook_PlayerAttributes_RollForCriticalHit(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (H[156].orig) {
        H[156].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    }
    int is_crit = (rand() % 100) < 50 ? 1 : 0;
    static int s_crit_log_cnt = 0;
    if (s_crit_log_cnt++ < 30) {
        flog("ROLL_CRIT: PlayerAttributes.RollForCriticalHit called on %p -> 50%% roll: %d", a0, is_crit);
    }
    return (void*)(intptr_t)is_crit;
}

// Slot 160: PlayerBlockState.OnEnter
void* hook_PlayerBlockState_OnEnter(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* pc = fld_p(a0, 0x18);
    void* r = H[160].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        if (obj_ok(pc) && *(int32_t*)((uintptr_t)pc + 0xF4) == 0) {
            g_p0_controller = pc;
            g_p0_block_enter_ms = propgo_now_ms();
            g_p0_block_reset_done = 0;
            flog("BLOCK_ENTER (0x0D32A00): P0 started guarding at %llu ms (timer armed, hold >= 200ms required)",
                 (unsigned long long)g_p0_block_enter_ms);
        }
    });
    return r;
}

// Slot 163: PlayerController.AddMana
void* hook_PlayerController_AddMana(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    float amt;
    __asm__ volatile ("fmov %w0, s0" : "=r"(amt));
    if (obj_ok(a0)) {
        int32_t p_idx = *(int32_t*)((uintptr_t)a0 + 0xF4);
        if (p_idx != 0) {
            amt *= g_combat_enemy_mana_gain;
        } else {
            amt *= g_combat_player_mana_gain;
        }
    }
    __asm__ volatile ("fmov s0, %w0" : : "r"(amt));
    return H[163].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// Slot 165: PlayerDodgeState.OnEnter
void* hook_PlayerDodgeState_OnEnter(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = H[165].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        void* pc = fld_p(a0, 0x18);
        g_p0_block_enter_ms = 0;
        g_p0_block_reset_done = 0;
        if (obj_ok(pc) && *(int32_t*)((uintptr_t)pc + 0xF4) == 0) {
            flog("DODGE_ENTER (0x0D34E6C) on P0: reset attack chain to allow shooting");
            reset_player_attack_chain(pc);
        } else if (obj_ok(g_p0_controller)) {
            flog("DODGE_ENTER (0x0D34E6C): a0+0x18 did not resolve to P0 (pc=%p) -> reset via cached g_p0_controller", pc);
            reset_player_attack_chain(g_p0_controller);
        }
    });
    return r;
}

// Slot 168: PlayerController.GetAvailableSpecialTier
void* hook_PlayerController_GetAvailableSpecialTier(void* self, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    uint64_t now = propgo_now_ms();
    if (tftf_get_enable_swipe_specials() && self == g_p0_controller && g_intended_special_tier > 0 && (now - g_intended_special_time_ms < 600)) {
        int target_tier = g_intended_special_tier;
        void* power_meter = *(void**)((char*)self + 0x80);
        if (power_meter_can_use_special(power_meter, target_tier)) {
            flog("GET_AVAIL_SP_TIER: P0 overriding special tier to %d (valid power)", target_tier);
            return (void*)(intptr_t)target_tier;
        } else {
            flog("GET_AVAIL_SP_TIER: P0 intended tier %d not enough power, falling back to stock", target_tier);
            g_intended_special_tier = 0;
        }
    }
    void* r = H[168].orig(self, a1, a2, a3, a4, a5, a6, a7);
    if (self == g_p0_controller) {
        flog("GET_AVAIL_SP_TIER: P0 stock returned tier=%d", (int)(intptr_t)r);
    }
    return r;
}

// Slot 169: HudSpecialMeter.OnSpecialButtonPressed
void* hook_HudSpecialMeter_OnSpecialButtonPressed(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (!tftf_get_enable_swipe_specials()) {
        return H[169].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    }
    g_sp_btn_pressed_fired = 1;
    PROTECT({
        Vector3_t mpos = unity_get_mouse_position();
        float dx = 0.0f, dy = 0.0f;
        if (g_sp_touch_tracking) {
            dx = mpos.x - g_sp_touch_start_x;
            dy = mpos.y - g_sp_touch_start_y;
        }
        int intent = 0;
        if (dx > 35.0f && dx > fabsf(dy)) {
            intent = 1; // Swipe Right -> SP1
        } else if (dy > 35.0f && dy > fabsf(dx)) {
            intent = 2; // Swipe Up -> SP2
        } else {
            intent = 0; // Tap -> Max / SP3
        }
        g_intended_special_tier = intent;
        g_intended_special_time_ms = propgo_now_ms();
        flog("HUD_SP_BUTTON_PRESSED: cur=(%.1f, %.1f), start=(%.1f, %.1f), dx=%.1f, dy=%.1f -> intended_tier=%d",
             mpos.x, mpos.y, g_sp_touch_start_x, g_sp_touch_start_y, dx, dy, intent);
    });
    return H[169].orig(a0, a1, a2, a3, a4, a5, a6, a7);
}

// Slot 171: BLOCKENTER2
void* hook_PlayerBlockState_OnEnter2(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* pc = fld_p(a0, 0x18);
    void* r = H[171].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        void* target = (obj_ok(pc) && *(int32_t*)((uintptr_t)pc + 0xF4) == 0) ? pc
                     : (obj_ok(g_p0_controller) ? g_p0_controller : NULL);
        if (target) {
            g_p0_controller = target;
            g_p0_block_enter_ms = propgo_now_ms();
            g_p0_block_reset_done = 0;
            flog("BLOCK_ENTER (0x1173848): P0 started guarding at %llu ms (timer armed, hold >= 200ms required)",
                 (unsigned long long)g_p0_block_enter_ms);
        }
    });
    return r;
}

// Slot 172: DODGEENTER2
void* hook_PlayerDodgeState_OnEnter2(void* a0, void* a1, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = H[172].orig(a0, a1, a2, a3, a4, a5, a6, a7);
    PROTECT({
        void* pc = fld_p(a0, 0x18);
        g_p0_block_enter_ms = 0;
        g_p0_block_reset_done = 0;
        if (obj_ok(pc) && *(int32_t*)((uintptr_t)pc + 0xF4) == 0) {
            flog("DODGE_ENTER (0x117E4AC) on P0: reset attack chain to allow shooting");
            reset_player_attack_chain(pc);
        } else if (obj_ok(g_p0_controller)) {
            flog("DODGE_ENTER (0x117E4AC): a0+0x18 did not resolve to P0 (pc=%p) -> reset via cached g_p0_controller", pc);
            reset_player_attack_chain(g_p0_controller);
        }
    });
    return r;
}

// Slot 177: PlayerAttributes.ApplyDamage
typedef float (*fn_apply_dmg)(void* self, float damage, void* a1, int32_t a2, void* a3, int32_t a4, int32_t a5, float s1, float s2);
float hook_PlayerAttributes_ApplyDamage(void* self, float damage, void* a1, int32_t a2, void* a3, int32_t a4, int32_t a5, float s1, float s2) {
    if (tftf_is_picnic_quest_active()) {
        PROTECT({
            if (self && obj_ok(self)) {
                int32_t p_idx = *(int32_t*)((char*)self + 0x38);
                void* owner = *(void**)((char*)self + 0x28);
                int is_enemy = (p_idx == 1 || (owner && owner == g_p1_controller) || (owner && g_p0_controller && owner != g_p0_controller));
                if (is_enemy) {
                    int is_melee = 0;
                    if (g_p0_controller && obj_ok(g_p0_controller)) {
                        uint32_t l = *(uint32_t*)((char*)g_p0_controller + 0x1c0);
                        uint32_t m = *(uint32_t*)((char*)g_p0_controller + 0x1c4);
                        uint32_t r = *(uint32_t*)((char*)g_p0_controller + 0x1c8);
                        int is_heavy = (*(uint32_t*)((char*)g_p0_controller + 0x13c) & 1) || g_p0_after_heavy;

                        typedef int (*fn_pc_bool)(void*);
                        fn_pc_bool is_melee_fn = (fn_pc_bool)(g_base + 0x011754B8);
                        fn_pc_bool is_dash_fn = (fn_pc_bool)(g_base + 0x011755E0);
                        fn_pc_bool is_shooting_fn = (fn_pc_bool)(g_base + 0x01175508);

                        int native_melee = is_melee_fn ? is_melee_fn(g_p0_controller) : 0;
                        int native_dash = is_dash_fn ? is_dash_fn(g_p0_controller) : 0;
                        int native_shooting = is_shooting_fn ? is_shooting_fn(g_p0_controller) : 0;

                        if (l > 0 || m > 0 || is_heavy || native_melee || native_dash) {
                            is_melee = 1;
                        }
                        if (r > 0 || native_shooting) {
                            is_melee = 0;
                        }

                        static int s_dmg_log = 0;
                        if (s_dmg_log++ < 30 || is_melee) {
                            flog("PICNIC_DMG: enemy=%p dmg=%.1f->%.1f is_melee=%d (l=%u m=%u r=%u hvy=%d n_mel=%d n_dsh=%d n_sht=%d)",
                                 self, damage, is_melee ? 0.0f : damage, is_melee, l, m, r, is_heavy, native_melee, native_dash, native_shooting);
                        }
                    }
                    if (is_melee) {
                        damage = 0.0f;
                    }
                }
            }
        });
    }

    if (!H[177].orig) return 0.0f;
    return ((fn_apply_dmg)H[177].orig)(self, damage, a1, a2, a3, a4, a5, s1, s2);
}
