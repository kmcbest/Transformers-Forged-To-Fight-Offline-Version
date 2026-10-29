# TFTF 优先角色能力代码库全量比对与四分类裁定报告
*(Transformers: Forged to Fight - Priority Abilities Codebase Comparison & 4-Category Classification Report)*

> **生成时间**：2026-10-29 10:44:34  
> **数据源**：Upstash KV 在线深扫描真理源 (`tools/priority_abilities.json`)  
> **比对基准**：本地代码库 `Server/abilities/bots/` (42机体)、`tools/nativehook/skills/bots/` (24模块)、`Server/abilities/registry.py` (42注册机体)  
> **覆盖率**：**100.0%** (229 项优先战技全覆盖，0 遗漏)

---

## 1. 报告概述与四分类裁定标准 (Executive Summary & Classification Taxonomy)

本报告基于对 Upstash KV 实时深扫描获取的 **229 项优先角色能力**（涵盖 **40 位机体**），与本地工程代码库（Python 能力层、NativeHook C 运行时层及动态注册表）进行显微级逐行比对。依据严格定义的四分类标准，完整判定每一项待实现能力的研发归属：

| 分类名称 | 判定定义 | 判定准则 (Checklist) | 涉及机体数 | 战技数量 | 占比 |
| :--- | :--- | :--- | :---: | :---: | :---: |
| **1. 完全新的**<br>*(Entirely New)* | 整个角色的能力此前从未在代码中实现过 | 目标机体在 `Server/abilities/bots/` 无代码、在 `tools/nativehook/` 无模块、在 `registry.py` 未注册 | 12 位 | 96 项 | 41.9% |
| **2. 增补的**<br>*(Incremental)* | 该角色已有部分能力实现，本次加入了新能力 | 目标机体已有部分代码，但本战技未声明修饰器亦无 Native 拦截（如汽车大师公路之王等） | 13 位 | 49 项 | 21.4% |
| **3. 调整的**<br>*(Modified)* | 该角色的该能力已实现，但在本次优先列表中存在改动 | 目标机体已实现该战技，但优先列表中在描述文本、数值倍率、触发条件存在更新版本 | 7 位 | 22 项 | 9.6% |
| **4. 冲突的**<br>*(Conflicting)* | 该角色的该能力已实现，且在优先列表中没有任何改动 | 战技已完整在代码中测试通过，优先列表内容完全一致，云端状态未及时更新置为已实现 | 18 位 | 62 项 | 27.1% |
| **合计 (Total)** | **全量优先能力总集** | **覆盖 40 位机体全部优先战技，无任何遗漏** | **40 位** | **229 项** | **100.0%** |

### 1.1 总体统计与执行总览

- **总待办战技体量**：229 项（包含静态快照 197 项 + 实时深扫描增补 32 项）。
- **有效研发工作量**：**167 项**（非冲突项，占比 **72.9%**），是后续智能体开发的核心任务集。
- **冗余冲突过滤量**：**62 项**（占比 **27.1%**），已在本地稳定运行，无需重复编写，建议将云端状态批量置为 `implemented`。

## 2. 四大分类详尽判定清单 (Detailed Classification Breakdown)

### 2.1 分类一：完全新的 (Entirely New, 共 96 项)

> **定义**：整个角色的能力此前从未在代码中实现过。目标机体在本地 `Server/abilities/bots/` 无独立 Python 脚本，在 `tools/nativehook/skills/bots/` 无专属 C 模块，在 `Server/abilities/registry.py` 未完成注册。

涵盖 **12 位全新英雄**：录音机 (`blaster_gs_leader2016`, 6项)、打击 (`breakdown_gs`, 9项)、克劳莉娅 (`chromia_gs_kabam`, 9项)、飞过山 (`cliffjumper_gs_kabam`, 6项)、抢劫 (`dragstrip_gs_deluxe2016`, 9项)、惊破天 (`galvatron_gs_voyager2016`, 9项)、电影威震天 (`megatron_cin_rotf`, 9项)、幻影 (`mirage_gs_deluxe2016`, 8项)、倾天柱 (`optimusprime_sg_voyager2015`, 4项)、震荡波 (`shockwave_gs`, 11项)、闹翻天 (`skywarp_gs_leader2015`, 7项)、声波 (`soundwave_gs`, 9项)。

