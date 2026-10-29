# TFTF 优先待办战技机制复用与研发可行性深度分析报告
*(TFTF Priority Abilities Mechanism Reuse & Engineering Feasibility Analysis)*

> **生成时间**：2026-10-29 10:46:09  
> **分析基准**：Upstash KV 非冲突优先战技全集（**167 项**，涵盖 **29 位机体**）  
> **底层引擎对照**：`Server/abilities/core.py` (18类机制工厂)、`tools/nativehook/skills/` (24个C技能模块与dispatcher)  
> **技术契约验证**：严格对齐 `tools/validate_bot_ability.py` 反编译契约约束与 `combat-test-cases.md` 六大战斗质量门禁  
---

## 1. 报告概述与分析范围 (Executive Summary & Scope)

本报告专门针对《优先角色能力代码库全量比对与四分类裁定报告》所裁定的 **167 项非冲突待实现战技**（排除 62 项已在代码中完整落地的冲突冗余项，包含 96 项完全新的、49 项增补的、22 项调整的）进行底层机制复用评估与研发可行性技术解构。

### 1.1 三分类复用度全景统计

| 机制分类级别 | 核心判定标准 | 战技数量 | 占比 | 涉及英雄数 | 主要技术实现方案 | 研发成本与风险 |
| :--- | :--- | :---: | :---: | :---: | :--- | :--- |
| **级别 1：完全套用已有机制**<br>*(Directly Reusable)* | 100% 对应 `core.py` 核心工厂函数，原生触发器与目标，无需 C 代码 | **67 项** | **40.1%** | 24 位 | 纯 Python 数据配置脚本，调用工厂函数并填入数值 | **极低**（批量自动化生成，测试零风险） |
| **级别 2：衍生已有机制**<br>*(Derived / Composite)* | 现有机制复合组合、模式互斥切换、状态联动门禁、承伤截断或阈值分段判定 | **96 项** | **57.5%** | 26 位 | 多 StatMod 组合联动 + 轻量 NativeHook 回调门禁拦截 | **中等**（单英雄联调，逻辑可自洽闭环） |
| **级别 3：全新机制**<br>*(Novel Mechanisms)* | 涉及跨帧伤害历史队列回溯、高频仿真时钟充能衰减、复杂吟唱打断 | **4 项** | **2.4%** | 3 位 | NativeHook 专用微秒级状态机与环形缓冲队列研发 | **较高**（需专题攻坚与实机战斗帧率防线） |
| **合计 (Total)** | **全量非冲突待办战技总集** | **167 项** | **100.0%** | **29 位** | **分层落地，敏捷攻坚** | **整体架构复用度达 97.6%** |

### 1.2 核心结论速览

1. **超高复用率（97.6%）**：167 项待办战技中，**163 项**（占比 97.6%）可直接复用或衍生现有成熟机制架构，仅 **4 项**（占比 2.4%）需要突破底层全新引擎逻辑。
2. **风险极度收敛**：全新机制全部集中在 3 位特征英雄（**震荡波**的回溯、**惊破天**的0.065s充能与大帝意志、**千斤顶**的4s重击升级构建），其余 26 位机体均可在现有 Python+NativeHook 架构下直接快速开发落地。
3. **研发效率预期**：级别 1 基础能力可支撑后续智能体通过脚本化批量生产（首期覆盖 40%+），级别 2 能力按机体模板化组装，级别 3 能力安排独立专题突破。

## 2. 机制复用判定准则与技术门槛 (Evaluation Criteria & Technical Gates)

为确保工程实施的统一性与防御性，确立以下三级机制判定铁律：

### 2.1 级别 1【完全套用已有机制】(Directly Reusable)

- **准入条件 (Checklist)**：

  1. 技能效果 100% 映射至 `Server/abilities/core.py` 封装的核心工厂函数之一；

  2. 触发条件 `tr` 为原生支持事件（`onHit`, `onCrit`, `onSpecial1Activate`, `onSpecial2Activate`, `onSpecial3Activate`, `onSpecialHit`, `onPlayerStateEnter` 等）；

  3. 作用作用域 `trs` 采用原生标准标签（`level=Light,Medium,Heavy`, `level=Special1`, `dmgFlags=LastHit`, `state=Block/Dash/Dodge`）；

  4. 目标 `ta` 为纯正 `self` 或 `opponent`，作用类别 `mt` 为 `buff`, `debuff` 或 `passive`；

  5. **无需编写任何 C 语言 Hook**，仅需在 `Server/abilities/bots/<hero>.py` 中调用工厂函数并填入数值参数。

### 2.2 级别 2【衍生已有机制】(Derived / Minor Extension)

- **准入条件 (Checklist)**：

  1. 核心效果本质上仍由现有工厂函数构成，但包含**复合多效果联动**（如命中时自身获得攻击Buff同时给敌方上破甲Debuff）；

  2. 包含**模式互斥与状态机切换**（如幻影 K.E.R.S 破坏/失能/敏捷三模式切换，进入一种需自动移除其余两种）；

  3. 包含**跨状态条件门禁**（如黄豹禁疗效果绑定对方流血状态存续，流血结束禁疗自解）；

  4. 包含**伤害/效果随条件浮动换算**（如根据对手剩余能量反比线性放大伤害倍率，或每损失20%血量堆叠1层增益）；

  5. **技术支撑**：Python 侧多个 StatMod 组合烘焙，或配合 NativeHook 现有的 `on_buff_gated`, `on_buff_applied`, `on_evade_check` 等回调拦截完成。

### 2.3 级别 3【全新机制】(Novel Underlying Mechanisms)

- **准入条件 (Checklist)**：

  1. 涉及全新的战斗时空物理规则、跨帧承伤历史滚动记录、或高频毫秒级物理仿真状态机；

  2. 客户端 IL2CPP 完全没有内置对应的 `BuffEffect`，且无法通过静态 Wire JSON 数据包描述；

  3. **技术支撑**：必须在 `tools/nativehook/skills/bots/` 中深度编写专用 C 运行时拦截器，维护私有数据结构与帧时钟。


## 3. 已有机制库全景矩阵 (Existing Mechanism Architecture Matrix)

### 3.1 核心工厂函数库 (`Server/abilities/core.py` 18大武器库)

| 序号 | 工厂函数名称 | 属性代码 (`t`) | 目标与类型 | 默认 PUA 图标与色系 | 典型应用技能 |
| :---: | :--- | :---: | :---: | :--- | :--- |
| 1 | `make_bleed_statmod` | `dmg_bleed` | `opponent` / `debuff` | `\uE401` 鲜血红 (`EF4444`) | 黄豹暴击流血、横炮流血、犀牛远程流血 |
| 2 | `make_burn_statmod` | `dmg_burn` | `opponent` / `debuff` | `\uE41D` 火焰橙 (`EF4444`) | 钢锁重击燃烧、横炮SP2燃烧、黄蜂勇士SP3燃烧 |
| 3 | `make_shock_statmod` | `dmg_shock` | `opponent` / `debuff` | `\uE914` 离子红 (`EF4444`) | 千斤顶SP1震击、红蜘蛛零射线、惊天雷SP3震击 |
| 4 | `make_direct_dmg_statmod` | `dmg_direct` | `opponent` / `passive` | 无呼出图标 | 狂飙黑暗场直伤、阿尔茜爆头直伤 |
| 5 | `make_unstoppable_statmod` | `unstoppable` | `self` / `buff` | `\uE915` 霸体金 (`FFE000`) | 汽车大师前冲霸体、野牛狂暴霸体、飞毛腿残血霸体 |
| 6 | `make_attack_boost_statmod` | `attack_buff` | `self` / `buff` | `\uE406` 狂怒金 (`FF8800`) | G1擎天柱SP1加攻、野牛冲锋近战增益、天火远程增益 |
| 7 | `make_armor_up_statmod` | `armor_up` | `self` / `buff` | `\uE517` 坚盾青 (`29EBF4`) | G1铁皮开局重甲、野牛天然护甲、猩猩队长格挡护甲 |
| 8 | `make_armor_break_statmod` | `armor_break` | `opponent` / `debuff` | `\uE516` 破甲红 (`EF4444`) | G1擎天柱SP1/SP2破甲、补天士重击破甲 |
| 9 | `make_crit_rate_statmod` | `crit_rate` | `self` / `buff` | `\uE406` 琥珀金 (`FF8800`) | 横炮暴击率堆叠、小黄蜂后闪暴击几率 |
| 10 | `make_crit_damage_statmod` | `crit_damage` | `self` / `buff` | `\uE406` 琥珀金 (`FF8800`) | 电影铁皮SP2暴伤加成、横炮暴击伤害 |
| 11 | `make_stun_statmod` | `stun` | `opponent` / `debuff` | `\uE605` 眩晕黄 (`FFE000`) | 千斤顶SP1眩晕、狂飙反制眩晕、热破重击眩晕 |
| 12 | `make_power_leak_statmod` | `power_gain` (负值) | `opponent` / `debuff` | `\uE607` 控能红 (`EF4444`) | 千斤顶特殊技能量流失、反冲暴击吸气 |
| 13 | `make_power_lock_statmod` | `power_lock` | `opponent` / `debuff` | `\uE523` 禁锢红 (`EF4444`) | 黄豹SP3能量锁定、警车SP3能量锁定 |
| 14 | `make_ranged_boost_statmod` | `ranged_buff` | `self` / `buff` | `\uE41B` 射手橙 (`FF8800`) | 警车SP2远程增益、黄蜂勇士远程射速增益 |
| 15 | `make_nullify_statmod` | `nullify` | `opponent` / `debuff` | `\uE950` 虚空青 (`29EBF4`) | 红蜘蛛零射线驱散、狂飙黑暗场驱散、补天士近战驱散 |
| 16 | `make_evade_grant_statmod` | `evade_melee` / `ranged`| `self` / `buff` | `\uE509`/`\uE518` 敏捷绿 | 小黄蜂后闪规避、路障击倒规避、反冲前冲规避 |
| 17 | `make_evade_consume_statmod`| `remove` | `self` / `buff` | `\uE509` 规避消耗 | 小黄蜂规避动作触发后清除 Buff 并呼出跳字 |
| 18 | `make_heal_statmod` | `heal` | `self` / `buff` | `\uE503`/`\uE60E` 生命绿 | 救护车自我诊断治疗、抢劫修复战技 |


