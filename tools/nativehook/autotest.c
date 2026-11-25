#ifdef TFTF_AUTOTEST

#include "autotest.h"
#include "skills/skill_env.h"

#include <android/log.h>
#include <ctype.h>
#include <dlfcn.h>
#include <pthread.h>
#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define AT_LOG(...) do { \
    char _at_buf[1024]; \
    snprintf(_at_buf, sizeof(_at_buf), __VA_ARGS__); \
    __android_log_print(ANDROID_LOG_INFO, "TFTFHOOK", "%s", _at_buf); \
    autotest_log_append(_at_buf); \
} while (0)

#define AT_RING_CAP (128 * 1024)

static const char* s_scenario_paths[] = {
    "/data/data/com.kabam.bigrobot/files/test_scenario.json",
    "/data/user/0/com.kabam.bigrobot/files/test_scenario.json",
    "/sdcard/Android/data/com.kabam.bigrobot/files/test_scenario.json",
    "/storage/emulated/0/Android/data/com.kabam.bigrobot/files/test_scenario.json",
    NULL
};

static pthread_mutex_t s_at_lock = PTHREAD_MUTEX_INITIALIZER;
static AutotestScenario s_sc;
static int s_sc_initialized = 0;
static char s_sc_raw[8192] = {0};

static char s_ring[AT_RING_CAP];
static size_t s_ring_len = 0;
static pthread_mutex_t s_ring_lock = PTHREAD_MUTEX_INITIALIZER;

static uint64_t at_now_ms(void) {
    struct timespec ts;
    clock_gettime(CLOCK_MONOTONIC, &ts);
    return (uint64_t)ts.tv_sec * 1000ULL + (uint64_t)(ts.tv_nsec / 1000000ULL);
}

static int ptr_sane(void* p) {
    uintptr_t v = (uintptr_t)p;
    return v >= 0x100000ULL && (v & 3ULL) == 0;
}

void autotest_log_append(const char* line) {
    if (!line || !line[0]) return;
    size_t len = strlen(line);
    if (len > 1000) len = 1000;
    pthread_mutex_lock(&s_ring_lock);
    if (s_ring_len + len + 2 >= AT_RING_CAP) {
        size_t keep = AT_RING_CAP / 2;
        if (keep < s_ring_len) {
            char* nl = memchr(s_ring + (s_ring_len - keep), '\n', keep);
            size_t start = nl ? (size_t)(nl - s_ring + 1) : (s_ring_len - keep);
            memmove(s_ring, s_ring + start, s_ring_len - start);
            s_ring_len -= start;
        } else {
            s_ring_len = 0;
        }
    }
    memcpy(s_ring + s_ring_len, line, len);
    s_ring_len += len;
    if (len == 0 || line[len - 1] != '\n') {
        s_ring[s_ring_len++] = '\n';
    }
    s_ring[s_ring_len] = '\0';
    pthread_mutex_unlock(&s_ring_lock);
}

void autotest_log_clear(void) {
    pthread_mutex_lock(&s_ring_lock);
    s_ring_len = 0;
    s_ring[0] = '\0';
    pthread_mutex_unlock(&s_ring_lock);
}

size_t autotest_get_logs(char* out, size_t max_out) {
    if (!out || max_out == 0) return 0;
    pthread_mutex_lock(&s_ring_lock);
    size_t copy_n = s_ring_len < (max_out - 1) ? s_ring_len : (max_out - 1);
    if (copy_n > 0) {
        memcpy(out, s_ring + (s_ring_len - copy_n), copy_n);
    }
    out[copy_n] = '\0';
    pthread_mutex_unlock(&s_ring_lock);
    return copy_n;
}

/* --------------------------------------------------------------------------
 * Minimal JSON Helpers (no heap churn, safe bounds)
 * -------------------------------------------------------------------------- */
static const char* skip_ws(const char* p, const char* end) {
    while (p < end && isspace((unsigned char)*p)) p++;
    return p;
}

static const char* find_json_val(const char* obj, const char* end, const char* key) {
    if (!obj || !end || !key) return NULL;
    size_t klen = strlen(key);
    const char* p = obj;
    int depth = 0;
    while (p < end) {
        if (*p == '"' && (p == obj || p[-1] != '\\')) {
            const char* s = p + 1;
            const char* e = s;
            while (e < end && !(*e == '"' && e[-1] != '\\')) e++;
            if (e >= end) break;
            const char* after = skip_ws(e + 1, end);
            if (after < end && *after == ':' && depth == 1 && (size_t)(e - s) == klen && memcmp(s, key, klen) == 0) {
                return skip_ws(after + 1, end);
            }
            p = e + 1;
            continue;
        }
        if (*p == '{' || *p == '[') depth++;
        else if (*p == '}' || *p == ']') {
            depth--;
            if (depth <= 0 && p > obj) break;
        }
        p++;
    }
    return NULL;
}

static const char* find_block_end(const char* open, const char* end) {
    if (!open || open >= end) return NULL;
    char oc = *open;
    char cc = (oc == '{') ? '}' : (oc == '[' ? ']' : 0);
    if (!cc) return NULL;
    int depth = 0;
    int in_str = 0;
    for (const char* p = open; p < end; p++) {
        if (*p == '"' && (p == open || p[-1] != '\\')) in_str = !in_str;
        if (in_str) continue;
        if (*p == oc) depth++;
        else if (*p == cc) {
            depth--;
            if (depth == 0) return p + 1;
        }
    }
    return NULL;
}

static int parse_jstr(const char* val, const char* end, char* out, size_t max_out) {
    if (!val || val >= end || *val != '"' || max_out == 0) return 0;
    const char* s = val + 1;
    const char* e = s;
    while (e < end && !(*e == '"' && e[-1] != '\\')) e++;
    if (e >= end) return 0;
    size_t n = (size_t)(e - s);
    if (n >= max_out) n = max_out - 1;
    memcpy(out, s, n);
    out[n] = '\0';
    return 1;
}

