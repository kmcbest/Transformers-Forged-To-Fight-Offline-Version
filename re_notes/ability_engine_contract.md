# TFTF 战斗能力引擎底层契约与二层收口权威规范

> **权威依据**：直接提取自仓库内 `decomp_310_source/`（`BuffTriggerFactory.cs`、`TFormBuffTriggerConstants.cs`、`TFormBuffTriggerFactory.cs`、`GenericHit_BuffTrigger.cs`、`BuffConditionFactory.cs`、`TFormBuffConditionFactory.cs`、`OnPlayerStateEnter_BuffTrigger.cs` 等）与 `abcode.html`，作为 `TFTF` 仓库内唯一技术真理源。
> **工作纪律**：严禁 AI 为猜测触发器或条件键而重新反汇编 `libil2cpp.so`；所有不确定问题优先查阅本契约与 `Server/abilities/contract_schema.json`。

---

## 一、极简二层收口架构铁律（Architecture Contract）

角色能力逻辑严格收敛在以下两层，**禁止出现“三头马车”或跨层猜谜**：

1. **Python 数据声明层 (`Server/abilities/bots/<bot>.py`)**
   - **职责**：
     - 定义该角色所有 Buff / StatMod 的外观（`StatModAppear`：文字、PUA 图标、颜色 `tc`/`gt`/`gb`）、数值（伤害/治疗/护甲/暴击等比例）、持续时间；
     - 仅允许挂载**单一、无条件/纯静态作用域的原生触发**（例如 `always`、`onIntroStart`、`onCrit + level=Ranged`、`onPlayerStateEnter + state=Block`）。
   - **禁止事项**：
     - **严禁**在 Python 的 `trs` 中编造客户端不认识的键（如 `isLastHit=true`、`target_has_bleed=True`）。
     - **严禁**把多段命中限定（`index=`、`count=`、`dmgFlags=LastHit`）或动态状态条件（`opp.status=`、`self.status=`）寄托在 `trs` 字符串中——**统一设 `tr: []`（由 C 模块触发）或把触发与条件判断完全收口到 C 模块**！

2. **C 技能插件层 (`tools/nativehook/skills/bots/skill_<bot>.c`)**
   - **职责**：
     - 凡涉及**多段第几击 / 末击**（`ctx->hit_index`、`ctx->is_last_hit`）、**动态前置条件联动**（`skill_has_buff`、`skill_count_buffs`、血量阈值、驱散成功计数）、**计时/充能/状态机**，全部写在独立 C 模块的回调（`on_hit_connected`、`on_test_roll`、`on_buff_gated`、`on_simulation_tick` 等）中，通过 `skill_apply_buff` / `skill_apply_buff_dur` 主动施加 Python 层定义好的 StatMod。
   - **禁止事项**：
     - **严禁**只弹出 `skill_overlay(...)` HUD 假提示而不真正施加 Buff 或结算效果；
     - **严禁**将新角色专属判断写进 `tools/nativehook/hook.c`（`hook.c` 事件总线已冻结）。

---

## 二、C# 客户端原生支持的触发器全集 (`tr`)

来自 `TFormBuffTriggerConstants.cs`、`TFormBuffTriggerFactory.cs` 与 `BuffTriggerFactory.cs`：

| 类别 | 合法 `tr` 名称 | 底层实现类 / 说明 |
| :--- | :--- | :--- |
| **常驻/开局** | `always`, `onStart`, `onPreStart`, `onIntroStart` | 开局初始化或常驻挂载 |
| **综合命中** | `onHit`, `onNormalHit`, `onSpecialHit` | 自动展开为对应 `AttackLevel` Hit 列表 |
| **细分命中** | `onLightHit`, `onMediumHit`, `onHeavyHit`, `onRangedHit`, `onSpecial1Hit`, `onSpecial2Hit`, `onSpecial3Hit` | `GenericHit_BuffTrigger` |
| **格挡/暴击/结算** | `onBlocked`, `onCrit`, `onHitStarted`, `onHitResolved`, `onBlockedResolved`, `onPreDamage`, `onAttackEnded` | `GenericHit_BuffTrigger` |
| **必杀技激活/结束** | `onSpecialActivate`, `onSpecial1Activate`, `onSpecial2Activate`, `onSpecial3Activate`, `onSpecial3Expiry` | `OnSpecialActivate_BuffTrigger` / 激活期触发 |
| **属性/状态变化** | `onHpGain`, `onHpLost`, `onPowerGain`, `onPowerLost`, `onPlayerStateEnter`, `onAnimStateEnter`, `onAnimStateExit` | 仅在原生状态变更瞬间派发 |
| **Buff 生命周期** | `onAbilityActivate`, `onAbilityExpiry`, `onTypeActivate`, `onTypeExpiry`, `onBuffImmune` | 需配合特定条件键（`id` / `type` / `modType`） |
| **区域触发** | `onAreaEnable`, `onAreaDisable`, `onAreaEnter`, `onAreaExit` | `Area_BuffTrigger`（配合 `id=`） |

