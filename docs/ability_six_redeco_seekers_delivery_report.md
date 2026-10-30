# TFTF 寻猎空军红蜘蛛重涂 6 机战技全量实施交付与验收报告
*(Transformers: Forged to Fight - 6 Starscream Redeco Seekers Abilities Full Delivery & Acceptance Report)*

> **首次实现日期**：2026-10-30  
> **报告维护**：TFTF Revival Engineering Team  
> **实施分支**：`ability-refactor`  
> **数据真理源**：Upstash KV 在线清单 (`tools/six_redeco_seekers_upstash.json`)、SQLite 官方战技库 (`Server/tftf_database.db`)  
> **实施范围**：涵盖“红蜘蛛重涂 Seekers”的**全部 6 位英雄**、**37 项核心战技**  
> **质量门禁体系**：底层 IL2CPP 数据契约校验器 (`tools/validate_bot_ability.py`) + 战斗物理仿真器全套门禁 (`tools/sim/run_tests.py`)  
> **测试验收状态**：**100% 全部通过 (60 位注册角色零报错全量回归，模拟器 22 组专属套件全绿)**

---

## 一、交付全景与概述 (Executive Summary)

针对 2026-10-29 夜间由用户在 Upstash KV 上更新并锁定的 6 位红蜘蛛重涂空军角色（Bitstream、Hotlink、Ionstorm、Novastorm、Acidstorm、Sunstorm），工程团队已完成全部战技数据的拉取、本地数据库同步、Python 能力模块构建、数据契约校验与仿真测试全套闭环。

系统总注册英雄数量从 54 位增至 **60 位**，官方能力库 StatMods 总数提升至 515 个，Appearances 达 436 个。

### 1.1 6 机交付总览

| 英雄名称 | 内部标识 (`bot_id`) | 职业/阵营 | 战技数 | 核心机制特征 | 契约校验 | 仿真测试 | 交付状态 |
| :--- | :--- | :---: | :---: | :--- | :---: | :---: | :---: |
| **比特流** (Bitstream) | `bitstream_gs_leader2015` | 科技 / 霸天虎 | 6 项 | 远程射击注入数据木马特殊技锁定 3 秒；开局 4 层数据防火墙伤害截断与护盾耗尽系统反噬震击；觉醒零日漏洞 60% 概率退回能量格并强锁 4 秒；SP1 脉冲能量锁定与 50% 眩晕；SP2 逻辑蠕虫能量窃取与流失；SP3 全盘系统重置清空能量与强效虚弱 | ✅ 0 ERRORS | ✅ 全绿 | **已交付** |
| **热链接** (Hotlink) | `hotlink_gs_leader2015` | 战术 / 霸天虎 | 6 项 | 天然免疫燃烧伤害；重击烈焰火海持续灼烧且对手燃烧时近战增伤 25%；半血熔岩充盈触发 6 秒霸体与近战叠加层；SP1 高温喷流灼烧与自身近战增益；SP2 熔火投弹 85% 灼烧与 50% 眩晕；SP3 烈焰地狱 100% 灼烧、护甲强化与 4 秒不可阻挡 | ✅ 0 ERRORS | ✅ 全绿 | **已交付** |
| **离子风** (Ionstorm) | `ionstorm_gs_leader2015` | 科技 / 霸天虎 | 6 项 | 基础射击高频电离冲击降低能量获取率 35%；重击电离破甲 30% 且 100% 驱散敌方护甲与不可阻挡霸体；觉醒电磁逆火反制特技并流失能量；SP1 高压电弧震击且对霸体破防增伤 50%；SP2 离子风暴 90% 破甲与 70% 震击；SP3 湮灭电离破甲 40% 与攻击暴增 30% | ✅ 0 ERRORS | ✅ 全绿 | **已交付** |
| **新星风** (Novastorm) | `novastorm_gs_leader2015` | 战术 / 霸天虎 | 6 项 | 远程射击概率施加核辐射热灼烧；5 倍数连击触发爆轰充能（重击必暴+暴伤提升）；觉醒热核殉爆（特技暴击引爆现有燃烧造成瞬时热爆发，无燃烧则附加高额燃烧）；SP1 辐射爆轰与暴伤提升；SP2 技能全程不可阻挡与双层重度燃烧；SP3 恒星坍缩歼灭三重核爆燃烧并即时扣除能量 | ✅ 0 ERRORS | ✅ 全绿 | **已交付** |
| **酸雨** (Acidstorm) | `acidstorm_gs_leader2015` | 科技 / 霸天虎 | 7 项 | 远程强酸侵蚀破甲；受击强酸飞溅反制削减护甲；重击强酸侵蚀 35% 与破甲 10%，对手酸蚀时全攻击增伤 20%；觉醒酸性气溶胶护盾（单次受击伤害上限截断为 70%，受击消耗反击一层酸化）；SP1 强酸喷雾；SP2 硫酸洪流 70% 酸化与 45% 破甲；SP3 暴雨倾盆双层强酸与 30% 极效破甲 | ✅ 0 ERRORS | ✅ 全绿 | **已交付** |
| **太阳风** (Sunstorm) | `sunstorm_gs_leader2015` | 战术 / 霸天虎 | 6 项 | 近战辐射撕裂流血与破甲；重击聚变灼烧、暴击追加辐射灼烧，对手灼烧时规避率压制 -35%；觉醒失控恒星反应堆过热（掉血转化为常驻近战攻击增益，上限 4 层）；SP1 太阳喷射与暴击强化；SP2 耀斑轰炸双层灼烧与 50% 眩晕；SP3 日冕风暴三层终极灼烧与暴伤飙升 35% | ✅ 0 ERRORS | ✅ 全绿 | **已交付** |
| **合计 (Total)** | **6 位重涂空军** | — | **37 项** | **6 角色官方全套技能库与战斗机制完整落地** | **60机体全绿** | **22套件全绿** | **全量达成** |

