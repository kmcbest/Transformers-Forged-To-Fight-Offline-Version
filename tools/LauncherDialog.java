package com.kabam.bigrobot;

import android.app.Activity;
import android.app.Dialog;
import android.content.Context;
import android.content.Intent;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.net.Uri;
import android.os.Build;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.JavascriptInterface;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.nio.charset.StandardCharsets;

public class LauncherDialog {
    private static final String TAG = "TFTF_LAUNCHER";
    private static final String SETTINGS_FILE = "user_settings.json";

    public static void show(final Activity activity) {
        if (activity == null) {
            Log.e(TAG, "Activity is null, cannot show launcher dialog");
            return;
        }

        File filesDir = activity.getFilesDir();
        File configFile = new File(filesDir, SETTINGS_FILE);
        if (configFile.exists()) {
            try {
                byte[] bytes = new byte[(int) configFile.length()];
                FileInputStream fis = new FileInputStream(configFile);
                fis.read(bytes);
                fis.close();
                String content = new String(bytes, StandardCharsets.UTF_8);
                if (content.contains("\"skip_launcher_next_time\": true") ||
                    content.contains("\"skip_launcher_next_time\":true")) {
                    Log.i(TAG, "Launcher skipped according to user_settings.json");
                    return;
                }
            } catch (Exception e) {
                Log.w(TAG, "Error checking user_settings.json: " + e.getMessage());
            }
        }

        activity.runOnUiThread(new Runnable() {
            @Override
            public void run() {
                try {
                    showDialogOnUI(activity);
                } catch (Throwable t) {
                    Log.e(TAG, "Failed to show LauncherDialog", t);
                }
            }
        });
    }

    private static void showDialogOnUI(final Activity activity) {
        if (activity == null || activity.isFinishing()) {
            Log.w(TAG, "Activity is null or finishing, aborting dialog");
            return;
        }
        if (Build.VERSION.SDK_INT >= 17 && activity.isDestroyed()) {
            Log.w(TAG, "Activity is destroyed, aborting dialog");
            return;
        }

        final Dialog dialog = new Dialog(activity, 0x01030007); // android.R.style.Theme_Black_NoTitleBar_Fullscreen
        dialog.requestWindowFeature(Window.FEATURE_NO_TITLE);
        dialog.setCancelable(false);

        Window window = dialog.getWindow();
        if (window != null) {
            // Hardware acceleration (0x01000000) and dark opaque background to eliminate software blending lag
            window.setBackgroundDrawable(new ColorDrawable(0xff070b14));
            window.setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
            window.setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN | 0x01000000, WindowManager.LayoutParams.FLAG_FULLSCREEN | 0x01000000);
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.KITKAT) {
                window.getDecorView().setSystemUiVisibility(
                    View.SYSTEM_UI_FLAG_LAYOUT_STABLE
                    | View.SYSTEM_UI_FLAG_LAYOUT_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_LAYOUT_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                    | View.SYSTEM_UI_FLAG_FULLSCREEN
                    | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                );
            }
        }

        final WebView webView = new WebView(activity);
        webView.setBackgroundColor(0xff070b14);
        WebSettings ws = webView.getSettings();
        if (ws != null) {
            ws.setJavaScriptEnabled(true);
            ws.setDomStorageEnabled(true);
            ws.setAllowFileAccess(true);
            ws.setAllowContentAccess(true);
        }

        File configFile = new File(activity.getFilesDir(), SETTINGS_FILE);
        String loaded = "";
        if (configFile.exists()) {
            try {
                byte[] bytes = new byte[(int) configFile.length()];
                FileInputStream fis = new FileInputStream(configFile);
                fis.read(bytes);
                fis.close();
                loaded = new String(bytes, StandardCharsets.UTF_8);
            } catch (Exception e) {}
        }
        final String currentConfig = loaded;

        webView.addJavascriptInterface(new JsBridge(activity, dialog, currentConfig), "Android");
        webView.setWebViewClient(new LauncherExternalClient());
        webView.setWebChromeClient(new WebChromeClient() {
            @Override
            public boolean onConsoleMessage(ConsoleMessage cm) {
                Log.i(TAG, "[JS Console] " + cm.message() + " (line " + cm.lineNumber() + ")");
                return true;
            }
        });

        dialog.setContentView(webView);
        dialog.show();
        webView.loadUrl("file:///android_asset/launcher_menu.html");
        Log.i(TAG, "LauncherDialog displayed successfully with hardware acceleration");
    }

    public static class LauncherExternalClient extends WebViewClient {
        @Override
        public void onPageFinished(WebView view, String url) {
            super.onPageFinished(view, url);
            try {
                Log.i(TAG, "LAUNCHER hardware=" + view.isHardwareAccelerated());
            } catch (Throwable t) {}
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, String url) {
            if (url != null && url.startsWith("file:///android_asset/")) {
                return false;
            }
            try {
                Intent intent = new Intent(Intent.ACTION_VIEW, Uri.parse(url));
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK);
                view.getContext().startActivity(intent);
                Log.i(TAG, "External link opened: " + url);
            } catch (Throwable t) {
                Log.w(TAG, "Cannot open external link: " + t.getMessage());
            }
            return true;
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            if (request != null && request.getUrl() != null) {
                return shouldOverrideUrlLoading(view, request.getUrl().toString());
            }
            return false;
        }
    }

    public static class JsBridge {
        private final Activity activity;
        private final Dialog dialog;
        private final String initialConfig;

        public JsBridge(Activity activity, Dialog dialog, String initialConfig) {
            this.activity = activity;
            this.dialog = dialog;
            this.initialConfig = initialConfig;
        }

        @JavascriptInterface
        public String getInitialSettings() {
            return initialConfig;
        }

        @JavascriptInterface
        public void saveAndLaunch(final String jsonStr) {
            Log.i(TAG, "saveAndLaunch called with: " + jsonStr);
            try {
                CustomMusicPlayer.loadSettings();
            } catch (Throwable t) {}
            try {
                File file = new File(activity.getFilesDir(), SETTINGS_FILE);
                FileOutputStream fos = new FileOutputStream(file);
                fos.write(jsonStr.getBytes(StandardCharsets.UTF_8));
                fos.close();
                Log.i(TAG, "Saved user settings to " + file.getAbsolutePath());
            } catch (Exception e) {
                Log.e(TAG, "Failed to save internal settings: " + e.getMessage());
            }

            try {
                File extDir = activity.getExternalFilesDir(null);
                if (extDir != null) {
                    File extFile = new File(extDir, SETTINGS_FILE);
                    FileOutputStream fos = new FileOutputStream(extFile);
                    fos.write(jsonStr.getBytes(StandardCharsets.UTF_8));
                    fos.close();
                    Log.i(TAG, "Saved user settings to external: " + extFile.getAbsolutePath());
                }
            } catch (Exception e) {}

            activity.runOnUiThread(new Runnable() {
                @Override
                public void run() {
                    try {
                        if (dialog != null && dialog.isShowing()) {
                            dialog.dismiss();
                            Log.i(TAG, "LauncherDialog dismissed");
                        }
                    } catch (Exception e) {
                        Log.e(TAG, "Error dismissing dialog: " + e.getMessage());
                    }
                }
            });
        }
    }
}
