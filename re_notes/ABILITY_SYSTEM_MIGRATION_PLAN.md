# TFTF 战斗能力（Ability / Buff）系统技术架构与官方还原迁移方案

> **文档定位**：记录 TFTF 离线版战斗能力系统的底层技术机制、上游 PR #10（dedguy21）的逆向成果与设计模式，并制定契合我们 `redeco` 分支（Python + 原生官方还原理念）的完整落地与迁移方案。
> **参考输入**：
> - 上游 Pull Request: [#10 `feat(abilities): server-authored ability kits that execute real damage in combat`](https://github.com/Gummygamer/Transformers-Forged-To-Fight-Offline-Version/pull/10)
> - 上游设计规范：`ABILITY_AUTHORING.md`
> - 官方技能百科全书：`d:\Agent\personal\TFTF\tftf_all_characters.json`（全角色官方技能、数值曲线、阶级表与触发机制）

---

## 一、 技术底座认知与突破（Client IL2CPP 底层真相）

经过对客户端 `libil2cpp.so`、`global-metadata.dat` 以及 PR #10 的系统性审查，确认了以下关于战斗能力系统的关键技术事实：

### 1. 客户端具备完备的原生 Ability 执行引擎
- **无需在底层逆向编写战斗 Buff 轮询状态机**：游戏客户端本身就拥有完整的 `BuffsController`、`Damage_BuffEffect`、`HudBuffWidget` 等 C# 原生实现。
- 只要服务端下发的数据结构遵循客户端的序列化协议，客户端底层就会自动：
  1. 在战斗初始化（`BattleArbiter.OnFightStart`）时解析并注册 `statMods`；
  2. 监听普攻、暴击、挨打等事件（`tr: ["onHit", "onCrit", ...]`）；
  3. 触发后实例化对应的 `*_BuffEffect`（如 `Damage_BuffEffect`）；
  4. 按照设定时间间隔（如 `0.5s`）进行 Tick 伤害结算；
  5. 驱动 UI 层在双方血条下方创建 `HudBuffWidget` 图标，并在图标外圈渲染倒计时圆弧进度条；
  6. 触发战斗跳字系统（`HudFloatingText`）弹出伤害或特效跳字。

### 2. Buff 图标的本质：Tecnica 字体中的 Unicode PUA 字形
- **不是散装 PNG/Texture 贴图**：能力图标实际上存放在 `assets/bin/Data/811e9b20e41fd447796b1e264201af71`（即 `Tecnica_Bold_116.ttf` 矢量字体）中。
- **编码范围**：属于私有使用区（PUA），主要集中在 `U+E401` ~ `U+E60C`：
  - `\uE402`：流血（Bleed，利刃与血滴）
  - `\uE412`：感电 / 超载（Shock / Overcharge，带电拳头）
  - `\uE41D`：灼烧 / 热能脉冲（Burn / Thermal Pulse，火焰）
  - `\uE501`：护甲提升（Armor Up，盾牌向上）
  - `\uE502` / `\uE515`：格挡 / 防御（Block / Shield）
  - `\uE604`：眩晕（Stun）
- **通信契约**：客户端没有类似于 `@@E402@@` 的占位符解析器。服务端的 `statModAppears` 的 `t` 字段必须真实下发 Unicode PUA 字符（即 JSON 中的 `\uE402`）。

---

### 二、 上游 PR #10 / PR #16 架构解析与关键逆向成果

### 1. PR #10 的核心设计与基础打通
1. **彻底打通了数据流四部曲**：
   - `build_buffs_set()`：配置全局 Buff 行为（`globalBuffs`，camelCase 字段，定义效果参数 `p`）。
   - `build_stat_modifiers()`：配置修饰器（`statMods`，缩写键，指定触发器 `tr`、几率 `c`、时长 `d`、数值 `m`、目标 `ta`、类型 `mt`）。
   - `build_stat_mod_appears()`：配置视觉表现（`statModAppears`，关联图标字形 `t`、标题 `a`、描述 `l`、颜色 `tc`/`gt`/`gb` 等）。
   - **四位一体赋予**：在 `build_hero_base`、`build_hero_entry`、`build_base_hero_details` 和 **`quest_team`（关键战斗编队）** 中统一下发。

### 2. PR #16 的关键突破与纠偏（dedguy21）
上游 PR #16（`docs(abilities): correct the conditions and magnitude sections, add the instrumentation behind them`）与本地逆向实测彻底澄清了以下致命认知偏差：

1. **数值 `m`（Magnitude）是绝对固定伤害总值，绝非攻击力百分比！**
   - `Damage_BuffEffect.OnTick` 底层源码计算公式为：
     $$\text{per\_tick} = \frac{m}{d \times 2}$$
     （客户端默认伤害结算周期为 0.5s，即每秒 2 次 Tick，总计 $2d$ 次 Tick）。
   - 该公式**完全不乘以角色的攻击力**！
   - 战斗跳字系统 `HudFloatingTextController.Play` 要求传入 `int` 整型。如果服务端按照百分比下发 `m = 0.6`（持续 3 秒），每跳伤害为 $0.6 / (3 \times 2) = 0.1$，强转整型后直接截断为 `0`！这导致不仅敌人血条不扣血，跳字系统也会被完全静默，造成“Buff 生效了但毫无效果”的假象。
   - **正确做法**：`m` 必须下发总伤害绝对数值（如 $600.0$，在 3 秒内每次跳 $100$ 伤害）。
2. **条件表达式 `trs`（Trigger String）的底层语法完全可解析！**
   - 客户端在 `BuffTriggerFactory.ParseConditions` 中通过正则提取条件：
     ```regex
     ([\w\.]+)(=|<=|>=|!=|>|<)(.+)
     ```
   - **关键语法契约**：
     - 等于号为**单等号** `=`，绝不可写成 `==`！
     - 目标前缀：支持 `self:` 或 `opponent:`，若省略则默认指向 `self:`。
     - **支持的 12 个键名**：
       - `arena`（当前竞技场地名称，字符串）
       - `canAttack`（是否可攻击，布尔值）
       - `class`（职业枚举，整数）
       - `currAnim`（当前动画 Hash，整数）
       - `fightType`（战斗类型枚举）
       - `heavyType`（重击类型）
       - `isAi`（是否为 AI 电脑，布尔值）
       - `isFinalBoss`（是否为关卡 Boss，布尔值）
       - `playerID`（玩家 ID）
       - `prevAnim`（上一动作动画 Hash）
       - `state`（玩家战斗状态机状态）
       - `tags`（英雄标签 Tag）
   - **局限性**：不支持内联的 `AND`/`OR` 复合布尔逻辑；条件中不能有多余空格；复杂组合需通过拆分为多个 `statMods` 叠加实现。
3. **跳字累加器（`floating_text`）必须作为常驻被动注入**：
   - `Damage_BuffEffect` 计算出伤害后，本身并不直接弹跳字，而是把伤害累加到 `_ftd` 变量中，由 `floating_text` 类型的被动修饰器在 `onIntroStart` 时挂载（持续时间 `d = -1.0`，`tm = "v=_ftd;s=7"`）并轮询渲染红字跳字。
   - 缺失 `gp_dmg_ft` 时，伤害能正常扣血，但头顶不会跳出伤害数字。

---

## 三、 本地 Redeco 分支的落地技术规范 (Python 版)

我们将采用**“底层使用已验证的原生通信协议，上层使用 `tftf_all_characters.json` 官方正统数据”**的设计方案。

### 1. 核心数据结构字典定义规范 (Python 格式)

#### (1) `buffs_set` 与 `buffs_config`
```python
def build_buffs_config():
    return {
        "groupings": {
            "floating_text": {"stackable": True, "active_display": False},
            "floating_text_dmg": {"stackable": True, "active_display": False},
            "floating_text_heal": {"stackable": True, "active_display": False},
            "dmg_bleed": {"stackable": True, "active_display": True},
        }
    }

def build_buffs_set():
    return {
        "globalBuffs": {
            "floating_text": {
                "id": "floating_text",
                "buffType": "floating_text",
                "group": "floating_text",
                "p": {"key": "_ftd", "style": 0},
                "hasDuration": False,
            },
            "dmg_bleed": {
                "id": "dmg_bleed",
                "buffType": "damage",
                "group": "dmg_bleed",
                "p": {"damage_type": "bleed"},
                "hasDuration": True,
                "time": {"amount": 3.0},
            },
        }
    }
```

#### (2) `stat_modifiers`（触发条件与修饰器）
```python
def build_stat_modifiers():
    return {
        "gp_dmg_ft": {
            "id": "gp_dmg_ft",
            "t": "floating_text",
            "tm": "v=_ftd;s=7",
            "tr": ["onIntroStart"],
            "trr": "update",
            "d": -1.0,
            "ta": "self",
            "mt": "passive",
        },
        "arcee_headshot_bleed": {
            "t": "dmg_bleed",             # 必须严格与 globalBuffs 的 ID 保持一致 (且伤害类以 dmg_ 开头)
            "tr": ["onHit"],              # 触发事件 (列表类型!)
            "uit": ["onHit"],             # UI触发 (列表类型!)
            "a": ["arcee_headshot_bleed"],# 关联外观 (列表类型!)
            "trr": "repeat",              # 触发模式
            "c": 1.0,                     # 几率 (1.0 = 100%)
            "m": 600.0,                   # 绝对伤害总值 (600 / (3 * 2) = 每跳 100 点伤害)
            "d": 3.0,                     # 持续时间 (3 秒)
            "ta": "opponent",             # 施加目标: opponent / self
            "mt": "debuff",               # 视觉分类: debuff / buff / passive
            "st": 1                       # 堆叠层数
        },
    }
```

#### (3) `stat_mod_appears`（外观与 Unicode 字体图标映射）
```python
def build_stat_mod_appears():
    return {
        "arcee_headshot_bleed": {
            "id": "arcee_headshot_bleed",
            "a": "Headshot Bleed",
            "s": "Bleed",
            "l": "Direct bleed damage over 3 seconds.",
            "t": "\uE401",                # Tecnica_Bold_116 真实字形: \uE401 (能量块滴液流血)
            "st": "BLEED",                # 触发呼出横幅文字
            "tc": "FF0000",               # 必须为纯 6 位 Hex! 严禁写 "#FF0000"!
            "gt": "FF0000",
            "gb": "FF0000",
        },
    }
```

---

## 四、 关键陷阱与防御守则（逆向实测沉淀）

| 序号 | 陷阱 / Bug 现象 | 根本原因 | 防护铁律 |
| :---: | :--- | :--- | :--- |
| **1** | 进副本战斗后技能完全不生效 | `quest_team`（副本队伍）硬编码了 `stat_mods: []`，导致战斗小队未携带。 | **铁律**：角色的 abilities 列表必须通过统一函数获取，并在 `quest_team()` 中同步注入。 |
| **2** | 技能不生效且没有任何报错 | `tr`、`uit`、`a` 在底层是 `List` 访问器，若传入单字符串，反序列化后会静默为空。 | **铁律**：`tr`、`uit`、`a` 字段的值必须使用 Python 数组（如 `["onHit"]`）。 |
| **3** | 图标显示为乱码或空白 | 图标未真实指向 Tecnica 矢量字体的 PUA 码点。 | **铁律**：图标字段 `t` 必须是真实的 Unicode PUA 字符（如 `\uE401`）。Python 输出 JSON 时自动转义为 `\uE401`。 |
| **4** | 伤害型技能不结算伤害 | 客户端的 `Damage_BuffEffect` 工厂类是通过类名 `dmg_` 前缀进行匹配实例化的。 | **铁律**：所有伤害结算类 Buff 的 `t` 必须以 `dmg_` 作为前缀。 |
| **5** | 技能触发但敌人不扣血、不跳字 | `m` 是绝对伤害而非百分比！若写 `0.6`，每跳伤害 $0.1$ 被强转为整型 `0`，伤害与跳字均被静默吞掉。 | **铁律**：`m` 必须配置绝对总伤害数值（例如 $600.0$）。同时必须在 `globalBuffs` 和 `statMods` 中注册被动跳字累加器 `gp_dmg_ft`。 |
| **6** | 图标和呼出字原本设为红色却显示为**黄色** | 底层 `NGUIMath.HexToColor`（RVA `0x18AF58C`）**不会剔除开头的 `#`**，直接从 index 0 按两两字符读取。由于非 Hex 字符在 `0x18AB274` 中返回 `0xF`，输入 `"#FF0000"` 时错位解析为：`(#F)(F0)(00)` $\rightarrow$ `(0xFF, 0xF0, 0x00)` 即 $\text{RGB}(255, 240, 0)$ **纯亮黄色**！血条下的倒计时圆环与图标（`HudBuffWidget` RVA `0xC64264`）以及呼出字均取自 `tc`，故全部变黄。 | **铁律**：`statModAppears` 中的所有颜色字段（`tc`、`gt`、`gb`）**必须严格使用不带 `#` 的 6 位 Hex 字符串**（如 `"FF0000"`），绝不能带前缀 `#`！ |
| **7** | 条件表达式 `trs` 解析失败 | 写成了双等号 `==` 或含有空格，或者使用了不受支持的键。 | **铁律**：条件表达式必须使用单等号（如 `isAi=true`），严格限制在 12 个原生支持的键名之内。 |
| **8** | 打开角色详情面板闪退 (SIGSEGV) | 觉醒等级 `sig_lvl > 0` 会强制加载客户端缺失的觉醒相关资产，导致崩溃。 | **铁律**：第一阶段保持 `sig_lvl = 0`，所有能力作为基础特长（Base Abilities）注入。 |
| **9** | 多层流血无法堆叠，未出现数字角标且生成多个重复图标 | 客户端 `BuffsConfig` 的 C# 自动属性字段为 `<groups>k__BackingField`，反序列化**仅认 `"groups"` 键名**。若下发 `"groupings"` 会导致 `groups` 为空，底层 `HudBuffsGrid` 找不到策略默认回退为 `stackable = false`。 | **铁律**：`buffs_config` 必须提供 `"groups"` 字典（同时保留 `"groupings"` 兼容）。需堆叠的 Buff 配置 `stackable: true, active_display: true`；即时直接伤害配置 `active_display: false` 避免冗余图标。 |
| **10** | 暴击触发技能在未暴击时依然触发（如不暴击也出流血） | 客户端 `statMods` 的触发器 `onRangedHit`/`onSpecial1Hit` 为基础受击事件，每次命中无条件广播，且 `trs` 原生支持的 12 个键中**不存在 `isCrit` 键**。 | **铁律**：暴击依赖型能力必须通过 Native Hook 门禁进行拦截。在 `hook_156`（`PlayerAttributes.RollForCriticalHit`，真实 RVA `0x0DADCA8`）拦截并捕获 `g_p0_last_hit_is_crit`；在 `hook_157`（`StatModifierController.GetStatModifier`，真实 RVA `0x0CCF35C`）中拦截对应技能 ID，未暴击直接返回 `0`。底层调用者 `0xCC2E58: tbz w0, #0` 即刻分支跳过施加逻辑，彻底终止未暴击流血！ |

---

## 五、 后续实施路线图

- [x] **阶段 1：底层通信协议打通与实机验证（已完成）**
  - 在 `Server/gamedata.py` 中完整实现了 `buffs_config`、`buffs_set`、`statMods`、`statModAppears` 的协同工作链路。
  - 在实体测试机（Xiaomi MI 8）上完成验证：
    1. 阿尔茜普通命中 100% 触发流血效果；
    2. 敌人头顶跳出红色 `"100"` 伤害跳字并实时扣减生命值；
    3. 敌人血条下方正常弹出倒计时圆环与 `\uE401` 图标；
    4. 彻底逆向搞清并修复了数值截断机制（绝对伤害 `m`）与颜色错位问题（剔除 `#`）。
- [ ] **阶段 2：解析官方数据并生成全量技能库**
  - 编写脚本从 `d:\Agent\personal\TFTF\tftf_all_characters.json` 中结构化提取官方金刚的基础能力（如阿尔茜的暴击流血、擎天柱的近战增伤/破甲、威震天的重击灼烧等）。
  - 根据官方数值公式，结合角色成长曲线，将技能伤害数值映射为符合战斗强度的绝对伤害数值 `m`。
  - 构建全角色 ID $\rightarrow$ 官方技能 ID 字典。
- [ ] **阶段 3：全角色能力在离线服务端的全量激活**
  - 在 `Server/gamedata.py` 中接入官方技能字典，批量生成完整的离线 payload。
  - 覆盖副本战、竞技场以及突袭战。
- [ ] **阶段 4：原创与魔改角色技能赋予**
  - 基于官方已经跑通的技能模板，为回春手（Lifeline）、重涂角色等自制人物配置符合其人设的技能组合。