static int parse_jint(const char* val, const char* end, int* out) {
    if (!val || val >= end) return 0;
    if (*val == 't') { *out = 1; return 1; }
    if (*val == 'f') { *out = 0; return 1; }
    char* ep = NULL;
    long v = strtol(val, &ep, 10);
    if (ep == val) return 0;
    *out = (int)v;
    return 1;
}

static int parse_jfloat(const char* val, const char* end, float* out) {
    if (!val || val >= end) return 0;
    char* ep = NULL;
    float v = (float)strtod(val, &ep);
    if (ep == val) return 0;
    *out = v;
    return 1;
}

static AutotestActionType parse_action_name(const char* s) {
    if (!s) return AT_ACT_NONE;
    if (!strcasecmp(s, "WAIT")) return AT_ACT_WAIT;
    if (!strcasecmp(s, "DASH")) return AT_ACT_DASH;
    if (!strcasecmp(s, "LIGHT")) return AT_ACT_LIGHT;
    if (!strcasecmp(s, "MEDIUM")) return AT_ACT_MEDIUM;
    if (!strcasecmp(s, "HEAVY")) return AT_ACT_HEAVY;
    if (!strcasecmp(s, "RANGED") || !strcasecmp(s, "SHOOT")) return AT_ACT_RANGED;
    if (!strcasecmp(s, "BLOCK")) return AT_ACT_BLOCK;
    if (!strcasecmp(s, "DODGE")) return AT_ACT_DODGE;
    if (!strcasecmp(s, "SIDESTEP_LEFT") || !strcasecmp(s, "SIDESTEP_UP")) return AT_ACT_SIDESTEP_LEFT;
    if (!strcasecmp(s, "SIDESTEP_RIGHT") || !strcasecmp(s, "SIDESTEP_DOWN")) return AT_ACT_SIDESTEP_RIGHT;
    if (!strcasecmp(s, "SP1")) return AT_ACT_SP1;
    if (!strcasecmp(s, "SP2")) return AT_ACT_SP2;
    if (!strcasecmp(s, "SP3")) return AT_ACT_SP3;
    return AT_ACT_NONE;
}

static void set_default_scenario(AutotestScenario* sc) {
    memset(sc, 0, sizeof(*sc));
    sc->active = 1;
    snprintf(sc->name, sizeof(sc->name), "sideswipe_vs_movie_sideswipe");
    snprintf(sc->qid, sizeof(sc->qid), "1.1.1");
    snprintf(sc->p0_bid, sizeof(sc->p0_bid), "sideswipe_cin_rotf");
    snprintf(sc->p1_bid, sizeof(sc->p1_bid), "sideswipe_gs");
    sc->p0_mana = -1.0f;
    sc->p1_mana = -1.0f;
    sc->auto_fight = 1;
    sc->freeze_enemy_ai = 0;
    sc->dummy_invincible = 0;
    sc->player_invincible = 0;
    sc->max_duration_ms = 25000;
}

static void parse_buffs_array(const char* arr, const char* arr_end, int target_player, AutotestScenario* sc) {
    if (!arr || !arr_end || *arr != '[') return;
    const char* p = arr + 1;
    while (p < arr_end && sc->initial_buff_count < AUTOTEST_MAX_INITIAL_BUFFS) {
        p = skip_ws(p, arr_end);
        if (p >= arr_end || *p == ']') break;
        if (*p == '{') {
            const char* obj_end = find_block_end(p, arr_end);
            if (!obj_end) break;
            AutotestInitBuff b;
            memset(&b, 0, sizeof(b));
            b.target_player = target_player;
            b.duration_s = -1.0f;
            b.stacks = 1;
            const char* vid = find_json_val(p, obj_end, "id");
            const char* vdur = find_json_val(p, obj_end, "dur");
            const char* vst = find_json_val(p, obj_end, "stacks");
            if (vid && parse_jstr(vid, obj_end, b.mod_id, sizeof(b.mod_id)) && b.mod_id[0]) {
                if (vdur) parse_jfloat(vdur, obj_end, &b.duration_s);
                if (vst) parse_jint(vst, obj_end, &b.stacks);
                if (b.stacks < 1) b.stacks = 1;
                if (b.stacks > 20) b.stacks = 20;
                sc->initial_buffs[sc->initial_buff_count++] = b;
            }
            p = obj_end;
        } else {
            p++;
        }
    }
}

