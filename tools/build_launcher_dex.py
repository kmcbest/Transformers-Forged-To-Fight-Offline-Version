#!/usr/bin/env python3
"""Build classes3.dex containing com.kabam.bigrobot.LauncherDialog.
Compiles against minimal Android stubs using local JDK 17 and D8.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "build"
DEX_WORK = BUILD_DIR / "launcher_dex_work"

def build_launcher_dex(output_dex: Path) -> Path:
    if DEX_WORK.exists():
        shutil.rmtree(DEX_WORK)
    DEX_WORK.mkdir(parents=True, exist_ok=True)

    src_dir = DEX_WORK / "src"
    stub_dir = DEX_WORK / "stubs"
    bin_dir = DEX_WORK / "bin"
    out_dir = DEX_WORK / "out"

    src_dir.mkdir()
    stub_dir.mkdir()
    bin_dir.mkdir()
    out_dir.mkdir()

    # 1. Generate minimal Android stubs
    (stub_dir / "android/app").mkdir(parents=True)
    (stub_dir / "android/content").mkdir(parents=True)
    (stub_dir / "android/view").mkdir(parents=True)
    (stub_dir / "android/webkit").mkdir(parents=True)
    (stub_dir / "android/graphics/drawable").mkdir(parents=True)
    (stub_dir / "android/os").mkdir(parents=True)
    (stub_dir / "android/util").mkdir(parents=True)
    (stub_dir / "android/net").mkdir(parents=True)
    (stub_dir / "android/media").mkdir(parents=True)
    (stub_dir / "android/content/res").mkdir(parents=True)

    (stub_dir / "android/os/Build.java").write_text("""package android.os;
public class Build {
    public static class VERSION { public static int SDK_INT = 30; }
    public static class VERSION_CODES { public static final int KITKAT = 19; }
}
""", encoding="utf-8")

    (stub_dir / "android/util/Log.java").write_text("""package android.util;
public class Log {
    public static int i(String tag, String msg) { return 0; }
    public static int e(String tag, String msg) { return 0; }
    public static int e(String tag, String msg, Throwable tr) { return 0; }
    public static int w(String tag, String msg) { return 0; }
}
""", encoding="utf-8")

    (stub_dir / "android/graphics/Color.java").write_text("""package android.graphics;
public class Color { public static final int TRANSPARENT = 0; }
""", encoding="utf-8")

    (stub_dir / "android/graphics/drawable/Drawable.java").write_text("""package android.graphics.drawable;
public class Drawable {}
""", encoding="utf-8")

    (stub_dir / "android/graphics/drawable/ColorDrawable.java").write_text("""package android.graphics.drawable;
public class ColorDrawable extends Drawable { public ColorDrawable(int color) {} }
""", encoding="utf-8")

    (stub_dir / "android/view/View.java").write_text("""package android.view;
public class View {
    public static final int SYSTEM_UI_FLAG_LAYOUT_STABLE = 256;
    public static final int SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION = 512;
    public static final int SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN = 1024;
    public static final int SYSTEM_UI_FLAG_HIDE_NAVIGATION = 2;
    public static final int SYSTEM_UI_FLAG_FULLSCREEN = 4;
    public static final int SYSTEM_UI_FLAG_IMMERSIVE_STICKY = 4096;
    public void setSystemUiVisibility(int visibility) {}
}
""", encoding="utf-8")

    (stub_dir / "android/view/ViewGroup.java").write_text("""package android.view;
public class ViewGroup extends View {
    public static class LayoutParams { public static final int MATCH_PARENT = -1; }
}
""", encoding="utf-8")

    (stub_dir / "android/view/Window.java").write_text("""package android.view;
import android.graphics.drawable.Drawable;
public class Window {
    public static final int FEATURE_NO_TITLE = 1;
    public void setBackgroundDrawable(Drawable d) {}
    public void setLayout(int width, int height) {}
    public void setFlags(int flags, int mask) {}
    public View getDecorView() { return null; }
}
""", encoding="utf-8")

    (stub_dir / "android/view/WindowManager.java").write_text("""package android.view;
public interface WindowManager {
    public static class LayoutParams { public static final int FLAG_FULLSCREEN = 1024; }
}
""", encoding="utf-8")

    (stub_dir / "android/content/Context.java").write_text("""package android.content;
import java.io.File;
import android.content.res.AssetManager;
public class Context {
    public File getFilesDir() { return null; }
    public File getExternalFilesDir(String type) { return null; }
    public AssetManager getAssets() { return null; }
    public Context getApplicationContext() { return this; }
    public void startActivity(Intent intent) {}
}
""", encoding="utf-8")

    (stub_dir / "android/content/res/AssetFileDescriptor.java").write_text("""package android.content.res;
