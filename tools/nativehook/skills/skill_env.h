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
const char* skill_get_bot_id(int player_index);

// 全局战斗状态访问器 (读/写)
int skill_get_p1_buffs_nullified(void);
void skill_set_p1_buffs_nullified(int val);

// 远程加成与能量流失状态设置
void skill_set_ranged_boost(int player_index, uint64_t duration_ms, float dmg_bonus, float spd_bonus);
void skill_set_power_leak(int player_index, uint64_t duration_ms, float step);
void skill_set_power_lock(int target_player_index, uint64_t duration_ms);

// 不可阻挡霸体状态设置与查询
void skill_set_unstoppable(int player_index, uint64_t duration_ms);
int skill_is_unstoppable(int player_index);

// 生命值与能量操作
float skill_get_hp_ratio(int player_index);
float skill_get_hp(int player_index);
float skill_get_max_hp(int player_index);
float skill_get_attack(int player_index);
void skill_heal(int player_index, float amount);
void skill_deal_damage(int target_player_index, float damage);
void skill_add_mana(int player_index, float norm_mana);
void skill_set_mana(int player_index, float norm_mana);
float skill_get_mana(int player_index);
int skill_is_special_attacking(int player_index);

// 格挡与控制
uint64_t skill_get_block_enter_ms(int player_index);
void skill_stun_player(int target_player_index, float duration_s);

// Buff / Debuff 活性与层数查询
int skill_has_buff(int player_index, const char* buff_id_substr);
int skill_count_buffs(int player_index, const char* buff_id_substr);

// Buff 与修饰器主动施加与消耗
void skill_apply_buff(int player_index, const char* mod_id);
void skill_apply_buff_dur(int player_index, const char* mod_id, float override_dur);
void skill_consume_buff(int player_index, const char* mod_id, int count);
int skill_fuse_target_debuffs(int target_player_index);

// 警车近战增益层数与充能状态查询/打断
int skill_get_prowl_melee_stacks(int player_index);
int skill_prowl_is_charging(int player_index);
void skill_prowl_finish_charge(int player_index, const char* reason);

// 重击状态实时查询 (包括蓄力与飞行/动作全程)
int skill_is_heavy_attacking(int player_index);

// 特殊技状态实时查询 (0=未放, 1=正在释放 S1/S2/S3)
int skill_is_special_attacking(int player_index);

#ifdef __cplusplus
}
#endif