---

## 二、6 位红蜘蛛重涂英雄 37 项战技实施明细对照表

### 1. 比特流 (`bitstream_gs_leader2015`) - 6 项核心战技
*模块文件*：`Server/abilities/bots/bitstream.py`

| 技能ID | 分类 | 战技名称 (中/英) | 机制实现方案与参数细节 |
| :---: | :---: | :--- | :--- |
| **3612** | `basic` | **网络干扰射击**<br>*Trojan Shot* | 远程攻击命中注入木马，100% 概率施加持续 3.0 秒特殊技锁定 (`bitstream_ranged_trojan_lock`)，阻止对手使用特殊技。PUA: `\uE523`。 |
| **3613** | `passive` | **数据防火墙与系统反噬**<br>*Data Firewall & Backlash* | 开局获得 4 层防火墙护盾 (`bitstream_firewall_shield`, PUA: `\uE515`)，单次受击伤害上限截断为 75%；护盾耗尽触发对敌 4.0 秒震击 DOT (`bitstream_shield_backlash_shock`, 50% ATK, PUA: `\uE914`)。 |
| **3614** | `signature` | **零日漏洞拦截**<br>*Zero-Day Exploit Lock* | 敌方蓄满任意一整格能量时，60% 概率退回 1 格能量并施加 4.0 秒能量锁定 (`bitstream_sig_refund_lock`, PUA: `\uE523`)。 |
| **3615** | `sp1` | **干扰脉冲**<br>*Interference Pulse* | 最后一击 100% 施加 3.5 秒能量锁定 (`bitstream_sp1_power_lock`, PUA: `\uE523`)，50% 概率施加 1.5 秒眩晕 (`bitstream_sp1_stun`, PUA: `\uE605`)。 |
| **3616** | `sp2` | **逻辑蠕虫**<br>*Logic Worm* | 最后一击 100% 窃取对手能量，并在 5.0 秒内施加能量流失 (`bitstream_sp2_power_leak`, 扣除 0.60 格能量, PUA: `\uE607`)。 |
| **3617** | `sp3` | **全盘系统重置**<br>*System Reset* | 最后一击扣除对方全部能量，技能结束施加 6.0 秒能量锁定与 25% 攻击弱化 (`bitstream_sp3_drain_lock`, PUA: `\uE523`)。 |

---

### 2. 热链接 (`hotlink_gs_leader2015`) - 6 项核心战技
*模块文件*：`Server/abilities/bots/hotlink.py`

