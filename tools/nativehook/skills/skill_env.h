#pragma once
#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

// 日志与 HUD Overlay 提示
void skill_log(const char* fmt, ...);
void skill_overlay(const char* fmt, ...);

// 时间与随机数
uint64_t skill_now_ms(void);
float skill_random_float(void); // 0.0f .. 1.0f

// 角色与队伍判定
int skill_is_p0_bc(void* bc);
int skill_is_p0_attr(void* attr);
int skill_obj_ok(void* ptr);

// 全局战斗状态访问器 (读/写)
int skill_get_p1_buffs_nullified(void);
void skill_set_p1_buffs_nullified(int val);

// 远程加成与能量流失状态设置
void skill_set_ranged_boost(int player_index, uint64_t duration_ms, float dmg_bonus, float spd_bonus);
void skill_set_power_leak(int player_index, uint64_t duration_ms, float step);
void skill_set_power_lock(int target_player_index, uint64_t duration_ms);

#ifdef __cplusplus
}
#endif