> 注：以上触发器还允许加 `opponent:` 前缀（由 `BuffUtils.SplitTargetFromOperand` 解析），但二层收口规范下，机器人技能如涉及对手动作联动优先在 C 模块处理。

---

## 三、C# 条件解析机制与常见静默陷阱 (`trs`)

### 1. 为什么未知的 `trs` 键会“静默失效”？
查看 `BuffConditionFactory.cs` 第 41-69 行可知：
当 `BuffTriggerFactory.ParseConditions` 解析 `key=value` 时，如果 `trigger.CreateTriggerCondition` 和 `TFormBuffConditionFactory.CreateCondition` 均未命中 `switch(key)`，代码会回落执行：
```csharp
buffCondition = new BuffFloatCondition(
    BuffValueFactory.Instance.CreateFloatValue(lhs),
    BuffValueFactory.Instance.CreateFloatValue(rhs),
    op
);
```
- 客户端**既不抛异常也不打错误日志**，而是把无法识别的字符串当成浮点 `0.0` 比较，导致条件永远走偏或静默不触发！
- **典型假键重灾区**：`isLastHit=true`（`HitResultData` 根本没有 `isLastHit` 字段）、`target_has_bleed=True`（正确原语是 `opp.status=...`）、`isCrit=true`（应用 `tr: ["onCrit"]` 或 C 门禁）。

### 2. C# 原生条件键完整清单 vs. 二层收口白名单

| 键名 | C# 源码出处 | 原生支持与否 | 本仓库二层收口策略 |
| :--- | :--- | :--- | :--- |
| `level` | `GenericHit_BuffTrigger` | 支持 (`Light,Medium,Heavy,Ranged,Special1,Special2,Special3`) | **允许**（极简静态攻击类型过滤） |
| `state` | `OnPlayerStateEnter` / `TFormBuffConditionFactory` | 支持 (`Block,Dash,Run,Dodge...`) | **允许**（如 `state=Block`） |
| `dmgType` | `GenericHit_BuffTrigger` | 支持 (`Physical,Energy,Direct`) | **允许** |
| `heavyType` | `TFormBuffConditionFactory` | 支持 | **允许** |
| `isAi` / `fightType` | `TFormBuffConditionFactory` | 支持 | **允许**（特殊关卡/AI开关） |
| `index` / `count` | `GenericHit_BuffTrigger` | 支持 | **禁用**（收口到 C `ctx->hit_index`） |
| `dmgFlags` | `GenericHit_BuffTrigger` | 支持 (`LastHit,Crit,Blocked,Projectile...`) | **禁用**（收口到 C `ctx->is_last_hit` 等） |
| `status` (`self.status`/`opp.status`) | `BuffConditionFactory` | 支持 | **禁用**（收口到 C `skill_has_buff`） |
| `isLastHit` / `target_has_bleed` / `isCrit` | **不存在** | **不支持（静默失效）** | **严禁（红灯报错）** |
| `type` / `modType` / `id` / `expiryFlags` / `stack` | `OnAbility*` / `OnType*` / `Area` | 仅特定 Trigger 支持 | 仅限 `SYSTEM_GLOBAL_STATMODS` 或对应 Trigger 专用 |

---

## 四、IL2CPP 数据结构四大硬契约（沿用并强制校验）

1. **颜色 6 位纯 Hex**：`tc`, `gt`, `gb`, `bc` 严禁带 `#` 前缀。
2. **DOT 单跳伤害防截断**：客户端每 `0.5s` 结算 1 跳且强转整型 `int`，必须满足 `m / (d * 2.0) >= 1.0`。
3. **List 包装**：`tr`, `uit`, `a`, `au` 必须为 Python `list`。
4. **目标与演员**：减益设 `ta: "opponent", mt: "debuff", s: "none"`；自身增益设 `ta: "self", mt: "buff"` 或 `"passive"`。
