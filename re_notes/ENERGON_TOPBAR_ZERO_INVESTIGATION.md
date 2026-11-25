# 顶栏能量晶体（Energon）显示 000000 —— 数据链路排查结论

日期：2026-09-19/20
涉及提交：`2ff7f82 feat(economy): unlock topbar currency rendering with RedeemerManager state fix and currency mappings`

## 一、结论摘要

| 项 | 状态 |
| :--- | :--- |
| 服务器数据（APK 内嵌 payload） | **完全正确**：`user_info.hc/hard/energon = 66666`、`redeemers.hard.amount = 66666` |
| 黄金格 | **正常**，且**已证实由 `/account/data` 的 `user_info` 驱动**（键名 `sc`） |
| 能量晶体格（能量晶体/Energon 图标） | **恒为 000000**，对 `user_info` 的任何键名都不响应 |
| 能量格（⚡） | 恒为 `0/0`，同样不响应 `user_info` |

**根因方向**：能量晶体格的值**不是**从 `/account/data.user_info` 取的。而客户端真正请求的三个接口
`/payments/payouts`、`/inventory`、`/gamestore/get-login-data` 在本仓库中**没有响应文件**，
一律落到默认空信封 `{"error":null,"result":{}}`。同一提交加的 `hook_173`（点击重定向到
`OnResourceClick`）会让这一格点击闪退，也是同一批缺失数据导致的。

尚未最终确认的一步：该槽位具体读哪个响应/字段。需要运行时插桩（见第五节）。

## 二、已证实的结论与实证

### 1. 顶栏读 `/account/data` 的 `user_info`（不是 `/redeemer/refresh`）

差分探针（`tools/probe_source.py`）把每个候选键写成可区分的值：

| 源 | 取值规则 |
| :--- | :--- |
| `redeemers.<key>.amount` | `3<序号>00`（soft→30000，hc→30400） |
| `user_info.<key>.v` | `4<序号>00`（soft→40000，hc→40400，sc→40100） |

屏幕实测：金色格显示 **`40,100`** → 即 `user_info.sc`（序号 1）。
此前一轮（`tools/probe_currency_keys.py`）金色格显示 `220002` → `user_info.gold`；
`raid_chip` 220011、`raid_ticket` 220012 也都原样出现。**均来自 user_info，且不存在于 redeemers。**

### 2. 客户端认识的资源键名（从 `global-metadata.dat` 字符串池核实）

导出命令：`tools/_dbg_strtab.py`（生成 `build/_dbg_tokens.txt`，90787 个 token）

| 存在 | 不存在 |
| :--- | :--- |
| `sc` `hc` `bc` `rc` `rt` `gold` `soft` `Soft` `Hard` `HardCurrency` `SoftCurrency` | `hard` `energon` `hard_currency` `crystal` |

> `re_notes/TOPBAR_CURRENCY_REDEEMER_UNLOCK_PLAN.md` 里 `soft`/`gold`、`hard`/`energon`
> 的别名映射是**未经运行时验证的推断**，其中 `hard` / `energon` 在客户端根本不存在。

### 3. 能量晶体格不吃任何 `user_info` 键

- `probe_hc_keys.py`：16 个候选键（`hc/hard/energon/hard_currency/hardcurrency/HardCurrency/…`）
  同时写入 `user_info`，值各不相同 → 紫色格仍 `000000`。
- `probe_case.py`：11 个大小写变体（`Hard/Soft/HardCurrency/SoftCurrency/HC/SC/…`）→ 仍 `000000`。
- `probe_source.py`（21 键 × 两数据源）→ 仍 `000000`。

因此不是"键名写错"，而是**这个槽位的值根本不来自 `user_info`**。

### 4. 三个客户端请求但服务端无响应的接口

设备上直接 curl APK 内置服务器（`tools/_dbg_http_probe.py`）：

```
/payments/payouts           -> {"error":null,"result":{}}   ← 无响应文件
/inventory                  -> {"error":null,"result":{}}   ← 无响应文件
/gamestore/get-login-data   -> {"error":null,"result":{}}   ← 无响应文件
/offers/getLoginData        -> {"error":null,"result":{}}
/pvp/get-login-data         -> {"error":null,"result":{}}
/gamestats/get-login-data   -> {"error":null,"result":{}}
/ds/1000000000001/          -> {"error":null,"result":{}}
/redeemer/refresh           -> 正常（但顶栏不消费它）
```