| 技能ID | 分类 | 战技名称 (中/英) | 机制实现方案与参数细节 |
| :---: | :---: | :--- | :--- |
| **3603** | `passive` | **燃烧免疫**<br>*Burn Immunity* | 常驻免疫燃烧减益效果 (`hotlink_burn_immune`)，受到灼烧时立即消除。PUA: `\uE517`。 |
| **3604** | `passive` | **烈焰猛火**<br>*Raging Inferno* | 重击命中 100% 施加 6.0 秒燃烧 (`hotlink_heavy_burn`, 60% ATK, PUA: `\uE517`)；对手处于燃烧时近战额外增伤 25% (`hotlink_burn_melee_boost`, PUA: `\uE412`)。 |
| **3605** | `signature` | **熔岩充盈**<br>*Magma Infusion* | 生命值低于 50% 触发：获得持续 6.0 秒不可阻挡 (`hotlink_sig_unstoppable`, PUA: `\uE915`)；期间近战命中燃烧敌人叠加 15% 近战增益（上限 3 层, PUA: `\uE412`）。 |
| **3606** | `sp1` | **高温喷流**<br>*Thermal Stream* | 最后一击 100% 施加 5.0 秒燃烧 (`hotlink_sp1_burn`, 50% ATK, PUA: `\uE41D`)；技能结束自身获得 20% 近战增益持续 6.0 秒 (`hotlink_sp1_melee_buff`, PUA: `\uE412`)。 |
| **3607** | `sp2` | **熔火投弹**<br>*Molten Bombardment* | 每一击 85% 施加 6.0 秒燃烧 (`hotlink_sp2_burn`, 70% ATK, PUA: `\uE41D`)；50% 概率造成 1.5 秒眩晕 (`hotlink_sp2_stun`, PUA: `\uE605`)。 |
| **3608** | `sp3` | **烈焰地狱**<br>*Infernal Conflagration* | 最后一击 100% 施加 8.0 秒极效燃烧 (`hotlink_sp3_burn`, 100% ATK, PUA: `\uE41D`)；技能结束获得 30% 护甲增益 8.0 秒与 4.0 秒不可阻挡 (`hotlink_sp3_armor`, `hotlink_sp3_unstoppable`)。 |

---

### 3. 离子风 (`ionstorm_gs_leader2015`) - 6 项核心战技
*模块文件*：`Server/abilities/bots/ionstorm.py`

| 技能ID | 分类 | 战技名称 (中/英) | 机制实现方案与参数细节 |
| :---: | :---: | :--- | :--- |
| **3576** | `basic` | **电离冲击**<br>*Ion Impact* | 远程攻击命中施加 4.0 秒电离冲击 (`ionstorm_ion_impact`)，降低目标 35% 能量获取率。PUA: `\uE607`。 |
| **3577** | `passive` | **电离破甲与霸体驱散**<br>*Ion Armor Break & Dispel* | 重击 100% 施加 30% 破甲 6.0 秒 (`ionstorm_heavy_armor_break`)，移除对手 1 层护甲增益 (`ionstorm_heavy_nullify_armor`)，驱散不可阻挡霸体 (`ionstorm_heavy_nullify_unstop`)；对手破甲时全攻击增伤 25% (`ionstorm_armor_broken_boost`)。 |
| **3578** | `signature` | **电磁逆火**<br>*Electromagnetic Backfire* | 敌方施放特技时 70% 概率触发电磁逆火：施加 5.0 秒震击 (`ionstorm_sig_backfire_shock`, 60% ATK, PUA: `\uE914`) 并扣除其 30% 格能量 (`ionstorm_sig_backfire_drain`)。 |
| **3579** | `sp1` | **高压电弧**<br>*High-Voltage Arc* | 最后一击 85% 施加 4.0 秒震击 (`ionstorm_sp1_shock`, 45% ATK, PUA: `\uE914`)；对处于护甲或霸体状态的敌人增伤 50% (`ionstorm_sp1_unstop_punish`)。 |
| **3580** | `sp2` | **离子风暴**<br>*Ion Storm* | 每一击 90% 施加 30% 破甲 6.0 秒 (`ionstorm_sp2_break`)；70% 追加 5.0 秒震击 (`ionstorm_sp2_shock`, 50% ATK, PUA: `\uE914`)。 |
| **3581** | `sp3` | **湮灭电离轰击**<br>*Annihilation Ion Barrage* | 最后一击驱散全部护甲并施加 40% 破甲 8.0 秒 (`ionstorm_sp3_break`)；技能结束自身提升 30% 攻击力 6.0 秒 (`ionstorm_sp3_atk_buff`, PUA: `\uE406`)。 |

