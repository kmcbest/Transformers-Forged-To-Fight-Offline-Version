---
name: tftf_ability_authoring
description: Standard authoring pipeline and quality gate guide for implementing character abilities in Transformers: Forged to Fight (TFTF). Use when creating or updating bot-specific abilities under Server/abilities/bots/, querying official Chinese skill descriptions from the database, adhering to IL2CPP combat contracts, and validating via tools/validate_bot_ability.py.
---

# TFTF Character Ability Authoring Guide & Standard Protocol
# (变形金刚：百炼为战 角色技能工业化流水线编写指南)

本指南为所有参与 TFTF 离线版角色专属战斗能力（Passive / Buff / Debuff / Special Effects）制作的 Agent 与开发者提供统一规范、代码模板、底层契约与自动化验收门禁。

---

## 1. 架构与目录权责分工 (Architecture & Directory Layout)

技能系统采用三层解耦架构，严禁将所有英雄逻辑堆砌在单个单体文件中：

```
Server/
  ├── gamedata.py                     # [顶层总装配] 全局单一真理源，组装所有角色 stat_mods 与 buffs
  └── abilities/                      # [中层核心库与中枢包]
        ├── __init__.py               # 对外统一 Facade 接口 (bot_abilities, build_stat_modifiers, build_buffs_*)
        ├── core.py                   # 通用机制模板工厂 (make_bleed_statmod, etc.) 与 IL2CPP 契约校验器
        ├── registry.py               # 机器人能力动态自动扫描与注册引擎 (@register_bot)
        ├── sp_callouts.py            # 全员 78 位英雄 SP1/SP2/SP3 呼出大字与外观映射
        └── bots/                     # [底层角色能力库] 每个英雄独立一个 .py 文件
              ├── __init__.py
              ├── arcee.py            # 官方标杆范例 (侦察兵阿尔茜：爆头直伤、流血、冲锋反制)
              ├── windblade.py        # 风刃 (待编写)
              ├── drift.py            # 漂移 (待编写)
              └── <bot_id>.py         # 其他任意英雄独立模块
```

---

## 2. 编写步骤与流程规范 (Step-by-Step Workflow)

制作任何新英雄能力时，严格遵循以下 4 步工业化流程：

### 步骤 1：查询官方技能真理源 (Ground Truth)

严禁凭空编造技能参数与触发条件。必须从官方技能真理源获取角色的官方中英文描述、机制说明与 6/60 基准数值。

> [!IMPORTANT]
> **真理源查询优先级规范（Priority Order）**：
> 1. **【最优先·首选】在线静态真理源 CDN API**：免鉴权、零延迟、全球 CDN 缓存，任何环境下的 Agent 均可直接 HTTP 请求，无需依赖本地环境与数据库同步。
> 2. **【次选】在线网页端交互与 Prompt 生成器 (`https://kmcbest.github.io/tftfr/api.html`)**：支持可视化浏览与一键生成 LLM 专用的 Markdown / Hook Prompt。
> 3. **【实时在线】动态云数据库 (Upstash KV REST)**：支持实时动态修改的云端 KV 数据库。
> 4. **【本地离线】本地校验门禁与 SQLite 数据库**：当无网络连接或离线开发时，使用本地 `Server/tftf_database.db` 或校验脚本。

#### 1.1 【最优先】在线静态真理源 CDN API (Online Endpoints)
| 资源 | URL 端点 | 说明 |
| :--- | :--- | :--- |
| **单机体详细档案【核心】** | `https://kmcbest.github.io/tftfr/data/characters/{bot_id}.json` | **最常用**：指定机体的所有基础能力、被动、特殊技 (SP1/SP2/SP3)、觉醒技 (Signature) 与协同羁绊及 6/60 基准属性 |
| **全角色技能总库** | `https://kmcbest.github.io/tftfr/data/all_abilities.json` | 包含全部 78 位角色、1324 项技能及机制描述的完整字典 |
| **全角色概览与 6/60 属性** | `https://kmcbest.github.io/tftfr/data/overview.json` | 阵营、职业默认倍率、生命值 (HP)、攻击力 (ATK)、评分 (Rating) |
| **PUA 专用字体码表** | `https://kmcbest.github.io/tftfr/data/pua_icons.json` | 游戏中所有派系、职业与战技图标的 Unicode 十六进制码 |

**智能体 2 行代码直接获取技能真理源 (Python 接入范例)**：
```python
import json, urllib.request

url = f"https://kmcbest.github.io/tftfr/data/characters/{bot_id}.json"
bot = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers={"User-Agent": "TFTF-Agent/1.0"})).read().decode("utf-8"))

print(f"角色: {bot['name_zh']} ({bot['name_en']}), 6/60 HP: {bot['hp']}, ATK: {bot['attack']}")
for ab in bot.get("abilities", []):
    print(f"[{ab['category'].upper()}] {ab['title_zh']} ({ab.get('title_en', '')}): {ab['desc_zh']}")
```

