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

#ifdef __cplusplus
}
#endif
