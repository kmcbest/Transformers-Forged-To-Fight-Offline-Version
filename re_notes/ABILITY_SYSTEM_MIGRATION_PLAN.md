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

## 二、 上游 PR #10 架构解析与优缺点评估

### 1. PR #10 的核心设计优点
1. **彻底打通了数据流四部曲**：
   - `build_buffs_set()`：配置全局 Buff 行为（`globalBuffs`，camelCase 字段，定义效果参数 `p`）。
   - `build_stat_modifiers()`：配置修饰器（`statMods`，缩写键，指定触发器 `tr`、几率 `c`、时长 `d`、数值 `m`、目标 `ta`、类型 `mt`）。
   - `build_stat_mod_appears()`：配置视觉表现（`statModAppears`，关联图标字形 `t`、标题 `a`、描述 `l` 等）。
   - **四位一体赋予**：在 `build_hero_base`、`build_hero_entry`、`build_base_hero_details` 和 **`quest_team`（关键战斗编队）** 中统一下发。
2. **踩通并沉淀了关键坑点（见下文铁律）**。

### 2. PR #10 的局限与不适配之处
1. **语言与构建栈不兼容**：
   - 上游使用的是其自研的 **Legible (`.lbl`)** 语言体系（`gamedata.lbl`），需要专有编译工具 `legible`。
   - 我们的 `redeco` 分支是**标准 Python 架构**（`Server/gamedata.py`），绝不能引入 `.lbl`。
2. **原创与数值随意（不合“官方还原”理念）**：
   - 上游作者基于规避版权考量，完全自己编排了所谓的 `kit_bleed`、`kit_shock`、`kit_burn`，且胡乱修改了角色的职业和能力分配，这与我们**“原汁原味还原官方体验、优先以官方数据服众”**的核心理念相背离。

---

## 三、 本地 Redeco 分支的迁移技术方案（Python 版）

我们将采用**“底层使用 PR #10 验证成功的原生通信协议，上层使用 `tftf_all_characters.json` 官方正统数据”**的设计方案。

### 1. 架构设计与单一真理源划分

```
[官方数据源: tftf_all_characters.json]
   │
   ├── 提取: 77+ 名官方角色的职业(Class)、基础能力(Abilities)、大招特效(Special Attacks)
   │
   ▼
[Server/abilities_db.py] (新增: 官方技能与效果库)
   │  ├── GLOBAL_BUFFS: 流血/灼烧/护甲/破甲/护盾等基础引擎行为定义
   │  ├── STAT_MOD_APPEARS: 官方图标字形(\uE4xx)与多语言文本映射
   │  └── BOT_OFFICIAL_ABILITIES: 角色ID -> 官方技能 ID 列表
   │
   ▼
[Server/gamedata.py] (全项目单一真理源)
   │  ├── build_buffs_set()        -> 注入 loginData / account_data
   │  ├── build_stat_modifiers()    -> 注入 loginData / account_data
   │  ├── build_stat_mod_appears()  -> 注入 loginData / account_data
   │  └── 统一分发至:
   │       ├── build_hero_base()
   │       ├── build_hero_entry()
   │       ├── build_base_hero_details()
   │       └── quest_team()   <-- 确保战斗副本 Squad 携带能力!
   │
   ▼
[export_payload.py -> tftf_offline_payload.bin]
   │
   ▼
[客户端原生执行: 伤害Tick + 跳字 + 血条下方倒计时圆环图标]
```

### 2. 核心数据结构字典定义规范 (Python 格式)

#### (1) `buffs_set`（全局行为定义）
```python
def build_buffs_set():
    return {
        "globalBuffs": {
            "dmg_bleed": {
                "buffType": "dmg_bleed",
                "valueType": "attack_percent",
                "value": 0.4,
                "displayValue": 40,
                "hasDuration": True,
                "time": {"amount": 6.0},
                "group": "bleed",
                "scope": "fight",
                "modeAvail": "all",
                "p": {"damage_type": "bleed"}
            },
            # 依此类推：dmg_shock, dmg_burn, armor_up, armor_break, evade...
        },
        "userBuffs": {}
    }
```