static void parse_scenario_json_into(const char* json, size_t len, AutotestScenario* sc) {
    set_default_scenario(sc);
    if (!json || len == 0) return;
    const char* start = skip_ws(json, json + len);
    const char* end = json + len;
    if (start >= end || *start != '{') return;

    const char* v;
    if ((v = find_json_val(start, end, "active"))) parse_jint(v, end, &sc->active);
    if ((v = find_json_val(start, end, "name"))) parse_jstr(v, end, sc->name, sizeof(sc->name));
    if ((v = find_json_val(start, end, "qid"))) parse_jstr(v, end, sc->qid, sizeof(sc->qid));
    if ((v = find_json_val(start, end, "auto_fight"))) parse_jint(v, end, &sc->auto_fight);
    if ((v = find_json_val(start, end, "freeze_enemy_ai"))) parse_jint(v, end, &sc->freeze_enemy_ai);
    if ((v = find_json_val(start, end, "dummy_invincible"))) parse_jint(v, end, &sc->dummy_invincible);
    if ((v = find_json_val(start, end, "player_invincible"))) parse_jint(v, end, &sc->player_invincible);
    if ((v = find_json_val(start, end, "max_duration_ms"))) parse_jint(v, end, &sc->max_duration_ms);

    if ((v = find_json_val(start, end, "p0")) && *v == '{') {
        const char* oe = find_block_end(v, end);
        if (oe) {
            const char* pv;
            if ((pv = find_json_val(v, oe, "bid"))) parse_jstr(pv, oe, sc->p0_bid, sizeof(sc->p0_bid));
            if ((pv = find_json_val(v, oe, "mana"))) parse_jfloat(pv, oe, &sc->p0_mana);
            if ((pv = find_json_val(v, oe, "initial_buffs")) && *pv == '[') {
                const char* ae = find_block_end(pv, oe);
                if (ae) parse_buffs_array(pv, ae, 0, sc);
            }
        }
    }
    if ((v = find_json_val(start, end, "p1")) && *v == '{') {
        const char* oe = find_block_end(v, end);
        if (oe) {
            const char* pv;
            if ((pv = find_json_val(v, oe, "bid"))) parse_jstr(pv, oe, sc->p1_bid, sizeof(sc->p1_bid));
            if ((pv = find_json_val(v, oe, "mana"))) parse_jfloat(pv, oe, &sc->p1_mana);
            if ((pv = find_json_val(v, oe, "freeze_ai"))) parse_jint(pv, oe, &sc->freeze_enemy_ai);
            if ((pv = find_json_val(v, oe, "invincible_dummy"))) parse_jint(pv, oe, &sc->dummy_invincible);
            if ((pv = find_json_val(v, oe, "initial_buffs")) && *pv == '[') {
                const char* ae = find_block_end(pv, oe);
                if (ae) parse_buffs_array(pv, ae, 1, sc);
            }
        }
    }
    if ((v = find_json_val(start, end, "p0_script")) && *v == '[') {
        const char* ae = find_block_end(v, end);
        if (ae) {
            const char* p = v + 1;
            while (p < ae && sc->script_len < AUTOTEST_MAX_SCRIPT_STEPS) {
                p = skip_ws(p, ae);
                if (p >= ae || *p == ']') break;
                if (*p == '{') {
                    const char* oe = find_block_end(p, ae);
                    if (!oe) break;
                    AutotestScriptStep st;
                    memset(&st, 0, sizeof(st));
                    st.repeat = 1;
                    st.duration_ms = 500;
                    char act_name[32] = {0};
                    const char* sv;
                    if ((sv = find_json_val(p, oe, "action")) && parse_jstr(sv, oe, act_name, sizeof(act_name))) {
                        st.action = parse_action_name(act_name);
                    }
                    if ((sv = find_json_val(p, oe, "duration_ms"))) parse_jint(sv, oe, &st.duration_ms);
                    if ((sv = find_json_val(p, oe, "hold_ms"))) parse_jint(sv, oe, &st.duration_ms);
                    if ((sv = find_json_val(p, oe, "repeat"))) parse_jint(sv, oe, &st.repeat);
                    if (st.repeat < 1) st.repeat = 1;
                    if (st.repeat > 20) st.repeat = 20;
                    if (st.action != AT_ACT_NONE) {
                        sc->script[sc->script_len++] = st;
                    }
                    p = oe;
                } else {
                    p++;
                }
            }
        }
    }
}

void autotest_init(void) {
    pthread_mutex_lock(&s_at_lock);
    if (!s_sc_initialized) {
        s_sc_initialized = 1;
        set_default_scenario(&s_sc);
        snprintf(s_sc_raw, sizeof(s_sc_raw),
                 "{\"active\":true,\"name\":\"%s\",\"qid\":\"%s\","
                 "\"p0\":{\"bid\":\"%s\"},\"p1\":{\"bid\":\"%s\"},"
                 "\"auto_fight\":true,\"freeze_enemy_ai\":false,\"max_duration_ms\":%d}",
                 s_sc.name, s_sc.qid, s_sc.p0_bid, s_sc.p1_bid, s_sc.max_duration_ms);
        for (int i = 0; s_scenario_paths[i]; i++) {
            FILE* f = fopen(s_scenario_paths[i], "rb");
            if (f) {
                size_t n = fread(s_sc_raw, 1, sizeof(s_sc_raw) - 1, f);
                fclose(f);
                if (n > 0) {
                    s_sc_raw[n] = '\0';
                    parse_scenario_json_into(s_sc_raw, n, &s_sc);
                    AT_LOG("[AUTOTEST] Loaded scenario from %s (p0=%s p1=%s auto_fight=%d)",
                           s_scenario_paths[i], s_sc.p0_bid, s_sc.p1_bid, s_sc.auto_fight);
                    break;
                }
            }
        }
        AT_LOG("[AUTOTEST] Init active=%d name=%s p0=%s p1=%s auto_fight=%d script_steps=%d",
               s_sc.active, s_sc.name, s_sc.p0_bid, s_sc.p1_bid, s_sc.auto_fight, s_sc.script_len);
    }
    pthread_mutex_unlock(&s_at_lock);
}

int autotest_is_active(void) {
    if (!s_sc_initialized) autotest_init();
    return s_sc.active;
}

const char* autotest_get_p0_bid(void) {
    if (!s_sc_initialized) autotest_init();
    return (s_sc.active && s_sc.p0_bid[0]) ? s_sc.p0_bid : NULL;
}

const char* autotest_get_p1_bid(void) {
    if (!s_sc_initialized) autotest_init();
    return (s_sc.active && s_sc.p1_bid[0]) ? s_sc.p1_bid : NULL;
}

int autotest_override_freeze_enemy_ai(void) {
    if (!s_sc_initialized) autotest_init();
    return s_sc.active ? s_sc.freeze_enemy_ai : -1;
}

int autotest_override_player_invincible(void) {
    if (!s_sc_initialized) autotest_init();
    return s_sc.active ? s_sc.player_invincible : -1;
}

int autotest_is_dummy_invincible(void) {
    if (!s_sc_initialized) autotest_init();
    return s_sc.active && s_sc.dummy_invincible;
}

