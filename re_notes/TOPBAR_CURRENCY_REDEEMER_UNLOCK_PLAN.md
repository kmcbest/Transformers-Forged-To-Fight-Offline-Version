# 顶部通货栏（黄金、能量晶体、行动力）显示机制逆向分析与解锁方案

## 一、问题背景与现状诊断

在《变形金刚：百炼为战》（Transformers: Forged to Fight）离线版中，主界面与战役选人/准备界面右上角的资源栏（TopBar）展示了三项核心货币与资源：
1. ⚡ **能量 / 行动力 (Energy)**：显示为 `0/0` 或无法正常显示。
2. 🔶 **黄金 / 金币 (Gold / Soft Currency)**：显示为 `0`。
3. 🟪 **能量晶体 (Energon / Hard Currency)**：显示为 `0`。

在此前尝试直接修改静态数据（例如修改 `Server/responses/GET__account_data.json` 中的 `soft_currency: 100000`）后，重新打包离线数据包并热重载进入游戏，右上角数值依然没有任何变化，顽固保持为 `0`。

本文档深入剖析该现象的底层原因，梳理从 UI 展示层、ViewModel 绑定层、SubSystem 状态机到离线 HTTP 响应包的完整数据链路，并给出具备 100% 可行性的工程化落地实现方案。

---

## 二、底层逆向分析与机制根因 (Reverse Engineering Analysis)

经过对客户端 `libil2cpp.so`、`global-metadata.dat` 符号表以及运行时 Native Hook 日志的深度逆向追踪，确认了该问题并非单纯的“缺少某个 JSON 字段”，而是由于 **接口调用链分歧** 与 **底层 Sparx SubSystem 状态机死锁** 共同导致的。

### 1. 资产体系与 UI 呈现层映射

在客户端 UI 层，顶部资源栏的核心控制结构如下：
- **表现层组件**：`TransformersTopBarPresentation`（继承自 `TopBarPresentation`）
- **数据绑定视图模型**：`TopBarModel`

UI 绑定的三大资产在底层代码与配置中映射的内部 Key 为：
| UI 显示项 | 内部通货类型 | 客户端枚举/常量 ID | 数据包字段 Key | 典型展示格式 |
| :--- | :--- | :--- | :--- | :--- |
| ⚡ **能量 / 行动力** | `Energy` | `ID_REDEEMER_ENERGY` | `energy` | `100 / 100` (`current / max`) |
| 🔶 **黄金 / 软通货** | `Soft Currency` | `ID_REDEEMER_SOFT` | `soft` 或 `gold` | `999,999` (千分位数值) |
| 🟪 **能量晶体 / 硬通货** | `Hard Currency` | `ID_REDEEMER_HARD` | `hard` 或 `energon` | `88,888` (千分位数值) |

### 2. 误区排查：为什么修改 `/account/data` 完全无效？

在游戏最初的离线化 Mock 资源中，存在 `Server/responses/GET__account_data.json`，其中包含：
```json
{
  "soft_currency": 100000,
  "hard_currency": 500
}
```
通过在 Native Hook 拦截所有 HTTP 请求后证实：
> **游戏进入主界面、战役选人界面（HeroesScreen / PrefightScreen）期间，根本不会请求 `GET /account/data`！**
> 该接口仅在早期旧版登录协议或某些遗留全量账号同步中使用。客户端的通货资产展示完全解耦为独立微服务模块——**Redeemer 兑换与通货子系统**。

真正驱动顶部资产栏更新的网络请求接口为：
- **`GET /redeemer/refresh`**：拉取玩家当前所有通货、代币、能量的余额及恢复周期字典。
- **`GET /inventory`**：拉取玩家背包道具、火种、升星材料。
- **`GET /ds/1000000000001/`**：数据仓库（DataStore）持久化配置。

### 3. 核心死因：Sparx SubSystem 状态机死锁 (`RedeemerManager st=1`)

即便在离线服务器（`inapk_server.c`）中补齐了 `GET /redeemer/refresh` 接口并返回了包含金币、能量块的完整数据包，真机 UI 依然显示为 `0`。

通过抓取 Native Hook 的运行时日志（`logcat -s TFTFHOOK:*`），在 `Hub.SubSystemConnecting` 监测点捕获到了根本死因：
```
TFTFHOOK: == CONNECTING size=4 ==
TFTFHOOK:   STUCK RedeemerManager st=1
```

#### 状态机流转原理
客户端架构基于 Kabam / EA 经典的 **Sparx 框架**（`EB.Sparx` 命名空间）。游戏内各个功能模块被划分为 `SubSystem`：
- `st = 0`：`Disconnected`（未连接）
- `st = 1`：`Connecting`（正在握手/初始化）
- `st = 2`：`Connected`（连接成功，模块激活）
- `st = 3`：`Error / Disconnected`（连接异常）