客户端侧与之对应的类型（token 证据）：`EB.UI.Payouts`、`PayoutsModel`、`PayoutsPresentation`、
`PopulateTabs`、`GetDefaultTabId`、`TabId`、`TabInfo`、`_tabs`、`DirectRedeemers`、`payoutId`、
`_payoutsSeenList`、`startingHCCount`、`SoftCurrentToPay`、`SoftCurrencyConfig`、
`RedeemerAPI`、`RedeemerConfig`、`Redeemers`、`NextRefresh`、`GrowthInterval`。

相关 UI 原语（bundle 证据）：`TopBarCurrencyButton`（`cc0cf1248bb8c47618103a5a1652011f`）、
`HCicon`（`374d6d3e9d4c14c67aeea89a0c4fb3da`）、`TopBar`（`c8d0bc921c3f14c5bb8aac5a75247ec2`）。

客户端实际请求顺序（logcat）：`/account/data` → `/payments/payouts` → `/redeemer/refresh`
→ `/ds/<uid>/` → `/inventory`。

## 三、已排除的假设

| 假设 | 排除依据 |
| :--- | :--- |
| 打包时 payload 漏了数据 | 从设备拉取已安装 APK 解析：`hc=66666` 存在（`tools/_dbg_installed.py`） |
| 字形/字体导致 6 个 0 看着不对 | 字体 `zero` 字形就是"窄方框+斜杠"，`888,888` 与 `000000` 分别为 `8`/`0` |
| 客户端不认识 `hard`/`energon` 键 | 已证实（token 表），但换成 `hc`/大小写变体也无效 |
| `/account/data` 没送达 | 金色格/芯片/ticket 都跟着探针变，说明已送达且被消费 |
| `user_info` 值被覆盖 | 探针里 `hc` 是最后一次写入，紫色格仍 0 |

## 四、复现用探针（都可用，无需重编 APK）

热重载路径优先级（`inapk_server.c`）：`/data/local/tmp/tftf_offline_payload.bin` **优先于**
`/sdcard/Android/data/com.kabam.bigrobot/files/tftf_offline_payload.bin`。

```powershell
# 任选一个探针生成后推送
python tools/probe_source.py        # 源+键 判别（21 键）
python tools/probe_hc_keys.py       # 广别名（16 候选）
python tools/probe_case.py          # 大小写变体（11 候选）
adb push build/probe_source_payload.bin /data/local/tmp/tftf_offline_payload.bin
# 然后手动重启游戏（不要用 adb 强杀，会丢 logcat 上下文）
```

确认探针生效：`adb shell "logcat -d | grep 'HOT RELOAD payload active'"`

辅助工具：
- `tools/_dbg_http_probe.py` / `_dbg_http_probe2.py` — 直接 curl 设备内置服务器任意路由
- `tools/_dbg_tokens.txt` — 客户端 metadata 全量 token（查"客户端认不认某字段"）
- `tools/_dbg_keyrefs.py` — 扫 `ADRP+ADD` 定位代码里引用某字符串字面量的位置
- `tools/_dbg_installed.py` — 解析设备上已安装 APK 的内嵌 payload

## 五、诊断插桩实验（已全部回退）

本文件早期版本在这里记录了一批诊断 slot（175-186）与一份 `RESCLICKGUARD` 修复，
**这些内容已作废**：所有诊断 slot 已从 `hook.c` 移除，`RESCLICKGUARD` 并不存在于最终代码中，
当时“已修复”的结论是错误的（实测仍然崩溃）。完整失败清单见第九节。

保留下来仍有价值的一条方法论：**帧指针回溯**。`_Unwind_Backtrace` 在本工程的路径上返回
`_URC_FATAL_PHASE1_ERROR`，改用 x29 链即可拿到调用栈：

```c
uintptr_t fp; __asm__ volatile("mov %0, x29" : "=r"(fp));
while (fp && !(fp & 7)) {
    uintptr_t lr = *(uintptr_t*)(fp + 8);   // 返回地址
    uintptr_t nx = *(uintptr_t*)fp;          // 上一层 x29
    flog("lr_rva=0x%lx", (long)(lr - g_base));
    fp = nx;
}
```

