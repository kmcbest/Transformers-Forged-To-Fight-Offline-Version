# Repository instructions

- Never add files from `media/` to Git. Screenshots and recordings are local-only captures;
  they may include copyrighted game audiovisual content. Keep them ignored and out of commits.

## Git and pull requests

- The canonical repository for all pushes and pull requests is
  `Gummygamer/Transformers-Forged-To-Fight-Offline-Version`.
- Never create, target, or suggest a pull request for the `geamztheangrybirds727` fork.
- Before creating a pull request, verify that the repository remote resolves to the
  `Gummygamer` repository.

## Shell and Python execution guidelines

- The development environment runs on Windows with PowerShell. Never use multi-line inline Python commands (`python -c "..."`). PowerShell misparses multi-line strings, nested quotes, `$`, and regex escapes, triggering `ParameterBindingException`.
- Always write logic into a script file (e.g. in `tools/` or temporary `.py` file) and run `python <script_path>.py` instead.
- Prefer explicit PowerShell commands (e.g. `Select-String` or dedicated scripts) over GNU Unix tools like `grep` unless verified available.

## AssetBundle and UnityPy packaging guidelines

- When modifying or re-saving UnityFS AssetBundles using `UnityPy`, never call `env.file.save()` without compression arguments. UnityPy defaults to uncompressed raw output (`packer=None`), which inflates APK package size from 0.9 GB to 1.35+ GB.
- Always explicitly pass `packer="lz4"` or `packer="original"` to `env.file.save()`.

## APK installation tools

- Use `INSTALL-ADB.py` located in the root directory for graphical and automated APK installation via ADB with standard flags (`-r --no-incremental`).

## Moveset and Netflix AssetBundle guidelines

- Never extract or overwrite `moves.assetbundle` from the base Kabam 9.2.0 APK. Chromia (克劳莉娅, 12 moves) and Dead End (封锁, 8 moves) are Netflix exclusives; their moves only exist in `assets_netflix/moves.assetbundle`.
- Any tool generating `assets_redeco/moves.assetbundle` must base on `assets_netflix/moves.assetbundle`, preserve Lifeline's stitched moves (`move_lifeline_special_01` & `02`), and verify that total moves count is >= 945.

## Combat and combo quality gates

- Any modification affecting combat input handling, attack chains, or state machines in `tools/nativehook/hook.c` must strictly adhere to the 6 quality gate test cases defined in `re_notes/combat-test-cases.md`.
- **Combat Truth Source Protection (战斗手感与连招真理源保护原则)**:
  `re_notes/combat_truth_source.md` 与 `tools/nativehook/combat_truth_backup.c` 是战斗手感逻辑的**黄金基线/真理源**。严禁在未经用户明确同意与门禁全绿测试前修改或弱化其中的任何规则；若后续开发不慎改坏手感，必须以真理源为标准立即对照还原。
- Never endlessly chase machine code / disassembly in `libil2cpp.so` for combat combo logic; inspect and reason through high-level state, hooks, and variables in `hook.c` directly.
- Verify via logcat that no `[COMBAT_RULE_VIOLATION]` assertions are triggered during combat testing.

## Troubleshooting and investigation guidelines (排查与分析方法规范)

- **Avoid Disassembly and Machine Code Rabbit Holes (严禁陷入反汇编与机器码死循环)**:
  TFTF is heavily data-driven (`JSON` wire payloads + local offline cache). Never endlessly disassemble ARM64 instructions, trace registers, or inspect deep il2cpp internals to debug UI numbers, missing attributes, or level stats. UI display anomalies (e.g. PI, HP, ATK showing 0, missing names) are virtually always caused by data payload mismatches (`(bid, rank, level)` query mismatching the local cache, or missing wire keys).
- **Black-Box Data Diff First (对比排查优先)**:
  Always compare the HTTP request/response payloads (especially `/bcg/getBaseHeroData`, `/quests/quest-movedir`, and `/quests/quest-begin`) between working scenarios (e.g. 1.1.1) and failing scenarios (e.g. 1.1.2, 1.1.3). Verify that `(bid, rank, level)` in `/bcg/getBaseHeroData` strictly matches `battleEnemy` in `/quests/quest-movedir`. A mismatch causes the client's cache lookup to fail, resulting in 0 stats.
- **Do Not Analyze Build Scripts for Game Logic Issues (禁止无关工具发散分析)**:
  When diagnosing gameplay, quest, or UI bugs, do NOT inspect or analyze build scripts like `build_apk.py` or `INSTALL-ADB.py`. Focus exclusively on the data flow (`gamedata.py`, `export_payload.py`), native server responses (`inapk_server.c`), and relevant hooks (`hook.c`).

## Execution and decision-action guidelines (方案确认与即时执行规范)

- **Immediate Execution upon Alignment (方案确认即坚决执行，严禁过度重复探查)**:
  一旦向用户完成了原因排查与走查汇报，并明确提出了具体的修改方案，且获得了用户的同意与执行指令（如用户回复“好的直接改”、“改了编译”、“做吧”等），**必须立即执行对应的代码修改并完成编译验证**。
- **Strictly Ban Redundant Circular Research (严禁在方案已确定后二次发散)**:
  严禁在用户确认方案后，重新发起一轮无意义的代码大面积搜索、重复反汇编或发散性探查。方案既然已经阐明清楚，行动阶段就要做到“指哪打哪、雷厉风行、精准修改”。
