package com.kabam.bigrobot;

import android.app.Activity;
import android.app.Application;
import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.content.res.AssetManager;
import android.media.MediaPlayer;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.util.Log;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Random;

public class CustomMusicPlayer {
    private static final String TAG = "TFTF_Jukebox";
    private static final String SETTINGS_FILE = "user_settings.json";

    private static Context sContext;
    private static boolean sEnabled = true;
    private static float sMasterVolume = 1.0f;
    private static boolean sIsPaused = false;
    private static boolean sAppInBackground = false;
    private static boolean sLifecycleRegistered = false;

    private static String sCurrentCategory = "";
    private static String sCurrentTrackName = "";
    private static String sSessionMainTrack = ""; // Fixed track for 'main' during this session

    private static MediaPlayer sActivePlayer;
    private static Handler sHandler;
    private static final Random sRandom = new Random();

    private static final Map<String, List<String>> sCategoryTracks = new HashMap<>();
    private static final Map<String, String> sLastPlayedTrack = new HashMap<>();

    // Static fallback track names in case AssetManager.list() fails or returns empty
    private static final Map<String, String[]> FALLBACK_TRACKS = new HashMap<>();
    static {
        FALLBACK_TRACKS.put("main", new String[]{
            "Original_Theme_Loop.mp3",
            "Subterranean Hum.mp3"
        });
        FALLBACK_TRACKS.put("quest", new String[]{
            "Hydraulic_Engine_Bay.mp3",
            "quest-1.mp3",
            "The_Bridge_at_World_s_End.mp3"
        });
        FALLBACK_TRACKS.put("fight", new String[]{
            "Original_Fight_Loop.mp3",
            "Torn_Alloy.mp3",
            "Zero Impact.mp3"
        });
        FALLBACK_TRACKS.put("arena", new String[]{
            "Floor_Beneath_the_Blade.mp3"
        });
        FALLBACK_TRACKS.put("raid", new String[]{
            "Sector_Defense.mp3"
        });
        FALLBACK_TRACKS.put("bot_showcase", new String[]{
            "bot_showcase-1.mp3"
        });
    }

    private static Handler getHandler() {
        if (sHandler == null) {
            sHandler = new Handler(Looper.getMainLooper());
        }
        return sHandler;
    }

    public static synchronized void ensureInit() {
        if (sContext != null) return;
        try {
            Class<?> upCls = Class.forName("com.unity3d.player.UnityPlayer");
            Activity act = (Activity) upCls.getField("currentActivity").get(null);
            if (act != null) {
                init(act);
                return;
            }
        } catch (Throwable ignored) {}

        try {
            Class<?> atCls = Class.forName("android.app.ActivityThread");
            Object appObj = atCls.getMethod("currentApplication").invoke(null);
            if (appObj instanceof Context) {
                initContext((Context) appObj);
                return;
            }
        } catch (Throwable ignored) {}
    }

    public static synchronized void init(Activity activity) {
        if (activity == null) return;
        initContext(activity.getApplicationContext());
        registerLifecycle(activity);
    }

    private static void registerLifecycle(Activity activity) {
        if (sLifecycleRegistered || activity == null) return;
        try {
            Application app = activity.getApplication();
            if (app != null) {
                app.registerActivityLifecycleCallbacks(new Application.ActivityLifecycleCallbacks() {
                    private int mStartedCount = 0;

                    @Override
                    public void onActivityStarted(Activity a) {
                        mStartedCount++;
                        if (mStartedCount == 1) {
                            Log.i(TAG, "App entered foreground, resuming music");
                            resumeFromBackground();
                        }
                    }

                    @Override
                    public void onActivityStopped(Activity a) {
                        mStartedCount--;
                        if (mStartedCount <= 0) {
                            mStartedCount = 0;
                            Log.i(TAG, "App entered background / screen locked, pausing music");
                            pauseForBackground();
                        }
                    }

                    @Override public void onActivityCreated(Activity a, Bundle b) {}
                    @Override public void onActivityResumed(Activity a) {}
                    @Override public void onActivityPaused(Activity a) {}
                    @Override public void onActivitySaveInstanceState(Activity a, Bundle b) {}
                    @Override public void onActivityDestroyed(Activity a) {}
                });
                sLifecycleRegistered = true;
                Log.i(TAG, "ActivityLifecycleCallbacks registered successfully");
            }
        } catch (Throwable t) {
            Log.w(TAG, "Failed to register ActivityLifecycleCallbacks: " + t.getMessage());
        }
    }

