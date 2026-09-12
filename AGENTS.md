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