---

### 4. 新星风 (`novastorm_gs_leader2015`) - 6 项核心战技
*模块文件*：`Server/abilities/bots/novastorm.py`

| 技能ID | 分类 | 战技名称 (中/英) | 机制实现方案与参数细节 |
| :---: | :---: | :--- | :--- |
| **3585** | `basic` | **核辐射射击**<br>*Nuclear Radiation Shot* | 远程攻击 40% 施加 4.0 秒核辐射燃烧 (`novastorm_ranged_burn`, 35% ATK, PUA: `\uE41D`)。 |
| **3586** | `passive` | **爆轰充能与重击烈焰**<br>*Detonation Charge & Heavy Burn* | 连击数每达 5 的倍数获得重击必暴与 35% 暴伤 (`novastorm_combo_crit_rate`, `novastorm_combo_crit_dmg`)；重击 100% 施加 5.0 秒燃烧 (`novastorm_heavy_burn`, 60% ATK)。 |
| **3587** | `signature` | **热核殉爆**<br>*Thermonuclear Detonation* | 特殊攻击暴击时引爆敌方全部燃烧造成 45% ATK 瞬时爆轰伤害 (`novastorm_sig_detonate`)；无燃烧时施加 5.0 秒 75% ATK 燃烧 (`novastorm_sig_burn`)。 |
| **3588** | `sp1` | **辐射爆轰**<br>*Radiation Blast* | 每一击 75% 施加 4.0 秒燃烧 (`novastorm_sp1_burn`, 40% ATK)；暴击额外获得 30% 暴伤持续 4.0 秒 (`novastorm_sp1_crit_dmg`)。 |
| **3589** | `sp2` | **超新星突进**<br>*Supernova Surge* | 释放获得不可阻挡 (`novastorm_sp2_unstoppable`)；最后一击 100% 施加 2 层 6.0 秒燃烧 (`novastorm_sp2_burn`, 80% ATK)。 |
| **3590** | `sp3` | **恒星坍缩歼灭**<br>*Stellar Collapse Annihilation* | 最后一击 100% 施加 3 层 7.0 秒核爆燃烧 (`novastorm_sp3_burn`, 120% ATK)；即时扣除对方 20% 能量 (`novastorm_sp3_drain`)。 |

---

### 5. 酸雨 (`acidstorm_gs_leader2015`) - 7 项核心战技
*模块文件*：`Server/abilities/bots/acidstorm.py`

| 技能ID | 分类 | 战技名称 (中/英) | 机制实现方案与参数细节 |
| :---: | :---: | :--- | :--- |
| **3566** | `basic` | **强酸喷射**<br>*Corrosive Jet* | 远程攻击命中 40% 施加 4.0 秒强酸 (`acidstorm_ranged_acid`, 30% ATK, PUA: `\uE524`)。 |
| **3567** | `basic` | **酸蚀外壳**<br>*Acidic Plating* | 受到近战攻击时 25% 强酸飞溅反制削弱攻击者 15% 护甲 (`acidstorm_splash_break`, PUA: `\uE516`)。 |
| **3568** | `passive` | **酸化侵蚀与酸蚀增伤**<br>*Corrosive Acidification* | 重击 35% 施加 5.0 秒酸化 (`acidstorm_heavy_acid`, 35% ATK) 与 10% 破甲 (`acidstorm_heavy_acid_break`)；对手酸化时全攻击增伤 20% (`acidstorm_acid_atk_boost`)。 |
| **3569** | `signature` | **酸性气溶胶护盾**<br>*Acidic Aerosol Shield* | 战斗开始获得 3 层气溶胶护盾 (`acidstorm_sig_aerosol_shield`, PUA: `\uE515`)，单次受击伤害上限截断为 70%。 |
| **3570** | `sp1` | **强酸喷雾**<br>*Acid Spray* | 最后一击 70% 施加 4.0 秒酸化 (`acidstorm_sp1_acid`, 40% ATK, PUA: `\uE524`)。 |
| **3571** | `sp2` | **硫酸洪流**<br>*Sulfuric Deluge* | 每一击 70% 施加 5.0 秒酸化 (`acidstorm_sp2_acid`, 50% ATK)；45% 追加 20% 破甲持续 6.0 秒 (`acidstorm_sp2_break`)。 |
| **3572** | `sp3` | **暴雨倾盆**<br>*Skyfall Acid Deluge* | 最后一击 100% 施加 2 层 6.5 秒极效酸化 (`acidstorm_sp3_acid`, 80% ATK)；并施加 30% 破甲持续 8.0 秒 (`acidstorm_sp3_break`)。 |