int autotest_set_scenario_json(const char* json, size_t len) {
    if (!json || len == 0 || len >= sizeof(s_sc_raw)) return -1;
    pthread_mutex_lock(&s_at_lock);
    s_sc_initialized = 1;
    memcpy(s_sc_raw, json, len);
    s_sc_raw[len] = '\0';
    parse_scenario_json_into(s_sc_raw, len, &s_sc);
    for (int i = 0; s_scenario_paths[i]; i++) {
        FILE* f = fopen(s_scenario_paths[i], "wb");
        if (f) {
            fwrite(s_sc_raw, 1, len, f);
            fclose(f);
            break;
        }
    }
    pthread_mutex_unlock(&s_at_lock);
    AT_LOG("[AUTOTEST] Scenario updated via HTTP: p0=%s p1=%s auto_fight=%d buffs=%d script=%d",
           s_sc.p0_bid, s_sc.p1_bid, s_sc.auto_fight, s_sc.initial_buff_count, s_sc.script_len);
    return 0;
}

size_t autotest_get_scenario_json(char* out, size_t max_out) {
    if (!s_sc_initialized) autotest_init();
    if (!out || max_out == 0) return 0;
    pthread_mutex_lock(&s_at_lock);
    size_t n = strlen(s_sc_raw);
    if (n >= max_out) n = max_out - 1;
    memcpy(out, s_sc_raw, n);
    out[n] = '\0';
    pthread_mutex_unlock(&s_at_lock);
    return n;
}

/* --------------------------------------------------------------------------
 * IL2CPP Reflection & Boot-to-Fight Navigation Hooks
 * -------------------------------------------------------------------------- */
static uintptr_t s_base = 0;
static autotest_strnew_fn s_strnew = NULL;
static autotest_objnew_fn s_objnew = NULL;

typedef void* (*fn_domain_get)(void);
typedef void** (*fn_domain_get_assemblies)(void* domain, size_t* size);
typedef void* (*fn_assembly_get_image)(void* assembly);
typedef void* (*fn_class_from_name)(void* image, const char* ns, const char* name);
typedef void* (*fn_class_get_nested)(void* klass, void** iter);
typedef const char* (*fn_class_get_name)(void* klass);
typedef void* (*fn_class_get_static_data)(void* klass);

static fn_domain_get p_domain_get = NULL;
static fn_domain_get_assemblies p_domain_get_asms = NULL;
static fn_assembly_get_image p_asm_get_image = NULL;
static fn_class_from_name p_class_from_name = NULL;
static fn_class_get_nested p_class_get_nested = NULL;
static fn_class_get_name p_class_get_name = NULL;
static fn_class_get_static_data p_class_get_static_data = NULL;

static void resolve_il2cpp_reflection(void) {
    if (p_class_from_name) return;
    void* h = dlopen("libil2cpp.so", RTLD_NOLOAD);
    p_domain_get = (fn_domain_get)(dlsym(RTLD_DEFAULT, "il2cpp_domain_get") ?: (h ? dlsym(h, "il2cpp_domain_get") : NULL));
    p_domain_get_asms = (fn_domain_get_assemblies)(dlsym(RTLD_DEFAULT, "il2cpp_domain_get_assemblies") ?: (h ? dlsym(h, "il2cpp_domain_get_assemblies") : NULL));
    p_asm_get_image = (fn_assembly_get_image)(dlsym(RTLD_DEFAULT, "il2cpp_assembly_get_image") ?: (h ? dlsym(h, "il2cpp_assembly_get_image") : NULL));
    p_class_from_name = (fn_class_from_name)(dlsym(RTLD_DEFAULT, "il2cpp_class_from_name") ?: (h ? dlsym(h, "il2cpp_class_from_name") : NULL));
    p_class_get_nested = (fn_class_get_nested)(dlsym(RTLD_DEFAULT, "il2cpp_class_get_nested_types") ?: (h ? dlsym(h, "il2cpp_class_get_nested_types") : NULL));
    p_class_get_name = (fn_class_get_name)(dlsym(RTLD_DEFAULT, "il2cpp_class_get_name") ?: (h ? dlsym(h, "il2cpp_class_get_name") : NULL));
    p_class_get_static_data = (fn_class_get_static_data)(dlsym(RTLD_DEFAULT, "il2cpp_class_get_static_field_data") ?: (h ? dlsym(h, "il2cpp_class_get_static_field_data") : NULL));
}

static void* find_class_by_name(const char* name) {
    resolve_il2cpp_reflection();
    if (!p_domain_get || !p_domain_get_asms || !p_asm_get_image || !p_class_from_name) return NULL;
    void* dom = p_domain_get();
    if (!dom) return NULL;
    size_t cnt = 0;
    void** asms = p_domain_get_asms(dom, &cnt);
    for (size_t i = 0; i < cnt; i++) {
        void* img = p_asm_get_image(asms[i]);
        if (!img) continue;
        void* k = p_class_from_name(img, "", name);
        if (k) return k;
    }
    return NULL;
}

static void* find_nested_class(void* parent_klass, const char* nested_name) {
    if (!parent_klass || !p_class_get_nested || !p_class_get_name) return NULL;
    void* iter = NULL;
    void* nk = NULL;
    while ((nk = p_class_get_nested(parent_klass, &iter)) != NULL) {
        const char* n = p_class_get_name(nk);
        if (n && strcmp(n, nested_name) == 0) return nk;
    }
    return NULL;
}

typedef void* (*fn_il2cpp_8)(void*, void*, void*, void*, void*, void*, void*, void*);

static fn_il2cpp_8 orig_LangPopup_WindowEnter = NULL;
static fn_il2cpp_8 orig_FlowManager_Update = NULL;
static fn_il2cpp_8 orig_HomeFlow_OpenScreens = NULL;
static fn_il2cpp_8 orig_QuestFlow_GameBoardReady = NULL;
static fn_il2cpp_8 orig_Gameboard_BuildComplete = NULL;
static fn_il2cpp_8 orig_NodeInfoPopup_WindowEnter = NULL;
static fn_il2cpp_8 orig_NodeInfoPopup_OnDisable = NULL;

static volatile int s_home_entered = 0;
static volatile uint64_t s_home_entered_ms = 0;
static volatile int s_quest_pushed = 0;
static volatile int s_team_confirmed = 0;
static volatile int s_in_combat = 0;
static void* s_gameboard = NULL;
static volatile uint64_t s_last_board_step_ms = 0;
static void* s_pending_node_popup = NULL;
static uint64_t s_pending_node_popup_ms = 0;
static void* s_pending_prefight = NULL;
static uint64_t s_pending_prefight_ms = 0;
static void* s_pending_team_pres = NULL;
static uint64_t s_pending_team_pres_ms = 0;