    public static synchronized void pauseForBackground() {
        sAppInBackground = true;
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                if (sActivePlayer != null) {
                    try {
                        if (sActivePlayer.isPlaying()) {
                            sActivePlayer.pause();
                        }
                    } catch (Exception ignored) {}
                }
            }
        });
    }

    public static synchronized void resumeFromBackground() {
        sAppInBackground = false;
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                if (!sEnabled || sIsPaused) return;
                if (sActivePlayer != null) {
                    try {
                        if (!sActivePlayer.isPlaying()) {
                            sActivePlayer.start();
                        }
                    } catch (Exception ignored) {}
                }
            }
        });
    }

    public static synchronized void initContext(Context context) {
        if (context == null) return;
        sContext = context;
        loadSettings();
        scanTracks();
        Log.i(TAG, "CustomMusicPlayer initialized. Enabled=" + sEnabled + ", SessionMain=" + sSessionMainTrack);
    }

    public static synchronized void setEnabled(boolean enabled) {
        sEnabled = enabled;
        Log.i(TAG, "setEnabled: " + enabled);
        if (!sEnabled) {
            stopMusic();
        }
    }

    public static synchronized boolean isEnabled() {
        return sEnabled;
    }

    public static synchronized void loadSettings() {
        if (sContext == null) return;
        try {
            File f = new File(sContext.getFilesDir(), SETTINGS_FILE);
            if (!f.exists()) {
                File ext = new File(sContext.getExternalFilesDir(null), SETTINGS_FILE);
                if (ext.exists()) f = ext;
            }
            if (f.exists()) {
                FileInputStream fis = new FileInputStream(f);
                byte[] data = new byte[(int) f.length()];
                fis.read(data);
                fis.close();
                String json = new String(data, StandardCharsets.UTF_8);
                if (json.contains("\"enable_custom_music\"")) {
                    int idx = json.indexOf("\"enable_custom_music\"");
                    int colon = json.indexOf(':', idx);
                    if (colon > 0) {
                        String sub = json.substring(colon + 1).trim();
                        sEnabled = !sub.startsWith("false");
                    }
                }
            }
            Log.i(TAG, "loadSettings finished: sEnabled=" + sEnabled);
        } catch (Exception e) {
            Log.w(TAG, "Error reading user_settings.json: " + e.getMessage());
        }
    }

    private static void scanTracks() {
        if (sContext == null) return;
        sCategoryTracks.clear();
        String[] categories = new String[]{"main", "quest", "fight", "arena", "raid", "bot_showcase"};
        AssetManager am = sContext.getAssets();
        for (String cat : categories) {
            List<String> list = new ArrayList<>();
            try {
                String[] files = am.list("music/" + cat);
                if (files != null) {
                    for (String file : files) {
                        if (file.toLowerCase().endsWith(".mp3")) {
                            list.add("music/" + cat + "/" + file);
                        }
                    }
                }
            } catch (IOException e) {
                Log.w(TAG, "Failed to list music/" + cat + ": " + e.getMessage());
            }

            // Fallback check if list is empty
            if (list.isEmpty() && FALLBACK_TRACKS.containsKey(cat)) {
                Log.i(TAG, "am.list was empty, using fallback track list for category: " + cat);
                for (String fallbackName : FALLBACK_TRACKS.get(cat)) {
                    String fullPath = "music/" + cat + "/" + fallbackName;
                    try {
                        AssetFileDescriptor testAfd = am.openFd(fullPath);
                        if (testAfd != null) {
                            list.add(fullPath);
                            testAfd.close();
                        }
                    } catch (IOException e) {
                        Log.w(TAG, "Fallback track not found in assets: " + fullPath);
                    }
                }
            }

            sCategoryTracks.put(cat, list);
            Log.i(TAG, "Category [" + cat + "] found " + list.size() + " tracks: " + list);
        }

        // Fixed session track for 'main' (base menu)
        List<String> mainTracks = sCategoryTracks.get("main");
        if (mainTracks != null && !mainTracks.isEmpty()) {
            sSessionMainTrack = mainTracks.get(sRandom.nextInt(mainTracks.size()));
        } else {
            sSessionMainTrack = "";
        }
        Log.i(TAG, "Selected session locked main track: " + sSessionMainTrack);
    }

    public static synchronized void playCategory(final String category) {
        ensureInit();
        if (!sEnabled || sContext == null) {
            Log.w(TAG, "playCategory ignored: enabled=" + sEnabled + ", hasContext=" + (sContext != null));
            return;
        }
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                doPlayCategory(category);
            }
        });
    }

    private static void doPlayCategory(String category) {
        if (!sEnabled || sContext == null) return;
        String trackPath = null;
        if ("main".equals(category)) {
            if (sSessionMainTrack != null && !sSessionMainTrack.isEmpty()) {
                trackPath = sSessionMainTrack;
            } else {
                List<String> list = sCategoryTracks.get("main");
                if (list != null && !list.isEmpty()) trackPath = list.get(0);
            }
        } else {
            List<String> list = sCategoryTracks.get(category);
            if (list == null || list.isEmpty()) {
                if ("arena".equals(category) || "raid".equals(category)) {
                    list = sCategoryTracks.get("fight");
                } else {
                    list = sCategoryTracks.get("main");
                }
            }
            if (list != null && !list.isEmpty()) {
                if (list.size() == 1) {
                    trackPath = list.get(0);
                } else {
                    String last = sLastPlayedTrack.get(category);
                    List<String> candidates = new ArrayList<>(list);
                    if (last != null && candidates.size() > 1) {
                        candidates.remove(last);
                    }
                    trackPath = candidates.get(sRandom.nextInt(candidates.size()));
                }
                sLastPlayedTrack.put(category, trackPath);
            }
        }

        if (trackPath == null) {
            Log.w(TAG, "No track found for category: " + category);
            return;
        }

        // If the exact same track is already playing, keep it playing smoothly
        if (trackPath.equals(sCurrentTrackName) && sActivePlayer != null) {
            try {
                if (sActivePlayer.isPlaying()) {
                    Log.i(TAG, "Track already playing smoothly: " + trackPath);
                    return;
                }
            } catch (Exception ignored) {}
        }

        sCurrentCategory = category;
        sCurrentTrackName = trackPath;
        startCrossfade(trackPath);
    }

    private static void startCrossfade(final String assetPath) {
        if (sContext == null) return;
        try {
            AssetManager am = sContext.getAssets();
            AssetFileDescriptor afd = am.openFd(assetPath);
            final MediaPlayer nextPlayer = new MediaPlayer();
            try {
                nextPlayer.setDataSource(afd.getFileDescriptor(), afd.getStartOffset(), afd.getLength());
                nextPlayer.setLooping(true);
                nextPlayer.setVolume(0f, 0f);
                nextPlayer.prepare();
            } finally {
                try {
                    afd.close();
                } catch (Exception ignored) {}
            }
            if (!sAppInBackground && !sIsPaused) {
                nextPlayer.start();
            }
            Log.i(TAG, "Successfully started MediaPlayer for: " + assetPath);

            final MediaPlayer oldPlayer = sActivePlayer;
            sActivePlayer = nextPlayer;

            if (oldPlayer == null) {
                final int steps = 5;
                final float volTarget = sMasterVolume;
                for (int i = 1; i <= steps; i++) {
                    final int step = i;
                    getHandler().postDelayed(new Runnable() {
                        @Override
                        public void run() {
                            float progress = (float) step / steps;
                            float vol = (float) Math.sqrt(progress) * volTarget;
                            if (sActivePlayer == nextPlayer && !sAppInBackground && !sIsPaused) {
                                try {
                                    nextPlayer.setVolume(vol, vol);
                                } catch (Exception ignored) {}
                            }
                        }
                    }, i * 40);
                }
                return;
            }

            // Snappy crossfade over 350ms in 7 steps (50ms interval) with equal-power curve
            final int steps = 7;
            final float volTarget = sMasterVolume;
            for (int i = 1; i <= steps; i++) {
                final int step = i;
                getHandler().postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        float progress = (float) step / steps;
                        float newVol = (float) Math.sqrt(progress) * volTarget;
                        float oldVol = (float) Math.sqrt(1.0f - progress) * volTarget;

                        if (sActivePlayer == nextPlayer && !sAppInBackground && !sIsPaused) {
                            try {
                                nextPlayer.setVolume(newVol, newVol);
                            } catch (Exception ignored) {}
                        }
                        if (oldPlayer != null) {
                            try {
                                if (oldPlayer.isPlaying()) {
                                    oldPlayer.setVolume(oldVol, oldVol);
                                }
                            } catch (Exception ignored) {}
                            if (step == steps) {
                                try {
                                    oldPlayer.stop();
                                    oldPlayer.release();
                                } catch (Exception ignored) {}
                            }
                        }
                    }
                }, i * 50);
            }
            Log.i(TAG, "Crossfading into: " + assetPath + " (vol=" + volTarget + ")");
        } catch (Exception e) {
            Log.e(TAG, "Failed to crossfade track " + assetPath + ": " + e.getMessage());
        }
    }

    public static synchronized void fadeOut(final int durationMs) {
        ensureInit();
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                if (sActivePlayer == null) return;
                final MediaPlayer playerToFade = sActivePlayer;
                final float curVol = sMasterVolume;
                final int steps = Math.max(1, durationMs / 50);
                for (int i = 1; i <= steps; i++) {
                    final int step = i;
                    getHandler().postDelayed(new Runnable() {
                        @Override
                        public void run() {
                            float progress = (float) step / steps;
                            float vol = (float) Math.sqrt(1.0f - progress) * curVol;
                            try {
                                if (playerToFade.isPlaying()) {
                                    playerToFade.setVolume(vol, vol);
                                }
                            } catch (Exception ignored) {}
                            if (step == steps) {
                                try {
                                    playerToFade.stop();
                                    playerToFade.release();
                                } catch (Exception ignored) {}
                                if (sActivePlayer == playerToFade) {
                                    sActivePlayer = null;
                                    sCurrentCategory = "";
                                    sCurrentTrackName = "";
                                }
                            }
                        }
                    }, i * 50);
                }
            }
        });
    }

    public static synchronized void setVolume(final float volume) {
        ensureInit();
        sMasterVolume = Math.max(0.0f, Math.min(1.0f, volume));
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                if (sActivePlayer != null && !sAppInBackground && !sIsPaused) {
                    try {
                        sActivePlayer.setVolume(sMasterVolume, sMasterVolume);
                    } catch (Exception ignored) {}
                }
            }
        });
    }

    public static synchronized void pauseMusic(final boolean pause) {
        ensureInit();
        sIsPaused = pause;
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                if (sActivePlayer != null) {
                    try {
                        if (pause) {
                            if (sActivePlayer.isPlaying()) sActivePlayer.pause();
                        } else {
                            if (!sAppInBackground && sEnabled && !sActivePlayer.isPlaying()) {
                                sActivePlayer.start();
                            }
                        }
                    } catch (Exception ignored) {}
                }
            }
        });
    }

    public static synchronized void stopMusic() {
        ensureInit();
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                if (sActivePlayer != null) {
                    try {
                        sActivePlayer.stop();
                        sActivePlayer.release();
                    } catch (Exception ignored) {}
                    sActivePlayer = null;
                }
                sCurrentCategory = "";
                sCurrentTrackName = "";
            }
        });
    }
}