在官方线上版本中，游戏启动时 `Hub` 遍历所有注册的 `SubSystem` 并调用其 `Connect()` 方法。子系统向 Sparx 后端发起长连接握手或验证包，收到 ACK 后将内部状态置为 `Connected (2)`。
但在离线单机环境下：
1. `RedeemerManager` 发起连接请求后，因缺少长连接服务或特定的握手确认事件，其内部状态一直停留在 `st=1`（`Connecting`）。
2. `TopBarModel` 在向 `RedeemerManager` 注册监听或查询当前通货时，会检测其状态。如果 SubSystem 处于非 `Connected` 状态，数据流派发管道被熔断，UI 保持默认的零值。
3. 此前开发团队在离线化早期，对其他类似卡死子系统采用了针对性修复（见 `hook.c` 第 3161~3168 行的 `MKFIX`）：
   - `fixXlate`（`EB.Sparx.XlateManager.Connect`，RVA: `0x1593888`）
   - `fixQuestL`（`Legacy.QuestsManager.Connect`，RVA: `0xD64370`）
   - `fixQuestN`（`Quests.QuestsManager.Connect`，RVA: `0xD6A1B0`）
   上述模块均通过在 Native 层将 `*(int*)((char*)subsystem + 0x18) = 2` 强行解锁为 Connected 状态。而 `RedeemerManager` 此前从未被加入该白名单，导致其永久挂起！

---

## 三、工程化落地实现方案

要彻底点亮顶部通货栏并显示自定义的金币、能量块数量，必须采用 **“服务端数据包注入 + 客户端 Native Hook 解锁”** 双管齐下的方案。

### 阶段一：服务端离线响应包补齐 (`GET__redeemer_refresh.json`)

在 `Server/responses/` 目录下创建标准的通货全量响应包 `GET__redeemer_refresh.json`：
```json
{
  "error": null,
  "result": {
    "nextrefresh": 2147483647,
    "redeemers": {
      "soft": {
        "name": "soft",
        "amount": 999999,
        "max": 999999999,
        "growthInterval": 0,
        "spendWarn": false
      },
      "hard": {
        "name": "hard",
        "amount": 88888,
        "max": 999999999,
        "growthInterval": 0,
        "spendWarn": false
      },
      "gold": {
        "name": "gold",
        "amount": 999999,
        "max": 999999999,
        "growthInterval": 0,
        "spendWarn": false
      },
      "energon": {
        "name": "energon",
        "amount": 88888,
        "max": 999999999,
        "growthInterval": 0,
        "spendWarn": false
      },
      "energy": {
        "name": "energy",
        "amount": 100,
        "max": 100,
        "growthInterval": 0,
        "spendWarn": false
      }
    }
  }
}
```
同时兼容 `soft`/`gold` 和 `hard`/`energon` 的双重别名映射，确保不论客户端取哪个字典 Key 均能安全取到数值。

### 阶段二：客户端 Native Hook 解锁 (`hook.c`)

在 `tools/nativehook/hook.c` 中针对 `RedeemerManager` 进行状态迁移干预。有两种实现路径：

#### 路径 A：在 `hook_21`（`Hub.SubSystemConnecting`）中进行动态状态提升（推荐，安全轻量）
无需反编译寻找 `RedeemerManager.Connect` 的具体机器码地址，直接在巡检 Connecting 列表时，匹配到名称为 `"RedeemerManager"` 的对象时就将其强制置为 `2`：
```c
// 在 tools/nativehook/hook.c hook_21 中：
if(items>=0x100000 && size>0 && size<80) for(int k=0;k<size;k++){
    uintptr_t sub=*(uintptr_t*)(items+0x20+k*8);
    if(sub>=0x100000){
        int st=*(int*)(sub+0x18);
        char nm[40];
        rdname(sub, nm);
        if(strcmp(nm, "RedeemerManager") == 0 && st == 1) {
            *(int*)(sub + 0x18) = 2; // 强行解除挂起，跃迁到 Connected
            flog("  FORCE CONNECTED: %s st 1 -> 2", nm);
        } else {
            flog("  STUCK %s st=%d", nm, st);
        }
    }
}
```

#### 路径 B：通过静态 RVA 为 `EB.Sparx.RedeemerManager.Connect` 建立 `MKFIX`
从 `global-metadata.dat` 提取 `EB.Sparx.RedeemerManager.Connect` 的 Method RVA，在 `H[]` 数组中添加对应的 hook slot，使用已有的 `MKFIX` 宏在原函数执行完毕后将 `*(int*)((char*)a0 + 0x18) = 2`。

### 阶段三：集成编译与打包流

1. 将 `GET__redeemer_refresh.json` 包含进离线打包脚本：
   - 检查 `tools/export_payload.py`，确保 `GET /redeemer/refresh` 请求被打包进 `tftf_offline_payload.bin`。
2. 重新编译 `libtftfhook.so` 并打包进 APK（或通过 ADB 动态重载测试）。
3. 使用 `INSTALL-ADB.py` 自动化部署到测试设备。

---

## 四、验证与验收门禁 (Verification Quality Gates)

1. **Logcat 无死锁断言**：
   - 过滤日志：`adb logcat -s TFTFHOOK:* | Select-String "RedeemerManager"`
   - 预期输出：`FORCE CONNECTED: RedeemerManager st 1 -> 2`，且不再出现 `STUCK RedeemerManager st=1`。
2. **UI 渲染验收**：
   - 进入主界面，右上角资源栏不再呈现 `0`。
   - ⚡ 能量栏正确显示 `100/100`。
   - 🔶 黄金栏正确显示 `999,999`。
   - 🟪 能量晶体栏正确显示 `88,888`。
3. **稳定性验证**：
   - 进出关卡地图、战斗准备界面与英雄详情界面，UI 资源栏不出现空指针崩溃或数值回退。

---

## 五、总结

通过本逆向分析，明确了修改单一 JSON 无法生效的核心技术阻碍，揭示了 Sparx 框架的 SubSystem 状态机生命周期原理，并提供了最小侵入、最高稳定性的 Native + Payload 联合解锁方案。