static void* hooked_LangPopup_WindowEnter(void* self, void* isFirst, void* method, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = orig_LangPopup_WindowEnter ? orig_LangPopup_WindowEnter(self, isFirst, method, a3, a4, a5, a6, a7) : NULL;
    if (autotest_is_active() && ptr_sane(self) && s_base) {
        AT_LOG("[AUTOTEST] Auto-confirming LanguageSelectionPopup");
        ((void(*)(void*, void*, void*))(s_base + 0xF049B0))(self, NULL, NULL); // LanguageSelectionPopup.OnActionButtonClicked
    }
    return r;
}

static void* hooked_HomeFlow_OpenScreens(void* self, void* method, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = orig_HomeFlow_OpenScreens ? orig_HomeFlow_OpenScreens(self, method, a2, a3, a4, a5, a6, a7) : NULL;
    if (!s_home_entered) {
        s_home_entered = 1;
        s_home_entered_ms = at_now_ms();
        AT_LOG("[AUTOTEST] HomeFlow.OpenScreens reached; arming QuestFlow launch for %s", s_sc.qid);
    }
    return r;
}

static void* hooked_QuestFlow_GameBoardReady(void* self, void* method, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = orig_QuestFlow_GameBoardReady ? orig_QuestFlow_GameBoardReady(self, method, a2, a3, a4, a5, a6, a7) : NULL;
    if (autotest_is_active() && ptr_sane(self) && s_base) {
        void* gb = *(void**)((char*)self + 0x50); // QuestFlow._gameBoard
        if (ptr_sane(gb)) {
            s_gameboard = gb;
            s_last_board_step_ms = at_now_ms();
            AT_LOG("[AUTOTEST] QuestFlow.GameBoardReady gb=%p -> enabling AutoMission + AutoFight", gb);
            ((void(*)(int, void*))(s_base + 0xC9D6E8))(1, NULL); // AutoFightManager.ToggleAutoMission(true)
            ((void(*)(int, void*))(s_base + 0xC9D9A0))(1, NULL); // AutoFightManager.ToggleAutoFight(true)
        }
    }
    return r;
}

static void* hooked_Gameboard_BuildComplete(void* self, void* onComplete, void* method, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = orig_Gameboard_BuildComplete ? orig_Gameboard_BuildComplete(self, onComplete, method, a3, a4, a5, a6, a7) : NULL;
    if (autotest_is_active() && ptr_sane(self)) {
        s_gameboard = self;
        s_last_board_step_ms = at_now_ms();
        AT_LOG("[AUTOTEST] Gameboard.OnGameBoardBuildComplete gb=%p", self);
    }
    return r;
}

static void* hooked_NodeInfoPopup_WindowEnter(void* self, void* config, void* onComplete, void* method, void* a4, void* a5, void* a6, void* a7) {
    void* r = orig_NodeInfoPopup_WindowEnter ? orig_NodeInfoPopup_WindowEnter(self, config, onComplete, method, a4, a5, a6, a7) : NULL;
    if (autotest_is_active() && ptr_sane(self)) {
        s_pending_node_popup = self;
        s_pending_node_popup_ms = at_now_ms();
        AT_LOG("[AUTOTEST] NodeInfoPopup entered -> scheduled OnFightClicked");
    }
    return r;
}

static void* hooked_NodeInfoPopup_OnDisable(void* self, void* method, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    if (self == s_pending_node_popup) {
        s_pending_node_popup = NULL;
    }
    return orig_NodeInfoPopup_OnDisable ? orig_NodeInfoPopup_OnDisable(self, method, a2, a3, a4, a5, a6, a7) : NULL;
}

void autotest_on_team_select_intro(void* tsp) {
    if (!autotest_is_active() || !ptr_sane(tsp) || s_team_confirmed) return;
    s_pending_team_pres = tsp;
    s_pending_team_pres_ms = at_now_ms();
    AT_LOG("[AUTOTEST] TeamSelectPresentation intro complete -> scheduled OnBeginQuestClicked");
}

void autotest_on_prefight_ready(void* pfs) {
    if (!autotest_is_active() || !ptr_sane(pfs)) return;
    s_pending_prefight = pfs;
    s_pending_prefight_ms = at_now_ms();
    AT_LOG("[AUTOTEST] PreFightScreen intro complete -> scheduled OnFight");
}

void autotest_on_prefight_exit(void) {
    s_pending_prefight = NULL;
}

static void try_push_quest_flow(void) {
    if (!s_base || !s_strnew || !s_objnew) return;
    void* qm = ((void*(*)(void*))(s_base + 0xD6A7C8))(NULL); // QuestsManager.get_Instance()
    if (!ptr_sane(qm)) return;
    void* cat_str = s_strnew("Story");
    void* qid_str = s_strnew(s_sc.qid);
    if (!cat_str || !qid_str) return;
    void* summary = ((void*(*)(void*, void*, void*, void*))(s_base + 0xD6B304))(qm, cat_str, qid_str, NULL);
    if (!ptr_sane(summary)) return;

    void* qf_klass = find_class_by_name("QuestFlow");
    void* init_klass = find_nested_class(qf_klass, "InitInfo");
    if (!qf_klass || !init_klass) {
        AT_LOG("[AUTOTEST] ERROR: failed to resolve QuestFlow (%p) or InitInfo (%p)", qf_klass, init_klass);
        s_quest_pushed = 1;
        return;
    }

    void* fm = ((void*(*)(void*))(s_base + 0xDC8D58))(NULL); // FlowManager.get_Instance()
    if (!ptr_sane(fm)) return;
    int in_prog = ((int(*)(void*, void*))(s_base + 0xDC91BC))(fm, NULL);
    if (in_prog) return;

    void* init_info = s_objnew(init_klass);
    if (!ptr_sane(init_info)) return;
    ((void(*)(void*, void*))(s_base + 0xF42C18))(init_info, NULL); // InitInfo..ctor()
    *(void**)((char*)init_info + 0x10) = cat_str;
    *(void**)((char*)init_info + 0x18) = qid_str;
    *(void**)((char*)init_info + 0x28) = summary;
    *(uint8_t*)((char*)init_info + 0x38) = 0; // preview = false

    void* qflow = s_objnew(qf_klass);
    if (!ptr_sane(qflow)) return;
    ((void(*)(void*, void*, void*))(s_base + 0x12E8E64))(qflow, init_info, NULL); // QuestFlow..ctor(initInfo)

    s_quest_pushed = 1;
    AT_LOG("[AUTOTEST] Pushing QuestFlow Story:%s (summary=%p qflow=%p)", s_sc.qid, summary, qflow);
    ((void(*)(void*, void*, void*, void*, void*))(s_base + 0xDC95D0))(fm, qflow, NULL, NULL, NULL);
}