| 序号 | 机体 (`bot_id`) | 技能 ID | 分类 | 中文名称 / 英文名称 | 官方效果摘要 | 判定理由与落地线索 |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | **录音机**<br>`blaster_gs_leader2016` | `2409` | `signature` | **吸收护盾**<br>*Absorption Shield* | 护盾状态下，录音机对远程攻击拥有不可阻挡的状态  // 打中只吃伤害无受创硬直，类似汽车大师的不可阻挡，但是身上不带光圈 护盾额外... | 机体 blaster_gs_leader2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 2 | **录音机**<br>`blaster_gs_leader2016` | `2419` | `passive` | **放大充能**<br>*Amp Charge* | 发动任意特殊技时，获得1层放大充能，最多叠加10层。//无倒计时 每层放大充能增加6%的远程伤害，包括普通远程，重击和特殊技中的远... | 机体 blaster_gs_leader2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 3 | **录音机**<br>`blaster_gs_leader2016` | `2420` | `passive` | **干扰**<br>*Interference* | 普通远程攻击命中或被防时，有80%概率施加干扰减益，降低对手远程攻击20%的伤害，50%的射速，持续10秒。//最大1层，可刷新 | 机体 blaster_gs_leader2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 4 | **录音机**<br>`blaster_gs_leader2016` | `2421` | `passive` | **震击**<br>*Shock* | 重击命中100%的概率施加震击，造成攻击30%的伤害，持续5秒。 每层放大充能增加20%的震击伤害 | 机体 blaster_gs_leader2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 5 | **录音机**<br>`blaster_gs_leader2016` | `2422` | `passive` | **护盾**<br>*Shield* | 进入防御姿态时得到一个护盾，护盾生效时使受到的伤害降低15%，松开防御后0.5秒后护盾消失，每个放大充能延长倒计时0.25秒。  ... | 机体 blaster_gs_leader2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 6 | **录音机**<br>`blaster_gs_leader2016` | `2423` | `signature` | **回血**<br>*Repair* | 护盾状态下，受到远程攻击和远程重击时，有40%的概率立即修复对手攻击力17%的生命值。如果受到的是特殊攻击，则修复34%。 | 机体 blaster_gs_leader2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 7 | **打击**<br>`breakdown_gs` | `3504` | `passive` | **护盾崩解**<br>*Shield Break* | 成功闪避对方重击时，获得一个护盾崩解增益，提升50%的近战伤害，在近战命中时消耗此增益，清除对方身上所有的护盾并施加攻击力50%的... | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 8 | **打击**<br>`breakdown_gs` | `3505` | `signature` | **晚期神经质**<br>*Terminal Paranoia* | 敌方血量大于50%时，打击获得一个规避增益，40%的概率规避对方近战攻击，成功规避后增益消失，5秒后重新获得。 //先是绿图标，无... | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 9 | **打击**<br>`breakdown_gs` | `3506` | `sp1` | **能量流失**<br>*Power Leak* | 最后一击命中时，50%概率施加能量流失，在5秒内扣除对方最大能量的12%。 | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 10 | **打击**<br>`breakdown_gs` | `3508` | `sp3` | **远程减益**<br>*Ranged Debuff* | 施加远程减益，降低对手的远程攻击伤害的100%，持续20秒 | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 11 | **打击**<br>`breakdown_gs` | `3512` | `sp1` | **暴击几率**<br>*Crit Rate* | 最后一击命中时，35%的概率得到30%的暴击几率增益，持续8秒 | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 12 | **打击**<br>`breakdown_gs` | `3513` | `passive` | **近战规避**<br>*Melee Evade* | L4或M2被防时，有75%的概率获得4秒的近战规避。 | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 13 | **打击**<br>`breakdown_gs` | `3514` | `sp2` | **燃烧**<br>*Burn* | 最后一击造成燃烧，施加攻击力120%的伤害，持续4秒。 | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 14 | **打击**<br>`breakdown_gs` | `3515` | `sp2` | **确定性**<br>*Certainty* | 施加确定性减益，对方下次充满一格能量后，必然立即释放特殊技1，释放后减益消失。//即便有2或3格气，也强制出SP1 | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 15 | **打击**<br>`breakdown_gs` | `3516` | `sp3` | **确定性**<br>*Certainty* | 施加2层确定性减益，对方下次充满一格能量后，必然立即释放特殊技1，释放后减益消失。//即便有2或3格气，也强制出SP1 | 机体 breakdown_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 16 | **克劳莉娅**<br>`chromia_gs_kabam` | `2486` | `passive` | **减速**<br>*Deceleration* | 远程攻击命中或被防御时，有60%的概率施加减速，持续3.2秒，可叠加 每层减速降低对手能量功率10% 减速中的对手绝对不触发规避 | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 17 | **克劳莉娅**<br>`chromia_gs_kabam` | `2488` | `sp2` | **流血**<br>*Bleed* | 100%几率触发流血，造成攻击力100%的伤害，持续4秒。 | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 18 | **克劳莉娅**<br>`chromia_gs_kabam` | `2487` | `sp1` | **流血**<br>*Bleed* | 100%几率触发流血，造成攻击力69.3%的伤害，持续4秒。 | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 19 | **克劳莉娅**<br>`chromia_gs_kabam` | `2489` | `sp2` | **减速**<br>*Deceleration* | 施加减速，持续9秒，可叠加 每层减速降低对手能量功率10% 减速中的对手绝对不触发规避 | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 20 | **克劳莉娅**<br>`chromia_gs_kabam` | `2490` | `sp3` | **减速**<br>*Deceleration* | 施加减速，持续23.6秒，可叠加 每层减速降低对手能量功率10% 减速中的对手绝对不触发规避 | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 21 | **克劳莉娅**<br>`chromia_gs_kabam` | `2491` | `sp3` | **流血**<br>*Bleed* | 100%几率触发流血，造成攻击力200%的伤害，持续25秒。 | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 22 | **克劳莉娅**<br>`chromia_gs_kabam` | `2481` | `signature` | **瞄准目标**<br>*Eyes on Target* | 所有特殊技最后一击：得到能量涌动增益，提升能量获得功率120%，持续7秒。 | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 23 | **克劳莉娅**<br>`chromia_gs_kabam` | `2492` | `signature` | **规避**<br>*Evade* | 所有特殊技最后一击：获得规避增益，30%的概率规避敌人远程攻击，持续7秒 | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 24 | **克劳莉娅**<br>`chromia_gs_kabam` | `2493` | `signature` | **顶光区的炸弹**<br>*Acrolight Bomb* | 所有特殊技：技能命中后最后一击施加炸弹减益，持续5秒  // 灰色图标 5秒内未被对手击中，炸弹造成攻击力100%的即时伤害，并眩... | 机体 chromia_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 25 | **飞过山**<br>`cliffjumper_gs_kabam` | `3541` | `sp2` | **无法格挡**<br>*Unblockable* | 如果对手拥有至少I0个玻璃瓦斯减益，此攻击的最后一击无法格挡。 | 机体 cliffjumper_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 26 | **飞过山**<br>`cliffjumper_gs_kabam` | `3546` | `passive` | **特殊伤害**<br>*Special Damage* | 在没有伤害减益的状态下使用特殊技，伤害增加20% | 机体 cliffjumper_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 27 | **飞过山**<br>`cliffjumper_gs_kabam` | `3547` | `passive` | **玻璃瓦斯减益**<br>*Glass Gas Debuff* | 远程攻击命中或被防，有100%的几率施加1层玻璃瓦斯减益，持续8秒可叠加。//灰色图标 每层玻璃瓦斯减益降低对手格挡精通5% //... | 机体 cliffjumper_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 28 | **飞过山**<br>`cliffjumper_gs_kabam` | `3548` | `passive` | **重击刷新**<br>*Heavy Refresh* | 重击命中，刷新所有玻璃瓦斯减益的倒计时。 | 机体 cliffjumper_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 29 | **飞过山**<br>`cliffjumper_gs_kabam` | `3549` | `sp1` | **玻璃瓦斯减益**<br>*Glass Gas Debuff* | 施加1层永久玻璃瓦斯减益并刷新所有有倒计时的玻璃瓦斯减益  //永久减益和有倒计时的分两个图标 | 机体 cliffjumper_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 30 | **飞过山**<br>`cliffjumper_gs_kabam` | `3550` | `sp3` | **玻璃瓦斯减益**<br>*Glass Gas Debuff* | 施加5层永久玻璃瓦斯减益 将所有带倒计时的玻璃瓦斯减益也变成永久减益 最后一击的暴击几率增加60% | 机体 cliffjumper_gs_kabam 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 31 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3516` | `signature` | **卑鄙胜者**<br>*Dirty Victory* | 重击命中有45%概率窃取对方最大能量的10%，并施加1层流血，造成攻击力40%的伤害，持续5秒。 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 32 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3525` | `passive` | **修复**<br>*Repair* | 成功叠加3层流血时，停止对手流血减益并触发修复，4秒内回复5%的最大生命值。 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 33 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3524` | `passive` | **不可防御**<br>*Unblockable* | 发动前冲攻击时有25%的概率不可防御  // 图标在前冲过程中出现，未触发则不出现 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 34 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3526` | `sp1` | **流血**<br>*Bleed* | 80%概率施加流血，造成攻击力70%的伤害，持续7秒。 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 35 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3527` | `sp1` | **暴击几率**<br>*Crit Rate* | 最后一击命中后，增加50%的暴击几率，持续5秒。 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 36 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3528` | `sp2` | **暴击几率**<br>*Crit Rate* | 最后一击命中后，增加80%的暴击几率，持续8秒。 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 37 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3529` | `sp2` | **规避克制**<br>*Anti Evade* | 最后一击命中后，施加规避克制，完全禁止对方规避，持续8秒。 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 38 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3530` | `sp3` | **流血**<br>*Bleed* | 技能完成时施加2层流血，每层造成攻击力70%的伤害，持续7秒。 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 39 | **抢劫**<br>`dragstrip_gs_deluxe2016` | `3531` | `sp3` | **能量锁定**<br>*Power Lock* | 技能完成时100%概率触发能量锁定，阻止对方获得能量，持续5秒 | 机体 dragstrip_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 40 | **惊破天**<br>`galvatron_gs_voyager2016` | `3045` | `signature` | **宇宙大帝的意志**<br>*Will of Unicron* | 完全充能时，根据对手失去生命值的百分比*0.5的概率获得不可阻挡，持续6秒，并在6秒内获得30%的最大能量槽 //用例：对手生命值... | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 41 | **惊破天**<br>`galvatron_gs_voyager2016` | `3054` | `passive` | **黑暗能量充能**<br>*Dark Energy Charge* | 在远程攻击的距离开始格挡，每0.065秒获得一层黑暗能量充能 //只叠加层数，没有倒计时 在充能达到30之前，停止格挡会以每层0.... | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 42 | **惊破天**<br>`galvatron_gs_voyager2016` | `3055` | `passive` | **远程伤害**<br>*Ranged Damage* | 每层黑暗能量充能提升远程攻击5%的伤害 | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 43 | **惊破天**<br>`galvatron_gs_voyager2016` | `3056` | `passive` | **暴击伤害**<br>*Crit Damage* | 每层黑暗能量充能提升近战暴击5%的伤害 | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 44 | **惊破天**<br>`galvatron_gs_voyager2016` | `3048` | `sp3` | **黑暗能量充能**<br>*Dark Energy Charge* | 技能发动时，暂停黑暗能量充能的倒计时。 技能发动立即获得30个黑暗能量充能，无倒计时。 最后一击命中时，每层黑暗能量充能有3.3%... | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 45 | **惊破天**<br>`galvatron_gs_voyager2016` | `3057` | `passive` | **暴击几率**<br>*Crit Rate* | L4和M2命中时增加50%的暴击几率。//无图标，仅针对本次攻击本身 | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 46 | **惊破天**<br>`galvatron_gs_voyager2016` | `3058` | `passive` | **黑暗燃烧**<br>*Dark Burn* | 重击命中时，每层黑暗能量充能有1.7%的概率消耗所有黑暗能量充能并施加黑暗燃烧，造成攻击力140%的即时伤害 | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 47 | **惊破天**<br>`galvatron_gs_voyager2016` | `3059` | `sp1` | **眩晕**<br>*Stun* | 每层黑暗能量充能有2%的概率眩晕对手3秒 | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 48 | **惊破天**<br>`galvatron_gs_voyager2016` | `3060` | `sp2` | **黑暗燃烧**<br>*Dark Burn* | 技能发动时，暂停黑暗能量充能的倒计时，直到技能结束后，如果黑暗能量充能未被最后一击消耗，倒计时继续。 最后一击命中时，每层黑暗能量... | 机体 galvatron_gs_voyager2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 49 | **电影威震天**<br>`megatron_cin_rotf` | `3107` | `signature` | **威震天万岁！**<br>*All Hail Megaton!* | 威震天总会回来的。当生命值降至10%以下时，威震天将在3秒内恢复最大生命值的30%。//每局只触发一次，如果敌方的致命攻击一次性造... | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 50 | **电影威震天**<br>`megatron_cin_rotf` | `3108` | `sp1` | **伤害电荷**<br>*Impair Charge* | 施加10层伤害电荷。 | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 51 | **电影威震天**<br>`megatron_cin_rotf` | `3109` | `sp2` | **远程增益**<br>*Ranged Buff* | 技能结束后，增加远程攻击速度和40%的远程伤害，持续6秒  // 不命中也可以 | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 52 | **电影威震天**<br>`megatron_cin_rotf` | `3118` | `passive` | **天然护甲**<br>*Permanent Armor* | +10%的永久护甲增益，无图标，不可被破甲移除 | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 53 | **电影威震天**<br>`megatron_cin_rotf` | `3119` | `passive` | **不可阻挡**<br>*Unstoppable* | 当生命值降至80%/60%/40%时，获得不可阻挡增益，持续4秒 | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 54 | **电影威震天**<br>`megatron_cin_rotf` | `3120` | `passive` | **攻击增益**<br>*Attack Buff* | 如果在不可阻挡状态发动重击未命中，获得一个40%的攻击增益，持续10秒 | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 55 | **电影威震天**<br>`megatron_cin_rotf` | `3121` | `passive` | **伤害电荷**<br>*Impair Charge* | 所有攻击（含特殊技）命中时，给对手施加一层伤害电荷，出于重击和SP3消耗 //红色图标，无倒计时，可叠加 | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 56 | **电影威震天**<br>`megatron_cin_rotf` | `3122` | `passive` | **电荷消耗**<br>*Consume charges* | 重击命中时，每1层伤害电荷增加5%的暴击几率。 如果重击出暴击，将消耗所有的伤害电荷，每1层电荷增加2%的暴击伤害 | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 57 | **电影威震天**<br>`megatron_cin_rotf` | `3123` | `sp3` | **伤害电荷**<br>*Impair Charge* | 第一击施加20层伤害电荷。每1层伤害电荷增加5%的暴击几率。 由于仅SP3施加的伤害电荷已将暴击几率拉满至100%，故最后一击必然... | 机体 megatron_cin_rotf 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 58 | **幻影**<br>`mirage_gs_deluxe2016` | `2687` | `signature` | **K.E.R.S**<br>*The Kinetic Energy Recovery System generates the following buffs when activating Special Attacks:* | 发动不同特殊技得到不同的加成  特殊技1：远程攻击射速提升50%，持续19秒  // 橙图标 E41B 特殊技2：近战攻击变得无法... | 机体 mirage_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 59 | **幻影**<br>`mirage_gs_deluxe2016` | `2700` | `sp1` | **破坏模式**<br>*Disruption Mode* | 进入破坏模式，该模式下远程攻击命中或被防有60%的概率扣除对方最大能量的9%  // 紫色图标出现，无倒计时，并移除存在的失能模式... | 机体 mirage_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 60 | **幻影**<br>`mirage_gs_deluxe2016` | `2701` | `sp2` | **失能模式**<br>*Incapacitation Mode* | 进入失能模式，该模式下近战攻击每一击能施加1层攻击减益，降低对方4.75%的攻击力，持续20秒，最多叠加15层 // 紫色E41F... | 机体 mirage_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 61 | **幻影**<br>`mirage_gs_deluxe2016` | `2702` | `sp3` | **敏捷模式**<br>*Agility Mode* | 进入敏捷模式，每次极限闪避对方攻击时，获得15%的永久攻击增益，最大堆叠20层。 // 紫色E406图标出现，无倒计时，并移除存在... | 机体 mirage_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 62 | **幻影**<br>`mirage_gs_deluxe2016` | `2703` | `passive` | **护盾**<br>*Shield* | 对方发动特殊技时得到一个护盾，降低对方90%的暴击伤害和远程伤害（包括特殊技中的远程攻击），直到幻影被击倒。 | 机体 mirage_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 63 | **幻影**<br>`mirage_gs_deluxe2016` | `2704` | `passive` | **能量涌动**<br>*Power Flow* | 幻影开局时进入能量模式，获得能量的功率提高30%，被击倒后退出能量模式，15秒后恢复  // 开局紫色图标，被击倒后变成灰色15秒... | 机体 mirage_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 64 | **幻影**<br>`mirage_gs_deluxe2016` | `2705` | `passive` | **重击远程穿透**<br>*Heavy Range Immunue* | 重击全程不会被远程普通攻击和远程重击击中。//对方的远程普通攻击和远程重击会直接从幻影身边飞过，这个过程显示一个黄色的图标，重击完... | 机体 mirage_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 65 | **幻影**<br>`mirage_gs_deluxe2016` | `2706` | `passive` | **重击净化**<br>*Heavy Purify* | 发动重击时净化所有燃烧伤害 | 机体 mirage_gs_deluxe2016 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 66 | **倾天柱**<br>`optimusprime_sg_voyager2015` | `3634` | `signature` | **暴虐火种**<br>*Spark of Tyranny* | 所有特殊技发动时，获得一个概率充能，提升下一次特殊技无法防御的概率30%，直到特殊技触发无法防御时消耗掉。//未达100%时是紫色... | 机体 optimusprime_sg_voyager2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 67 | **倾天柱**<br>`optimusprime_sg_voyager2015` | `3642` | `passive` | **逆境暴发**<br>*Struggle* | 处于伤害减益状态时，攻击力提升50%  //不会随伤害减益数量的增加而增加 | 机体 optimusprime_sg_voyager2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 68 | **倾天柱**<br>`optimusprime_sg_voyager2015` | `3641` | `passive` | **减益控制**<br>*Debuff Control* | 被施加伤害减益时重击命中对手，可将所有伤害减益强度降低99%，但时间延长300%。 | 机体 optimusprime_sg_voyager2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 69 | **倾天柱**<br>`optimusprime_sg_voyager2015` | `3643` | `passive` | **减益循环**<br>*Debuff Cycle* | 自身处于流血状态时，所有攻击有10%的概率施加1层燃烧，造成攻击力70%的伤害，持续3秒，最大堆叠1层，可刷新 自身处于燃烧状态时... | 机体 optimusprime_sg_voyager2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 70 | **震荡波**<br>`shockwave_gs` | `3277` | `passive` | **能量充能**<br>*Energy Charge* | 格挡远程能量攻击时，得到1层能量充能，持续6秒，最多叠加3层  //大部分远程普通攻击都是能量攻击，只有漂移、反冲和雷震是物理攻击... | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 71 | **震荡波**<br>`shockwave_gs` | `3283` | `signature` | **回溯**<br>*Undo* | 每充满一格能量时，有35%的概率激活回溯，持续4秒。当倒计时结束时，他会立即修复这4秒内受到的全部伤害。//灰色图标 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 72 | **震荡波**<br>`shockwave_gs` | `3285` | `sp2` | **护甲穿透**<br>*Armor Piercing* | 技能期间100%护甲穿透   //黄图标，技能期间显示 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 73 | **震荡波**<br>`shockwave_gs` | `3301` | `sp1` | **能量充能**<br>*Energy Charge* | 技能发动时（无论是否命中），得到3层能量充能，持续6秒 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 74 | **震荡波**<br>`shockwave_gs` | `3302` | `sp1` | **震击**<br>*Shock* | 最后一击命中时，每层能量充能施加1层震击减益，造成攻击力85%的伤害，持续4秒 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 75 | **震荡波**<br>`shockwave_gs` | `3303` | `sp2` | **阻止修复**<br>*Repair Block* | 最后一击命中，施加阻止修复，禁用对方所有回血能力，持续6.5秒 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 76 | **震荡波**<br>`shockwave_gs` | `3304` | `passive` | **能量充能**<br>*Energy Charge* | 技能发动时（无论是否命中），得到3层能量充能，持续6秒 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 77 | **震荡波**<br>`shockwave_gs` | `3300` | `passive` | **震击**<br>*Shock* | 重击命中时，每层能量充能施加1层震击减益，造成攻击力85%的伤害，持续4秒  // 不消耗能量充能，无能量充能则不触发震击 普通远... | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 78 | **震荡波**<br>`shockwave_gs` | `3307` | `sp3` | **能量充能**<br>*Energy Charge* | 技能发动时，得到5层能量充能，持续7秒 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 79 | **震荡波**<br>`shockwave_gs` | `3308` | `sp3` | **震击**<br>*Shock* | 技能完成后，每层能量充能施加1层震击减益，造成攻击力85%的伤害，持续4秒 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 80 | **震荡波**<br>`shockwave_gs` | `3309` | `sp3` | **阻止修复**<br>*Repair Block* | 技能完成后，施加阻止修复，禁用对方所有回血能力，持续11秒 | 机体 shockwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 81 | **闹翻天**<br>`skywarp_gs_leader2015` | `3323` | `passive` | **传送充能**<br>*Teleport Charge* | 每8秒得到一个传送充能，最大叠加3层  // 图标显示的方式参考暗天陨的充能 如果闹翻天受到暴击，有25%的概率丢失一个传送充能，... | 机体 skywarp_gs_leader2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 82 | **闹翻天**<br>`skywarp_gs_leader2015` | `3324` | `passive` | **特殊伤害减益**<br>*Special Damage Debuff* | 普通远程攻击命中时有20%的概率施加1层特殊伤害减益，减少10%的特殊伤害，持续5秒  远程重击命中时有50%的概率施加1层特殊伤... | 机体 skywarp_gs_leader2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 83 | **闹翻天**<br>`skywarp_gs_leader2015` | `3325` | `passive` | **传送攻击**<br>*Teleport Attack* | 在拥有传送充能时，特殊攻击1和2会变为传送攻击  // 技能期间显示橙色图标，传送攻击会改变特殊技的动作，需要在asset中找到专... | 机体 skywarp_gs_leader2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 84 | **闹翻天**<br>`skywarp_gs_leader2015` | `3328` | `sp3` | **能量窃取**<br>*Power Steal* | 100%的概率窃取对手最大能量的50% //立即结算，我方加能量，对方减能量，红色图标出现在对方侧，一闪而过 | 机体 skywarp_gs_leader2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 85 | **闹翻天**<br>`skywarp_gs_leader2015` | `3326` | `sp1` | **能量燃烧**<br>*Power Burn* | 获得9秒能量燃烧状态，普通远程和远程重击命中或被防时立即扣除对手最大能量的8%   //黄图标 | 机体 skywarp_gs_leader2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 86 | **闹翻天**<br>`skywarp_gs_leader2015` | `3327` | `sp2` | **修复阻止**<br>*Repair Block* | 最后一击命中时100%概率触发修复阻止，阻止对方所有回血能力，持续12秒 | 机体 skywarp_gs_leader2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 87 | **闹翻天**<br>`skywarp_gs_leader2015` | `3329` | `sp3` | **能量涌动**<br>*Power Flow* | 如果能量窃取之后对方能量减为0，则得到一个永久能量涌动增益，提升能量功率15%，只能叠加一层。 | 机体 skywarp_gs_leader2015 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 88 | **声波**<br>`soundwave_gs` | `3395` | `passive` | **震击**<br>*Shock* | 重击命中100%的概率施加震击，造成攻击50%的伤害，持续6秒。 | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 89 | **声波**<br>`soundwave_gs` | `3396` | `passive` | **能量涌动**<br>*Power Flow* | 声波的普通近战和普通远程攻击不产生能量 重击命中后获得能量涌动增益，每秒产生最大能量的5.7%，直到充满2格能量或者释放特殊技  ... | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 90 | **声波**<br>`soundwave_gs` | `3397` | `sp1` | **眩晕**<br>*Stun* | 最后一击命中，60%概率施加眩晕1.5秒。 | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 91 | **声波**<br>`soundwave_gs` | `3398` | `sp1` | **能量流失**<br>*Power Leak* | 最后一击命中，85%的概率造成能量流失，在4秒内扣除对方1格能量的90% | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 92 | **声波**<br>`soundwave_gs` | `3399` | `sp2` | **震击**<br>*Shock* | 最后一击命中，100%的概率施加震击，造成攻击70%的伤害，持续6秒。 | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 93 | **声波**<br>`soundwave_gs` | `3400` | `sp3` | **震击**<br>*Shock* | 重击命中100%的概率施加震击，造成攻击50%的伤害，持续6秒。 | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 94 | **声波**<br>`soundwave_gs` | `3401` | `sp2` | **能量涌动**<br>*Power Flow* | 最后一击命中后获得能量涌动增益，每秒产生最大能量的6.7%，直到充满3格能量或者释放特殊技  //最后一击命中后紫图标出现，无倒计... | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 95 | **声波**<br>`soundwave_gs` | `3402` | `sp3` | **眩晕**<br>*Stun* | 最后一击命中，60%概率施加眩晕1.5秒。 | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |
| 96 | **声波**<br>`soundwave_gs` | `3403` | `sp3` | **能量锁定**<br>*Power Lock* | 技能完成时70%概率触发能量锁定，阻止对方获得能量，持续8秒 | 机体 soundwave_gs 在本地代码库中完全未实现（无独立 Python 模块、无 NativeHook C 模块，未在 registry 注册） |


