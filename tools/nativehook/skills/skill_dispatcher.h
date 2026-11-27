#pragma once
#include "skill_types.h"

#ifdef __cplusplus
extern "C" {
#endif

// 初始化派发系统
void skill_dispatcher_init(uintptr_t base_addr);

// 战斗重置回调
void skill_dispatch_fight_reset(void);

// 命中伤害分发
void skill_dispatch_hit_connected(SkillHitContext* ctx);

// Buff 施加过滤分发 (返回 1 表示已被某技能接管判定，*out_allowed 为结果；返回 0 表示未接管，走原生逻辑)
int skill_dispatch_buff_gate(SkillBuffGateContext* ctx, int* out_allowed);

// Buff 施加成功后回调分发
void skill_dispatch_buff_applied(SkillBuffAppliedContext* ctx);

// 闪避检定分发 (返回 1 表示已被某技能接管判定，*out_evade 为结果；返回 0 表示未接管，走原生逻辑)
int skill_dispatch_evade_check(SkillEvadeContext* ctx, int* out_evade);

// TestRoll 触发判定分发 (返回 1 表示已被某技能接管判定，*out_res 为结果；返回 0 表示未接管，走原生逻辑)
int skill_dispatch_test_roll(SkillTestRollContext* ctx, int* out_res);
void skill_dispatch_test_roll_post(SkillTestRollContext* ctx, int roll_result);

// 新一轮打击命中解析开始通知 & 闪避触发通知 & 通用英雄名解析
void skill_dispatch_hit_begin(void);
void skill_dispatch_evade_triggered(int evader_player_index, int is_ranged);
const char* skill_dispatch_get_display_name(const char* bot_id);

// 能量获取率倍率修正分发 (返回倍率，默认 1.0f)
float skill_dispatch_power_gain_rate_mod(int player_index);

// 远程子弹反射检定分发 (返回 1 表示已被某技能接管判定，*out_reflect_mod 为反弹倍率；返回 0 表示走原生逻辑)
int skill_dispatch_reflect_proj(int player_index, float* out_reflect_mod);

// 弹丸飞行速度倍率修正分发 (返回倍率，默认 1.0f)
float skill_dispatch_projectile_speed(int player_index, int is_heavy);

// 每帧模拟驱动
void skill_dispatch_simulation_tick(uint64_t now_ms);

// 动作状态变化分发
void skill_dispatch_block_state(int player_index, int entered);
void skill_dispatch_dodge_enter(int player_index);
void skill_dispatch_hitreact_enter(int player_index);
void skill_dispatch_attack_start(int player_index, int action_type);

// 单次打击事件终态结算分发 (含统一“落空”状态机判定)
void skill_dispatch_attack_ended(SkillAttackEndContext* ctx);
// 必杀技状态机进出分发 (sp_level: 1=SP1, 2=SP2, 3=SP3; entered: 1=进入, 0=退出)
void skill_dispatch_special_state(int player_index, int sp_level, int entered);

// 动态被动暴击率加权分发
float skill_dispatch_crit_chance_mod(int player_index, int atk_level);
// 暴击判定结果分发 (在 GetDamageInflicted 计算暴击伤害倍率前调用)
void skill_dispatch_crit_rolled(int player_index, int atk_level, int is_last_hit, int is_crit);

#ifdef __cplusplus
}
#endif
