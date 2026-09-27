# TFTF SP3 大招变形修复与全角色批量校准规范指南

本文档总结了 TFTF 离线版中 S3（SP3）大招载具/野兽变形、慢动作同步（Slomo）、骨骼动画驱动（Animator）以及批量校准的完整底层机理与修复方法。

---

## 一、 核心问题剖析与机理

### 1. 为什么变形后模型会僵住（T-Pose 或静止）？
- **官方骨骼双机架构**：
  官方角色的载具/野兽形态并不是单纯的网格挂载，而是在 `transformed` 子节点下拥有**独立专属的 Animator 控制器**（例如猩猩队长挂载了 `override_OptimusPrimal_BW_MP32_beast`，汽车大师挂载了 `override_Motormaster_GS_Voyager2015_car`）。
- **SP3 节流与唤醒机制**：
  在进入 SP3 特写时，Matinee 引擎出于节流会把所有非活动 Animator 的 `speed` 置为 `0`。
  如果仅仅调用 `PlayerController.Transform(alt)` 切换渲染器显示，`transformed` 节点的 Animator 仍然处于暂停/未播放状态，导致野兽/载具模型被激活后呈现完全僵硬静止。

### 2. 为什么部分角色变形时机错位或提前变回？
- **慢动作（Slomo）轨道拉伸**：
  部分角色（如汽车大师、猩猩队长、碎骨魔）在 SP3 中有慢动作特写曲线（Track 0 的 `MatineeSpeedProperty`），导致真实时间轴与现实世界时钟（Wall Clock）脱节。
- **纯肉眼估算误差**：
  视频估算容易将开场转身/蓄力误当做变身终点，导致载具在真正冲撞打击阶段（如碎骨魔第 2.6s ~ 6.0s 的轮滑冲刺与机械爪重击）被提前强制切回人形。

---

## 二、 修复方案与底层调用

### 1. 慢镜头动态时间线同步
Hook `TFormMatineeStage.Update`（`0xE6FA78`），从当前 Stage 挂载的 `MatineeContainer` 动态读取实时缩放后的 `runningTime`（`[stage + 0x80..0xD0] -> [+0x38]`），完全废弃墙上时钟计数。

### 2. 官方骨骼动画双重驱动
在 `sp3_beat_apply(alt)` 中：
```c
// 1. 切换载具/网格渲染器
sp3_prop_mirror(prop_trans, alt);
sp3_prop_mirror(prop_char, !alt);

// 2. 唤醒并播放野兽/载具专属 Animator
if (alt) {
    // PropData.SetAnimatorSpeed @0xEA0660
    ((void(*)(void*, float, void*))(g_base + 0xEA0660))(prop_trans, 1.0f, NULL);
    if (g_strnew) {
        void* st_base = g_strnew("Base.SpecialAttack03");
        void* st_norm = g_strnew("SpecialAttack03");
        // PropData.PlayAnimatorState @0xEA05B4
        ((void(*)(void*, void*, void*))(g_base + 0xEA05B4))(prop_trans, st_base, NULL);
        ((void(*)(void*, void*, void*))(g_base + 0xEA05B4))(prop_trans, st_norm, NULL);
    }
}

// 3. 驱动人形主骨骼状态机
((void(*)(void*, int, void*))(g_base + 0x117A67C))(pc, alt, NULL);
```

### 3. 帧泵（`sp3_beat_pump`）持续保持活动
在变身持续期间，每帧保持 `prop_trans` Animator 的 `speed = 1.0f`，确保全套多段连击（如猩猩推倒 -> 重砸 -> 捶胸咆哮）完整播放。

---

## 三、 批量修复新角色的自动化流程

无需肉眼盲调，全游戏所有角色的准确时间点均可直接从官方 AssetBundle 提取：

1. **运行全量解析脚本**：
   ```bash
   python tools/parse_all_sp3.py
   ```
   脚本会自动扫描 `extracted_apk/assets/assetpack/` 下所有角色的 AssetBundle，提取 `MatineeContainer` 中的 `HitEvent`、`AttachToTransformEvent`（如武器挂载、`transformed` 挂载）和总时长。

2. **在 `tools/nativehook/sp3_exact_intervals.h` 中登记区间**：
   根据提取出的打击和挂载事件，填入对应角色的 `on_ms` 与 `off_ms`。
   例如：
   - 汽车大师 `motormaster_gs_voyager2015`：`{3950, 6800}`（空中起跳至落地滑行结束）
   - 碎骨魔 `bonecrusher_cin_rotf`：`{2100, 6200}`（冲刺全速撞飞碾压阶段）

3. **在 `hook.c` 的 `sp3_load_timing_for_character` 登记副武器（如有）**：
   - 猩猩队长：`shoulderguns` (`0 ~ 1833ms`)
   - 汽车大师：`sword` (`0 ~ 3950ms`)
   - 碎骨魔：`claw` (`0 ~ 2100ms`)

4. **一键构建离线 APK**：
   ```bash
   python build_apk.py
   ```