拿到 RVA 后用 `python tools/il2cpp_meta.py resolve 0xRVA` 反查所属函数
（二分法不可用：代码注册表有空洞；改为反向扫描帧建立指令 `mov x29, sp` = `0x910003FD`）。

## 八、当前状态（2026-09-19 收尾）

**`tools/nativehook/hook.c` 已用 `git checkout HEAD -- tools/nativehook/hook.c` 回退，然后逐行重建了
实验前的工作区状态**（即本文件记录的 173/174 两个 hook）。校验：`libdothook.so` 回到 1055920 字节，
与实验前一致；`git diff HEAD -- tools/nativehook/hook.c` = 30 insertions / 1 deletion，只有那两个 hook。
所有 175–186 诊断 slot 已移除。

> 注意：173/174 这两个 hook **从未提交**，只存在于工作区。做 `git checkout <file>` 之前务必先确认
> 目标文件的工作区改动是否需要保留——本次回退时误删过一次，靠推理重建。

### 仍待解决

| 问题 | 状态 |
| :--- | :--- |
| 顶栏能量晶体格显示 `000000`（应为 66666） | ❌ 未解决 |
| 点能量晶体格触发 `IndexOutOfRangeException` 崩溃 | ❌ 未解决 |
| 两者共同卡点 | `/payments/payouts` 一直返回默认空信封，客户端侧 `PaymentsTab[]` 为 null |

### 唯一可靠的下一步

**拿到一份可用的 `/payments/payouts` 响应样例**（线上版抓包、或任何商店能正常打开的版本的响应）。
理由：崩溃与显示问题的卡点是**同一处数据缺失**，补对数据可一次性解决两者；
而靠"改点击处理链/拦窗口"已经证明无效（见下节失败路径）。

## 九、失败的尝试与错误的地址（避免重复踩坑）

### 崩溃真身（游戏自带崩溃上报器 `last_bug_report.json`，多次一致）

```
condition: IndexOutOfRangeException: Index was outside the bounds of the array.

EB.UI.Payouts.PayoutsModel.GetDefaultTabId (EB.Sparx.PaymentsTab[] tabs)
EB.UI.Payouts.PayoutsModel.Awake ()
UnityEngine.Object.Instantiate[T]
NGUITools.AddChild
WindowManager+<>c__DisplayClass140_0.<LoadWindowObject>b__2
WindowManager.PreloadWindow / ClaimPreloadOrCreateWindow / Open_MoveToTop / Open
EB.Action`1[T].Invoke
UICamera.Notify (GameObject go, String funcName, Object obj)
UICamera.ProcessRelease / ProcessTouch
```

入口是一次 **UICamera 触摸释放**（按钮的 NGUI 点击回调），进入某个 `WindowManager.Open`，
实例化带 `PayoutsModel` 的窗口预制体时抛异常。

### 试过但无效的六条路

| # | 做法 | 结果 |
| :--- | :--- | :--- |
| 1 | hook 173 拦 `OnHardCurrencyClick`（返回 NULL） | ❌ 仍崩；日志显示点击**不走**这个函数 |
| 2 | 173 转发到 `OnResourceClick` | ❌ 仍崩 |
| 3 | 拦 `OpenPayoutsStoreInternal (0xA4F8C0)` 返回 NULL | ❌ 仍崩（日志确认拦截生效，说明还有别的开窗路径） |
| 4 | 183 把 `OnResourceClick` 转发到金色格的 `0x141CD54` | ❌ 仍崩（日志确认 `ONRESOURCECLICK` 一条都没有） |
| 5 | hook `Awake (0xDA0608)` 打 `tabs` 长度 | ❌ 探针**零触发**，说明该地址不是实际执行的 `Awake` |
| 6 | patch `Awake` 内 `0xDA0684` 的条件跳转 | ❌ 未执行——核对机器码发现编码是 `54000482`（偏移 0x482），与我推算的 `54000182` 不符，**函数边界判断错误，不能盲打** |

### 坐标教训（很关键，别再搞错）

设备 2248×1080 横屏，顶栏三个格子的实际像素位置：

| 格子 | 标签 | x |
| :--- | :--- | :--- |
| ⚡ | 能量 | ~1848 |
| 🔶 | 黄金 | ~2015 |
| 🟪 | 能量晶体（紫色立方体） | ~2160 |

早期用 `x≈2050` 模拟点击"金色格"，实际落在黄金格附近，导致把 `ONHCCLICK` 误判为能量晶体格的处理器，
浪费了多轮。**做点击实验前必须用像素/背景色重新测量槽位边界。**

### 已确认的地址（可复用）

| RVA | 方法 | 备注 |
| :--- | :--- | :--- |
| `0x141CD54` | `TransformersTopBarPresentation.OnHardCurrencyClick` | 金色格点击；可正常打开资源详情 |
| `0x141F8F8` | `TransformersTopBarPresentation.OnResourceClick` | 打开那个会崩的窗口；**能量晶体格不经过它** |
| `0x141FAB0` | `TransformersTopBarPresentation.OnEnergyClick` | 点击时静默 |
| `0x141CE38` | `TransformersTopBarPresentation.UpdateCurrency` | 等级/进度条比例，非货币格 |
| `0x141C57C` | `TransformersTopBarPresentation.ConfigureResourceDisplay` | 初始化时配置每个格子 |
| `0x141F70C` | `TransformersTopBarPresentation.OnResourceChanged` | 顶栏刷新主入口，**本作从未触发** |
| `0x141EE98` | `TransformersTopBarPresentation.SetSoftCurrencies` | 收到**空集合**（`a1=0x0`） |
| `0x141C094` | 顶栏初始化里对 `OnHardCurrencyClick` 的引用点 | **是注册回调，不是点击** |
| `0xA4F8C0` | `OpenPayoutsStoreInternal` | 由 RVA `0xA4F730` 的函数在 `0xA4F79C` 调用 |
| `0xDA0608` / `0xDA0720` | `PayoutsModel.Awake` / `GetDefaultTabId` | 崩溃栈里的名字，但 hook 未触发 → 地址存疑 |

### 未验证的观察（不要当作结论）

- `ONHCCLICK#1` 的 `lr_rva=0x141c098` 出现在**启动/注册阶段**，`PAYOUTOPEN` 也在同一时段。
  这暗示"开 Payouts 窗口"可能是**启动期行为**，与用户点哪个格子无关——但这一点没有被单独实验证实。

