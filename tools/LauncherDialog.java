package com.kabam.bigrobot;

import android.app.Activity;
import android.app.Dialog;
import android.graphics.Color;
import android.graphics.drawable.ColorDrawable;
import android.os.Build;
import android.util.Log;
import android.view.View;
import android.view.ViewGroup;
import android.view.Window;
import android.view.WindowManager;
import android.webkit.JavascriptInterface;
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
            window.setBackgroundDrawable(new ColorDrawable(Color.TRANSPARENT));
            window.setLayout(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT);
            window.setFlags(WindowManager.LayoutParams.FLAG_FULLSCREEN, WindowManager.LayoutParams.FLAG_FULLSCREEN);
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
        webView.setBackgroundColor(Color.TRANSPARENT);
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

        class JsBridge {
            @JavascriptInterface
            public String getInitialSettings() {
                return currentConfig;
            }

            @JavascriptInterface
            public void saveAndLaunch(final String jsonStr) {
                Log.i(TAG, "saveAndLaunch called with: " + jsonStr);
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
                            dialog.dismiss();
                            Log.i(TAG, "LauncherDialog dismissed");
                        } catch (Exception e) {
                            Log.e(TAG, "Error dismissing dialog: " + e.getMessage());
                        }
                    }
                });
            }
        }

        webView.addJavascriptInterface(new JsBridge(), "Android");
        webView.setWebViewClient(new WebViewClient());

        dialog.setContentView(webView);
        dialog.show();
        webView.loadUrl("file:///android_asset/launcher_menu.html");
        Log.i(TAG, "LauncherDialog displayed successfully");
    }
}