static void suppress_team_warnings(void) {
    resolve_il2cpp_reflection();
    if (!p_class_get_static_data) return;
    void* ts_klass = find_class_by_name("TeamSelect");
    if (ts_klass) {
        uint8_t* sf = (uint8_t*)p_class_get_static_data(ts_klass);
        if (sf) {
            sf[0] = 1; // HasSeenTeamSpaceWarning
            sf[1] = 1; // HasSeenWeakTeamWarning
            sf[2] = 1; // HasSeenGateWarning
        }
    }
    void* tsp_klass = find_class_by_name("TeamSelectPresentation");
    if (tsp_klass) {
        uint8_t* sf = (uint8_t*)p_class_get_static_data(tsp_klass);
        if (sf) {
            sf[0] = 1; // HasSeenTeamSpaceWarning
            sf[1] = 1; // HasSeenWeakTeamWarning
        }
    }
}

static void try_advance_gameboard_node(void* gb) {
    if (!ptr_sane(gb) || !s_base) return;

    // 1. Prefer tapping the exact node marked _canRequestMove (blue ring on board)
    void* nodes_list = *(void**)((char*)gb + 0x48); // Gameboard._nodes (List<QuestNodeController>)
    if (ptr_sane(nodes_list)) {
        void* items = *(void**)((char*)nodes_list + 0x10);
        int32_t count = *(int32_t*)((char*)nodes_list + 0x18);
        if (ptr_sane(items) && count > 0 && count < 256) {
            for (int32_t i = 0; i < count; i++) {
                void* qnc = *(void**)((char*)items + 0x20 + i * sizeof(void*));
                if (!ptr_sane(qnc)) continue;
                uint8_t can_move = *(uint8_t*)((char*)qnc + 0xA4); // QuestNodeController._canRequestMove
                void* map_tile = *(void**)((char*)qnc + 0x38);     // NodeController._mapTile
                if (can_move && ptr_sane(map_tile)) {
                    AT_LOG("[AUTOTEST] Tapping movable node idx=%d qnc=%p tile=%p", i, qnc, map_tile);
                    ((void(*)(void*, void*, void*))(s_base + 0xA55FA4))(gb, map_tile, NULL); // Gameboard.OnNodeTapped
                    return;
                }
            }
        }
    }

    // 2. Fallback: find any valid Direction (0..7) and call RequestMove
    typedef int (*fn_is_move_valid)(void*, int, void*);
    typedef void (*fn_req_move)(void*, int, void*);
    fn_is_move_valid is_valid = (fn_is_move_valid)(s_base + 0xA547E4);
    fn_req_move req_move = (fn_req_move)(s_base + 0xA54540);
    for (int dir = 0; dir < 8; dir++) {
        if (is_valid(gb, dir, NULL)) {
            AT_LOG("[AUTOTEST] RequestMove valid dir=%d on gb=%p", dir, gb);
            req_move(gb, dir, NULL);
            return;
        }
    }

    // 3. Final fallback: AutoSelectNextNode
    AT_LOG("[AUTOTEST] Fallback Gameboard.AutoSelectNextNode(%p)", gb);
    ((void(*)(void*, void*))(s_base + 0xA55D0C))(gb, NULL);
}

static void* hooked_FlowManager_Update(void* self, void* method, void* a2, void* a3, void* a4, void* a5, void* a6, void* a7) {
    void* r = orig_FlowManager_Update ? orig_FlowManager_Update(self, method, a2, a3, a4, a5, a6, a7) : NULL;
    if (!autotest_is_active() || !s_base) return r;

    uint64_t now_ms = at_now_ms();

    if (s_home_entered && !s_quest_pushed && (now_ms - s_home_entered_ms >= 600)) {
        try_push_quest_flow();
    }

    if (s_pending_team_pres && !s_team_confirmed && (now_ms - s_pending_team_pres_ms >= 400)) {
        void* tsp = s_pending_team_pres;
        s_pending_team_pres = NULL;
        s_team_confirmed = 1;
        suppress_team_warnings();
        AT_LOG("[AUTOTEST] Invoking TeamSelectPresentation.OnBeginQuestClicked(%p)", tsp);
        ((void(*)(void*, void*, void*))(s_base + 0xFA1A48))(tsp, NULL, NULL);
    }

    if (!s_in_combat && ptr_sane(s_gameboard) && !s_pending_node_popup && !s_pending_prefight) {
        if (now_ms - s_last_board_step_ms >= 1500) {
            s_last_board_step_ms = now_ms;
            try_advance_gameboard_node(s_gameboard);
        }
    }

    if (s_pending_node_popup && (now_ms - s_pending_node_popup_ms >= 450)) {
        void* popup = s_pending_node_popup;
        s_pending_node_popup = NULL;
        AT_LOG("[AUTOTEST] Invoking NodeInfoPopup.OnFightClicked(%p)", popup);
        ((void(*)(void*, void*, void*))(s_base + 0xD82720))(popup, NULL, NULL);
    }

    if (s_pending_prefight && (now_ms - s_pending_prefight_ms >= 450)) {
        void* pfs = s_pending_prefight;
        s_pending_prefight = NULL;
        AT_LOG("[AUTOTEST] Invoking PreFightScreen.OnFight(%p)", pfs);
        ((void(*)(void*, void*))(s_base + 0xE397BC))(pfs, NULL);
    }

    return r;
}