## 十、工具与探针

```
python tools/il2cpp_meta.py tokens [正则]        # 导出/检索 metadata 字符串表（90786 个 token）
python tools/il2cpp_meta.py method <名字>        # 方法名 → 索引/RVA + 调用点
python tools/il2cpp_meta.py method-index N [M]   # 打印方法索引区间
python tools/il2cpp_meta.py methods-in LO HI     # 某地址区间里有哪些方法
python tools/il2cpp_meta.py resolve 0xA 0xB      # 返回地址 → 所属函数（扫 mov x29,sp 帧建立）
python tools/il2cpp_meta.py callers 0xRVA        # 谁调用这个地址（BL/B 全镜像扫描）
python tools/il2cpp_meta.py slot PAGE OFF        # 解引用 il2cpp metadata slot
python tools/il2cpp_meta.py disasm 0xRVA [LEN]   # 反汇编
```

探针脚本（无副作用，热重载 payload 用）：

| 文件 | 用途 |
| :--- | :--- |
| `tools/probe_source.py` | 生成"数据源+键名"判别 payload（redeemers `3<ii>00` vs user_info `4<ii>00`） |
| `tools/probe_currency_keys.py` | 21 键广别名差分探针 |
| `tools/probe_hc_keys.py` | 16 个硬通货候选键探针 |
| `tools/probe_case.py` | 11 个大小写变体探针 |

体系性守卫（建议每次加 hook slot 后先跑）：

```
python tools/check_hook_table.py    # H[] 表项与 handlers[] 必须严格一一对应，否则会跳非法指针崩溃
```

热重载路径优先级：`/data/local/tmp/tftf_offline_payload.bin` **优先于**
`/sdcard/Android/data/com.kabam.bigrobot/files/tftf_offline_payload.bin`。

排查用命令（设备内置服务器直连）：

```powershell
adb shell "curl -s -m 5 http://127.0.0.1:8080/payments/payouts | head -c 300"
adb logcat -d | Select-String "TFTFHOOK"
```
。