---

### 6. 太阳风 (`sunstorm_gs_leader2015`) - 6 项核心战技
*模块文件*：`Server/abilities/bots/sunstorm.py`

| 技能ID | 分类 | 战技名称 (中/英) | 机制实现方案与参数细节 |
| :---: | :---: | :--- | :--- |
| **3594** | `basic` | **近战辐射撕裂**<br>*Radiation Tear* | 近战攻击 45% 施加 4.0 秒流血 (`sunstorm_melee_bleed`, 35% ATK, PUA: `\uE401`) 与 10% 破甲 (`sunstorm_melee_break`)。 |
| **3595** | `passive` | **聚变燃烧与规避压制**<br>*Fusion Burn & Anti-Evade* | 重击 100% 施加 4.5 秒聚变燃烧 (`sunstorm_heavy_burn`, 50% ATK)；暴击 50% 额外追加 4.0 秒燃烧 (`sunstorm_crit_burn`)；对手燃烧时规避几率降低 35% (`sunstorm_burn_anti_evade`)。 |
| **3596** | `signature` | **失控恒星反应堆**<br>*Runaway Stellar Reactor* | 恒星过热获得常驻近战增益 (`sunstorm_sig_melee_gain`, 每层 15%, 上限 4 层, PUA: `\uE412`)。 |
| **3597** | `sp1` | **太阳喷射**<br>*Solar Jet* | 最后一击 100% 施加 4.0 秒燃烧 (`sunstorm_sp1_burn`, 45% ATK)；技能结束提升 25% 暴击率持续 4.0 秒 (`sunstorm_sp1_crit_buff`)。 |
| **3598** | `sp2` | **耀斑轰炸**<br>*Solar Flare Bombardment* | 最后一击 80% 施加 2 层 5.0 秒燃烧 (`sunstorm_sp2_burn`, 60% ATK)；50% 概率眩晕 1.5 秒 (`sunstorm_sp2_stun`)。 |
| **3599** | `sp3` | **日冕风暴**<br>*Corona Storm* | 最后一击 100% 施加 3 层 6.0 秒终极燃烧 (`sunstorm_sp3_burn`, 90% ATK)；技能结束获得 35% 暴伤持续 6.0 秒 (`sunstorm_sp3_crit_dmg`)。 |

---

## 三、质量门禁与回归验收结果

1. **底层强类型契约校验 (`tools/validate_bot_ability.py`)**：
   - 检验全部 60 位注册机器人，包括 6 位重涂空军机体。
   - **结果**：`0 ERRORS, 0 WARNINGS, 100% 通过`。
2. **战斗物理仿真器全量测试 (`tools/sim/run_tests.py`)**：
   - 执行全部 22 组专属套件，覆盖 Movie Optimus、G1 Megatron、Prowl、Bumblebee、Windblade、Megatronus、Batches 2~4 英雄、12 位新英雄，以及第 22 组 6 位红蜘蛛重涂 Seeker 寻猎空军套件。
   - **结果**：`22 项门禁测试全部通过 (100% PASS)`。
3. **离线端数据一致性**：
   - `python Server/gamedata.py` 成功重构并生成全部 78 英雄登录配置及 `bot_info.h`，无断言失败。