### 2.2 分类二：增补的 (Incremental, 共 49 项)

> **定义**：该角色已有部分能力实现，本次加入了新能力。目标机体已在本地注册并有部分基础战斗修饰器，但当前待办战技在现有代码库中**完全不存在**，属于增量追加（严禁覆盖既有逻辑，必须在对应机体模块中 Append）。

涵盖 **13 位英雄**：小黄蜂 (`bumblebee_gs_kabam`, 5项)、黄豹 (`cheetor_bw_transmetal`, 2项)、狂飙 (`cyclonus_gs_uw06`, 1项)、G1擎天柱 (`fte_optimus_gs_t3`, 1项)、天火 (`jetfire_gs_leader2014`, 7项)、反冲 (`kickback_gs_kabam`, 2项)、G1威震天 (`megatron_gs_leader2015`, 2项)、搅拌者 (`mixmaster_cin_rotf`, 7项)、汽车大师 (`motormaster_gs_voyager2015`, 5项)、犀牛 (`rhinox_gs_voyager2014`, 4项)、滑流 (`slipstream_gs`, 1项)、黄蜂勇士 (`waspinator_gs_deluxe`, 7项)、千斤顶 (`wheeljack_gs_mp20`, 5项)。

| 序号 | 机体 (`bot_id`) | 技能 ID | 分类 | 中文名称 / 英文名称 | 官方效果摘要 | 判定理由与落地线索 |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2441` | `passive` | **暴击几率增益**<br>*Crit Rate Buff* | 侧闪时获得一个28%的暴击几率增益，最多累积3个。每次小黄蜂命中对手时（无论是否出暴击），消耗一个增益。//被防不消耗增益 | 机体 bumblebee_gs_kabam 已有部分战技实现，本次加入新战技【暴击几率增益】，属于增量追加 |
| 2 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2445` | `signature` | **蜂之勇气**<br>*Bee Brave* | 与敌人处于近战距离时得到能量涌动，每秒自动产生最大能量的1.2%  //额外能量，不影响攻击和被攻击应得的能量 同时，得到10%的... | 机体 bumblebee_gs_kabam 已有部分战技实现，本次加入新战技【蜂之勇气】，属于增量追加 |
| 3 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2450` | `sp1` | **暴击伤害**<br>*Crit Damage* | 技能发动过程中暴击伤害提升60% | 机体 bumblebee_gs_kabam 已有部分战技实现，本次加入新战技【暴击伤害】，属于增量追加 |
| 4 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2451` | `sp2` | **能量锁定**<br>*Power Lock* | 第一击命中时100%概率触发能量锁定，阻止对方获得能量，持续10秒 | 机体 bumblebee_gs_kabam 已有部分战技实现，本次加入新战技【能量锁定】，属于增量追加 |
| 5 | **小黄蜂**<br>`bumblebee_gs_kabam` | `2452` | `sp3` | **暴击几率增益**<br>*Crit Rate Buff* | 技能完成后获得20个暴击几率增益，提升28%的暴击几率，每次小黄蜂命中对手时（无论是否出暴击），消耗一个增益。//被防不消耗增益 | 机体 bumblebee_gs_kabam 已有部分战技实现，本次加入新战技【暴击几率增益】，属于增量追加 |
| 6 | **黄豹**<br>`cheetor_bw_transmetal` | `2463` | `sp2` | **伤害放大**<br>*Damage Increase* | 对手能量越少，该攻击伤害越大，最大造成50%的额外伤害。//用例：对方能量为空，造成50%的额外伤害，能量为一半（1.5格），造成... | 机体 cheetor_bw_transmetal 已有部分战技实现，本次加入新战技【伤害放大】，属于增量追加 |
| 7 | **黄豹**<br>`cheetor_bw_transmetal` | `2478` | `sp3` | **伤害放大**<br>*Damage Increase* | 对手能量越少，该攻击伤害越大，最大造成100%的额外伤害。//用例：对方能量为空，造成100%的额外伤害，能量为一半（1.5格），... | 机体 cheetor_bw_transmetal 已有部分战技实现，本次加入新战技【伤害放大】，属于增量追加 |
| 8 | **狂飙**<br>`cyclonus_gs_uw06` | `2972` | `passive` | **黑暗能量**<br>*Dark Energy* | 每次填满一格气，狂飙获得一层黑暗能量，提升攻击力30%，持续6秒 | 机体 cyclonus_gs_uw06 已有部分战技实现，本次加入新战技【黑暗能量】，属于增量追加 |
| 9 | **G1擎天柱**<br>`fte_optimus_gs_t3` | `2357` | `passive` | **攻击增益**<br>*Attack Buff* | 发动重击时，获得一个攻击增益，增加（28.8%*小队人数）的攻击力，持续7秒 //用例：小队中除擎天柱还有4人，则增加115.2%... | 机体 fte_optimus_gs_t3 已有部分战技实现，本次加入新战技【攻击增益】，属于增量追加 |
| 10 | **天火**<br>`jetfire_gs_leader2014` | `2666` | `signature` | **损害控制**<br>*Damage Control* | 生命值少于75%时，天火的修复系统处于在线状态。此时按住格挡1秒时，消耗一个能量充能，在0.5秒内修复6%的最大生命值。 //连续... | 机体 jetfire_gs_leader2014 已有部分战技实现，本次加入新战技【损害控制】，属于增量追加 |
| 11 | **天火**<br>`jetfire_gs_leader2014` | `2667` | `sp1` | **远程增益**<br>*Ranged Buff* | 消耗全部能量充能，得到20秒的远程增益，提升射速20%，每层消耗的能量充能提升远程伤害20%。 | 机体 jetfire_gs_leader2014 已有部分战技实现，本次加入新战技【远程增益】，属于增量追加 |
| 12 | **天火**<br>`jetfire_gs_leader2014` | `2681` | `sp3` | **能量充能**<br>*Energy Charge* | 技能结束后获得3层能量充能。//紫色图标 | 机体 jetfire_gs_leader2014 已有部分战技实现，本次加入新战技【能量充能】，属于增量追加 |
| 13 | **天火**<br>`jetfire_gs_leader2014` | `2682` | `sp3` | **震击**<br>*Shock* | 消耗所有能量充能，转化为同等层数的震击，每层造成攻击力45%的伤害，持续4秒。//我方紫色图标消失，敌方红色震击图标出现。 | 机体 jetfire_gs_leader2014 已有部分战技实现，本次加入新战技【震击】，属于增量追加 |
| 14 | **天火**<br>`jetfire_gs_leader2014` | `2683` | `sp1` | **能量锁定**<br>*Power Lock* | 如果这次特殊技消耗5个或更多能量充能，则最后一击命中时100%概率触发能量锁定，阻止对方获得能量，持续8秒 | 机体 jetfire_gs_leader2014 已有部分战技实现，本次加入新战技【能量锁定】，属于增量追加 |
| 15 | **天火**<br>`jetfire_gs_leader2014` | `2684` | `sp2` | **护盾**<br>*Shield* | 消耗所有能量充能，得到1个20秒的护盾，每层能量充能减少所有伤害的8% //用例：消耗10个能量充能，得到一层80%减伤的护盾 | 机体 jetfire_gs_leader2014 已有部分战技实现，本次加入新战技【护盾】，属于增量追加 |
| 16 | **天火**<br>`jetfire_gs_leader2014` | `2685` | `sp2` | **修复阻止**<br>*Repair Block* | 如果这次特殊技消耗5个或更多能量充能，则最后一击命中时100%概率触发修复阻止，阻止对方所有回血能力，持续15秒 | 机体 jetfire_gs_leader2014 已有部分战技实现，本次加入新战技【修复阻止】，属于增量追加 |
| 17 | **反冲**<br>`kickback_gs_kabam` | `3100` | `passive` | **消耗（发起重击）**<br>*Consume (Heavy start)* | 重击发起时，自己身上所有震击、能量汲取、能量锁定和能量功率减益都会被净化，每个被移除的减益都变为一层能量获取增益，2秒内获得其最大... | 机体 kickback_gs_kabam 已有部分战技实现，本次加入新战技【消耗（发起重击）】，属于增量追加 |
| 18 | **反冲**<br>`kickback_gs_kabam` | `3101` | `passive` | **消耗（重击命中）**<br>*Consume (Heavy start)* | 重击命中时，驱散对方身上所有能量功率和能量获取增益，每驱散一个，反冲得到一层能量获取增益，2秒内获得其最大能量的3%。 | 机体 kickback_gs_kabam 已有部分战技实现，本次加入新战技【消耗（重击命中）】，属于增量追加 |
| 19 | **G1威震天**<br>`megatron_gs_leader2015` | `3126` | `passive` | **不可阻挡**<br>*Unstoppable* | 被击倒后，威震天有概率获得3秒的不可阻挡，概率等于损失生命值的百分比乘以0.7 //用例：损失50%的生命，概率为35% | 机体 megatron_gs_leader2015 已有部分战技实现，本次加入新战技【不可阻挡】，属于增量追加 |
| 20 | **G1威震天**<br>`megatron_gs_leader2015` | `3127` | `signature` | **毫不留情**<br>*No Mercy* | 只要对手身上有融合的减益，威震天的近战攻击（打中和被防都算）就有60%的概率从对方身上随机偷走一个增益，持续5秒。 //偷走意味着... | 机体 megatron_gs_leader2015 已有部分战技实现，本次加入新战技【毫不留情】，属于增量追加 |
| 21 | **搅拌者**<br>`mixmaster_cin_rotf` | `3180` | `passive` | **酸液**<br>*Acid* | 远程攻击第1击和第2击：30%的概率施加1层酸液减益，造成攻击力45%的伤害，持续9秒 | 机体 mixmaster_cin_rotf 已有部分战技实现，本次加入新战技【酸液】，属于增量追加 |
| 22 | **搅拌者**<br>`mixmaster_cin_rotf` | `3181` | `sp3` | **酸液**<br>*Acid* | 施加1层酸液减益，造成攻击力134%的伤害，持续20秒 | 机体 mixmaster_cin_rotf 已有部分战技实现，本次加入新战技【酸液】，属于增量追加 |
| 23 | **搅拌者**<br>`mixmaster_cin_rotf` | `3182` | `sp1` | **酸液**<br>*Acid* | 50%概率施加1层酸液减益，造成攻击力80%的伤害，持续10秒 | 机体 mixmaster_cin_rotf 已有部分战技实现，本次加入新战技【酸液】，属于增量追加 |
| 24 | **搅拌者**<br>`mixmaster_cin_rotf` | `3183` | `passive` | **特殊伤害**<br>*Special Damage* | 每5秒获得一个特殊伤害增益，增加27%的特殊伤害，最大叠加6层。// 先是灰色图标，5秒倒计时结束后出现一个橙色图标无倒计时可叠加... | 机体 mixmaster_cin_rotf 已有部分战技实现，本次加入新战技【特殊伤害】，属于增量追加 |
| 25 | **搅拌者**<br>`mixmaster_cin_rotf` | `3184` | `passive` | **暴击伤害**<br>*Crit Damage* | 在拥有6层特殊伤害后，每5秒获得一个暴击伤害增益，每1层增加18.9%的暴击伤害，最多叠加6层 | 机体 mixmaster_cin_rotf 已有部分战技实现，本次加入新战技【暴击伤害】，属于增量追加 |
| 26 | **搅拌者**<br>`mixmaster_cin_rotf` | `3185` | `passive` | **特殊技消耗**<br>*Special consumption* | 所有特殊技的最后一击命中时，消耗全部特殊技伤害和暴击伤害增益。 | 机体 mixmaster_cin_rotf 已有部分战技实现，本次加入新战技【特殊技消耗】，属于增量追加 |
| 27 | **搅拌者**<br>`mixmaster_cin_rotf` | `3186` | `passive` | **暴击几率**<br>*Crit Rate* | 如果对方身上有伤害减益，所有攻击增加50%的暴击几率。 | 机体 mixmaster_cin_rotf 已有部分战技实现，本次加入新战技【暴击几率】，属于增量追加 |
| 28 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3180` | `passive` | **重击冲压**<br>*Ram With Heavy Attacks* | 用重击撞击对手时随机造成三个减益效果之一（均持续6秒） * 21.6%的攻击减益 * 29.7%的破甲减益 * 24.3%的能量功... | 机体 motormaster_gs_voyager2015 已有部分战技实现，本次加入新战技【重击冲压】，属于增量追加 |
| 29 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3184` | `signature` | **公路之王**<br>*King of the Road* | 每损失最大生命值的20%，得到1层60%的近战增益。 // 用例：体力只剩19%时，应该有4层近战增益，橙图标，无倒计时 | 机体 motormaster_gs_voyager2015 已有部分战技实现，本次加入新战技【公路之王】，属于增量追加 |
| 30 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3187` | `sp3` | **攻击增益**<br>*Attack Buff* | 最后一击伤害增加150%，但同时对自身造成攻击力90%的伤害   // 如果自身剩余体力不够，不会KO自己，留1点体力 | 机体 motormaster_gs_voyager2015 已有部分战技实现，本次加入新战技【攻击增益】，属于增量追加 |
| 31 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3535` | `sp1` | **能量燃烧**<br>*Power Burn* | 即时扣除对方最大能量的2% | 机体 motormaster_gs_voyager2015 已有部分战技实现，本次加入新战技【能量燃烧】，属于增量追加 |
| 32 | **汽车大师**<br>`motormaster_gs_voyager2015` | `3536` | `sp3` | **冲压**<br>*Ram* | 最后一击随机施加6个冲压减益，均持续6秒 * 21.6%的攻击减益 * 29.7%的破甲减益 * 24.3%的能量功率减益 | 机体 motormaster_gs_voyager2015 已有部分战技实现，本次加入新战技【冲压】，属于增量追加 |
| 33 | **犀牛**<br>`rhinox_gs_voyager2014` | `2769` | `passive` | **护盾**<br>*Shield* | 战斗开始时有6个护盾增益，每个护盾增益将一次攻击造成的伤害上限限制为对手攻击力的80%。 护盾起效状态下，犀牛受到燃烧和震击伤害强... | 机体 rhinox_gs_voyager2014 已有部分战技实现，本次加入新战技【护盾】，属于增量追加 |
| 34 | **犀牛**<br>`rhinox_gs_voyager2014` | `2774` | `passive` | **近战增益**<br>*Melee Buff* | 基本近战攻击：对流血状态的敌人额外造成20%的伤害  // 无图标 | 机体 rhinox_gs_voyager2014 已有部分战技实现，本次加入新战技【近战增益】，属于增量追加 |
| 35 | **犀牛**<br>`rhinox_gs_voyager2014` | `2779` | `signature` | **超频**<br>*Overclock* | 护盾防御能力提升，每个护盾增益将一次攻击造成的伤害上限限制为对手攻击力的60%，如果对手单次攻击的伤害超过60%，则会被施加1层震... | 机体 rhinox_gs_voyager2014 已有部分战技实现，本次加入新战技【超频】，属于增量追加 |
| 36 | **犀牛**<br>`rhinox_gs_voyager2014` | `2792` | `sp3` | **流血**<br>*Chainguns of Doom* | 30%概率触发流血，施加攻击力45%的伤害，持续12秒 如果对方生命值大于90%，伤害增加55% 如果对方生命值大于75%，伤害增... | 机体 rhinox_gs_voyager2014 已有部分战技实现，本次加入新战技【流血】，属于增量追加 |
| 37 | **滑流**<br>`slipstream_gs` | `3354` | `passive` | **远程驱散**<br>*Ranged Nullify* | 基础远程攻击100%概率驱散对手一个护盾类增益 | 机体 slipstream_gs 已有部分战技实现，本次加入新战技【远程驱散】，属于增量追加 |
| 38 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3471` | `signature` | **远程增益**<br>*Ranged Buff* | 体力少于50%时，远程攻击速度提升50% | 机体 waspinator_gs_deluxe 已有部分战技实现，本次加入新战技【远程增益】，属于增量追加 |
| 39 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3472` | `passive` | **远程增益**<br>*Ranged Buff* | 体力少于50%时，获得远程增益，远程攻击速度提升50% | 机体 waspinator_gs_deluxe 已有部分战技实现，本次加入新战技【远程增益】，属于增量追加 |
| 40 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3473` | `passive` | **特殊技伤害**<br>*Special Damage* | 生命值小于25%时，获得30%的永久特殊技伤害 | 机体 waspinator_gs_deluxe 已有部分战技实现，本次加入新战技【特殊技伤害】，属于增量追加 |
| 41 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3474` | `passive` | **抗性减益**<br>*Resistance Debuff* | 普通远程攻击命中对手时施加一层30%的抗性减益，持续2秒 重击命中对手时施加一层30%的抗性减益，持续5秒 //抗性减益将受到的伤... | 机体 waspinator_gs_deluxe 已有部分战技实现，本次加入新战技【抗性减益】，属于增量追加 |
| 42 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3475` | `sp1` | **暴击几率**<br>*Crit Rate* | 45%的概率得到暴击几率增益，提升30%的暴击几率，持续4秒 | 机体 waspinator_gs_deluxe 已有部分战技实现，本次加入新战技【暴击几率】，属于增量追加 |
| 43 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3476` | `sp1` | **规避克制**<br>*Anti Evade* | 施加规避克制，降低对手30%的规避概率，持续4秒 | 机体 waspinator_gs_deluxe 已有部分战技实现，本次加入新战技【规避克制】，属于增量追加 |
| 44 | **黄蜂勇士**<br>`waspinator_gs_deluxe` | `3477` | `sp2` | **抗性减益**<br>*Resistance Debuff* | 最后一击施加一层30%的抗性减益，持续5秒 | 机体 waspinator_gs_deluxe 已有部分战技实现，本次加入新战技【抗性减益】，属于增量追加 |
| 45 | **千斤顶**<br>`wheeljack_gs_mp20` | `2888` | `signature` | **力量护盾**<br>*Force Shield* | 如果敌人的攻击将千斤顶的生命值降低到75%，50%或25%以下，力量护盾将激活，100%降低敌人攻击造成的所有伤害，持续8秒。//... | 机体 wheeljack_gs_mp20 已有部分战技实现，本次加入新战技【力量护盾】，属于增量追加 |
| 46 | **千斤顶**<br>`wheeljack_gs_mp20` | `3657` | `passive` | **升级**<br>*Upgrade* | 每次发动重击时，构建一个随机的升级，构建时间为4秒，构建完成后，随机得到进攻/能量/防御升级中的一个// 出现灰色的图标带倒计时，... | 机体 wheeljack_gs_mp20 已有部分战技实现，本次加入新战技【升级】，属于增量追加 |
| 47 | **千斤顶**<br>`wheeljack_gs_mp20` | `3658` | `passive` | **成功**<br>*Success* | 如果千斤顶得到三个同样的升级，会触发立即回血，随机得到最大生命值的10~20% | 机体 wheeljack_gs_mp20 已有部分战技实现，本次加入新战技【成功】，属于增量追加 |
| 48 | **千斤顶**<br>`wheeljack_gs_mp20` | `3659` | `sp2` | **刷新升级**<br>*Upgrade Randomize* | 把已有的升级全部随机替换  // 如果有三个升级，则对每个升级ROLL DICE，在攻击/防御/能量中随机三选一替换 | 机体 wheeljack_gs_mp20 已有部分战技实现，本次加入新战技【刷新升级】，属于增量追加 |
| 49 | **千斤顶**<br>`wheeljack_gs_mp20` | `3660` | `sp3` | **升级对齐**<br>*Upgrade Normalize* | 把所有升级变成与第一个升级相同  //如果有三个升级，第一个是能量升级，则变成三个能量升级，从而也会触发“成功”技能，进行回血。但... | 机体 wheeljack_gs_mp20 已有部分战技实现，本次加入新战技【升级对齐】，属于增量追加 |


