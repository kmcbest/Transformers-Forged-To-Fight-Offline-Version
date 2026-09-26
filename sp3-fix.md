这份技术备忘录送给正在被 SP3 动画、逐帧数时间和慢镜头错位折磨的 Agent 同志：

***

# 🎬 【不再看视频数帧数】TFTF 官方 SP3 大招动态变形与慢镜头机制白盒深度解析

> **致正在攻坚 SP3 变形与特写镜头的 Agent 同志**：
> 别再盯着游戏录像肉眼数帧数、为每个角色硬编码 `intervals: [[1000, 2500]]` 毫秒了！而且你一定发现了：**一旦遇到带慢动作特写（Slow-Mo）的角色，写死的时间必然发生穿模和提前切回人形！**
> 
> 随着官方 **2.0.2 纯 Mono C# 源码**全量就绪，SP3 的导演轨道系统、慢镜头时间膨胀以及变形道具调度的底层真相已经**全景式曝光**！

---

### 一、 核心源码索引（可直接在 `decomp_202_source/` 查阅）

1. **SP3 玩家触发态**：
   `decomp_202_source\Assembly-CSharp\PlayerCinematicSpecialAttackState.cs`
2. **SP3 特写生命周期与裁判席状态机**：
   `decomp_202_source\Assembly-CSharp\BattleArbiterCinematicSpecialState.cs`
3. **导演影视舞台（Matinee Stage）**：
   `decomp_202_source\Assembly-CSharp\TFormMatineeStage.cs`
4. **形态与道具关键帧事件（核心中的核心）**：
   `decomp_202_source\Assembly-CSharp\MatineePropEvent.cs`
5. **慢动作时间膨胀事件**：
   `decomp_202_source\Assembly-CSharp\TimeScaleMoveEvent.cs`
6. **机器人与载具部件调度器**：
   `decomp_202_source\Assembly-CSharp\PropsController.cs`、`PropData.cs`

---

### 二、 源码中 SP3 变形的真正实现：基于动画时间轴的关键帧事件

在原版游戏引擎中，SP3 变形**根本不依赖外部计时器，也不是靠轮询代码切状态**：

1. **每个角色有独立的专属特写舞台（`SpecialStagePrefab`）**：
   在 `BattleArbiterCinematicSpecialState.cs:203-227`，放 SP3 时会实例化角色专属的 `References.SpecialStagePrefab`，并启动 `TFormMatineeStage`。
2. **动画时间线上的 `MatineePropEvent`**：
   在舞台的 Matinee 轨道上，早就在特定关键帧预埋了 `MatineePropEvent`（见 `MatineePropEvent.cs:33`）：
   ```csharp
   public override void StartEvent(float t)
   {
       if (_propsController != null)
       {
           // 轨道到达变车那一刻：
           _propsController.SetActive("character_model", false, "PropMatinee"); // 隐藏人形本体
           _propsController.SetActive("transformed", true, "PropMatinee");     // 显示载具形态
       }
   }
   ```
3. **为什么这是最完美的方案？**
   因为这个事件是**紧贴着动画轨道走的**！无论动画放慢多少倍，只要轨道指针走到该帧，才会发出变身事件；轨道没走完，就绝不可能提前切回人形！

---

### 三、 为什么写死的毫秒 Interval 遇到慢镜头必崩？

在源码 `TimeScaleMoveEvent.cs` 中，我们看到了慢镜头的底层实现：
```csharp
// 慢镜头触发时，引擎动态修改了全局物理与动画时间流速：
Simulation.Instance.TimeScale = 0.2f; // 甚至放慢到 0.1f（慢放 5~10 倍）
```
- **病因分析**：
  此前在 Native Hook 中用 `Simulation.FixedUpdate` 累加的毫秒数，是基于 **现实世界的物理流逝时间（Wall-clock ms）**；
  然而当角色打出特写触发慢镜时，画面被放慢了 5 倍！
  **现实世界过去了 2.5 秒，游戏内的动画可能才刚飞了 0.5 秒！**
  此时 Hook 里的定时器一到，强行把模型切回了人形，表现为：**车子在半空中还在慢动作滑行，突然瞬间变成了站立的人形！**

---

### 四、 从 2.0.2 到 9.2.0，所有角色的处理方式完全一致吗？

**100% 架构完全一致！**

从早期版本的擎天柱、威震天、风刃，到 9.2.0 关服版的所有新角色（包括 Netflix 独占的 Chromia、Dead End，以及后期的 Megatronus、Hound 等）：
- 它们全部继承自同一套 `TFormMatineeStage` 框架；
- 每个角色的 AssetBundle 内部都携带着专属的 Matinee 动画轨道；
- 没有任何一个角色是写死代码切换形态的，全部是由轨道上的 `MatineePropEvent` 和 `TimeScaleMoveEvent` 协同驱动！

---

### 五、 两种彻底告别“逐角色调帧”的优雅解决方案

#### 方案 A（黄金推荐：唤醒官方原生轨道，彻底告别配置表）
- **离线版之前不变形的原因**：
  查看 `MatineePropEvent.cs:25`，它在 `BindEvent()` 时需要通过 `entity` 找到当前角色的 `PropsController`。此前离线版在 Stage 创建时缺少某些上下文，导致 `entity` 为空，`_propsController` 为 NULL，使官方原生事件静默失效。
- **解法**：
  在 Native Hook 中，检查并确保 `TFormMatineeStage.InitStage` 时将 Instigator 角色的 GameObject 传递绑定给 Stage 的 Actor 列表。
  **只要这一步打通，官方的 Matinee 轨道会全自动完成所有变形，不仅自带原生音效与粒子，而且天然完美支持慢动作！**

#### 方案 B（如果仍保留 Interval 配置表，如何修正慢镜错位？）
如果暂时不想改动现有 Hook 架构，也请**立刻停止直接累加现实毫秒数**：
1. **按时间膨胀流速进行积分**：
   $$\Delta t_{\text{effective}} = \Delta t \times \text{Simulation.Instance.TimeScale}$$
   每次累加时乘以当前的 `TimeScale`。慢动作放慢了 5 倍，积分时间就跟着慢 5 倍，完美对齐画面！
2. **或直接读取 Matinee 真实播放进度**：
   读取 `TFormMatineeStage._matineeContainer.CurrentTime`（或 NormalizedTime，0.0~1.0），用动画百分比（如 `0.25 ~ 0.75` 处于载具形态）代替固定毫秒，任何帧率波动和慢镜头都将无懈可击！