#### 1.2 在线网页端交互与 Prompt 生成器
- **在线网址**: `https://kmcbest.github.io/tftfr/api.html`
- **Agent 便捷参数**:
  - `?bot=grimlock` 或 `?bid=grimlock_gs_mp08`：指定角色名或 ID（亦支持中文如 `?bot=钢锁`）。
  - `?format=markdown`：生成可直接喂给大模型 (LLM) 进行代码编写的标准 Prompt。
  - `?format=json`：输出标准结构化 JSON。
  - `?format=hooks`：输出 C / Python Hook 代码脚手架。

#### 1.3 动态云数据库 (Upstash KV REST)
- **REST URL**: `https://deciding-bulldog-136761.upstash.io`
- **只读 Token**: `ggAAAAAAAhY5AAIgcDG7a511dMnvUap5JjML7kdCMH0hQAG95-3BtwD6YEaFeQ`
- **查询方式**:
  ```bash
  curl -H "Authorization: Bearer ggAAAAAAAhY5AAIgcDG7a511dMnvUap5JjML7kdCMH0hQAG95-3BtwD6YEaFeQ" \
       https://deciding-bulldog-136761.upstash.io/get/tftf:char:{bot_id}
  ```

#### 1.4 【本地备选】本地工具与 SQLite 检索
当离线运行或需要快速本地排查时使用：
- **方式 A（本地校验器）**：
  ```bash
  python tools/validate_bot_ability.py <bot_id>
  ```
  校验器会在开头直接打印收录的所有被动、必杀加成、协同加成及其中英文描述（本地无 DB 时会自动 fallback 在线 API）。
- **方式 B（本地 SQL 检索）**：
  ```sql
  SELECT category, title_zh, title_en, desc_zh, desc_en, pua_icon, sort_order
  FROM character_abilities
  WHERE bot_id = '<bot_id>'
  ORDER BY sort_order;
  ```
- **方式 C（本地 Web API）**：
  - 请求 `http://127.0.0.1:8888/api/character/<bot_id>`（本地 `tools/db_server.py` 服务运行中）。

---

### 步骤 2：在 `Server/abilities/bots/` 创建独立 py 文件

以 `arcee.py` 为标准模板，创建 `Server/abilities/bots/<hero_alias>.py`。

#### 核心代码规范要求：
1. **模块文档字符串 (Docstring)**：必须逐字列出真理源的官方中文描述，并清晰注明对应的代码实现方案。
2. **注册装饰器**：使用 `@register_bot(BOT_ID, name_zh="...", desc="...")`。
3. **函数签名**：`def build_<hero>_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):`
   - 基准属性默认传入 5星50级 数值，所有伤害、护盾与回复均基于 `base_atk` 或 `base_hp` 动态计算百分比。
4. **返回值**：统一返回 `(mods, appears, buffs)` 三元组：
   - `mods`: `{ mod_id: stat_mod_dict }`
   - `appears`: `{ appr_id: appear_dict }`
   - `buffs`: `{ buff_id: buff_dict }`（可为空字典 `{}`）

---

### 步骤 3：底层 IL2CPP 契约四大铁律 (Critical Contract Rules)

> [!CAUTION]
> 客户端 IL2CPP 反编译 C# 代码对数据结构有强类型要求，违反以下铁律会导致游戏黑屏、数值为 0 或跳字错位！

1. **颜色代码纯 6 位 Hex 铁律**：
   - `tc`, `gt`, `gb`, `bc` 必须为纯 6 位十六进制字符串（如 `"FF0000"` 表示纯红，`"FFE066"` 表示金黄）。
   - **严禁带 `#` 前缀！** 客户端解析器如果遇到 `#`，会将字符按每位解析，导致纯红 `#FF0000` 被错位解析成黄色！
2. **单次 Tick 伤害截断铁律**：
   - TFTF 持续伤害机制在客户端每 0.5 秒结算一次（即持续 $d$ 秒总共有 $d \times 2.0$ 次 Tick）。
   - 修饰器的 `m` 字段是持续时间内的**总伤害绝对值**，单跳伤害公式为：
     $$\text{dmg\_per\_tick} = \frac{m}{d \times 2.0}$$
   - **如果 $\text{dmg\_per\_tick} < 1.0$，IL2CPP 客户端在强制转为整型时会截断为 0，导致完全静默无伤害！**
3. **List 包装铁律**：
   - `tr`（触发器列表）、`uit`（UI 触发器列表）、`a`（外观 ID 列表）、`au`（更新外观 ID 列表）必须是 Python `list`（如 `["onCrit"]`），绝不能传单个 `str`。
4. **目标与演员 (Target Actor)**：
   - 负面效果 / 流血 / 扣血：`ta: "opponent"`，`mt: "debuff"`，`s: "none"`。
   - 自身增益 / 护盾 / 呼出：`ta: "self"`，`mt: "buff"` 或 `"passive"`。

---

## 3. 标准代码范例 (Canonical Reference: `arcee.py`)