### 3.2 NativeHook C 运行时回调拦截矩阵 (`tools/nativehook/skills/`)

| 回调函数名 | 拦截介入点 | 业务机制赋能 | 典型代表机体 |
| :--- | :--- | :--- | :--- |
| `on_hit_connected` | 命中判定结算瞬间 | 动态伤害倍率放大、按层数动态增伤、吸血换算、流血触发 | 黄豹、狂飙、钢锁、天火、反冲、威震天 |
| `on_buff_gated` | 施加 Buff 前置过滤 | 动作段数过滤（仅 LastHit 放行）、减益免疫守护门禁 | 阿尔茜踢击门禁、黄豹能量免疫、千斤顶末段判定 |
| `on_buff_applied` | 施加 Buff 响应完成 | 延时状态清理（钢锁恐龙之怒 1.0s 延时净化）、模式互斥驱散 | 钢锁、阿尔茜、热破、狂飙 |
| `on_evade_check` | 规避几率判定拦截 | 强制闪避成功、特定攻击等级（如远程重击）绝对穿透/免伤 | 黄豹重击穿透、反冲前冲闪避、风刃重击无视远程 |
| `on_power_gain_rate` | 能量获取率计算 | 能量涌动功率倍率动态缩放、狂暴减益 | 天火、震天尊 |
| `on_reflect_proj` | 投射物即将命中 | 远程子弹反弹与护盾偏折 | 天火 |
| `on_projectile_speed` | 子弹发射出膛 | 改变投射物飞行速度（加速/减速子弹） | 威震天融合炮 |
| `on_attack_start` | 攻击动作发起瞬间 | 动态霸体判定（汽车大师冲锋距离 >= 10.0m 赋予霸体） | 汽车大师、横炮、反冲、滑流 |
| `on_simulation_tick` | 物理帧每帧时钟步进 | 持续能量生成、定时倒计时、充能衰减状态机 | 电影大黄蜂、黄豹、震天尊、亡灵天尊 |
| `on_fight_reset` | 战斗重置或KO | 私有计时器、计数器、连击堆叠状态清零 | 全员 24 个 Native 模块必挂 |


## 4. 待办战技三分类详尽评估清单 (Detailed Categorization & Feasibility Matrix)

### 4.1 级别 1：完全套用已有机制清单 (Tier 1: Directly Reusable, 共 67 项)

> **实施指南**：此类战技无需任何 C 语言改动。开发者只需在 `Server/abilities/bots/<hero>.py` 中引入对应的 `make_*_statmod` 工厂函数，将官方描述中的伤害数值、持续时间 `duration`、触发概率 `chance` 与触发事件 `trigger` 填入字典，即可由游戏客户端原生 IL2CPP 引擎完美解析运行。

