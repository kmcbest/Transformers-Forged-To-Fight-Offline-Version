# 已验收锁定代表角色档案与锁定制度（Accepted & Locked Exemplars）

本文档登记所有**已通过靶场/真机全项验收并物理哈希锁定**的代表性角色。
锁定的角色同时受 [accepted_bots_lock.json](file:///e:/Agent/TFTF/Server/abilities/accepted_bots_lock.json) 与质量门禁脚本 [check_accepted_lock.py](file:///e:/Agent/TFTF/tools/check_accepted_lock.py) 保护（已集成至 [run_ability_gate.py](file:///e:/Agent/TFTF/tools/run_ability_gate.py) 门禁 2B）。

> [!CAUTION]
> **锁定保护铁律**：凡状态为 `🔒 已验收锁定` 的角色，其 `Server/abilities/bots/*.py`、`tools/nativehook/skills/bots/skill_*.c` 及对应 `tools/autotest_scenarios/*.json` 均受 SHA-256 锁定保护。
> 未经用户明确批准，**严禁以顺手重构、统一风格或优化命名等理由修改已锁定角色的源码或剧本**。若确需修复经用户确认的问题，必须在改完并通过真机复验后运行 `python tools/check_accepted_lock.py --lock <bot_id>` 重新封存。

---

## 一、代表人物总览台账

| 序号 | 角色 | `bot_id` | 代表机制原型 | 状态 | 验收日期 | 回归剧本数 |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 阿尔茜 (Arcee) | `arcee_gs_deluxe2014` | **暴击率联动 / DOT(流血) / 远程规避 Callout** | 🔒 已验收锁定 | 2026-11-26 | 6 |
| 2 | 艾丽塔 (Elita-1) | `elita_one_gs` (`elita_one_gs_kabam`) | **动态职业判定 / 霸体近战规避 / 落空减益 / 技能打断与封锁** | 🧪 自动化通过，待人工验证 *(未锁定)* | 2026-11-26 | 10 |
| 3 | 电影铁皮 (Ironhide ROTF) | `ironhide_cin_rotf` | **单次命中暴击率门控 / 叠层燃烧 / 黄色暴伤与每局一次 SP 暴击觉醒** | 🔒 已验收锁定 | 2026-11-26 | 7 |
| 4 | 闪电 (Blitzwing) | `blitzwing_gs` | **双形态长按防御切换 / 抑制夹钳(增益阻断·减益阻断·SP3通用) / 绝处逢生全数引爆眩晕** | 🧪 自动化通过，待人工验收 *(未锁定)* | 2026-11-27 | 7 |
| 5 | 暗天陨 (Nemesis Prime) | `nemesisprime_gs_voyager2015` | **血线变速暗能量充能 / 亚空间脉冲克隆 / SP1减益复制复刻 / SP2双驱散 / 赝品领导模块吸血 / SP3浅紫不可防御** | 🧪 自动化通过，待人工验收 *(未锁定)* | 2026-11-27 | 6 |
| 6 | 眩晕 (Blackout) | `blackout_cin_tf` | **连击暴击与无尽怒火溢出转暴伤 / 重击与SP3末击+50%暴击燃烧 / 追猎落空回能 / SP1浅紫不可防御** | 🧪 自动化通过，待人工验收 *(未锁定)* | 2026-11-27 | 1 |
| — | *(预留代表位)* | — | 破甲 / 震撼 / 护甲减伤类代表 | 待验收 | — | — |
| — | *(预留代表位)* | — | 治疗 / 净化 / 减益转化类代表 | 待验收 | — | — |
| — | *(预留代表位)* | — | 聚气充能 / 双形态切换类代表 | 待验收 | — | — |
| — | *(预留代表位)* | — | 控气 / 能量窃取 / 不可阻挡类代表 | 待验收 | — | — |

常用管理命令：
```powershell
# 查看当前所有代表人物与锁定状态
python tools/check_accepted_lock.py --list

# 校验证书与源码/剧本是否发生未授权篡改（run_ability_gate.py 默认自动运行）
python tools/check_accepted_lock.py --check

# 一键在 MuMu 15 重跑全部已锁定角色的真机靶场回归测试
python tools/check_accepted_lock.py --run-device --serial 127.0.0.1:7555
```

---

## 二、代表人物详细档案

### 1. 阿尔茜 (`arcee_gs_deluxe2014`) —— 暴击 + DOT(流血) 标杆代表

- **验收环境**：MuMu 15 (`127.0.0.1:7555`)，6/6 场景全绿通过
- **锁定源码与资产**：
  - 技能定义：[arcee.py](file:///e:/Agent/TFTF/Server/abilities/bots/arcee.py)
  - 运行时状态机：[skill_arcee.c](file:///e:/Agent/TFTF/tools/nativehook/skills/bots/skill_arcee.c)
  - 关联公共能力：`gp_evade_callout` / `appr_evade_callout`（[__init__.py](file:///e:/Agent/TFTF/Server/abilities/__init__.py)）
- **靶场回归剧本（6 条）**：

| 序号 | 剧本文件 | 验证核心机制 | 关键验收标准 |
| :--- | :--- | :--- | :--- |
| #1 | [arcee_test_blocked_ranged.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/arcee_test_blocked_ranged.json) | 远程攻击被格挡时不触发被动 | 格挡命中 P1 后 `must_not_apply_buffs`：`arcee_headshot_direct` / `dmg_bleed` / `dmg_direct` 均为 0 |
| #2 | [arcee_test_headshot_stack.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/arcee_test_headshot_stack.json) | 爆头 49.7% 直伤连发可叠加 | 连发远程直伤/流血正常叠加（`st=10` 不被 0.5s 刷新顶掉）并持续跳 DOT |
| #3 | [arcee_test_passive_rush.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/arcee_test_passive_rush.json) | 20.7% 远程规避绿字 Callout + 前冲 +50% 暴击 + 暴击回能 | 触发 `EVT=EVADE`、`gp_evade_callout`（无状态栏图标仅绿色“规避”呼出）、`ARCEE_DASH_PUNISHMENT`、`ARCEE_CRIT_POWER_GAIN` |
| #4 | [arcee_test_sp1_trick_shot.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/arcee_test_sp1_trick_shot.json) | SP1 特技射击增伤与提速 | 施加 `arcee_sp1_trick_shot`（+35% 远程伤害、+40% 射速 6.5s）并激活 `RANGED_BOOST_ACTIVATED` |
| #5 | [arcee_test_sp2_bleed.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/arcee_test_sp2_bleed.json) | SP2 仅暴击触发 108% 流血 | 暴击时挂载 `arcee_sp2_bleed`（4s 108% ATK）并产生流血 DOT Tick |
| #6 | [arcee_test_sp3_snipe.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/arcee_test_sp3_snipe.json) | SP3 前序小枪与尾击狙击分离 + 黄色觉醒图标 + 碎骨魔不反伤 | 仅末击触发 `arcee_sp3_snipe_direct` / `arcee_sp3_snipe_bleed`；SP 发动概率挂黄色 `arcee_sig_ferocity`；且 `hit=6` 暴击碎骨魔时 `P0` 不挂 `bonecrusher_struck_crit_bleed` |

- **后续同类型（暴击 / DOT）角色可直接复用的经验规范**：
  1. **短持续直伤/DOT 修饰器若可连续高频触发**，必须设置足够 `st`（如 `st=10`），避免同一波连射内后一发顶掉前一发直伤。
  2. **所有攻击命中触发型被动**必须显式判断 `!ctx->is_blocked`，防止攻击被格挡时仍透传流血或回能。
  3. **纯提示 Callout（无血条状态图标）**统一复用 `appr_*` 设 `"t": ""` + 挂入 `sp_callout` 系模式，仅触发 `HudCalloutController` 大字而不生成图标组件。
  4. **多段混合武器特技（手枪 + 终结狙击等）**在 `on_hit_connected` 中必须区分 `ctx->is_last_hit` 与 `ctx->hit_index`，避免前段小枪误享尾击大招特效。
  5. **受击方“仅限近战暴击反制”**必须检查 `ctx->is_melee`，禁止再用 `!ctx->is_ranged` 替代（SP 远程/特技段的 `is_ranged` 也为 `0`）。

- **一键单独复测阿尔茜**：
  ```powershell
  python tools/check_accepted_lock.py --run-device --bot arcee_gs_deluxe2014 --serial 127.0.0.1:7555
  ```

---

### 2. 艾丽塔 (`elita_one_gs` / `elita_one_gs_kabam`) —— *(未锁定，待人工实机复核后择机封存)*

- **当前状态**：`🧪 自动化通过，待人工验证`（仅记录，未加入 `accepted_bots_lock.json` 哈希锁，可随时根据实机观感微调）
- **自动化验证环境**：MuMu 15 (`127.0.0.1:7555`)，10/10 场景全绿通过（204.14s）
- **关联源码**：
  - 技能定义：[elita_one.py](file:///e:/Agent/TFTF/Server/abilities/bots/elita_one.py)
  - 运行时状态机：[skill_elita.c](file:///e:/Agent/TFTF/tools/nativehook/skills/bots/skill_elita.c)
- **靶场验证剧本（10 条）**：
  - [elita_test_tactical_insight.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_tactical_insight.json)（#1 战术洞察规避霸体+绿字+30%近战增益）
  - [elita_test_nimble_counter_proc.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_nimble_counter_proc.json)（#2a 侧/后闪50%获锦囊+反击眩晕）
  - [elita_test_nimble_counter_gates.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_nimble_counter_gates.json)（#2b 打格挡保留、命中眩晕一次、无锦囊不连晕）
  - [elita_test_nimble_counter_missed.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_nimble_counter_missed.json)（#3 任一攻击落空施加50%攻击减益）
  - [elita_test_joint_aim.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_joint_aim.json)（#4 关节狙击远程穿甲+命中/被防刷新减益+远程暴击破甲）
  - [elita_test_commanders_presence.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_commanders_presence.json)（#5 领袖威仪DOT倒计时加速20%）
  - [elita_test_sp1_brawler.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_sp1_brawler.json)（#6a SP1对斗士50%破甲+满能燃烧5%）
  - [elita_test_sp1_non_brawler.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_sp1_non_brawler.json)（#6b SP1对非斗士35%破甲）
  - [elita_test_sp2_sp3_lockdown.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_sp2_sp3_lockdown.json)（#7 SP2驱散+末击震击、SP3末击流血+8s战术封锁）
  - [elita_test_resistance_flame.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/elita_test_resistance_flame.json)（#8 抵抗军之火低血强化与每局1次SP1/2打断）

---

### 3. 电影铁皮 (`ironhide_cin_rotf`) —— 爆破系暴伤 + 叠层燃烧 + 末击暴击唤醒代表

- **验收环境**：MuMu 15 (`127.0.0.1:7555`)，7/7 全套脚本实机通过（`223.10s`），黄色图标改色后增量冒烟 `#4`（`30.70s`）通过
- **锁定源码与资产**：
  - 技能定义：[ironhide.py](file:///e:/Agent/TFTF/Server/abilities/bots/ironhide.py)
  - 运行时状态机：[skill_ironhide.c](file:///e:/Agent/TFTF/tools/nativehook/skills/bots/skill_ironhide.c)（与 G1 铁皮共用文件，已隔离 `is_movie_ironhide` / `is_g1_ironhide`）
- **靶场回归剧本（7 条）**：

| 序号 | 剧本文件 | 验证核心机制 | 关键验收标准 |
| :--- | :--- | :--- | :--- |
| #1 | [ironhide_cin_test_01_heavy_crit_burn.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/ironhide_cin_test_01_heavy_crit_burn.json) | 重击导弹 +100% 必暴、80% 初次燃烧与 30% 叠层燃烧 | 连发重击全暴、4 秒窗口内叠层燃烧并产生 DOT 跳伤，无 G1 Buff 泄露 |
| #2 | [ironhide_cin_test_02_basic_and_block_gate.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/ironhide_cin_test_02_basic_and_block_gate.json) | 前冲/轻中击无导弹必暴；格挡 SP1 无燃烧眩晕 | `al=1/2` 导弹暴击日志为 0；格挡 SP1 不施加任何燃烧/眩晕 |
| #3 | [ironhide_cin_test_03_sp1_last_hit_stun_burn.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/ironhide_cin_test_03_sp1_last_hit_stun_burn.json) | SP1 仅末击导弹必暴 + 80% 2.5s 眩晕 + 燃烧 | `al=16 last=0` 暴击加成严格为 0；`last=1` 全部暴击并触发 `ironhide_sp1_stun` 与燃烧 |
| #4 | [ironhide_cin_test_04_sp2_missiles_crit_dmg.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/ironhide_cin_test_04_sp2_missiles_crit_dmg.json) | SP2 全段导弹必暴叠层燃烧 + 76% +75% 黄色暴伤 | `al=32` 全段暴击、挂载 `ironhide_s2_crit_dmg` 与叠层燃烧 |
| #5 | [ironhide_cin_test_05_passive_struck_crit_dmg.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/ironhide_cin_test_05_passive_struck_crit_dmg.json) | 受击 12% 概率获得 8 秒 +140% 黄色暴击伤害 | P0 在无敌状态下仍正常触发 `on_hit_connected` 受击被动并挂载 `ironhide_struck_crit_dmg` |
| #6 | [ironhide_cin_test_06_sp3_last_hit_burn.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/ironhide_cin_test_06_sp3_last_hit_burn.json) | SP3 仅末击 30% 施加 8s 100% ATK 燃烧 | 前段无燃烧、`last=1` 触发 `ironhide_s3_burn` 并产生 DOT Tick |
| #7 | [ironhide_cin_test_07_sig_obliteration_once.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/ironhide_cin_test_07_sig_obliteration_once.json) | 觉醒技“抹杀”仅 SP 末击且暴击时 50% 触发 +600% 暴伤 | 在 `ROLL_CRIT` 当帧叠加 `CRIT_DMG_MULT=7.50x` 轰出 `9834.8` 单击，全场严格 1 次并在收招时立即消费 |

- **一键单独复测电影铁皮**：
  ```powershell
  python tools/check_accepted_lock.py --run-device --bot ironhide_cin_rotf --serial 127.0.0.1:7555
  ```

---

### 4. 闪电 (`blitzwing_gs`) —— *(未锁定，自动化通过，待人工验收)*

- **当前状态**：`🧪 自动化通过，待人工验收`（未加入 `accepted_bots_lock.json` 哈希锁）
- **自动化验证环境**：MuMu 15 (`127.0.0.1:7555`)，7/7 剧本全绿通过
- **关联源码**：
  - 技能定义：[blitzwing.py](file:///e:/Agent/TFTF/Server/abilities/bots/blitzwing.py)
  - 运行时状态机：[skill_blitzwing.c](file:///e:/Agent/TFTF/tools/nativehook/skills/bots/skill_blitzwing.c)
- **靶场验证剧本（7 条）**：
  - [blitzwing_test_01_transform_armor_crit.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/blitzwing_test_01_transform_armor_crit.json)（#1 开局坦克护甲 + 长按防御1秒切换战机/坦克形态与暴击增益）
  - [blitzwing_test_02_clamp_apply_l4_m2_heavy.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/blitzwing_test_02_clamp_apply_l4_m2_heavy.json)（#2 抑制夹钳命中门禁：格挡不施加 / L4-M2-重击施加）
  - [blitzwing_test_03_clamp_gate_and_batch.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/blitzwing_test_03_clamp_gate_and_batch.json)（#3 坦克阻断对手增益与“增益阻断”红字呼出 + 战机同击批量阻断减益与“减益阻断”红字呼出）
  - [blitzwing_test_04_sp3_universal_clamp_exempt.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/blitzwing_test_04_sp3_universal_clamp_exempt.json)（#4 SP3 五层通用永久夹钳双向阻断红字呼出 + 充能/遗迹豁免）
  - [blitzwing_test_05_sp1_sp2_modes.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/blitzwing_test_05_sp1_sp2_modes.json)（#5 双形态 SP1 攻击减益/红色破甲与 SP2 攻击增益/暴击几率）
  - [blitzwing_test_06_second_wind_tank_detonate.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/blitzwing_test_06_second_wind_tank_detonate.json)（#6 绝处逢生坦克形态 75% 护甲与引爆夹钳 2.5s 眩晕）
  - [blitzwing_test_07_second_wind_jet_special.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/blitzwing_test_07_second_wind_jet_special.json)（#7 绝处逢生战机形态 75% 特殊伤害增益）

---

### 5. 暗天陨 (`nemesisprime_gs_voyager2015`) —— *(未锁定，自动化通过，待人工验收)*

- **当前状态**：`🧪 自动化通过，待人工验收`（未加入 `accepted_bots_lock.json` 哈希锁）
- **自动化验证环境**：MuMu 15 (`127.0.0.1:7555`)，6/6 剧本全绿通过
- **关联源码**：
  - 技能定义：[nemesisprime.py](file:///e:/Agent/TFTF/Server/abilities/bots/nemesisprime.py)
  - 运行时状态机：[skill_nemesis.c](file:///e:/Agent/TFTF/tools/nativehook/skills/bots/skill_nemesis.c)
- **靶场验证剧本（6 条）**：
  - [nemesis_test_01_dark_energy_and_heavy.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/nemesis_test_01_dark_energy_and_heavy.json)（#1 黑暗能量 10s/7s/5s 周期充能与上限 10 层 + 重击驱散/增伤）
  - [nemesis_test_02_subspace_cloner.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/nemesis_test_02_subspace_cloner.json)（#2 亚空间脉冲克隆对手护甲与近战增益，且不与黑暗能量计数合并）
  - [nemesis_test_03_matrix_lifesteal.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/nemesis_test_03_matrix_lifesteal.json)（#3 觉醒赝品领导模块特技 25% 逐段吸血）
  - [nemesis_test_04_sp1_clone_debuffs.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/nemesis_test_04_sp1_clone_debuffs.json)（#4 SP1 复制自身减益至对手并正确在对手侧持续跳红字 DOT + 结束 +2 层充能）
  - [nemesis_test_05_sp2_axe_of_evil.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/nemesis_test_05_sp2_axe_of_evil.json)（#5 SP2 邪恶之斧双驱散施加近战减益/破甲与消耗黑暗能量）
  - [nemesis_test_06_sp3_unblockable.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/nemesis_test_06_sp3_unblockable.json)（#6 SP3 消耗全部黑暗能量与 7s+0.5s/层浅紫色不可防御）

---

### 6. 眩晕 (`blackout_cin_tf`) —— *(未锁定，自动化通过，待人工验收)*

- **当前状态**：`🧪 自动化通过，待人工验收`（未加入 `accepted_bots_lock.json` 哈希锁）
- **自动化验证环境**：MuMu 15 (`127.0.0.1:7555`)，核心连击/暴击燃烧/追猎落空回能/SP3末击+50%暴击率靶场验证通过
- **关联源码**：
  - 技能定义：[blackout.py](file:///e:/Agent/TFTF/Server/abilities/bots/blackout.py)
  - 运行时状态机：[skill_blackout.c](file:///e:/Agent/TFTF/tools/nativehook/skills/bots/skill_blackout.c)
- **靶场验证剧本（1 条）**：
  - [blackout_test_callouts.json](file:///e:/Agent/TFTF/tools/autotest_scenarios/blackout_test_callouts.json)（连击暴击与无尽怒火、重击暴击燃烧、追猎落空能量功率增益、SP3 末击+50%暴击率与燃烧）