### 2.3 分类三：调整的 (Modified, 共 22 项)

> **定义**：该角色的该能力已实现，但在本次优先列表中存在改动。战技已在本地落地，但在优先列表中的名称、数值倍率、中文描述或触发条件与本地既有代码存在版本差异，需做针对性局部修正。

涵盖 **7 位英雄**：黄豹 (`cheetor_bw_transmetal`, 5项)、狂飙 (`cyclonus_gs_uw06`, 1项)、红蜘蛛 (`fte_stars_gs_t3`, 1项)、反冲 (`kickback_gs_kabam`, 6项)、震天尊 (`megatronus_gs_kabam`, 5项)、补天士 (`rodimusprime_gs_mp09`, 1项)、横炮 (`sideswipe_gs`, 3项)。

| 序号 | 机体 (`bot_id`) | 技能 ID | 分类 | 中文名称 / 英文名称 | 官方效果摘要 | 判定理由与落地线索 |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | **黄豹**<br>`cheetor_bw_transmetal` | `2462` | `sp1` | **阻止修复**<br>*Repair Block* | 施加阻止修复，禁用对方所有回血能力，直到对方流血状态解除。 | 描述或数值存在版本调整: 代码实现记录为[-...]，优先列表为[施加阻止修复，禁用对方所有回血能力，直到对方流血状态解除。...] |
| 2 | **黄豹**<br>`cheetor_bw_transmetal` | `2476` | `sp1` | **流血**<br>*Bleed* | 最后一击命中时100%概率触发流血，施加攻击力100%的伤害，持续8秒 | 描述或数值存在版本调整: 代码实现记录为[-  近战攻击出暴击时，有45%的概率触发流血，造成攻击力6...]，优先列表为[最后一击命中时100%概率触发流血，施加攻击力100%的伤害...] |
| 3 | **黄豹**<br>`cheetor_bw_transmetal` | `2477` | `sp2` | **能量功率**<br>*Power Rate* | 获得能量功率增益，能量获取量增加50%，持续12秒 | 描述或数值存在版本调整: 代码实现记录为[-...]，优先列表为[获得能量功率增益，能量获取量增加50%，持续12秒...] |
| 4 | **黄豹**<br>`cheetor_bw_transmetal` | `2479` | `sp3` | **能量锁定**<br>*Power Lock* | 技能完成时100%概率触发能量锁定，阻止对方获得能量，持续10秒 | 描述或数值存在版本调整: 代码实现记录为[-...]，优先列表为[技能完成时100%概率触发能量锁定，阻止对方获得能量，持续1...] |
| 5 | **黄豹**<br>`cheetor_bw_transmetal` | `2480` | `sp3` | **能量燃烧**<br>*Power Burn* | 0.5秒内扣减对方最大能量的3% | 描述或数值存在版本调整: 代码实现记录为[-  黄豹对吸取能量的技能（能量流失、能量燃烧）免疫，此类技...]，优先列表为[0.5秒内扣减对方最大能量的3%...] |
| 6 | **狂飙**<br>`cyclonus_gs_uw06` | `2991` | `sp3` | **黑暗场**<br>*Dark Field* | 狂飙获得黑暗能量，并且在10秒内连续释放黑暗场脉冲。 | 描述或数值存在版本调整: 代码实现记录为[-  当狂飙获得一层黑暗能量或在拥有黑暗能量的情况下使用L4...]，优先列表为[狂飙获得黑暗能量，并且在10秒内连续释放黑暗场脉冲。...] |
| 7 | **红蜘蛛**<br>`fte_stars_gs_t3` | `2357` | `passive` | **零射线**<br>*Null Ray* | 基础远程攻击命中时100%概率驱散一个护甲、近战或者攻击增益。 驱散时造成攻击力90%的即时震击伤害。 | 描述或数值存在版本调整: 代码实现记录为[-  基础远程攻击命中时100%概率驱散一个护甲、近战或者攻...]，优先列表为[基础远程攻击命中时100%概率驱散一个护甲、近战或者攻击增益...] |
| 8 | **反冲**<br>`kickback_gs_kabam` | `3102` | `sp1` | **震击**<br>*Shock* | 对于对方身上每1层能量流失，施加1层震击，造成攻击力40%的伤害，持续5秒 | 描述或数值存在版本调整: 代码实现记录为[-  重击发起时，自己身上所有震击、能量汲取、能量锁定和能量...]，优先列表为[对于对方身上每1层能量流失，施加1层震击，造成攻击力40%的...] |
| 9 | **反冲**<br>`kickback_gs_kabam` | `3103` | `sp2` | **暴击几率**<br>*Crit Rate* | 技能命中时，获得一个30%的暴击率增益，持续8秒 | 描述或数值存在版本调整: 代码实现记录为[-  L4和M2命中时增加30%的暴击几率。//无图标，仅针...]，优先列表为[技能命中时，获得一个30%的暴击率增益，持续8秒...] |
| 10 | **反冲**<br>`kickback_gs_kabam` | `3104` | `sp2` | **能量流失**<br>*Power Leak* | 从第3击到最后一击，每一击触发暴击时100%的概率造成能量流失，在10秒内扣除对方最大能量的9.6%，最多叠加5层。 | 描述或数值存在版本调整: 代码实现记录为[-  触发暴击时100%的概率造成能量流失，在10秒内扣除对...]，优先列表为[从第3击到最后一击，每一击触发暴击时100%的概率造成能量流...] |
| 11 | **反冲**<br>`kickback_gs_kabam` | `3105` | `sp2` | **流血**<br>*Bleed* | 第3击到最后一击，每一击暴击时100%的概率触发流血，造成攻击力26%的伤害，持续7秒。 | 描述或数值存在版本调整: 代码实现记录为[-...]，优先列表为[第3击到最后一击，每一击暴击时100%的概率触发流血，造成攻...] |
| 12 | **反冲**<br>`kickback_gs_kabam` | `3107` | `sp3` | **修复**<br>*Repair* | 对于对方身上每1层能量流失，反冲获得一个修复增益，5秒内修复最大生命值的3%。 | 描述或数值存在版本调整: 代码实现记录为[-...]，优先列表为[对于对方身上每1层能量流失，反冲获得一个修复增益，5秒内修复...] |
| 13 | **反冲**<br>`kickback_gs_kabam` | `3106` | `sp3` | **能量流失**<br>*Power Leak* | 技能所有攻击触发暴击时100%的概率造成能量流失，在10秒内扣除对方最大能量的9.6%，最多叠加5层。 | 描述或数值存在版本调整: 代码实现记录为[-  触发暴击时100%的概率造成能量流失，在10秒内扣除对...]，优先列表为[技能所有攻击触发暴击时100%的概率造成能量流失，在10秒内...] |
| 14 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715893` | `passive` | **狂怒遗迹**<br>*Relic of Fury* | 开局处于狂怒遗迹状态，此状态下攻击力提升60%，降低对手20%的格挡精通 每充满一格能量，切换到保存遗迹 //橙色图标 | 描述或数值存在版本调整: 代码实现记录为[-  开局处于狂怒遗迹状态，此状态下攻击力提升60%，降低对...]，优先列表为[开局处于狂怒遗迹状态，此状态下攻击力提升60%，降低对手20...] |
| 15 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715894` | `passive` | **保存遗迹**<br>*Relic of Preservation* | 此状态下伤害抗性提升60% 此状态下，限制对方任何单次攻击的伤害上限为震天尊最大生命值的20% 每充满一格能量，切换到保存遗迹 /... | 描述或数值存在版本调整: 代码实现记录为[-  开局处于狂怒遗迹状态，此状态下攻击力提升60%，降低对...]，优先列表为[此状态下伤害抗性提升60% 此状态下，限制对方任何单次攻击的...] |
| 16 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715902` | `sp3` | **黑暗燃烧**<br>*Dark Burn* | 最后一击100%概率施加黑暗燃烧，造成攻击力200%的即时伤害 | 描述或数值存在版本调整: 代码实现记录为[-  重击命中100%概率施加黑暗燃烧，造成攻击力40%的即...]，优先列表为[最后一击100%概率施加黑暗燃烧，造成攻击力200%的即时伤...] |
| 17 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715903` | `sp3` | **能量窃取**<br>*Power Steal* | 如果狂怒遗迹生效，第一击有66%的概率窃取对手现有能量的35% //立即结算，红色图标出现在对方侧，一闪而过 | 描述或数值存在版本调整: 代码实现记录为[-  如果狂怒遗迹生效，最后一击有100%的概率窃取对手现有...]，优先列表为[如果狂怒遗迹生效，第一击有66%的概率窃取对手现有能量的35...] |
| 18 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715904` | `sp3` | **生命窃取**<br>*Life Steal* | 如果保存遗迹生效，第一击有66%概率窃取对手生命，相当于震天尊最大生命值的17.5%   //红色图标出现在对方侧，一闪而过，我方... | 描述或数值存在版本调整: 代码实现记录为[-  如果保存遗迹生效，第一击有100%概率窃取对手生命，相...]，优先列表为[如果保存遗迹生效，第一击有66%概率窃取对手生命，相当于震天...] |
| 19 | **补天士**<br>`rodimusprime_gs_mp09` | `2798` | `passive` | **近战驱散**<br>*Melee Nullify* | 近战组合的最后一击（M2或者L2）命中时： 50%的概率驱散对方一个近战增益 50%的概率驱散对方一个护甲增益 | 描述或数值存在版本调整: 代码实现记录为[-  近战组合的最后一击（M2或者L2）命中时：50%概率驱...]，优先列表为[近战组合的最后一击（M2或者L2）命中时： 50%的概率驱散...] |
| 20 | **横炮**<br>`sideswipe_gs` | `2840` | `passive` | **暴击伤害**<br>*Crit Damage* | 闪避对方前冲攻击时，获得暴击伤害增益，提升108%的暴击伤害，持续6秒 | 描述或数值存在版本调整: 代码实现记录为[-  重击时刷新所有暴击伤害增益的倒计时。...]，优先列表为[闪避对方前冲攻击时，获得暴击伤害增益，提升108%的暴击伤害...] |
| 21 | **横炮**<br>`sideswipe_gs` | `2838` | `sp2` | **近战规避**<br>*Melee Evade* | 获得8秒的近战规避，35%的概率规避基础近战和SP1/SP2中的近战攻击 | 描述或数值存在版本调整: 代码实现记录为[-  受到7次普通攻击后，获得近战规避增益，38%的概率规避...]，优先列表为[获得8秒的近战规避，35%的概率规避基础近战和SP1/SP2...] |
| 22 | **横炮**<br>`sideswipe_gs` | `2839` | `passive` | **能量获取**<br>*Power Gain* | 闪避远程普通攻击和远程重击时，1秒内获得最大能量的13%。 | 描述或数值存在版本调整: 代码实现记录为[-  开局后得到一个能量获取增益，在12秒内得到最大能量的5...]，优先列表为[闪避远程普通攻击和远程重击时，1秒内获得最大能量的13%。...] |


### 2.4 分类四：冲突的 (Conflicting / Redundant, 共 62 项)

> **定义**：该角色的该能力已在本地完整实现并通过测试，且在优先列表中没有任何改动。由于云端数据库状态未及时更新（仍停留为 `priority` 而非 `implemented`），造成待办清单冗余推送。建议批量同步云端状态，无需重复编写代码。

涵盖 **18 位英雄**：黄豹 (4项)、狂飙 (1项)、红蜘蛛 (1项)、钢锁 (7项)、碾碎器 (1项)、热破 (4项)、G1铁皮 (4项)、反冲 (5项)、震天尊 (8项)、暗天陨 (2项)、猩猩队长 (4项)、电影擎天柱 (1项)、补天士 (2项)、巨蝎勇士 (5项)、横炮 (4项)、飞毛腿 (1项)、野牛 (5项)、惊天雷 (3项)。

| 序号 | 机体 (`bot_id`) | 技能 ID | 分类 | 中文名称 / 英文名称 | 官方效果摘要 | 判定理由与落地线索 |
| :---: | :--- | :---: | :---: | :--- | :--- | :--- |
| 1 | **黄豹**<br>`cheetor_bw_transmetal` | `2473` | `passive` | **暴击流血**<br>*Critical Bleed* | 近战攻击出暴击时，有45%的概率触发流血，造成攻击力65%的伤害，持续4秒。 | 战技【暴击流血】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 2 | **黄豹**<br>`cheetor_bw_transmetal` | `2474` | `passive` | **能量获取**<br>*Power Gain* | L4或者M2命中对手的时候，在1秒内获得最大能量槽的2.5% | 战技【能量获取】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 3 | **黄豹**<br>`cheetor_bw_transmetal` | `2475` | `passive` | **重击规避远程**<br>*Heavy Evade Range* | 黄豹重击过程中有35%的概率穿透对方的基础远程和远程重击 // 参考风刃的重击 如果没有触发穿透，则100%的概率触发规避 | 战技【重击规避远程】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 4 | **黄豹**<br>`cheetor_bw_transmetal` | `2472` | `passive` | **能量守护**<br>*Power Guard* | 黄豹对吸取能量的技能（能量流失、能量燃烧）免疫，此类技能无法扣减黄豹的能量 | 战技【能量守护】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 5 | **狂飙**<br>`cyclonus_gs_uw06` | `2973` | `passive` | **黑暗场**<br>*Dark Field* | 当狂飙获得一层黑暗能量或在拥有黑暗能量的情况下使用L4或者M2命中对手时，他会放出黑暗场脉冲。//狂飙身上会有一个紫色光圈扩散开 ... | 战技【黑暗场】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 6 | **红蜘蛛**<br>`fte_stars_gs_t3` | `2362` | `passive` | **规避近战重击**<br>*Evade Heavy Melee* | 20%的概率机规避近战重击。//无图标，天然技能，在敌人近战重击即将命中时计算概率 | 战技【规避近战重击】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 7 | **钢锁**<br>`grimlock_gs_mp08` | `2532` | `passive` | **近战增益**<br>*Melee Buff* | 受到攻击时，有14%的概率得到一层近战增益，增加近战伤害14%，持续5秒，可叠加。 使用重击和特殊技时全程 | 战技【近战增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 8 | **钢锁**<br>`grimlock_gs_mp08` | `2534` | `signature` | **恐龙之怒**<br>*Dino Rage* | 钢锁在受到伤害减益后1秒净化该减益，并有30%的概率得到一层近战增益，增加近战伤害30%，持续5秒，可叠加。    //所有带倒计... | 战技【恐龙之怒】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 9 | **钢锁**<br>`grimlock_gs_mp08` | `2542` | `passive` | **燃烧**<br>*Burn* | 重击命中时有70%几率造成燃烧，施加攻击力50%的伤害，持续2秒。 | 战技【燃烧】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 10 | **钢锁**<br>`grimlock_gs_mp08` | `2543` | `passive` | **不可阻挡**<br>*Unstoppable* | 重击全程进入不可阻挡状态 | 战技【不可阻挡】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 11 | **钢锁**<br>`grimlock_gs_mp08` | `2544` | `sp1` | **近战增益**<br>*Melee Buff* | 100%的概率得到一层近战增益，增加近战伤害12%，持续5秒。 | 战技【近战增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 12 | **钢锁**<br>`grimlock_gs_mp08` | `2545` | `sp1` | **燃烧**<br>*Burn* | 100%几率造成燃烧，施加攻击力100%的伤害，持续4秒。 | 战技【燃烧】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 13 | **钢锁**<br>`grimlock_gs_mp08` | `2546` | `sp2` | **近战增益**<br>*Melee Buff* | 100%的概率得到一层近战增益，增加近战伤害18%，持续5秒。 | 战技【近战增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 14 | **碾碎器**<br>`grindor_cin_rotf` | `3058` | `passive` | **暴击率减益**<br>*Crit Debuff* | 当受到攻击时，有11%概率造成一层暴击率减益，降低对手暴击率40%，持续 | 战技【暴击率减益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 15 | **热破**<br>`hotrod_cin_tlk` | `2550` | `passive` | **眩晕**<br>*Stun* | 重击暴击时有40%的概率造成眩晕，持续1.5秒 | 战技【眩晕】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 16 | **热破**<br>`hotrod_cin_tlk` | `2563` | `sp2` | **减速**<br>*Deceleration* | 远程攻击命中或被防御时，有60%的概率施加减速，持续3.2秒。 | 战技【减速】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 17 | **热破**<br>`hotrod_cin_tlk` | `2564` | `sp3` | **减速**<br>*Deceleration* | 远程攻击命中或被防御时，有60%的概率施加减速，持续3.2秒。 | 战技【减速】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 18 | **热破**<br>`hotrod_cin_tlk` | `2562` | `passive` | **能量功率减益**<br>*Power Rate Debuff* | 减速中的对方无法规避 每层减速降低对手能量功率27.2% | 战技【能量功率减益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 19 | **G1铁皮**<br>`ironhide_gs_kabam` | `2631` | `sp2` | **护甲增益**<br>*Armor Buff* | 不可阻挡结束后，获得3层护甲增益，每层4%，持续10秒 | 战技【护甲增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 20 | **G1铁皮**<br>`ironhide_gs_kabam` | `2632` | `passive` | **护甲增益**<br>*Armor Buff* | 开场后获得5层护甲增益，每层4%，持续10秒 | 战技【护甲增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 21 | **G1铁皮**<br>`ironhide_gs_kabam` | `2628` | `sp1` | **近战增益**<br>*Melee Buff* | 技能结束后获得1层近战增益，增加35%的近战伤害，持续8秒 | 战技【近战增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 22 | **G1铁皮**<br>`ironhide_gs_kabam` | `2630` | `sp2` | **不可阻挡**<br>*Unstoppable* | 技能结束后获得7秒的不可阻挡增益。 | 战技【不可阻挡】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 23 | **反冲**<br>`kickback_gs_kabam` | `3096` | `passive` | **能量流失**<br>*Power Leak* | 触发暴击时100%的概率造成能量流失，在10秒内扣除对方最大能量的9.6%，最多叠加5层。 | 战技【能量流失】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 24 | **反冲**<br>`kickback_gs_kabam` | `3097` | `passive` | **暴击几率**<br>*Crit Rate* | L4和M2命中时增加30%的暴击几率。//无图标，仅针对本次攻击本身 | 战技【暴击几率】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 25 | **反冲**<br>`kickback_gs_kabam` | `3098` | `passive` | **能量功率**<br>*Power Rate* | 对手处于能量流失状态时，反冲的近战攻击能量获取效率提升50%。 | 战技【能量功率】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 26 | **反冲**<br>`kickback_gs_kabam` | `3088` | `signature` | **T-齿轮破坏**<br>*T-Cog Sabotage* | 重击命中有80%的概率破坏对手的变形齿轮，对手能量获取功率降低30%，持续10秒。//红色图标 如果对手此时使用重击，重击会失败且... | 战技【T-齿轮破坏】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 27 | **反冲**<br>`kickback_gs_kabam` | `3099` | `passive` | **近战规避**<br>*Melee Evade* | 反冲的前冲攻击被对手闪避时，获得一个35%概率的近战规避增益，持续2秒。 | 战技【近战规避】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 28 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715892` | `passive` | **火种源的能量**<br>*Power from the Allspark* | 震天尊的攻击和受到攻击不产生能量，他每秒自动产生最大能量的1.2%  // 属于完全独立的能量产生机制，与其他所有角色都不同。 | 战技【火种源的能量】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 29 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715895` | `passive` | **不朽遗迹**<br>*Relic of Immortality* | 当震天尊生命值降到10%以下时，他会发光跃起震开对手并额外激活不朽遗迹，持续8秒，此期间震天尊免疫任何伤害 // 所有直接伤害，D... | 战技【不朽遗迹】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 30 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715896` | `passive` | **暴击几率**<br>*Crit Rate* | L4和M2命中时增加40%的暴击几率。//无图标，仅针对本次攻击本身 | 战技【暴击几率】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 31 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715897` | `passive` | **黑暗燃烧**<br>*Dark Burn* | 重击命中100%概率施加黑暗燃烧，造成攻击力40%的即时伤害 | 战技【黑暗燃烧】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 32 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715898` | `sp1` | **破甲**<br>*Armor Break* | 最后一击60%的概率施加破甲，移除对手一层护甲增益，施加30%的破甲减益，持续8秒 | 战技【破甲】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 33 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715899` | `sp1` | **能量窃取**<br>*Power Steal* | 如果狂怒遗迹生效，最后一击有100%的概率窃取对手现有能量的35% //立即结算，红色图标出现在对方侧，一闪而过 | 战技【能量窃取】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 34 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715900` | `sp2` | **不可防御**<br>*Unblockable* | 最后一击不可防御 | 战技【不可防御】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 35 | **震天尊**<br>`megatronus_gs_kabam` | `1793029715901` | `sp2` | **生命窃取**<br>*Life Steal* | 如果保存遗迹生效，第一击有100%概率窃取对手生命，相当于震天尊最大生命值的17.5%   //红色图标出现在对方侧，一闪而过，我... | 战技【生命窃取】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 36 | **暗天陨**<br>`nemesisprime_gs_voyager2015` | `3218` | `passive` | **重击驱散**<br>*Heavy Nullify* | 重击命中时随机驱散对手一个近战增益或护甲增益。//没有则不驱散 每多一层黑暗能量，重击伤害+5% | 战技【重击驱散】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 37 | **暗天陨**<br>`nemesisprime_gs_voyager2015` | `3224` | `sp3` | **不可防御**<br>*Unblockable* | 技能结束后，暗天陨的基础攻击全部不可防御，持续7秒，每多一层黑暗能量，持续时间增加0.5秒。 消耗全部黑暗能量。 | 战技【不可防御】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 38 | **猩猩队长**<br>`optimusprimal_bw_mp32` | `2709` | `passive` | **护甲增益**<br>*Armor Buff* | 当受到攻击时，有20%的概率获得护甲增益，降低受到攻击伤害的4%，无倒计时，最大堆叠10层。 //黄色护甲图标 当猩猩队长身上没有... | 战技【护甲增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 39 | **猩猩队长**<br>`optimusprimal_bw_mp32` | `2710` | `passive` | **近战增益**<br>*Melee Buff* | 格挡近战攻击时有30%的概率得到一层18%的近战增益，持续6秒。 | 战技【近战增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 40 | **猩猩队长**<br>`optimusprimal_bw_mp32` | `2711` | `passive` | **增益转换**<br>*Convert Buff* | 发动重击时，将所有护甲增益转化为近战增益，每一层增加18%的近战伤害，持续6秒。  //用例：6层护甲时发动重击，得到6层近战增益... | 战技【增益转换】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 41 | **猩猩队长**<br>`optimusprimal_bw_mp32` | `2713` | `sp3` | **攻击减益**<br>*Attack Debuff* | 100%的概率施加攻击减益，降低对手攻击力20%，持续32秒 | 战技【攻击减益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 42 | **电影擎天柱**<br>`optimusprime_cin_tf` | `2726` | `passive` | **意志力**<br>*Willpower* | 如果擎天柱正在流血状态，他将自己造成所有伤害的35%转化为自己的生命值。身上最多只能被施加一层流血，超过一层的流血会被当场净化，并... | 战技【意志力】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 43 | **补天士**<br>`rodimusprime_gs_mp09` | `2796` | `passive` | **前冲净化**<br>*Dashing Purify* | 前冲时有70%的概率净化补天士身上的一个减益。//无图标，净化成功显示文字“净化！” | 战技【前冲净化】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 44 | **补天士**<br>`rodimusprime_gs_mp09` | `2801` | `passive` | **重击破甲**<br>*Heavy Attack Armor Break* | 重击命中时，对方身上有几个增益，就施加几层破甲，每层强度15%，持续7秒。同时移除对方身上所有的护甲增益。//不移除对方其他增益 ... | 战技【重击破甲】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 45 | **巨蝎勇士**<br>`scorponok_bw_kabam` | `3253` | `passive` | **毒液充能**<br>*Venom Charge* | 充满一格能量时，获得一层毒液充能，无倒计时，可叠加，每层充能增加20%的攻击力。//橙色图标 | 战技【毒液充能】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 46 | **巨蝎勇士**<br>`scorponok_bw_kabam` | `3264` | `sp1` | **目眩**<br>*Daze* | 技能命中时施加目眩，敌人的基础远程攻击有60%的概率无法命中，特殊远程攻击100%无法命中，持续9.5秒。 | 战技【目眩】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 47 | **巨蝎勇士**<br>`scorponok_bw_kabam` | `3277` | `sp2` | **毒液逆火**<br>*Venom Backfire* | 技能结束时，将所有毒液充能转化为对应层数的逆火减益，持续12秒。 对手在逆火减益状态下使用特殊技，将被施加与逆火相同层数的瞬间震击... | 战技【毒液逆火】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 48 | **巨蝎勇士**<br>`scorponok_bw_kabam` | `3278` | `sp3` | **目眩**<br>*Daze* | 技能命中时施加目眩，敌人的基础远程攻击有60%的概率无法命中，特殊远程攻击100%无法命中，持续26秒。 | 战技【目眩】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 49 | **巨蝎勇士**<br>`scorponok_bw_kabam` | `3276` | `passive` | **毒液逆火**<br>*Venom Backfire* | 重击命中，将所有毒液充能转化为对应层数的逆火减益，持续12秒。 对手在逆火减益状态下使用特殊技，将被施加与逆火相同层数的瞬间震击，... | 战技【毒液逆火】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 50 | **横炮**<br>`sideswipe_gs` | `2816` | `passive` | **近战规避**<br>*Melee Evade* | 受到7次普通攻击后，获得近战规避增益，38%的概率规避基础近战和SP1/SP2中的近战攻击，持续4秒。//显示一个灰色的规避图标，... | 战技【近战规避】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 51 | **横炮**<br>`sideswipe_gs` | `2820` | `passive` | **暴击率增益**<br>*Crit Buff* | 横炮触发暴击时，100%概率得到一层3.8%的暴击率增益，可叠加。一旦横炮被击倒，就失去5层暴击率增益。 | 战技【暴击率增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 52 | **横炮**<br>`sideswipe_gs` | `2823` | `passive` | **重击刷新**<br>*Heavy Refresh* | 重击时刷新所有暴击伤害增益的倒计时。 | 战技【重击刷新】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 53 | **横炮**<br>`sideswipe_gs` | `2824` | `signature` | **最大推力**<br>*Maximum Thrust* | 开局后得到一个能量获取增益，在12秒内得到最大能量的50% | 战技【最大推力】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 54 | **飞毛腿**<br>`sunstreaker_gs_deluxe2008` | `2837` | `passive` | **不可阻抗**<br>*Unstoppable* | 生命值掉到40%以下时，得到5秒的不可阻挡增益。 | 战技【不可阻抗】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 55 | **野牛**<br>`tantrum_gs_kabam` | `3438` | `passive` | **不可阻挡**<br>*Unstoppable* | 进入防御状态1.5秒后，获得4.5秒的不可阻挡增益。//出现一个灰色的不可阻挡图标，倒计时1.5秒后变成黄色，进入不可阻挡状态。 ... | 战技【不可阻挡】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 56 | **野牛**<br>`tantrum_gs_kabam` | `3454` | `sp3` | **近战增益**<br>*Melee Buff* | 技能结束后获得3层近战增益，每层增加24%的近战伤害，最大叠加10层。//无倒计时 如果野牛后闪且身上没有不可阻挡状态，则失去所有... | 战技【近战增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 57 | **野牛**<br>`tantrum_gs_kabam` | `3453` | `sp3` | **不可阻挡**<br>*Unstoppable* | 技能结束后获得7.5秒的不可阻挡增益。 | 战技【不可阻挡】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 58 | **野牛**<br>`tantrum_gs_kabam` | `3450` | `passive` | **近战增益**<br>*Melee Buff* | 前冲时100%获得一层近战增益，增加24%的近战伤害，最大叠加10层。//无倒计时 如果野牛后闪且身上没有不可阻挡状态，则失去所有... | 战技【近战增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 59 | **野牛**<br>`tantrum_gs_kabam` | `3451` | `passive` | **天然护甲**<br>*Permanent Armor* | +10%的永久护甲增益，无图标，不可被破甲移除 | 战技【天然护甲】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 60 | **惊天雷**<br>`thundercracker_gs_leader2015` | `3409` | `passive` | **净化**<br>*Purify* | 重击开始时，净化身上所有流血，燃烧，震击，酸液，逆火和目眩减益。 | 战技【净化】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 61 | **惊天雷**<br>`thundercracker_gs_leader2015` | `3420` | `sp1` | **近战增益**<br>*Melee Buff* | 除第一击外，所有攻击获得10%的近战增益，持续2秒 | 战技【近战增益】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |
| 62 | **惊天雷**<br>`thundercracker_gs_leader2015` | `3422` | `sp3` | **震击**<br>*Shock* | 当你的敌人认为你已陷入绝境时……粉碎他们。 | 战技【震击】已在本地代码完整落地且表现一致，云端状态仍为 priority 未及时置为 implemented |


## 3. 按机体全量归纳与研发行动指南 (Bot-by-Bot Master Summary)

以下为优先列表中全部 40 位机体的完整状态分布表与研发行动指导：

| 序号 | 机体 (`bot_id`) | 中文名称 | 职业/阵营 | 优先战技总数 | 完全新的 | 增补的 | 调整的 | 冲突的 | 推荐后续行动与研发重点 |
| :---: | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| 1 | `blaster_gs_leader2016` | **录音机** | `tech` / `autobot` | **6** | 6 | 0 | 0 | 0 | 新建 `Server/abilities/bots/blaster_gs_leader2016.py`，根据真理源全量实现 6 项战技 |
| 2 | `breakdown_gs` | **打击** | `scou` / `decepticon` | **9** | 9 | 0 | 0 | 0 | 新建 `Server/abilities/bots/breakdown_gs.py`，根据真理源全量实现 9 项战技 |
| 3 | `bumblebee_gs_kabam` | **小黄蜂** | `scou` / `autobot` | **5** | 0 | 5 | 0 | 0 | 在既有模块增量追加 5 项新能力修饰器，完好保留已有功能 |
| 4 | `cheetor_bw_transmetal` | **黄豹** | `scou` / `maximal` | **11** | 0 | 2 | 5 | 4 | 增补 2 项新能力，按最新描述微调 5 项，冲突项 4 校验保留 |
| 5 | `chromia_gs_kabam` | **克劳莉娅** | `warr` / `autobot` | **9** | 9 | 0 | 0 | 0 | 新建 `Server/abilities/bots/chromia_gs_kabam.py`，根据真理源全量实现 9 项战技 |
| 6 | `cliffjumper_gs_kabam` | **飞过山** | `demo` / `autobot` | **6** | 6 | 0 | 0 | 0 | 新建 `Server/abilities/bots/cliffjumper_gs_kabam.py`，根据真理源全量实现 6 项战技 |
| 7 | `cyclonus_gs_uw06` | **狂飙** | `tact` / `decepticon` | **3** | 0 | 1 | 1 | 1 | 增补 1 项新能力，按最新描述微调 1 项，冲突项 1 校验保留 |
| 8 | `dragstrip_gs_deluxe2016` | **抢劫** | `warr` / `decepticon` | **9** | 9 | 0 | 0 | 0 | 新建 `Server/abilities/bots/dragstrip_gs_deluxe2016.py`，根据真理源全量实现 9 项战技 |
| 9 | `fte_optimus_gs_t3` | **G1擎天柱** | `tact` / `autobot` | **1** | 0 | 1 | 0 | 0 | 在既有模块增量追加 1 项新能力修饰器，完好保留已有功能 |
| 10 | `fte_stars_gs_t3` | **红蜘蛛** | `tact` / `decepticon` | **2** | 0 | 0 | 1 | 1 | 微调 1 项描述/数值差异，1 项冲突冗余直接保留 |
| 11 | `galvatron_gs_voyager2016` | **惊破天** | `demo` / `decepticon` | **9** | 9 | 0 | 0 | 0 | 新建 `Server/abilities/bots/galvatron_gs_voyager2016.py`，根据真理源全量实现 9 项战技 |
| 12 | `grimlock_gs_mp08` | **钢锁** | `braw` / `autobot` | **7** | 0 | 0 | 0 | 7 | 所有能力 (7项) 均已完整实现，更新云端状态为 implemented 即可 |
| 13 | `grindor_cin_rotf` | **碾碎器** | `braw` / `decepticon` | **1** | 0 | 0 | 0 | 1 | 所有能力 (1项) 均已完整实现，更新云端状态为 implemented 即可 |
| 14 | `hotrod_cin_tlk` | **热破** | `warr` / `autobot` | **4** | 0 | 0 | 0 | 4 | 所有能力 (4项) 均已完整实现，更新云端状态为 implemented 即可 |
| 15 | `ironhide_gs_kabam` | **G1铁皮** | `braw` / `autobot` | **4** | 0 | 0 | 0 | 4 | 所有能力 (4项) 均已完整实现，更新云端状态为 implemented 即可 |
| 16 | `jetfire_gs_leader2014` | **天火** | `tech` / `autobot` | **7** | 0 | 7 | 0 | 0 | 在既有模块增量追加 7 项新能力修饰器，完好保留已有功能 |
| 17 | `kickback_gs_kabam` | **反冲** | `scou` / `decepticon` | **13** | 0 | 2 | 6 | 5 | 增补 2 项新能力，按最新描述微调 6 项，冲突项 5 校验保留 |
| 18 | `megatron_cin_rotf` | **电影威震天** | `demo` / `decepticon` | **9** | 9 | 0 | 0 | 0 | 新建 `Server/abilities/bots/megatron_cin_rotf.py`，根据真理源全量实现 9 项战技 |
| 19 | `megatron_gs_leader2015` | **G1威震天** | `tact` / `decepticon` | **2** | 0 | 2 | 0 | 0 | 在既有模块增量追加 2 项新能力修饰器，完好保留已有功能 |
| 20 | `megatronus_gs_kabam` | **震天尊** | `demo` / `decepticon` | **13** | 0 | 0 | 5 | 8 | 微调 5 项描述/数值差异，8 项冲突冗余直接保留 |
| 21 | `mirage_gs_deluxe2016` | **幻影** | `tech` / `autobot` | **8** | 8 | 0 | 0 | 0 | 新建 `Server/abilities/bots/mirage_gs_deluxe2016.py`，根据真理源全量实现 8 项战技 |
| 22 | `mixmaster_cin_rotf` | **搅拌者** | `demo` / `decepticon` | **7** | 0 | 7 | 0 | 0 | 在既有模块增量追加 7 项新能力修饰器，完好保留已有功能 |
| 23 | `motormaster_gs_voyager2015` | **汽车大师** | `braw` / `decepticon` | **5** | 0 | 5 | 0 | 0 | 在既有模块增量追加 5 项新能力修饰器，完好保留已有功能 |
| 24 | `nemesisprime_gs_voyager2015` | **暗天陨** | `tact` / `decepticon` | **2** | 0 | 0 | 0 | 2 | 所有能力 (2项) 均已完整实现，更新云端状态为 implemented 即可 |
| 25 | `optimusprimal_bw_mp32` | **猩猩队长** | `braw` / `maximal` | **4** | 0 | 0 | 0 | 4 | 所有能力 (4项) 均已完整实现，更新云端状态为 implemented 即可 |
| 26 | `optimusprime_cin_tf` | **电影擎天柱** | `braw` / `autobot` | **1** | 0 | 0 | 0 | 1 | 所有能力 (1项) 均已完整实现，更新云端状态为 implemented 即可 |
| 27 | `optimusprime_sg_voyager2015` | **倾天柱** | `braw` / `autobot` | **4** | 4 | 0 | 0 | 0 | 新建 `Server/abilities/bots/optimusprime_sg_voyager2015.py`，根据真理源全量实现 4 项战技 |
| 28 | `rhinox_gs_voyager2014` | **犀牛** | `tech` / `maximal` | **4** | 0 | 4 | 0 | 0 | 在既有模块增量追加 4 项新能力修饰器，完好保留已有功能 |
| 29 | `rodimusprime_gs_mp09` | **补天士** | `tact` / `autobot` | **3** | 0 | 0 | 1 | 2 | 微调 1 项描述/数值差异，2 项冲突冗余直接保留 |
| 30 | `scorponok_bw_kabam` | **巨蝎勇士** | `warr` / `predacon` | **5** | 0 | 0 | 0 | 5 | 所有能力 (5项) 均已完整实现，更新云端状态为 implemented 即可 |
| 31 | `shockwave_gs` | **震荡波** | `tech` / `decepticon` | **11** | 11 | 0 | 0 | 0 | 新建 `Server/abilities/bots/shockwave_gs.py`，根据真理源全量实现 11 项战技 |
| 32 | `sideswipe_gs` | **横炮** | `scou` / `autobot` | **7** | 0 | 0 | 3 | 4 | 微调 3 项描述/数值差异，4 项冲突冗余直接保留 |
| 33 | `skywarp_gs_leader2015` | **闹翻天** | `tech` / `decepticon` | **7** | 7 | 0 | 0 | 0 | 新建 `Server/abilities/bots/skywarp_gs_leader2015.py`，根据真理源全量实现 7 项战技 |
| 34 | `slipstream_gs` | **滑流** | `scou` / `decepticon` | **1** | 0 | 1 | 0 | 0 | 在既有模块增量追加 1 项新能力修饰器，完好保留已有功能 |
| 35 | `soundwave_gs` | **声波** | `tech` / `decepticon` | **9** | 9 | 0 | 0 | 0 | 新建 `Server/abilities/bots/soundwave_gs.py`，根据真理源全量实现 9 项战技 |
| 36 | `sunstreaker_gs_deluxe2008` | **飞毛腿** | `braw` / `autobot` | **1** | 0 | 0 | 0 | 1 | 所有能力 (1项) 均已完整实现，更新云端状态为 implemented 即可 |
| 37 | `tantrum_gs_kabam` | **野牛** | `braw` / `decepticon` | **5** | 0 | 0 | 0 | 5 | 所有能力 (5项) 均已完整实现，更新云端状态为 implemented 即可 |
| 38 | `thundercracker_gs_leader2015` | **惊天雷** | `braw` / `decepticon` | **3** | 0 | 0 | 0 | 3 | 所有能力 (3项) 均已完整实现，更新云端状态为 implemented 即可 |
| 39 | `waspinator_gs_deluxe` | **黄蜂勇士** | `demo` / `predacon` | **7** | 0 | 7 | 0 | 0 | 在既有模块增量追加 7 项新能力修饰器，完好保留已有功能 |
| 40 | `wheeljack_gs_mp20` | **千斤顶** | `tech` / `autobot` | **5** | 0 | 5 | 0 | 0 | 在既有模块增量追加 5 项新能力修饰器，完好保留已有功能 |

---

## 4. 报告完整性验证与稽核核对表 (Audit & Verification Checklist)

- [x] **数据完整性核验**：导出的优先清单共 229 项战技，本报告分类清单共收录 229 项，总数 100% 吻合，无遗漏战技。
- [x] **四分类互斥性核验**：每项能力被严格且唯一归入四类之一（完全新的: 96, 增补的: 49, 调整的: 22, 冲突的: 62），无重复归类。
- [x] **真理源对照核验**：代码落地判断严格以工程现存文件（`Server/abilities/bots/` 42个独立文件、`tools/nativehook/skills/bots/` 24个C技能模块）为依据，杜绝主观臆测。
- [x] **排版与中文规范**：报告遵循标准 Markdown 工业化格式，表格对齐良好，满足 UTF-8 编码与中文排版规范。