| 序号 | 机体 (`bot_id`) | 技能 ID | 分类 | 中文名称 / 英文名称 | 对应核心工厂函数 | 推荐实现参数与落地说明 |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | **录音机**<br>`blaster_gs_leader2016` | `2419` | `passive` | **放大充能**<br>*Amp Charge* | `make_ranged_boost_statmod` | 机制与触发器完全契合工厂函数 make_ranged_boost_statmod，只需在 Server/abilities/bots/ 中调用并配置特殊技释放远程增益 |
| 2 | **录音机**<br>`blaster_gs_leader2016` | `2421` | `passive` | **震击**<br>*Shock* | `make_shock_statmod` | 机制与触发器完全契合工厂函数 make_shock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 3 | **录音机**<br>`blaster_gs_leader2016` | `2423` | `signature` | **回血**<br>*Repair* | `make_heal_statmod` | 机制与触发器完全契合工厂函数 make_heal_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 4 | **打击**<br>`breakdown_gs` | `3506` | `sp1` | **能量流失**<br>*Power Leak* | `make_power_leak_statmod` | 机制与触发器完全契合工厂函数 make_power_leak_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 5 | **打击**<br>`breakdown_gs` | `3508` | `sp3` | **远程减益**<br>*Ranged Debuff* | `make_ranged_boost_statmod` | 机制与触发器完全契合工厂函数 make_ranged_boost_statmod，配置 ta='opponent' 与 mt='debuff' 施加远程削弱 |
| 6 | **打击**<br>`breakdown_gs` | `3512` | `sp1` | **暴击几率**<br>*Crit Rate* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 7 | **打击**<br>`breakdown_gs` | `3513` | `passive` | **近战规避**<br>*Melee Evade* | `make_evade_grant_statmod` | 机制与触发器完全契合工厂函数 make_evade_grant_statmod，只需在 Server/abilities/bots/ 中调用并配置近战规避参数 |
| 8 | **打击**<br>`breakdown_gs` | `3514` | `sp2` | **燃烧**<br>*Burn* | `make_burn_statmod` | 机制与触发器完全契合工厂函数 make_burn_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 9 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2441` | `passive` | **暴击几率增益**<br>*Crit Rate Buff* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 10 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2450` | `sp1` | **暴击伤害**<br>*Crit Damage* | `make_crit_damage_statmod` | 机制与触发器完全契合工厂函数 make_crit_damage_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 11 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2451` | `sp2` | **能量锁定**<br>*Power Lock* | `make_power_lock_statmod` | 机制与触发器完全契合工厂函数 make_power_lock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 12 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2452` | `sp3` | **暴击几率增益**<br>*Crit Rate Buff* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 13 | **黄豹**<br>`cheetor_bw_transmetal` | `2476` | `sp1` | **流血**<br>*Bleed* | `make_bleed_statmod` | 机制与触发器完全契合工厂函数 make_bleed_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 14 | **黄豹**<br>`cheetor_bw_transmetal` | `2479` | `sp3` | **能量锁定**<br>*Power Lock* | `make_power_lock_statmod` | 机制与触发器完全契合工厂函数 make_power_lock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 15 | **黄豹**<br>`cheetor_bw_transmetal` | `2480` | `sp3` | **能量燃烧**<br>*Power Burn* | `make_burn_statmod` | 机制与触发器完全契合工厂函数 make_burn_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 16 | **克劳莉娅**<br>`chromia_gs_kabam` | `2488` | `sp2` | **流血**<br>*Bleed* | `make_bleed_statmod` | 机制与触发器完全契合工厂函数 make_bleed_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 17 | **克劳莉娅**<br>`chromia_gs_kabam` | `2487` | `sp1` | **流血**<br>*Bleed* | `make_bleed_statmod` | 机制与触发器完全契合工厂函数 make_bleed_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 18 | **克劳莉娅**<br>`chromia_gs_kabam` | `2491` | `sp3` | **流血**<br>*Bleed* | `make_bleed_statmod` | 机制与触发器完全契合工厂函数 make_bleed_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 19 | **克劳莉娅**<br>`chromia_gs_kabam` | `2492` | `signature` | **规避**<br>*Evade* | `make_evade_grant_statmod` | 机制与触发器完全契合工厂函数 make_evade_grant_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 20 | **狂飙**<br>`cyclonus_gs_uw06` | `2972` | `passive` | **黑暗能量**<br>*Dark Energy* | `make_attack_boost_statmod` | 机制与触发器完全契合工厂函数 make_attack_boost_statmod，只需在 Server/abilities/bots/ 中调用并配置气槽填满攻击增益 |
| 21 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3525` | `passive` | **修复**<br>*Repair* | `make_heal_statmod` | 机制与触发器完全契合工厂函数 make_heal_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 22 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3526` | `sp1` | **流血**<br>*Bleed* | `make_bleed_statmod` | 机制与触发器完全契合工厂函数 make_bleed_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 23 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3527` | `sp1` | **暴击几率**<br>*Crit Rate* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 24 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3528` | `sp2` | **暴击几率**<br>*Crit Rate* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 25 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3530` | `sp3` | **流血**<br>*Bleed* | `make_bleed_statmod` | 机制与触发器完全契合工厂函数 make_bleed_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 26 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3531` | `sp3` | **能量锁定**<br>*Power Lock* | `make_power_lock_statmod` | 机制与触发器完全契合工厂函数 make_power_lock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 27 | **G1擎天柱**<br>`fte_optimus_gs_t3` | `2357` | `passive` | **攻击增益**<br>*Attack Buff* | `make_attack_boost_statmod` | 机制与触发器完全契合工厂函数 make_attack_boost_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 28 | **惊破天**<br>`galvatron_gs_voyager2016` | `3057` | `passive` | **暴击几率**<br>*Crit Rate* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 29 | **惊破天**<br>`galvatron_gs_voyager2016` | `3059` | `sp1` | **眩晕**<br>*Stun* | `make_stun_statmod` | 机制与触发器完全契合工厂函数 make_stun_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 30 | **反冲**<br>`kickback_gs_kabam` | `3102` | `sp1` | **震击**<br>*Shock* | `make_shock_statmod` | 机制与触发器完全契合工厂函数 make_shock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 31 | **反冲**<br>`kickback_gs_kabam` | `3103` | `sp2` | **暴击几率**<br>*Crit Rate* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 32 | **反冲**<br>`kickback_gs_kabam` | `3104` | `sp2` | **能量流失**<br>*Power Leak* | `make_power_leak_statmod` | 机制与触发器完全契合工厂函数 make_power_leak_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 33 | **反冲**<br>`kickback_gs_kabam` | `3105` | `sp2` | **流血**<br>*Bleed* | `make_bleed_statmod` | 机制与触发器完全契合工厂函数 make_bleed_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 34 | **反冲**<br>`kickback_gs_kabam` | `3107` | `sp3` | **修复**<br>*Repair* | `make_heal_statmod` | 机制与触发器完全契合工厂函数 make_heal_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 35 | **反冲**<br>`kickback_gs_kabam` | `3106` | `sp3` | **能量流失**<br>*Power Leak* | `make_power_leak_statmod` | 机制与触发器完全契合工厂函数 make_power_leak_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 36 | **电影威震天**<br>`megatron_cin_rotf` | `3109` | `sp2` | **远程增益**<br>*Ranged Buff* | `make_ranged_boost_statmod` | 机制与触发器完全契合工厂函数 make_ranged_boost_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 37 | **电影威震天**<br>`megatron_cin_rotf` | `3118` | `passive` | **天然护甲**<br>*Permanent Armor* | `make_armor_up_statmod` | 机制与触发器完全契合工厂函数 make_armor_up_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 38 | **电影威震天**<br>`megatron_cin_rotf` | `3119` | `passive` | **不可阻挡**<br>*Unstoppable* | `make_unstoppable_statmod` | 机制与触发器完全契合工厂函数 make_unstoppable_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 39 | **电影威震天**<br>`megatron_cin_rotf` | `3120` | `passive` | **攻击增益**<br>*Attack Buff* | `make_attack_boost_statmod` | 机制与触发器完全契合工厂函数 make_attack_boost_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 40 | **G1威震天**<br>`megatron_gs_leader2015` | `3126` | `passive` | **不可阻挡**<br>*Unstoppable* | `make_unstoppable_statmod` | 机制与触发器完全契合工厂函数 make_unstoppable_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 41 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715902` | `sp3` | **黑暗燃烧**<br>*Dark Burn* | `make_burn_statmod` | 机制与触发器完全契合工厂函数 make_burn_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 42 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715903` | `sp3` | **能量窃取**<br>*Power Steal* | `make_power_leak_statmod` | 机制与触发器完全契合工厂函数 make_power_leak_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 43 | **幻影**<br>`mirage_gs_deluxe2016` | `2706` | `passive` | **重击净化**<br>*Heavy Purify* | `make_nullify_statmod` | 机制与触发器完全契合工厂函数 make_nullify_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 44 | **搅拌者**<br>`mixmaster_cin_rotf` | `3184` | `passive` | **暴击伤害**<br>*Crit Damage* | `make_crit_damage_statmod` | 机制与触发器完全契合工厂函数 make_crit_damage_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 45 | **搅拌者**<br>`mixmaster_cin_rotf` | `3186` | `passive` | **暴击几率**<br>*Crit Rate* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 46 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3535` | `sp1` | **能量燃烧**<br>*Power Burn* | `make_burn_statmod` | 机制与触发器完全契合工厂函数 make_burn_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 47 | **犀牛**<br>`rhinox_gs_voyager2014` | `2774` | `passive` | **近战增益**<br>*Melee Buff* | `make_attack_boost_statmod` | 机制与触发器完全契合工厂函数 make_attack_boost_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 48 | **犀牛**<br>`rhinox_gs_voyager2014` | `2792` | `sp3` | **流血**<br>*Chainguns of Doom* | `make_bleed_statmod` | 机制与触发器完全契合工厂函数 make_bleed_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 49 | **补天士**<br>`rodimusprime_gs_mp09` | `2798` | `passive` | **近战驱散**<br>*Melee Nullify* | `make_nullify_statmod` | 机制契合工厂函数 make_nullify_statmod，配置 trigger="onPlayerAttackHit", trigger_scope="level=Light,Medium", nullify_type="buff", nullify_count=1，分别配置近战与护甲增益驱散实例 |
| 50 | **震荡波**<br>`shockwave_gs` | `3302` | `sp1` | **震击**<br>*Shock* | `make_shock_statmod` | 机制与触发器完全契合工厂函数 make_shock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 51 | **震荡波**<br>`shockwave_gs` | `3300` | `passive` | **震击**<br>*Shock* | `make_shock_statmod` | 机制与触发器完全契合工厂函数 make_shock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 52 | **震荡波**<br>`shockwave_gs` | `3308` | `sp3` | **震击**<br>*Shock* | `make_shock_statmod` | 机制与触发器完全契合工厂函数 make_shock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 53 | **横炮**<br>`sideswipe_gs` | `2840` | `passive` | **暴击伤害**<br>*Crit Damage* | `make_crit_damage_statmod` | 机制与触发器完全契合工厂函数 make_crit_damage_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 54 | **横炮**<br>`sideswipe_gs` | `2838` | `sp2` | **近战规避**<br>*Melee Evade* | `make_evade_grant_statmod` | 机制与触发器完全契合工厂函数 make_evade_grant_statmod，只需在 Server/abilities/bots/ 中调用并配置近战规避参数 |
| 55 | **闹翻天**<br>`skywarp_gs_leader2015` | `3328` | `sp3` | **能量窃取**<br>*Power Steal* | `make_power_leak_statmod` | 机制与触发器完全契合工厂函数 make_power_leak_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 56 | **闹翻天**<br>`skywarp_gs_leader2015` | `3326` | `sp1` | **能量燃烧**<br>*Power Burn* | `make_burn_statmod` | 机制与触发器完全契合工厂函数 make_burn_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 57 | **滑流**<br>`slipstream_gs` | `3354` | `passive` | **远程驱散**<br>*Ranged Nullify* | `make_nullify_statmod` | 机制与触发器完全契合工厂函数 make_nullify_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 58 | **声波**<br>`soundwave_gs` | `3395` | `passive` | **震击**<br>*Shock* | `make_shock_statmod` | 机制与触发器完全契合工厂函数 make_shock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 59 | **声波**<br>`soundwave_gs` | `3397` | `sp1` | **眩晕**<br>*Stun* | `make_stun_statmod` | 机制与触发器完全契合工厂函数 make_stun_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 60 | **声波**<br>`soundwave_gs` | `3398` | `sp1` | **能量流失**<br>*Power Leak* | `make_power_leak_statmod` | 机制与触发器完全契合工厂函数 make_power_leak_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 61 | **声波**<br>`soundwave_gs` | `3399` | `sp2` | **震击**<br>*Shock* | `make_shock_statmod` | 机制与触发器完全契合工厂函数 make_shock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 62 | **声波**<br>`soundwave_gs` | `3400` | `sp3` | **震击**<br>*Shock* | `make_shock_statmod` | 机制与触发器完全契合工厂函数 make_shock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 63 | **声波**<br>`soundwave_gs` | `3402` | `sp3` | **眩晕**<br>*Stun* | `make_stun_statmod` | 机制与触发器完全契合工厂函数 make_stun_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 64 | **声波**<br>`soundwave_gs` | `3403` | `sp3` | **能量锁定**<br>*Power Lock* | `make_power_lock_statmod` | 机制与触发器完全契合工厂函数 make_power_lock_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 65 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3471` | `signature` | **远程增益**<br>*Ranged Buff* | `make_ranged_boost_statmod` | 机制与触发器完全契合工厂函数 make_ranged_boost_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 66 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3472` | `passive` | **远程增益**<br>*Ranged Buff* | `make_ranged_boost_statmod` | 机制与触发器完全契合工厂函数 make_ranged_boost_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |
| 67 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3475` | `sp1` | **暴击几率**<br>*Crit Rate* | `make_crit_rate_statmod` | 机制与触发器完全契合工厂函数 make_crit_rate_statmod，只需在 Server/abilities/bots/ 中调用并配置参数 |


### 4.2 级别 2：衍生已有机制清单 (Tier 2: Derived / Minor Extension, 共 96 项)

> **实施指南**：此类战技核心效果仍依赖基础工厂，但存在状态互斥、组合双向施加、专属外观、伤害截断或与对手特定姿态联动的触发条件。可通过在 Python 侧同时构建多个 StatMod，或在现有的 `tools/nativehook/skills/bots/` 回调中编写 5~15 行微量 C 代码实现精准联动。