import java.io.FileDescriptor;
import java.io.IOException;
public class AssetFileDescriptor {
    public FileDescriptor getFileDescriptor() { return null; }
    public long getStartOffset() { return 0; }
    public long getLength() { return 0; }
    public void close() throws IOException {}
}
""", encoding="utf-8")

    (stub_dir / "android/content/res/AssetManager.java").write_text("""package android.content.res;
import java.io.IOException;
public class AssetManager {
    public AssetFileDescriptor openFd(String fileName) throws IOException { return null; }
    public String[] list(String path) throws IOException { return null; }
}
""", encoding="utf-8")

    (stub_dir / "android/media/MediaPlayer.java").write_text("""package android.media;
import java.io.FileDescriptor;
import java.io.IOException;
public class MediaPlayer {
    public void setDataSource(FileDescriptor fd, long offset, long length) throws IOException {}
    public void setLooping(boolean looping) {}
    public void setVolume(float leftVolume, float rightVolume) {}
    public void prepare() throws IOException {}
    public void start() {}
    public void pause() {}
    public void stop() {}
    public void release() {}
    public boolean isPlaying() { return false; }
}
""", encoding="utf-8")

    (stub_dir / "android/os/Looper.java").write_text("""package android.os;
public class Looper {
    public static Looper getMainLooper() { return null; }
}
""", encoding="utf-8")

    (stub_dir / "android/os/Handler.java").write_text("""package android.os;
public class Handler {
    public Handler() {}
    public Handler(Looper looper) {}
    public boolean post(Runnable r) { return false; }
    public boolean postDelayed(Runnable r, long delayMillis) { return false; }
}
""", encoding="utf-8")

    (stub_dir / "android/content/Intent.java").write_text("""package android.content;
import android.net.Uri;
public class Intent {
    public static final String ACTION_VIEW = "android.intent.action.VIEW";
    public static final int FLAG_ACTIVITY_NEW_TASK = 0x10000000;
    public Intent(String action, Uri uri) {}
    public Intent addFlags(int flags) { return this; }
}
""", encoding="utf-8")

    (stub_dir / "android/net/Uri.java").write_text("""package android.net;
public class Uri {
    public static Uri parse(String uriString) { return null; }
    public String toString() { return ""; }
}
""", encoding="utf-8")

    (stub_dir / "android/app/Activity.java").write_text("""package android.app;
import java.io.File;
import android.content.Context;
import android.view.Window;
public class Activity extends Context {
    public void runOnUiThread(Runnable r) {}
    public Window getWindow() { return null; }
    public boolean isFinishing() { return false; }
    public boolean isDestroyed() { return false; }
}
""", encoding="utf-8")

    (stub_dir / "android/app/Dialog.java").write_text("""package android.app;
import android.content.Context;
import android.view.View;
import android.view.Window;
public class Dialog {
    public Dialog(Context context, int theme) {}
    public Dialog(Context context) {}
    public boolean requestWindowFeature(int feature) { return true; }
    public void setCancelable(boolean flag) {}
    public Window getWindow() { return null; }
    public void setContentView(View v) {}
    public void show() {}
    public void dismiss() {}
    public boolean isShowing() { return true; }
}
""", encoding="utf-8")

    (stub_dir / "android/webkit/JavascriptInterface.java").write_text("""package android.webkit;
import java.lang.annotation.*;
@Retention(RetentionPolicy.RUNTIME)
@Target(ElementType.METHOD)
public @interface JavascriptInterface {}
""", encoding="utf-8")

    (stub_dir / "android/webkit/WebSettings.java").write_text("""package android.webkit;
public class WebSettings {
    public void setJavaScriptEnabled(boolean b) {}
    public void setDomStorageEnabled(boolean b) {}
    public void setAllowFileAccess(boolean b) {}
    public void setAllowContentAccess(boolean b) {}
}
""", encoding="utf-8")

    (stub_dir / "android/webkit/ConsoleMessage.java").write_text("""package android.webkit;
public class ConsoleMessage {
    public String message() { return null; }
    public int lineNumber() { return 0; }
    public String sourceId() { return null; }
}
""", encoding="utf-8")

    (stub_dir / "android/webkit/WebChromeClient.java").write_text("""package android.webkit;
public class WebChromeClient {
    public boolean onConsoleMessage(ConsoleMessage cm) { return false; }
}
""", encoding="utf-8")

    (stub_dir / "android/webkit/WebResourceRequest.java").write_text("""package android.webkit;