void autotest_install_hooks(uintptr_t il2cpp_base,
                            autotest_inline_hook_fn hook_fn,
                            autotest_strnew_fn strnew_fn,
                            autotest_objnew_fn objnew_fn) {
    s_base = il2cpp_base;
    s_strnew = strnew_fn;
    s_objnew = objnew_fn;
    autotest_init();
    if (!autotest_is_active() || !il2cpp_base || !hook_fn) return;

    hook_fn((void*)(il2cpp_base + 0xF03F60), (void*)hooked_LangPopup_WindowEnter, (void**)&orig_LangPopup_WindowEnter);
    hook_fn((void*)(il2cpp_base + 0xDC8E14), (void*)hooked_FlowManager_Update, (void**)&orig_FlowManager_Update);
    hook_fn((void*)(il2cpp_base + 0xC5FE1C), (void*)hooked_HomeFlow_OpenScreens, (void**)&orig_HomeFlow_OpenScreens);
    hook_fn((void*)(il2cpp_base + 0x12E9FF8), (void*)hooked_QuestFlow_GameBoardReady, (void**)&orig_QuestFlow_GameBoardReady);
    hook_fn((void*)(il2cpp_base + 0xA52F64), (void*)hooked_Gameboard_BuildComplete, (void**)&orig_Gameboard_BuildComplete);
    hook_fn((void*)(il2cpp_base + 0xD818CC), (void*)hooked_NodeInfoPopup_WindowEnter, (void**)&orig_NodeInfoPopup_WindowEnter);
    hook_fn((void*)(il2cpp_base + 0xD82D34), (void*)hooked_NodeInfoPopup_OnDisable, (void**)&orig_NodeInfoPopup_OnDisable);

    AT_LOG("[AUTOTEST] Boot-to-fight navigation hooks installed (scenario=%s)", s_sc.name);
}

/* --------------------------------------------------------------------------
 * Combat State Injection, Scripted Action Driver & Telemetry
 * -------------------------------------------------------------------------- */
static volatile int s_combat_injected = 0;
static volatile uint64_t s_combat_start_ms = 0;
static volatile uint64_t s_last_snap_ms = 0;
static volatile int s_scenario_done = 0;
static volatile int s_script_idx = 0;
static volatile int s_script_rep = 0;
static volatile uint64_t s_script_step_start_ms = 0;
static volatile int s_block_holding = 0;

void autotest_on_combat_start(void) {
    s_in_combat = 1;
    s_pending_prefight = NULL;
    s_pending_node_popup = NULL;
    s_combat_injected = 0;
    s_combat_start_ms = 0;
    s_last_snap_ms = 0;
    s_scenario_done = 0;
    s_script_idx = 0;
    s_script_rep = 0;
    s_script_step_start_ms = 0;
    s_block_holding = 0;
    autotest_init();
    AT_LOG("[AUTOTEST] FIGHT_ENTER scenario=%s p0=%s p1=%s auto_fight=%d",
           s_sc.name, skill_get_bot_id(0), skill_get_bot_id(1), s_sc.auto_fight);
}

static void emit_snapshot(uint64_t elapsed_ms) {
    float p0_hp = skill_get_hp_ratio(0);
    float p1_hp = skill_get_hp_ratio(1);
    float p0_m = skill_get_mana(0);
    float p1_m = skill_get_mana(1);
    AT_LOG("[AUTOTEST] SNAPSHOT t=%llums P0(%s hp=%.2f mana=%.2f) P1(%s hp=%.2f mana=%.2f)",
           (unsigned long long)elapsed_ms,
           skill_get_bot_id(0), p0_hp, p0_m,
           skill_get_bot_id(1), p1_hp, p1_m);
}