| 序号 | 机体 (`bot_id`) | 技能 ID | 分类 | 中文名称 / 英文名称 | 衍生复合特征 | 推荐组合设计与 C Hook 扩展方案 |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2445` | `signature` | **蜂之勇气**<br>*Bee Brave* | 能量持续自然涌动或能量减益底层免疫门禁，需NativeHook底层能量判定支持 | 通过 `power_gain` 设定轻微持续产气，在 `on_simulation_tick` 中达到 2 格或触发特殊技时主动调用清除。 |
| 2 | **黄豹**<br>`cheetor_bw_transmetal` | `2462` | `sp1` | **阻止修复**<br>*Repair Block* | 跨状态生命周期绑定（如禁疗持续直至流血结束），需跨Buff联动监听或底层门禁移除 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 3 | **黄豹**<br>`cheetor_bw_transmetal` | `2463` | `sp2` | **伤害放大**<br>*Damage Increase* | 根据对手剩余能量反比动态放大伤害倍率，需动态倍率计算或分段区间修饰器 | 在 `on_hit_connected` 中读取对手当前能量槽浮点数 `opp_mana / 300.0f`，按 `1.0f - mana_ratio` 线性放大伤害输出。 |
| 4 | **黄豹**<br>`cheetor_bw_transmetal` | `2478` | `sp3` | **伤害放大**<br>*Damage Increase* | 根据对手剩余能量反比动态放大伤害倍率，需动态倍率计算或分段区间修饰器 | 在 `on_hit_connected` 中读取对手当前能量槽浮点数 `opp_mana / 300.0f`，按 `1.0f - mana_ratio` 线性放大伤害输出。 |
| 5 | **克劳莉娅**<br>`chromia_gs_kabam` | `2481` | `signature` | **瞄准目标**<br>*Eyes on Target* | 能量持续自然涌动或能量减益底层免疫门禁，需NativeHook底层能量判定支持 | 通过 `power_gain` 设定轻微持续产气，在 `on_simulation_tick` 中达到 2 格或触发特殊技时主动调用清除。 |
| 6 | **惊破天**<br>`galvatron_gs_voyager2016` | `3055` | `passive` | **远程伤害**<br>*Ranged Damage* | 效果幅度依据黑暗能量充能层数动态缩放或特殊技强制赋予30层充能，需层数关联判定 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 7 | **惊破天**<br>`galvatron_gs_voyager2016` | `3056` | `passive` | **暴击伤害**<br>*Crit Damage* | 效果幅度依据黑暗能量充能层数动态缩放或特殊技强制赋予30层充能，需层数关联判定 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 8 | **惊破天**<br>`galvatron_gs_voyager2016` | `3048` | `sp3` | **黑暗能量充能**<br>*Dark Energy Charge* | 效果幅度依据黑暗能量充能层数动态缩放或特殊技强制赋予30层充能，需层数关联判定 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 9 | **惊破天**<br>`galvatron_gs_voyager2016` | `3058` | `passive` | **黑暗燃烧**<br>*Dark Burn* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 10 | **惊破天**<br>`galvatron_gs_voyager2016` | `3060` | `sp2` | **黑暗燃烧**<br>*Dark Burn* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 11 | **天火**<br>`jetfire_gs_leader2014` | `2667` | `sp1` | **远程增益**<br>*Ranged Buff* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 12 | **天火**<br>`jetfire_gs_leader2014` | `2682` | `sp3` | **震击**<br>*Shock* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 13 | **天火**<br>`jetfire_gs_leader2014` | `2683` | `sp1` | **能量锁定**<br>*Power Lock* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 14 | **天火**<br>`jetfire_gs_leader2014` | `2684` | `sp2` | **护盾**<br>*Shield* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 15 | **天火**<br>`jetfire_gs_leader2014` | `2685` | `sp2` | **修复阻止**<br>*Repair Block* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 16 | **电影威震天**<br>`megatron_cin_rotf` | `3122` | `passive` | **电荷消耗**<br>*Consume charges* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 17 | **G1威震天**<br>`megatron_gs_leader2015` | `3127` | `signature` | **毫不留情**<br>*No Mercy* | 命中后从多个减益或增益池中随机抽取生效，需Python权重判定或NativeHook掷骰随机分发 | 通过 Python `random.choice` 或 NativeHook `on_hit_connected` 中 `rand() % 3` 动态分发攻击/破甲/能量功率减益之一。 |
| 18 | **幻影**<br>`mirage_gs_deluxe2016` | `2687` | `signature` | **K.E.R.S**<br>*The Kinetic Energy Recovery System generates the following buffs when activating Special Attacks:* | 多模式互斥状态机切换（进入当前模式自动驱散其余模式），需组合StatMod或NativeHook模式监听 | 定义破坏/失能/敏捷 3 个互斥 tag，通过 `on_buff_applied` 监听进入事件，调用 `Remove_BuffEffect` 抹杀其余 2 个模式。 |
| 19 | **幻影**<br>`mirage_gs_deluxe2016` | `2700` | `sp1` | **破坏模式**<br>*Disruption Mode* | 多模式互斥状态机切换（进入当前模式自动驱散其余模式），需组合StatMod或NativeHook模式监听 | 定义破坏/失能/敏捷 3 个互斥 tag，通过 `on_buff_applied` 监听进入事件，调用 `Remove_BuffEffect` 抹杀其余 2 个模式。 |
| 20 | **幻影**<br>`mirage_gs_deluxe2016` | `2701` | `sp2` | **失能模式**<br>*Incapacitation Mode* | 多模式互斥状态机切换（进入当前模式自动驱散其余模式），需组合StatMod或NativeHook模式监听 | 定义破坏/失能/敏捷 3 个互斥 tag，通过 `on_buff_applied` 监听进入事件，调用 `Remove_BuffEffect` 抹杀其余 2 个模式。 |
| 21 | **幻影**<br>`mirage_gs_deluxe2016` | `2702` | `sp3` | **敏捷模式**<br>*Agility Mode* | 多模式互斥状态机切换（进入当前模式自动驱散其余模式），需组合StatMod或NativeHook模式监听 | 定义破坏/失能/敏捷 3 个互斥 tag，通过 `on_buff_applied` 监听进入事件，调用 `Remove_BuffEffect` 抹杀其余 2 个模式。 |
| 22 | **幻影**<br>`mirage_gs_deluxe2016` | `2704` | `passive` | **能量涌动**<br>*Power Flow* | 多模式互斥状态机切换（进入当前模式自动驱散其余模式），需组合StatMod或NativeHook模式监听 | 定义破坏/失能/敏捷 3 个互斥 tag，通过 `on_buff_applied` 监听进入事件，调用 `Remove_BuffEffect` 抹杀其余 2 个模式。 |
| 23 | **幻影**<br>`mirage_gs_deluxe2016` | `2705` | `passive` | **重击远程穿透**<br>*Heavy Range Immunue* | 动作期间穿透或免疫远程投射物伤害，需NativeHook拦截命中判定或结合动作状态机 | 在 `on_evade_check` 中监听 `state == HeavyCharge`，检定对手是否释放 Ranged，强制置规避概率为 1.0f 并免伤。 |
| 24 | **搅拌者**<br>`mixmaster_cin_rotf` | `3185` | `passive` | **特殊技消耗**<br>*Special consumption* | 充能消耗与效果缩放转换机制（按消耗层数动态放大持续时间或伤害），需层数动态换算 | 在释放特殊技时读取当前 charge 层数，按层数动态缩放 `dmg_burn` 或 `shield` 持续时间，随后清零充能。 |
| 25 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3180` | `passive` | **重击冲压**<br>*Ram With Heavy Attacks* | 命中后从多个减益或增益池中随机抽取生效，需Python权重判定或NativeHook掷骰随机分发 | 通过 Python `random.choice` 或 NativeHook `on_hit_connected` 中 `rand() % 3` 动态分发攻击/破甲/能量功率减益之一。 |
| 26 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3184` | `signature` | **公路之王**<br>*King of the Road* | 血量阶梯式动态阈值层数结算（每损失X%生命值堆叠一层增益），需多阈值分段判定 | 在 `on_simulation_tick` 监控 `current_hp / max_hp`，每跨过一个 20% 区间动态给自身叠加 1 层 `attack_buff` (+60%)。 |
| 27 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3187` | `sp3` | **攻击增益**<br>*Attack Buff* | 伤己伤敌双向作用机制（释放高额增伤同时反噬扣除自身血量），需双重作用目标（self + opponent）组合配置 | 构建双修饰器：Mod1 `attack_buff` 赋予自身 150% 增伤；Mod2 `dmg_direct` 作用于 `self` 扣除 90% ATK 血量，设血量保护保底 1 点 HP。 |
| 28 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3536` | `sp3` | **冲压**<br>*Ram* | 命中后从多个减益或增益池中随机抽取生效，需Python权重判定或NativeHook掷骰随机分发 | 通过 Python `random.choice` 或 NativeHook `on_hit_connected` 中 `rand() % 3` 动态分发攻击/破甲/能量功率减益之一。 |
| 29 | **震荡波**<br>`shockwave_gs` | `3285` | `sp2` | **护甲穿透**<br>*Armor Piercing* | 动作期间穿透或免疫远程投射物伤害，需NativeHook拦截命中判定或结合动作状态机 | 在 `on_evade_check` 中监听 `state == HeavyCharge`，检定对手是否释放 Ranged，强制置规避概率为 1.0f 并免伤。 |
| 30 | **闹翻天**<br>`skywarp_gs_leader2015` | `3329` | `sp3` | **能量涌动**<br>*Power Flow* | 能量持续自然涌动或能量减益底层免疫门禁，需NativeHook底层能量判定支持 | 通过 `power_gain` 设定轻微持续产气，在 `on_simulation_tick` 中达到 2 格或触发特殊技时主动调用清除。 |
| 31 | **声波**<br>`soundwave_gs` | `3396` | `passive` | **能量涌动**<br>*Power Flow* | 跨状态生命周期绑定（如禁疗持续直至流血结束），需跨Buff联动监听或底层门禁移除 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 32 | **声波**<br>`soundwave_gs` | `3401` | `sp2` | **能量涌动**<br>*Power Flow* | 跨状态生命周期绑定（如禁疗持续直至流血结束），需跨Buff联动监听或底层门禁移除 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 33 | **千斤顶**<br>`wheeljack_gs_mp20` | `3658` | `passive` | **成功**<br>*Success* | 千斤顶升级子系统交互（同色成功回血、特殊技全重抽、特殊技升级同化对齐），需与升级状态机联动 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 34 | **千斤顶**<br>`wheeljack_gs_mp20` | `3659` | `sp2` | **刷新升级**<br>*Upgrade Randomize* | 千斤顶升级子系统交互（同色成功回血、特殊技全重抽、特殊技升级同化对齐），需与升级状态机联动 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 35 | **千斤顶**<br>`wheeljack_gs_mp20` | `3660` | `sp3` | **升级对齐**<br>*Upgrade Normalize* | 千斤顶升级子系统交互（同色成功回血、特殊技全重抽、特殊技升级同化对齐），需与升级状态机联动 | 在 Python 侧组合两个标准工厂修饰器，配合特定 `trs` 作用域实现复合生效。 |
| 36 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3529` | `sp2` | **规避克制**<br>*Anti Evade* | 破除/封锁对手规避判定（Anti-Evade debuff），阻断对手闪避几率检定 | Python 侧通过 `make_statmod_appearance` 构建规避抑制减益；在 NativeHook `on_evade_check` 拦截对手规避检定，命中若带有该减益则强行置 `evade_chance = 0.0f`。 |
| 37 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3476` | `sp1` | **规避克制**<br>*Anti Evade* | SP1 最后一击施加规避克制减益，封锁对手闪避判定 | Python 侧构建规避克制外观；在 NativeHook `on_evade_check` 中检定若目标带有减益则使闪避判定失效，确保后续攻击必中。 |
| 38 | **震荡波**<br>`shockwave_gs` | `3303` | `sp2` | **阻止修复**<br>*Repair Block* | SP2 命中施加阻止修复减益，阻断对手生命恢复与自我修复结算 | Python 侧使用 `make_statmod_appearance` 构建禁疗红图标减益；在 NativeHook 拦截 `PlayerController.ApplyHealing`，检定若目标存在此减益则将治疗量置零。 |
| 39 | **震荡波**<br>`shockwave_gs` | `3309` | `sp3` | **阻止修复**<br>*Repair Block* | SP3 终结命中施加高持续阻止修复减益，阻断对手生命恢复机制 | Python 侧构建 `repair_block` 减益；在 NativeHook 中拦截生命恢复结算函数，目标带有时治疗量强行截断为 0。 |
| 40 | **闹翻天**<br>`skywarp_gs_leader2015` | `3327` | `sp2` | **修复阻止**<br>*Repair Block* | SP2 命中施加修复阻止减益，阻断对手一切治疗与生命恢复 | Python 侧构建禁疗减益；在 NativeHook 拦截 `ApplyHealing`，带减益目标生命恢复量置零。 |
| 41 | **录音机**<br>`blaster_gs_leader2016` | `2409` | `signature` | **吸收护盾**<br>*Absorption Shield* | 护盾状态下赋予对远程攻击的不可阻挡状态（无受创硬直且不带光圈）并提供 20% 额外免伤 | 在 `on_hitreact_enter` 中检测自身拥有护盾且攻击类型为远程时豁免受创硬直；在 `on_damage_calculate` 中施加 0.80x 伤害减免。 |
| 42 | **录音机**<br>`blaster_gs_leader2016` | `2420` | `passive` | **干扰**<br>*Interference* | 普通远程命中/被防 80% 施加干扰减益，降低对手远程伤害 20% 并降低 50% 子弹飞行速度 | Python 侧配置 `ranged_buff` 负值减益；在 NativeHook `on_projectile_speed` 中检测发射方带有时，将投射物初速度缩放为 0.50x。 |
| 43 | **录音机**<br>`blaster_gs_leader2016` | `2422` | `passive` | **护盾**<br>*Shield* | 进入格挡获得护盾（降低 15% 承伤），松开格挡后延时 0.5 秒消失，每层放大充能额外延长 0.25 秒 | 挂载 `on_player_state_enter` (Block) 施加减伤护盾；在 `on_player_state_exit` 监听松开格挡，读取放大充能层数动态计算延时定时器 `0.5f + stacks * 0.25f` 后移除。 |
| 44 | **打击**<br>`breakdown_gs` | `3504` | `passive` | **护盾崩解**<br>*Shield Break* | 成功闪避对方重击获得护盾崩解增益（+50% 近战），近战命中时消耗该增益清除对方全部护盾并施加 50% 即时伤害 | 在 `on_evade_check` 成功规避重击时挂载增益；在 `on_hit_connected` 判定近战命中，调用 `Remove_BuffEffect(Shield)` 驱散对手全部护盾并结算 `make_direct_dmg_statmod(0.5f)`。 |
| 45 | **打击**<br>`breakdown_gs` | `3505` | `signature` | **晚期神经质**<br>*Terminal Paranoia* | 敌方血量 >50% 时获得近战规避（40% 几率，规避后 5s 冷却），敌方血量 <50% 时获得暴击率增益（40% 几率，暴击后 5s 冷却） | 在 `on_simulation_tick` 监控对手生命百分比切分双分支状态机；成功触发规避/暴击后切换为 5 秒灰色倒计时 Mod，冷却完毕后根据当前生命线重置激活。 |
| 46 | **打击**<br>`breakdown_gs` | `3515` | `sp2` | **确定性**<br>*Certainty* | 施加确定性减益，对手充满一格能量后必然强制释放 SP1（即使有 2/3 格气也强制出 SP1），释放后减益消耗 | IL2CPP 原生 StatMod 无法强制改写动作；需在 `tools/nativehook/skills/bots/skill_breakdown.c` 中拦截 `on_simulation_tick` 或 `AIController.DecideAction` / 输入控制流，检测对手能量槽满 1 格瞬间强制派发 SP1 动作指令。 |
| 47 | **打击**<br>`breakdown_gs` | `3516` | `sp3` | **确定性**<br>*Certainty* | 施加 2 层确定性减益，对手充满一格能量强制出 SP1（覆盖 2 次充能周期），释放后逐层消耗 | 在 NativeHook 中维护确定性层数计数器，对手每次能量达到阈值拦截其动作状态机强行切入 SP1，动作完成扣除 1 层直至归零。 |
| 48 | **黄豹**<br>`cheetor_bw_transmetal` | `2477` | `sp2` | **能量功率**<br>*Power Rate* | 获得能量功率增益，能量获取量增加 50%，持续 12 秒 | Python 侧使用 `make_statmod_appearance` 构建能量功率紫图标；在 NativeHook `on_power_gain_rate` 回调中将能量获取乘数放大 1.50x。 |
| 49 | **克劳莉娅**<br>`chromia_gs_kabam` | `2486` | `passive` | **减速**<br>*Deceleration* | 远程攻击命中/被防施加减速，每层降低对手能量功率 10% 且减速中绝对不触发规避 | Python 侧配置可叠加 `power_gain` 削减；在 NativeHook `on_evade_check` 中若检测对手带有减速减益，强制将规避率置零。 |
| 50 | **克劳莉娅**<br>`chromia_gs_kabam` | `2489` | `sp2` | **减速**<br>*Deceleration* | SP2 稳定施加长效减速减益（持续 9 秒，可叠加），压制能量功率并绝对禁止规避 | Python 侧配置基础属性减益；在 NativeHook 中联动 `on_power_gain_rate` (0.9x/层) 与 `on_evade_check` (绝对禁止)。 |
| 51 | **克劳莉娅**<br>`chromia_gs_kabam` | `2490` | `sp3` | **减速**<br>*Deceleration* | SP3 终结施加 23.6 秒超长减速减益，强力压制能量功率并阻绝对手任何规避触发 | Python 侧配置长持续减益参数；在 NativeHook 保持规避阻断与能量获取率压制。 |
| 52 | **克劳莉娅**<br>`chromia_gs_kabam` | `2493` | `signature` | **顶光区的炸弹**<br>*Acrolight Bomb* | 特殊技末段施加 5 秒定时炸弹，5 秒内若未被对手击中则引爆造成 100% 攻击力即时伤害并施加 2.5 秒眩晕 | 挂载 `on_hit_connected`（自身受击监听），若 5 秒内受到敌方命中则清除炸弹；5 秒倒计时结束未被打断则调用 `ApplyDamage` 与 `make_stun_statmod`。 |
| 53 | **飞过山**<br>`cliffjumper_gs_kabam` | `3541` | `sp2` | **无法格挡**<br>*Unblockable* | 若对手拥有至少 10 个玻璃瓦斯减益，此攻击的最后一击强制无法格挡 | 在 NativeHook `on_buff_gated` 或 `on_attack_hit_check` 中读取对手玻璃瓦斯层数，达到 10 层时动态给末段攻击注入 `Unblockable` 动作标志。 |
| 54 | **飞过山**<br>`cliffjumper_gs_kabam` | `3546` | `passive` | **特殊伤害**<br>*Special Damage* | 处于无任何伤害减益的纯净状态下使用特殊技，特殊技伤害提升 20% | 在特殊技发动瞬间遍历自身 `ActiveModList`，确认无 `debuff` 标签时，通过 `on_hit_connected` 动态放大特殊技伤害 1.20x。 |
| 55 | **飞过山**<br>`cliffjumper_gs_kabam` | `3547` | `passive` | **玻璃瓦斯减益**<br>*Glass Gas Debuff* | 远程攻击命中/被防 100% 施加玻璃瓦斯，降低对手格挡精通 5%（格挡承伤放大 5%）并提升飞过山特殊技伤害 5% | Python 侧使用 `make_statmod_appearance` 构建灰色瓦斯图标；在格挡承伤计算与特殊技结算中按瓦斯层数动态计算双向缩放。 |
| 56 | **飞过山**<br>`cliffjumper_gs_kabam` | `3548` | `passive` | **重击刷新**<br>*Heavy Refresh* | 重击命中瞬间，刷新并重置目标身上所有活跃玻璃瓦斯减益的倒计时 | 在 NativeHook `on_hit_connected` 监听重击命中，遍历对手身上的活跃 Mod 链表，将所有匹配玻璃瓦斯 ID 的 `remaining_timer` 重置为满额。 |
| 57 | **飞过山**<br>`cliffjumper_gs_kabam` | `3549` | `sp1` | **玻璃瓦斯减益**<br>*Glass Gas Debuff* | SP1 施加 1 层永久玻璃瓦斯减益并刷新所有带倒计时的玻璃瓦斯减益 | 组合配置永久 Mod（`duration=0.0`）与刷新逻辑，在动作命中时通过 NativeHook 重置限时层倒计时。 |
| 58 | **飞过山**<br>`cliffjumper_gs_kabam` | `3550` | `sp3` | **玻璃瓦斯减益**<br>*Glass Gas Debuff* | SP3 施加 5 层永久玻璃瓦斯，并将对手身上所有限时玻璃瓦斯减益全部永久化，末击暴击几率额外增加 60% | 在末段命中时遍历对手减益链表，将限时瓦斯替换为永久瓦斯 Mod 实例，末段通过 `make_crit_rate_statmod` 提升 60% 暴击。 |
| 59 | **狂飙**<br>`cyclonus_gs_uw06` | `2991` | `sp3` | **黑暗场**<br>*Dark Field* | 狂飙获得黑暗能量，并在 10 秒内连续周期性释放黑暗场脉冲驱散增益并造成伤害 | 在 `on_simulation_tick` 中维护 1.0 秒脉冲周期时钟，每秒触发一次 `make_direct_dmg_statmod` 与范围驱散判定。 |
| 60 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3516` | `signature` | **卑鄙胜者**<br>*Dirty Victory* | 重击命中 45% 概率窃取对手 10% 最大能量，并施加持续 5 秒造成 40% 伤害的流血 | 组合 `make_bleed_statmod` 与能量窃取逻辑，在 `on_hit_connected` 检定重击命中，从对手气槽扣除 10% 并转移至自身。 |
| 61 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3524` | `passive` | **不可防御**<br>*Unblockable* | 发动前冲攻击时有 25% 概率触发不可防御状态（动作期间即时呼出图标） | 挂载 `on_attack_start`，检定 `action == DashAttack`，随机 Roll 判定若 `< 0.25f` 则动态为该动作赋予破防属性。 |
| 62 | **红蜘蛛**<br>`fte_stars_gs_t3` | `2357` | `passive` | **零射线**<br>*Null Ray* | 基础远程命中 100% 驱散一个护甲/近战/攻击增益，驱散成功时追加 90% 攻击力的即时震击伤害 | 挂载 `on_hit_connected`，检测远程命中并调用 `PurgeBuff`，若成功清除目标一个增益则立即派发 `make_direct_dmg_statmod(0.9f)`。 |
| 63 | **天火**<br>`jetfire_gs_leader2014` | `2666` | `signature` | **损害控制**<br>*Damage Control* | 生命值 <75% 时按住格挡 1 秒消耗 1 个能量充能，在 0.5 秒内修复 6% 最大生命值 | 在 `on_simulation_tick` 监控格挡长按时间与当前血量阈值，满足条件时消耗 1 层充能并调用 `ApplyHealing(0.06f * max_hp)`。 |
| 64 | **天火**<br>`jetfire_gs_leader2014` | `2681` | `sp3` | **能量充能**<br>*Energy Charge* | 特殊技 3 释放完毕后稳定结算赋予自身 3 层专属能量充能资源 | Python 侧使用 `make_statmod_appearance` 构建专属紫色充能图标，通过 `stack=10` 支持后续战技消耗。 |
| 65 | **反冲**<br>`kickback_gs_kabam` | `3100` | `passive` | **消耗（发起重击）**<br>*Consume (Heavy start)* | 重击动作发起瞬间净化自身所有震击/能量汲取/锁定/功率减益，每移除一个转化为一层 2 秒获得 3% 能量的增益 | 挂载 `on_attack_start` (Heavy)，扫描自身减益链表，计数并移除匹配减益，按移除数量堆叠对应层数的能量获取 Buff。 |
| 66 | **反冲**<br>`kickback_gs_kabam` | `3101` | `passive` | **消耗（重击命中）**<br>*Consume (Heavy start)* | 重击命中瞬间驱散对手所有能量增益，每驱散一个自身获得一层 2 秒获得 3% 能量的增益 | 挂载 `on_hit_connected` (Heavy)，扫描对手增益链表并驱散，将驱散计数转化为自身能量获取层数。 |
| 67 | **电影威震天**<br>`megatron_cin_rotf` | `3107` | `signature` | **威震天万岁！**<br>*All Hail Megaton!* | 生命值降至 10% 以下在 3 秒内恢复 30% 最大生命值，单场仅生效一次，若单次致死过量伤害则跳过不触发直接 KO | 在受击伤害结算钩子中检定：若承伤后血量处于 `(0, 0.10 * max_hp]` 区间则激活 3 秒回血状态；若单次伤害直接将血量归零则不阻拦死亡。 |
| 68 | **电影威震天**<br>`megatron_cin_rotf` | `3108` | `sp1` | **伤害电荷**<br>*Impair Charge* | SP1 命中一次性给对手施加 10 层伤害电荷，作为重击与 SP3 的消耗资源 | Python 侧使用 `make_statmod_appearance` 配置红色可叠加电荷外观，`stack=30` 供连招系统调度。 |
| 69 | **电影威震天**<br>`megatron_cin_rotf` | `3121` | `passive` | **伤害电荷**<br>*Impair Charge* | 所有普通攻击与特殊技命中稳定施加 1 层伤害电荷，供后续重击/SP3 消耗 | Python 侧配置 `onHit` 触发器，多段打击持续堆叠伤害电荷资源计数器。 |
| 70 | **电影威震天**<br>`megatron_cin_rotf` | `3123` | `sp3` | **伤害电荷**<br>*Impair Charge* | SP3 首段施加 20 层电荷（每层 +5% 暴击几率已满 100%），末段必然暴击且每层电荷额外提升 2% 暴击伤害 | 组合 `make_crit_rate_statmod` 锁定满额暴击，末击读取当前电荷层数动态缩放暴击伤害倍率后清空消耗。 |
| 71 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715893` | `passive` | **狂怒遗迹**<br>*Relic of Fury* | 开局激活狂怒遗迹提升 60% 攻击力并削弱对手 20% 格挡精通，每充满一格能量与保存遗迹互斥轮转切换 | 在 NativeHook 中监听能量槽充满事件，执行狂怒遗迹与保存遗迹的进出切换，调用 `Remove_BuffEffect` 保持互斥。 |
| 72 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715894` | `passive` | **保存遗迹**<br>*Relic of Preservation* | 保存遗迹下伤害抗性提升 60%，并硬性限制对方任何单次攻击伤害上限为震天尊最大生命值的 20% | 挂载 `on_damage_calculate`，检定若处于保存遗迹状态，单次伤害若超过 `0.20 * max_hp` 则强制截断，满气切换至狂怒遗迹。 |
| 73 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715904` | `sp3` | **生命窃取**<br>*Life Steal* | 保存遗迹生效期间 SP3 首击 66% 窃取对手相当于自身 17.5% 最大生命值的血量（即便斩杀也全额恢复） | 在 `on_hit_connected` 判定保存遗迹前提，扣除对手对应数值生命并调用自身 `ApplyHealing`，不受对方残血限制。 |
| 74 | **幻影**<br>`mirage_gs_deluxe2016` | `2703` | `passive` | **护盾**<br>*Shield* | 对手发动特殊技时获得护盾，降低对手 90% 暴击伤害与远程伤害，直至幻影被击倒方才破除 | 监听对手 `onSpecialActivate` 施加特定减伤 Buff；挂载 `on_knockdown_enter` 监听倒地硬直，倒地时立即移除该护盾。 |
| 75 | **搅拌者**<br>`mixmaster_cin_rotf` | `3180` | `passive` | **酸液**<br>*Acid* | 远程攻击前两击 30% 施加酸液减益（攻击力 45% 伤害，持续 9 秒） | `core.py` 无酸液专属工厂；通过 `make_statmod_appearance` 定制腐蚀绿图标与标签，底层映射 `dmg_direct` / DOT 机制。 |
| 76 | **搅拌者**<br>`mixmaster_cin_rotf` | `3181` | `sp3` | **酸液**<br>*Acid* | SP3 施加长效酸液减益（攻击力 134% 伤害，持续 20 秒） | Python 侧使用自定义酸液外观与伤害参数，通过标准 DOT 契约挂载于对手。 |
| 77 | **搅拌者**<br>`mixmaster_cin_rotf` | `3182` | `sp1` | **酸液**<br>*Acid* | SP1 命中 50% 概率施加酸液减益（攻击力 80% 伤害，持续 10 秒） | Python 侧配置概率触发酸液 Mod，与 SP3/普攻酸液统一外观与图标色系。 |
| 78 | **搅拌者**<br>`mixmaster_cin_rotf` | `3183` | `passive` | **特殊伤害**<br>*Special Damage* | 每 5 秒获得一个特殊伤害增益（+27% 特殊伤害，最多叠加 6 层），通过 5 秒倒计时过渡后生成 | 采用暗天陨充能模式，在 `on_simulation_tick` 中循环 5 秒倒计时，到期后堆叠 1 层永久特殊伤害加成（上限 6 层）。 |
| 79 | **倾天柱**<br>`optimusprime_sg_voyager2015` | `3634` | `signature` | **暴虐火种**<br>*Spark of Tyranny* | 特殊技发动获得概率充能（+30% 破防概率直至触发消耗），不可防御命中额外获得下一次轻击/中击不可防御 | 在 NativeHook 中维护破防概率累加器；命中破防后挂载 1 次性 `Unblockable` 普攻触发器，消费后重置。 |
| 80 | **倾天柱**<br>`optimusprime_sg_voyager2015` | `3642` | `passive` | **逆境暴发**<br>*Struggle* | 处于任何伤害减益状态时自身攻击力提升 50%，不随减益数量重复叠加 | 挂载 `on_buff_applied` 与 `on_buff_removed`，动态检定自身是否存在 DOT 减益，二元激活/关闭 +50% 攻击力 Buff。 |
| 81 | **倾天柱**<br>`optimusprime_sg_voyager2015` | `3641` | `passive` | **减益控制**<br>*Debuff Control* | 处于伤害减益时重击命中对手，可将身上所有伤害减益强度降低 99%，但持续时间延长 300% | 挂载 `on_hit_connected` (Heavy)，遍历自身活跃 DOT 链表，将其实时伤害系数乘 0.01f，将剩余时间乘 4.0f。 |
| 82 | **倾天柱**<br>`optimusprime_sg_voyager2015` | `3643` | `passive` | **减益循环**<br>*Debuff Cycle* | 处于流血状态攻击施加燃烧、处于燃烧施加震击、处于震击施加酸液、处于酸液施加流血的多向相克循环反应 | 在 `on_hit_connected` 中依次检定自身持有的特定减益类型，条件命中时向对手施加下一顺位 DOT 减益。 |
| 83 | **犀牛**<br>`rhinox_gs_voyager2014` | `2769` | `passive` | **护盾**<br>*Shield* | 战斗开局 6 个护盾，单次承伤硬性截断为对手攻击力 80% 上限，受燃烧/震击减少 35%，受近战消耗，耗尽 8 秒充能刷新 | 挂载 `on_damage_calculate` 拦截单次承伤上限与属性减免；近战命中扣除护盾层数，计数归零开启 8 秒定时器重置 6 层护盾。 |
| 84 | **犀牛**<br>`rhinox_gs_voyager2014` | `2779` | `signature` | **超频**<br>*Overclock* | 护盾防御上限升级至 60% 对手攻击力，若单次攻击伤害超过 60%，反弹 1 层造成 160% 攻击力伤害的震击（防御不触发） | 挂载受创反弹钩子，非防御受击且伤害超额时，调用 `ApplyStatMod(make_shock_statmod(1.60f, 4.0f))` 实施反击震击。 |
| 85 | **震荡波**<br>`shockwave_gs` | `3277` | `passive` | **能量充能**<br>*Energy Charge* | 格挡远程能量攻击获得能量充能（最多 3 层），充能少于 3 个时格挡远程能量攻击承受 0 伤害 | 挂载格挡受击钩子，判定攻击类型为远程能量投射物时直接减免 100% 伤害并追加 1 层充能，上限 3 层。 |
| 86 | **震荡波**<br>`shockwave_gs` | `3301` | `sp1` | **能量充能**<br>*Energy Charge* | SP1 发动时无论命中与否均稳定获得 3 层能量充能，持续 6 秒 | Python 侧配置触发器为 `onSpecial1Activate`，通过标准资源修饰器赋予 3 层充能。 |
| 87 | **震荡波**<br>`shockwave_gs` | `3304` | `passive` | **能量充能**<br>*Energy Charge* | 技能发动时无论是否命中，得到 3 层能量充能，持续 6 秒 | 配置 `onSpecialActivate` 触发器，赋予自身 3 层能量充能。 |
| 88 | **震荡波**<br>`shockwave_gs` | `3307` | `sp3` | **能量充能**<br>*Energy Charge* | SP3 发动稳定获得 5 层能量充能，持续 7 秒 | 配置 `onSpecial3Activate` 触发器，一次性写入 5 层能量充能实例。 |
| 89 | **横炮**<br>`sideswipe_gs` | `2839` | `passive` | **能量获取**<br>*Power Gain* | 闪避远程普通攻击和远程重击时，1 秒内获得最大能量的 13% | 在 `on_evade_check` 检定规避动作，若规避对象为远程攻击，则触发持续 1.0 秒的能量注入，恢复 13% 能量槽。 |
| 90 | **闹翻天**<br>`skywarp_gs_leader2015` | `3323` | `passive` | **传送充能**<br>*Teleport Charge* | 每 8 秒自动获得传送充能（上限 3 层），受暴击 25%/50% 丢失充能，成功闪避特殊技获得充能 | 在 NativeHook 中运行 8 秒定时器堆叠充能；挂载受暴击钩子判定概率丢失；在 `on_evade_check` 闪避特殊技时补回充能。 |
| 91 | **闹翻天**<br>`skywarp_gs_leader2015` | `3324` | `passive` | **特殊伤害减益**<br>*Special Damage Debuff* | 远程攻击命中概率施加可叠加特殊伤害减益（普攻 20% 几率持续 5s，重击 50% 几率持续 9s，减少 10% 特殊伤害） | Python 侧使用 `make_statmod_appearance` 定制红色特殊伤害削弱减益，按轻/重远程分别配置对应触发率与时长。 |
| 92 | **闹翻天**<br>`skywarp_gs_leader2015` | `3325` | `passive` | **传送攻击**<br>*Teleport Attack* | 拥有传送充能时特殊技1和2变为传送攻击（专属动作改写、暴击率增加27%、不可防御、50%概率施加8秒能量锁定、100%净化震击） | NativeHook 挂载特殊技触发前置动作改写钩子；若拥有传送充能则覆写 SP1/SP2 动作容器并激活不可防御与暴击加成；命中后触发 50% 能量锁定并清除自身所有震击减益。 |
| 93 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3473` | `passive` | **特殊技伤害**<br>*Special Damage* | 生命值小于 25% 时，获得 30% 永久特殊技伤害加成 | 在 `on_simulation_tick` 监控生命线，一旦 `< 0.25 * max_hp` 激活永久特殊技增伤 Mod，血量恢复则自动清除。 |
| 94 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3474` | `passive` | **抗性减益**<br>*Resistance Debuff* | 远程命中与重击命中施加抗性减益（受到的伤害放大 30%） | Python 侧构建承伤放大减益外观；在 `on_damage_calculate` 中检定目标若有此减益，将全部受创伤害乘 1.30f。 |
| 95 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3477` | `sp2` | **抗性减益**<br>*Resistance Debuff* | SP2 最后一击施加持续 5 秒的 30% 抗性减益，放大后续伤害输出 | 配置特殊技末段触发器，施加统一抗性减益，与普攻/重击抗性减益无缝兼容。 |
| 96 | **千斤顶**<br>`wheeljack_gs_mp20` | `2888` | `signature` | **力量护盾**<br>*Force Shield* | 生命值被敌方攻击降至 75%、50% 或 25% 以下时激活力量护盾，100% 降低所有直伤 8 秒（不免 DOT） | 在受击结算中检测血量跨越 75%/50%/25% 阈值，触发持续 8 秒的力量护盾，拦截直伤并免除扣血，保留 DOT 伤害结算。 |


### 4.3 级别 3：全新机制清单 (Tier 3: Novel Underlying Mechanisms, 共 4 项)

> **实施指南**：此类战技属于 TFTF 引擎最底层的机制瓶颈，无法通过标准 JSON Wire 数据静态表达。必须在 `tools/nativehook/skills/bots/` 中新建专属 C 模块并注册至 `skill_dispatcher.c`，使用私有结构体与高频时钟驱动。

#### 4.3.1 [惊破天 `galvatron_gs_voyager2016`] 技能 ID: `3045` 【宇宙大帝的意志 / Will of Unicron】

- **技能定位**：`[signature]` 核心战略战技
- **核心瓶颈**：依据对手实时失去生命值百分比动态改写不可阻挡检定概率，需在受创前置拦截TestRoll并做浮点动态缩放
- **底层攻坚技术设计**：
  1. **受击前置挂载**：在 `skill_galvatron.c` 中挂载 `on_hit_connected`（承伤事件）与 `on_test_roll`。
  2. **动态血量换算**：获取对手实时血量 `float opp_hp_lost_pct = 1.0f - (opp->current_hp / opp->max_hp)`。
  3. **概率动态改写**：基础不可阻挡概率 $P = 15\% + (opp\_hp\_lost\_pct \times 70\%)$，当随机数 `roll < P` 时，强行赋予受击硬直豁免。


#### 4.3.2 [惊破天 `galvatron_gs_voyager2016`] 技能 ID: `3054` 【黑暗能量充能 / Dark Energy Charge】

- **技能定位**：`[passive]` 核心战略战技
- **核心瓶颈**：涉及远程格挡每0.065s高频充能1层与松开格挡每0.065s极速衰减状态机、30层锁定倒计时，需微秒级仿真tick驱动
- **底层攻坚技术设计**：
  1. **高频充能状态机**：在 `skill_galvatron.c` 中挂载 `on_simulation_tick`，以 65ms (0.065s) 为一个 Tick 周期。
  2. **距离与格挡判定**：每 Tick 读取自身动作状态 `state == Block` 且双方空间距离 `dist >= 5.0m`，则 `charge_stacks++`（上限 30 层）。
  3. **松开极速衰减**：若 `state != Block` 且尚未达到 30 层，每 65ms `charge_stacks--` 直至归零。
  4. **满层锁定与倒计时**：当 `charge_stacks == 30` 时，锁定充能并不再衰减，开启 6 秒超载倒计时，倒计时结束归零。


#### 4.3.3 [震荡波 `shockwave_gs`] 技能 ID: `3283` 【回溯 / Undo】

- **技能定位**：`[signature]` 核心战略战技
- **核心瓶颈**：涉及4秒跨帧历史承伤滑动窗口队列记录与到期瞬间全额回溯修复，需NativeHook深度时钟驱动
- **底层攻坚技术设计**：
  1. **数据结构**：在 `skill_shockwave.c` 中定义环形队列 `DamageHistoryQueue`（长度 120 帧，按每 100ms 记录 1 个承伤节点 `struct DamageNode { float damage; uint64_t timestamp; }`）。
  2. **承伤记录**：挂载 `on_hit_connected`（当作为受击方时），每受到一次攻击扣血，即时追加到队列尾部。
  3. **定时结算**：激活回溯 Buff（持续 4.0 秒），在 `on_simulation_tick` 中检测 4 秒到期，遍历队列计算近 4 秒内承受伤害总和 `total_recent_dmg`。
  4. **全额回溯**：调用 `PlayerController.ApplyHealing(total_recent_dmg)` 并派发 `_fth` 绿字跳字，清空历史队列。


#### 4.3.4 [千斤顶 `wheeljack_gs_mp20`] 技能 ID: `3657` 【升级 / Upgrade】

- **技能定位**：`[passive]` 核心战略战技
- **核心瓶颈**：重击发动4秒长吟唱构建升级、受暴击被打断、独立3槽随机生成与打断丢失最新升级，需重击吟唱控制器
- **底层攻坚技术设计**：
  1. **重击长吟唱拦截**：挂载 `on_attack_start`，检测 `action_type == HeavyAttack`，开启 4.0 秒吟唱计时器 `upgrade_chant_timer = 4.0f`。
  2. **受创打断监听**：在 `on_hitreact_enter` 监听受击硬直，若受暴击命中则强制置 `upgrade_chant_timer = 0`，判定构建失败。
  3. **槽位控制器**：维护 `uint8_t upgrade_slots[3]` 数组，构建完成随机填入 1 (进攻)、2 (防御)、3 (能量)。受暴击失去最新一个槽位。
  4. **同化触发**：当 `upgrade_slots[0] == upgrade_slots[1] == upgrade_slots[2]` 时，触发 `[3658] 成功` 结算 10%~20% 立即回血。


## 5. 典型复杂机体深度设计方案 (Deep Dives for Signature Bots)

### 5.1 震荡波 (Shockwave) 能量充能联动与回溯 (Undo) 算法设计

震荡波拥有科技系典型的时空逆转机制。其优先战技包含 11 项，核心机制链条如下：

```

             [受击承伤窗口]

    Enemy Attacks ───► on_hit_connected ───► DamageHistoryQueue (RingBuffer, 120 slots)

                             │                      ▲

                             ▼                      │

    [3283 回溯启动] ──► 4.0s Countdown Timer ───────────┤

                             │                      │

                   (到期 4.0s Tick Expiry)           │

                             │                      │

                             ▼                      │

                   Sum(Damage in 4s window) ────────┘

                             │

                             ▼

                PlayerController.ApplyHealing(Sum)

                Green Numbers Callout + Purge Debuffs