```python
#!/usr/bin/env python3
"""
Bot Ability Implementation: 阿尔茜 (Arcee)
=========================================
Bot ID: arcee_gs_deluxe2014
阵营: 汽车人 (Autobot) | 职业: 侦察兵 (Scout)

【官方技能真理源对照 (来自 character_abilities 数据库)】：
-----------------------------------------------------------------------------
1. [被动 - 爆头 / Head Shot]
   - 官方描述: "远距离攻击有 50% 几率造成爆头，立刻造成 60% 攻击力，并在 3 秒内造成相当于 60% 攻击力的流血伤害。"
   - 实现方案:
     a) arcee_headshot_direct: 触发 onCrit，限制 level=Ranged,Special1，造成 60% ATK 额外直伤。
     b) arcee_headshot_dot: 触发 onCrit，限制 level=Ranged,Special1 且目标非冲刺 (opponent:state!=Dash,Run)，
        造成 60% ATK 流血伤害持续 3.0 秒。呼出文字: "BLEED"。

2. [被动 - 冲锋反制 / Headshot Rush]
   - 官方描述: "对处于前冲或奔跑状态的敌人造成爆头时，100% 造成极速流血。"
   - 实现方案:
     c) arcee_headshot_rush: 触发 onCrit，限制 level=Ranged,Special1 且目标正在冲刺 (opponent:state=Dash,Run)，
        100% 概率施加 3 秒流血。呼出文字: "HEADSHOT"。

3. [特殊技 2 - 致命核心 / Special Attack 2 Bleed]
   - 官方描述: "提高远程伤害与射速，并造成持续 4 秒相当于 108% 攻击力的流血伤害。"
   - 实现方案:
     d) arcee_s2_bleed: 触发 onCrit，限制 level=Special2，造成 108% ATK 流血伤害持续 4.0 秒。呼出文字: "BLEED"。
-----------------------------------------------------------------------------
"""

from ..core import make_bleed_statmod, make_direct_dmg_statmod
from ..registry import register_bot

BOT_ID = "arcee_gs_deluxe2014"


@register_bot(BOT_ID, name_zh="阿尔茜", desc="侦察兵，爆头直伤与流血、冲锋反制")
def build_arcee_abilities(base_hp: float = 34850.0, base_atk: float = 3485.0):
    mods = {}
    appears = {}
    buffs = {}

    # 1. 爆头直接扣血 (60% ATK: 3485 * 0.6 = 2091)
    m1, a1 = make_direct_dmg_statmod(
        mod_id="arcee_headshot_direct",
        dmg=base_atk * 0.60,
        chance=0.5,
        trigger="onCrit",
        trigger_scope="level=Ranged,Special1",
        buff_id="dmg_direct",
    )
    mods.update(m1)
    appears.update(a1)

    # 2. 爆头流血 3 秒 DOT (60% ATK: 3485 * 0.6 = 2091, 50% 几率, 敌非前冲状态)
    m2, a2 = make_bleed_statmod(
        mod_id="arcee_headshot_dot",
        duration=3.0,
        total_dmg=base_atk * 0.60,
        chance=0.5,
        trigger="onCrit",
        trigger_scope="level=Ranged,Special1;opponent:state!=Dash,Run",
        appr_id="appr_arcee_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed",
    )
    mods.update(m2)
    appears.update(a2)

    # 3. 爆头冲锋反制 3 秒流血 (60% ATK, 100% 必发, 敌处于 Dash/Run 状态)
    m3, a3 = make_bleed_statmod(
        mod_id="arcee_headshot_rush",
        duration=3.0,
        total_dmg=base_atk * 0.60,
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Ranged,Special1;opponent:state=Dash,Run",
        appr_id="appr_arcee_headshot",
        callout_text="HEADSHOT",
        buff_id="dmg_bleed",
    )
    mods.update(m3)
    appears.update(a3)

    # 4. S2 暴击流血 4 秒 DOT (108% ATK: 3485 * 1.08 = 3764, 100% 几率)
    m4, a4 = make_bleed_statmod(
        mod_id="arcee_s2_bleed",
        duration=4.0,
        total_dmg=float(round(base_atk * 1.08)),
        chance=1.0,
        trigger="onCrit",
        trigger_scope="level=Special2",
        appr_id="appr_arcee_bleed",
        callout_text="BLEED",
        buff_id="dmg_bleed",
    )
    mods.update(m4)
    appears.update(a4)

    return mods, appears, buffs
```

---

## 4. 自动化质量门禁与验收 (Quality Gate & Validation)

完成代码编写后，必须在终端执行以下门禁检验。**有任何错误（Error）均不得合并！**

```bash
# 1. 验证目标角色的契约与数据完整性
python tools/validate_bot_ability.py <bot_id>

# 2. 运行单测回归套件
python Server/test_arcee_ability.py
python Server/test_sp_callout.py

# 3. 全量校验所有已注册角色
python tools/validate_bot_ability.py --all
```

通过上述校验后，新角色技能将自动被 `Server/gamedata.py` 动态加载并烘焙至离线数据包中，无需手动修改任何其他配置文件。
