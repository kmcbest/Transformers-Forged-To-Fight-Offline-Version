# Repository instructions

- Never add files from `media/` to Git. Screenshots and recordings are local-only captures;
  they may include copyrighted game audiovisual content. Keep them ignored and out of commits.

## Build and Output Rules

- If changes do not strictly require packaging a full APK (e.g. server-side/gamedata-only changes), export and output the standalone payload (`build/tftf_offline_payload.bin`).
- If packaging a full APK (`build/Transformers-9.2-offline-redeco-edition.apk`), do NOT output a separate standalone payload (since the payload is already embedded inside the APK).

### Full APK Packaging Standard Pipeline & Critical Pitfalls

When packaging `build/Transformers-9.2-offline-redeco-edition.apk`, you MUST execute the complete 4-step pipeline without skipping any step:

1. **Recompile Native Hook** (if native C code changed):
   ```cmd
   toolchain\android-ndk-r26d\toolchains\llvm\prebuilt\windows-x86_64\bin\aarch64-linux-android28-clang.cmd -shared -O2 -fPIC "-Wl,-soname,libdothook.so" -o tools\nativehook\libdothook.so tools\nativehook\hook.c tools\nativehook\inapk_server.c -llog
   ```

2. **Assemble Unsigned APK with Patched `libil2cpp`**:
   ```cmd
   python Server\build_phone_apk.py "com.kabam.bigrobot_9.2.0-123129100_minAPI23(arm64-v8a,armeabi-v7a)(nodpi)_apkmirror.com.apk" "build\unsigned.apk" --scheme http --server-host 127.0.0.1 --server-port 8080 --bundle-server --patched-il2cpp "build\libil2cpp-arm64-patched.so"
   ```
   > [!CRITICAL] **Pitfall 1 (Network Connection Error)**
   > MUST pass `--patched-il2cpp "build\libil2cpp-arm64-patched.so"`. If omitted, the APK retains the stock unpatched `libil2cpp.so` which lacks `DT_NEEDED: libdothook.so`. Without `libdothook.so`, the offline loopback server (127.0.0.1:8080) is never initialized on app launch, causing a fatal "连接网络出现问题 / Network connection failed" error at the title screen.

3. **Page-Align Native Shared Libraries (`zipalign`)**:
   ```cmd
   toolchain\android-13\zipalign.exe -f -p 4 build\unsigned.apk build\aligned.apk
   ```
   > [!CRITICAL] **Pitfall 2 (System Incompatibility Error)**
   > MUST run `zipalign -f -p 4` before signing. Android 11+ and 64-bit systems strictly enforce 4KB page alignment on uncompressed `.so` libraries. Signing an unaligned APK will cause Android Package Manager to reject installation with "安装包与系统不兼容 / INSTALL_FAILED_NO_MATCHING_ABIS / INSTALL_FAILED_INVALID_APK".

4. **Sign the Aligned APK & Clean Up**:
   ```cmd
   toolchain\android-13\apksigner.bat sign --ks build\debug.keystore --ks-pass pass:android --out build\Transformers-9.2-offline-redeco-edition.apk build\aligned.apk
   del build\unsigned.apk build\aligned.apk
   ```

## Git and pull requests

- The canonical repository for all pushes and pull requests is
  `Gummygamer/Transformers-Forged-To-Fight-Offline-Version`.
- Never create, target, or suggest a pull request for the `geamztheangrybirds727` fork.
- Before creating a pull request, verify that the repository remote resolves to the
  `Gummygamer` repository.
