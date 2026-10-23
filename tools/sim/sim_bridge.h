#pragma once
#include <stdint.h>
#include <stdbool.h>

#ifdef _WIN32
#define SIM_API __declspec(dllexport)
#else
#define SIM_API
#endif

#ifdef __cplusplus
extern "C" {
#endif

// 基础战斗模拟器 C 接口 (供 Python ctypes 调用)
SIM_API int sim_init(const char* p0_bot_id, const char* p1_bot_id,
                     float p0_max_hp, float p1_max_hp,
                     float p0_atk, float p1_atk);

SIM_API void sim_reset(void);

SIM_API void sim_tick(uint32_t dt_ms);

SIM_API int sim_attack(int attacker_idx, int action_type, int hit_index,
                       int is_last_hit, int is_blocked);

SIM_API void sim_set_block(int player_idx, int is_blocking);

SIM_API int sim_dodge(int player_idx, int dodge_type);

SIM_API int sim_inject_buff(int target_idx, const char* mod_id,
                            float duration_s, int stacks);

SIM_API int sim_remove_buff(int target_idx, const char* mod_id, int count);

SIM_API int sim_get_state_json(char* out_buf, int max_len);

SIM_API int sim_pop_logs(char* out_buf, int max_len);

SIM_API int sim_pop_floaters(char* out_buf, int max_len);

#ifdef __cplusplus
}
#endif