import android.net.Uri;
public interface WebResourceRequest {
    Uri getUrl();
}
""", encoding="utf-8")

    (stub_dir / "android/webkit/WebViewClient.java").write_text("""package android.webkit;
public class WebViewClient {
    public void onPageFinished(WebView view, String url) {}
    public boolean shouldOverrideUrlLoading(WebView view, String url) { return false; }
    public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) { return false; }
}
""", encoding="utf-8")

    (stub_dir / "android/webkit/WebView.java").write_text("""package android.webkit;
import android.content.Context;
import android.view.View;
public class WebView extends View {
    public WebView(Context context) {}
    public void setBackgroundColor(int color) {}
    public WebSettings getSettings() { return null; }
    public void addJavascriptInterface(Object obj, String name) {}
    public void setWebViewClient(WebViewClient client) {}
    public void setWebChromeClient(WebChromeClient client) {}
    public void loadUrl(String url) {}
    public boolean isHardwareAccelerated() { return true; }
    public Context getContext() { return null; }
}
""", encoding="utf-8")

    # 2. Copy LauncherDialog.java and CustomMusicPlayer.java
    launcher_src = ROOT / "tools" / "LauncherDialog.java"
    music_src = ROOT / "tools" / "CustomMusicPlayer.java"
    target_dir = src_dir / "com" / "kabam" / "bigrobot"
    target_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy(launcher_src, target_dir / "LauncherDialog.java")
    if music_src.exists():
        shutil.copy(music_src, target_dir / "CustomMusicPlayer.java")

    # 3. Compile
    javac = None
    for cand in [
        ROOT / "toolchain" / "jdk-17" / "bin" / "javac.exe",
        Path("C:/Program Files/Java/jdk-17/bin/javac.exe"),
        Path("C:/Program Files/Microsoft/jdk-17.0.20.8-hotspot/bin/javac.exe"),
    ]:
        if cand.exists():
            javac = str(cand)
            break
    if not javac:
        javac = shutil.which("javac")
    if not javac:
        raise FileNotFoundError("javac not found in toolchain or system JDK paths")

    stub_files = [str(p) for p in stub_dir.rglob("*.java")]
    src_files = [str(p) for p in src_dir.rglob("*.java")]

    subprocess.run([str(javac), "--release", "8", "-d", str(bin_dir)] + stub_files, check=True)
    subprocess.run([str(javac), "--release", "8", "-cp", str(bin_dir), "-d", str(bin_dir)] + src_files, check=True)

    # Clean stub class files
    for sf in stub_files:
        rel = Path(sf).relative_to(stub_dir).with_suffix(".class")
        target = bin_dir / rel
        if target.exists():
            target.unlink()
    for d in list(bin_dir.glob("android*")) + [bin_dir / "android"]:
        if d.exists():
            shutil.rmtree(d)

    # 4. Convert to DEX with D8
    java = None
    for cand in [
        ROOT / "toolchain" / "jdk-17" / "bin" / "java.exe",
        Path("C:/Program Files/Java/jdk-17/bin/java.exe"),
        Path("C:/Program Files/Microsoft/jdk-17.0.20.8-hotspot/bin/java.exe"),
    ]:
        if cand.exists():
            java = str(cand)
            break
    if not java:
        java = shutil.which("java")
    if not java:
        raise FileNotFoundError("java not found in toolchain or system JDK paths")

    d8_jar = None
    for cand in [
        ROOT / "toolchain" / "android-13" / "lib" / "d8.jar",
        ROOT / "toolchain" / "android-sdk" / "build-tools" / "34.0.0" / "lib" / "d8.jar",
    ] + list(ROOT.glob("toolchain/**/d8.jar")):
        if cand.exists():
            d8_jar = cand
            break
    if not d8_jar:
        raise FileNotFoundError("d8.jar not found in toolchain")

    class_files = [str(p) for p in bin_dir.rglob("*.class")]

    cmd = [str(java), "-cp", str(d8_jar), "com.android.tools.r8.D8", "--min-api", "23", "--output", str(out_dir)] + class_files
    subprocess.run(cmd, check=True)

    gen_dex = out_dir / "classes.dex"
    output_dex.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy(gen_dex, output_dex)
    print(f"[+] Successfully built {output_dex} ({output_dex.stat().st_size} bytes)")
    return output_dex

if __name__ == "__main__":
    out = BUILD_DIR / "classes3.dex"
    if len(sys.argv) > 1:
        out = Path(sys.argv[1])
    build_launcher_dex(out)
