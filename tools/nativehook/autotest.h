#ifndef TFTF_AUTOTEST_H
#define TFTF_AUTOTEST_H

#include <stddef.h>
#include <stdint.h>

typedef void (*autotest_inline_hook_fn)(void* target, void* detour, void** orig);
typedef void* (*autotest_strnew_fn)(const char* str);
typedef void* (*autotest_objnew_fn)(void* klass);

#ifdef TFTF_AUTOTEST

#define AUTOTEST_MAX_INITIAL_BUFFS 16
#define AUTOTEST_MAX_SCRIPT_STEPS 32

typedef enum {
    AT_ACT_NONE = 0,
    AT_ACT_WAIT,
    AT_ACT_DASH,
    AT_ACT_LIGHT,
    AT_ACT_MEDIUM,
    AT_ACT_HEAVY,
    AT_ACT_RANGED,
    AT_ACT_BLOCK,
    AT_ACT_DODGE,
    AT_ACT_SIDESTEP_LEFT,
    AT_ACT_SIDESTEP_RIGHT,
    AT_ACT_SP1,
    AT_ACT_SP2,
    AT_ACT_SP3,
    AT_ACT_APPLY_BUFF,
    AT_ACT_SET_MANA,
    AT_ACT_SET_HP
} AutotestActionType;

typedef struct {
    int target_player; // 0 = P0, 1 = P1
    char mod_id[64];
    float duration_s;
    int stacks;
} AutotestInitBuff;

typedef struct {
    AutotestActionType action;
    int duration_ms; // hold duration for BLOCK or wait duration for WAIT
    int repeat;
    int target_player; // -1 = script owner, 0 = P0, 1 = P1
    char mod_id[64];
    float float_val;
    int stacks;
} AutotestScriptStep;

typedef struct {
    int active;
    char name[64];
    char banner[128];
    char qid[32];
    char p0_bid[64];
    char p1_bid[64];
    float p0_mana;     // < 0 means leave default
    float p1_mana;     // < 0 means leave default
    float p0_hp_ratio; // < 0 means leave default
    float p1_hp_ratio; // < 0 means leave default
    int auto_fight;
    int freeze_enemy_ai; // -1 = use user_settings, 0 = off, 1 = on
    int dummy_invincible;
    int player_invincible;
    int max_duration_ms;
    int initial_buff_count;
    AutotestInitBuff initial_buffs[AUTOTEST_MAX_INITIAL_BUFFS];
    int script_len;
    AutotestScriptStep script[AUTOTEST_MAX_SCRIPT_STEPS];
    int p1_script_len;
    AutotestScriptStep p1_script[AUTOTEST_MAX_SCRIPT_STEPS];
} AutotestScenario;

void autotest_init(void);
int autotest_is_active(void);
const char* autotest_get_p0_bid(void);
const char* autotest_get_p1_bid(void);
int autotest_override_freeze_enemy_ai(void);
int autotest_override_player_invincible(void);
int autotest_is_dummy_invincible(void);

int autotest_set_scenario_json(const char* json, size_t len);
int autotest_run_scenario_json(const char* json, size_t len);
int autotest_is_ready(void);
size_t autotest_get_scenario_json(char* out, size_t max_out);

void autotest_log_append(const char* line);
void autotest_log_clear(void);
size_t autotest_get_logs(char* out, size_t max_out);

void autotest_install_hooks(uintptr_t il2cpp_base,
                            autotest_inline_hook_fn hook_fn,
                            autotest_strnew_fn strnew_fn,
                            autotest_objnew_fn objnew_fn);

void autotest_on_team_select_intro(void* tsp);
void autotest_on_prefight_ready(void* pfs);
void autotest_on_prefight_exit(void);
void autotest_on_combat_start(void);
void autotest_on_simulate_tick(void* player_pc, int pidx);
void autotest_set_intended_special_tier(int tier);

#else

static inline void autotest_init(void) {}
static inline int autotest_is_active(void) { return 0; }
static inline const char* autotest_get_p0_bid(void) { return NULL; }
static inline const char* autotest_get_p1_bid(void) { return NULL; }
static inline int autotest_override_freeze_enemy_ai(void) { return -1; }
static inline int autotest_override_player_invincible(void) { return -1; }
static inline int autotest_is_dummy_invincible(void) { return 0; }
static inline void autotest_log_append(const char* line) { (void)line; }
static inline void autotest_install_hooks(uintptr_t il2cpp_base, autotest_inline_hook_fn hook_fn, autotest_strnew_fn strnew_fn, autotest_objnew_fn objnew_fn) {
    (void)il2cpp_base; (void)hook_fn; (void)strnew_fn; (void)objnew_fn;
}
static inline void autotest_on_team_select_intro(void* tsp) { (void)tsp; }
static inline void autotest_on_prefight_ready(void* pfs) { (void)pfs; }
static inline void autotest_on_prefight_exit(void) {}
static inline void autotest_on_combat_start(void) {}
static inline void autotest_on_simulate_tick(void* player_pc, int pidx) { (void)player_pc; (void)pidx; }

#endif /* TFTF_AUTOTEST */

#endif /* TFTF_AUTOTEST_H */