#### (2) `stat_modifiers`（触发条件与修饰器）
```python
def build_stat_modifiers():
    return {
        "arcee_crit_bleed": {
            "t": "dmg_bleed",             # 必须严格与 globalBuffs 的 ID 保持一致 (且伤害类以 dmg_ 开头)
            "tr": ["onCrit"],             # 触发事件 (列表类型! 官方阿尔茜: 暴击触发流血)
            "uit": ["onCrit"],            # UI触发 (列表类型!)
            "a": ["appr_bleed"],          # 关联外观 (列表类型!)
            "trr": "repeat",              # 触发模式
            "c": 1.0,                     # 几率 (1.0 = 100%)
            "m": 0.6,                     # 幅度 (60% 攻击力)
            "d": 4.0,                     # 持续时间 (4秒)
            "ta": "opponent",             # 施加目标: opponent / self
            "mt": "debuff",               # 视觉分类: debuff / buff / passive
            "st": 1                       # 堆叠层数
        },
        # 其他官方技能修饰器...
    }
```

#### (3) `stat_mod_appears`（外观与 Unicode 字体图标映射）
```python
def build_stat_mod_appears():
    return {
        "appr_bleed": {
            "t": "\uE402",                # Tecnica_Bold_116 中的真实流血字形
            "f": "",                      # 特效预设 (可选)
            "a": "ABILITY_BLEED_TITLE",   # 技能标题多语言键
            "l": "ABILITY_BLEED_DESC",    # 详细说明
            "s": "Bleed",                 # 短文本
            "st": "Bleed"                 # 跳字/呼出文本
        },
        "appr_shock": {
            "t": "\uE412",                # 感电字形
            # ...
        },
        "appr_burn": {
            "t": "\uE41D",                # 灼烧字形
            # ...
        }
    }
```

---

## 四、 关键陷阱与防御守则（从上游吸收的经验）

| 序号 | 陷阱 / Bug 现象 | 根本原因 | 防护铁律 |
| :---: | :--- | :--- | :--- |
| **1** | 进副本战斗后技能完全不生效 | `quest_team`（副本队伍）硬编码了 `stat_mods: []`，导致即使图鉴和背包里有技能，战斗小队也未携带。 | **铁律**：角色的 abilities 列表必须通过统一函数获取，并在 `quest_team()` 中同步注入。 |
| **2** | 技能不生效且没有任何报错 | `tr`（触发器）、`uit`（UI触发器）、`a`（外观）在客户端代码中是 `List` 访问器，若传入单字符串，客户端反序列化会静默变为空。 | **铁律**：`tr`、`uit`、`a` 字段的值必须使用 Python 数组（如 `["onHit"]`）。 |
| **3** | 图标显示为 `@@@@` 乱码 | 客户端没有占位符替换机制，传 ASCII 标记会被字体渲染为字面字符。 | **铁律**：图标字段 `t` 必须是真实的 Unicode PUA 字符（如 `\uE402`）。Python 的 `json.dumps(..., ensure_ascii=True)` 会自动输出合法的 `\uE402`。 |
| **4** | 伤害型技能不结算伤害 | 客户端的 `Damage_BuffEffect` 工厂类是通过类名 `dmg_` 前缀进行匹配实例化的。 | **铁律**：所有伤害结算类 Buff 的 `t` 必须以 `dmg_` 作为前缀。 |
| **5** | 打开角色详情面板闪退 (SIGSEGV) | 觉醒等级 `sig_lvl > 0` 会强制加载客户端缺失的觉醒相关资产，导致崩溃。 | **铁律**：第一阶段暂不开启 `sig_lvl`（保持为 0），所有能力作为基础特长（Base Abilities）注入。 |

---

## 五、 后续实施路线图（分阶段推进）

- [ ] **阶段 1：观察与吸收（当前阶段）**
  - 暂不急于修改核心业务代码，等待上游 PR #10 及其后续 PR 将更多 `*_BuffEffect`（如护盾、格挡、破甲）和触发器的实测数据稳定下来。
  - 维护并细化 `re_notes/` 这里的技术方案。
- [ ] **阶段 2：解析官方数据并生成技能库**
  - 编写脚本从 `d:\Agent\personal\TFTF\tftf_all_characters.json` 中结构化提取官方金刚的基础能力（如阿尔茜的暴击流血、擎天柱的近战增伤/破甲、威震天的重击灼烧等）。
  - 构建角色 ID -> 官方技能 ID 字典。
- [ ] **阶段 3：Python 服务端载荷注入与验证**
  - 在 `Server/gamedata.py` 中接入上述字典，生成包含 `buffs_set` 与 `statMods` 的离线 payload。
  - 在真机（ADB 设备 `360943c1`）上通过常规副本战斗验证：
    1. 角色血条下方正常弹出 `\uE402` 红色流血图标；
    2. 图标外圈倒计时正常转动；
    3. 敌人头顶跳出伤害数字并持续掉血。
- [ ] **阶段 4：原创与魔改角色技能赋予**
  - 基于官方已经跑通的技能模板，为回春手（Lifeline）、重涂角色等自制人物配置符合其人设的技能组合。