static void drive_script_step(void* player_pc, uint64_t now_ms) {
    if (!ptr_sane(player_pc) || !s_base) return;
    if (s_script_idx >= s_sc.script_len) return;

    AutotestScriptStep* st = &s_sc.script[s_script_idx];
    if (s_script_step_start_ms == 0) {
        s_script_step_start_ms = now_ms;
    }

    if (st->action == AT_ACT_WAIT) {
        if ((int)(now_ms - s_script_step_start_ms) >= st->duration_ms) {
            AT_LOG("[AUTOTEST] STEP_DONE idx=%d action=WAIT(%dms)", s_script_idx, st->duration_ms);
            s_script_idx++;
            s_script_rep = 0;
            s_script_step_start_ms = 0;
        }
        return;
    }

    if (st->action == AT_ACT_BLOCK) {
        typedef int (*fn_act)(void*, int, void*);
        fn_act try_act = (fn_act)(s_base + 0x1179AF4);
        if (!s_block_holding) {
            if (try_act(player_pc, 2, NULL)) {
                s_block_holding = 1;
                s_script_step_start_ms = now_ms;
                AT_LOG("[AUTOTEST] STEP_EXEC idx=%d action=BLOCK_START", s_script_idx);
            }
        } else if ((int)(now_ms - s_script_step_start_ms) >= st->duration_ms) {
            try_act(player_pc, 4, NULL);
            s_block_holding = 0;
            AT_LOG("[AUTOTEST] STEP_DONE idx=%d action=BLOCK_RELEASE", s_script_idx);
            s_script_idx++;
            s_script_rep = 0;
            s_script_step_start_ms = 0;
        }
        return;
    }

    if ((now_ms - s_script_step_start_ms) < 180) return;

    int can_act = ((int(*)(void*, void*))(s_base + 0x1175714))(player_pc, NULL);
    int can_att = ((int(*)(void*, void*))(s_base + 0x11737B4))(player_pc, NULL);
    int att_win = ((int(*)(void*, void*))(s_base + 0x1173F94))(player_pc, NULL);
    float dist = ((float(*)(void*, void*))(s_base + 0x1175A28))(player_pc, NULL);

    typedef int (*fn_act)(void*, int, void*);
    typedef int (*fn_sp)(void*, int, void*);
    fn_act try_act = (fn_act)(s_base + 0x1179AF4);
    fn_sp use_sp = (fn_sp)(s_base + 0x1174300);

    int fired = 0;
    if (st->action == AT_ACT_RANGED) {
        if (dist < 3.6f) {
            if (can_act) try_act(player_pc, 8, NULL); // Dodge back to ranged distance first
            return;
        }
        if (can_act || can_att) fired = try_act(player_pc, 1, NULL);
    } else if (st->action == AT_ACT_LIGHT) {
        if (can_act || can_att || att_win) fired = try_act(player_pc, 1, NULL);
    } else if (st->action == AT_ACT_DASH || st->action == AT_ACT_MEDIUM) {
        if (can_act || can_att || att_win) fired = try_act(player_pc, 32, NULL);
    } else if (st->action == AT_ACT_HEAVY) {
        if (can_act || can_att || att_win) fired = try_act(player_pc, 0x100, NULL);
    } else if (st->action == AT_ACT_DODGE) {
        if (can_act) fired = try_act(player_pc, 8, NULL);
    } else if (st->action == AT_ACT_SIDESTEP_LEFT) {
        if (can_act) fired = try_act(player_pc, 64, NULL);
    } else if (st->action == AT_ACT_SIDESTEP_RIGHT) {
        if (can_act) fired = try_act(player_pc, 128, NULL);
    } else if (st->action == AT_ACT_SP1) {
        if (can_act || att_win) fired = use_sp(player_pc, 1, NULL);
    } else if (st->action == AT_ACT_SP2) {
        if (can_act || att_win) fired = use_sp(player_pc, 2, NULL);
    } else if (st->action == AT_ACT_SP3) {
        if (can_act || att_win) fired = use_sp(player_pc, 3, NULL);
    }

    if (fired) {
        AT_LOG("[AUTOTEST] STEP_EXEC idx=%d rep=%d/%d action=%d dist=%.2f",
               s_script_idx, s_script_rep + 1, st->repeat, (int)st->action, dist);
        s_script_rep++;
        s_script_step_start_ms = now_ms;
        if (s_script_rep >= st->repeat) {
            s_script_idx++;
            s_script_rep = 0;
        }
    }
}

void autotest_on_simulate_tick(void* player_pc, int pidx) {
    if (!autotest_is_active() || pidx != 0 || !ptr_sane(player_pc) || !s_base) return;
    uint64_t now_ms = at_now_ms();

    if (!s_combat_injected) {
        s_combat_injected = 1;
        s_combat_start_ms = now_ms;
        s_last_snap_ms = now_ms;

        if (s_sc.p0_mana >= 0.0f) {
            skill_set_mana(0, s_sc.p0_mana);
            AT_LOG("[AUTOTEST] INJECT_MANA target=P0 mana=%.2f", s_sc.p0_mana);
        }
        if (s_sc.p1_mana >= 0.0f) {
            skill_set_mana(1, s_sc.p1_mana);
            AT_LOG("[AUTOTEST] INJECT_MANA target=P1 mana=%.2f", s_sc.p1_mana);
        }
        for (int i = 0; i < s_sc.initial_buff_count; i++) {
            AutotestInitBuff* b = &s_sc.initial_buffs[i];
            for (int k = 0; k < b->stacks; k++) {
                skill_apply_buff_dur(b->target_player, b->mod_id, b->duration_s);
            }
            AT_LOG("[AUTOTEST] INJECT_BUFF target=P%d id=%s dur=%.2f stacks=%d",
                   b->target_player, b->mod_id, b->duration_s, b->stacks);
        }

        int af_want = (s_sc.script_len == 0) ? s_sc.auto_fight : 0;
        ((void(*)(int, void*))(s_base + 0xC9D9A0))(af_want, NULL); // AutoFightManager.ToggleAutoFight
        AT_LOG("[AUTOTEST] FIGHT_READY p0=%s p1=%s auto_fight=%d",
               skill_get_bot_id(0), skill_get_bot_id(1), af_want);
        emit_snapshot(0);
    }

    if (s_sc.script_len > 0 && s_script_idx < s_sc.script_len) {
        drive_script_step(player_pc, now_ms);
        if (s_script_idx >= s_sc.script_len && s_sc.auto_fight) {
            ((void(*)(int, void*))(s_base + 0xC9D9A0))(1, NULL); // Hand over to AutoFight after script finishes
            AT_LOG("[AUTOTEST] SCRIPT_FINISHED -> handing off to AutoFight");
        }
    } else if (s_sc.auto_fight) {
        int af_active = ((int(*)(void*))(s_base + 0xC9CEB0))(NULL);
        if (!af_active) {
            ((void(*)(int, void*))(s_base + 0xC9D9A0))(1, NULL);
        }
    }

    uint64_t elapsed = now_ms - s_combat_start_ms;
    if (now_ms - s_last_snap_ms >= 500) {
        s_last_snap_ms = now_ms;
        emit_snapshot(elapsed);
    }

    if (!s_scenario_done) {
        float p0_hp = skill_get_hp_ratio(0);
        float p1_hp = skill_get_hp_ratio(1);
        if (elapsed >= (uint64_t)s_sc.max_duration_ms || p0_hp <= 0.001f || p1_hp <= 0.001f) {
            s_scenario_done = 1;
            emit_snapshot(elapsed);
            AT_LOG("[AUTOTEST] SCENARIO_DONE name=%s elapsed=%llums p0_hp=%.2f p1_hp=%.2f",
                   s_sc.name, (unsigned long long)elapsed, p0_hp, p1_hp);
        }
    }
}

#endif /* TFTF_AUTOTEST */
