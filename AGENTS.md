# Repository instructions

- Never add files from `media/` to Git. Screenshots and recordings are local-only captures;
  they may include copyrighted game audiovisual content. Keep them ignored and out of commits.

## Build and Output Rules

- If changes do not strictly require packaging a full APK (e.g. server-side/gamedata-only changes), export and output the standalone payload (`build/tftf_offline_payload.bin`).
- If packaging a full APK (`build/Transformers-9.2-offline-redeco-edition.apk`), do NOT output a separate standalone payload (since the payload is already embedded inside the APK).

## Git and pull requests

- The canonical repository for all pushes and pull requests is
  `Gummygamer/Transformers-Forged-To-Fight-Offline-Version`.
- Never create, target, or suggest a pull request for the `geamztheangrybirds727` fork.
- Before creating a pull request, verify that the repository remote resolves to the
  `Gummygamer` repository.