```

- **代码落地规范**：在 `Server/abilities/bots/shockwave.py` 中声明被动回溯壳修饰器 `shockwave_undo_state`；在 `tools/nativehook/skills/bots/skill_shockwave.c` 中完整实现上述滑动窗口环形缓冲。


### 5.2 惊破天 (Galvatron) 远程格挡充能衰减与宇宙大帝意志状态机

惊破天是典型的距离依赖高频蓄能机体：

1. **状态机方程**：

   $$\text{Stacks}(t + \Delta t) = \begin{cases} \min(\text{Stacks}(t) + 1, 30), & \text{if } \text{State} = \text{Block} \land \text{Dist} \ge 5.0\text{m} \\ \max(\text{Stacks}(t) - 1, 0), & \text{if } \text{State} \ne \text{Block} \land \text{Stacks} < 30 \\ 30, & \text{if Locked (6s Timer Active)} \end{cases}$$

2. **宇宙大帝意志动态概率**：

   $$P_{\text{unstoppable}} = 0.15 + 0.70 \times \left(1.0 - \frac{\text{HP}_{\text{opponent}}}{\text{MaxHP}_{\text{opponent}}}\right)$$

   在对方残血时近乎必定触发不可阻挡，形成终局压制。


### 5.3 幻影 (Mirage) K.E.R.S 三模式互斥切换与重击穿透免伤

幻影（Mirage）拥有 8 项优先战技，核心在于 K.E.R.S 系统：

- **破坏模式 (Disruption)**：远程暴击造成破甲。

- **失能模式 (Disable)**：远程暴击造成能量流失。

- **敏捷模式 (Agility)**：提升闪避几率与移动速度。

- **互斥裁定**：进入任一模式时，立即通过 `make_remove_statmod` 清除其余两项的 Mod ID，实现三选一轮转。

- **重击穿透**：重击蓄力期间挂载 `on_evade_check`，对所有远程投射物赋予 100% 穿透免伤。


## 6. 研发实施路径与质量门槛建议 (Roadmap & Quality Gates)

为了以最高工程质量完成上述 167 项战技落地，建议后续智能体严格按以下三阶段排期推进：

### 6.1 敏捷三阶段推进排期表

| 研发阶段 | 攻坚目标 | 涵盖机体与战技体量 | 关键交付物 | 质量验收标准 |
| :--- | :--- | :--- | :--- | :--- |
| **阶段一：基础能力批量生产**<br>*(Phase 1: Tier 1 Batch)* | 覆盖所有级别 1 标准机制，快速做大落地基本盘 | **67 项战技**（涵盖 24 位机体） | 批量生成/更新 `Server/abilities/bots/*.py` 模块 | 100% 通过 `tools/validate_bot_ability.py` 严格校验 |
| **阶段二：复合衍生战技攻坚**<br>*(Phase 2: Tier 2 Derivative)* | 实现多模式切换、条件门禁、双向反噬、伤害截断与分段判定 | **96 项战技**（涵盖 26 位机体） | 编写复合 StatMod 并在 NativeHook 挂载基础门禁回调 | 单机体技能测试套件全绿，Buff 圆环 UI 呼出正常 |
| **阶段三：全新底层机制突破**<br>*(Phase 3: Tier 3 Novel)* | 突破震荡波回溯、惊破天蓄能、千斤顶升级状态机 | **4 项战技**（震荡波、惊破天、千斤顶） | 编写专属 C 模块并编译进 `libnativehook.so` | 6大战斗质量门禁 (`combat-test-cases.md`) 0违规 0崩溃 |


### 6.2 质量门禁与契约合规红线 (Quality Gates & Pitfall Defense)

所有新编写的技能模块必须无条件恪守以下底层铁律：

1. **色值六位规范**：`tc`, `gt`, `gb`, `bc` 严禁带 `#` 前缀，必须为合法 6 位 Hex（如 `EF4444`, `29EBF4`），违者触发 IL2CPP 材质解析崩溃。

2. **列表包装红线**：`tr`, `uit`, `a`, `au` 必须使用 Python `list` 包装，严禁传裸字符串。

3. **每跳截断保护**：所有持续伤害类 DOT（流血、燃烧、震击），必须满足：

   $$\text{per\_tick} = \frac{\text{total\_dmg}}{\text{duration} \times 2.0} \ge 1.0$$

   防止浮点截断为 0 导致客户端跳字卡死。

4. **战斗真理源保护**：修改 NativeHook 时严禁弱化 `tools/nativehook/combat_truth_backup.c` 中定义的前冲霸体、连招链条与硬直规则，logcat 严禁出现 `[COMBAT_RULE_VIOLATION]`。
