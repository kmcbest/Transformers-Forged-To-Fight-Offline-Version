package com.kabam.bigrobot;

import android.app.Activity;
import android.content.Context;
import android.content.res.AssetFileDescriptor;
import android.content.res.AssetManager;
import android.media.MediaPlayer;
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

    private static String sCurrentCategory = "";
    private static String sCurrentTrackName = "";
    private static String sSessionMainTrack = ""; // Requirement 1: fixed track for 'main' during this session

    private static MediaPlayer sActivePlayer;
    private static Handler sHandler;
    private static final Random sRandom = new Random();

    private static final Map<String, List<String>> sCategoryTracks = new HashMap<>();
    private static final Map<String, String> sLastPlayedTrack = new HashMap<>();

    private static Handler getHandler() {
        if (sHandler == null) {
            sHandler = new Handler(Looper.getMainLooper());
        }
        return sHandler;
    }

    public static synchronized void init(Activity activity) {
        if (activity == null) return;
        sContext = activity.getApplicationContext();
        loadSettings();
        scanTracks();
        Log.i(TAG, "CustomMusicPlayer initialized. Enabled=" + sEnabled + ", SessionMain=" + sSessionMainTrack);
    }

    public static synchronized void setEnabled(boolean enabled) {
        sEnabled = enabled;
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
            sCategoryTracks.put(cat, list);
            Log.i(TAG, "Category [" + cat + "] found " + list.size() + " tracks.");
        }

        // Requirement 1: Pick fixed session track for 'main'
        List<String> mainTracks = sCategoryTracks.get("main");
        if (mainTracks != null && !mainTracks.isEmpty()) {
            sSessionMainTrack = mainTracks.get(sRandom.nextInt(mainTracks.size()));
        } else {
            sSessionMainTrack = "";
        }
    }

    public static synchronized void playCategory(final String category) {
        if (!sEnabled || sContext == null) return;
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
                    Log.i(TAG, "Track already playing: " + trackPath);
                    return;
                }
            } catch (Exception ignored) {}
        }

        sCurrentCategory = category;
        sCurrentTrackName = trackPath;
        startCrossfade(trackPath);
    }

    private static void startCrossfade(String assetPath) {
        try {
            AssetFileDescriptor afd = sContext.getAssets().openFd(assetPath);
            final MediaPlayer nextPlayer = new MediaPlayer();
            nextPlayer.setDataSource(afd.getFileDescriptor(), afd.getStartOffset(), afd.getLength());
            afd.close();
            nextPlayer.setLooping(true);
            nextPlayer.setVolume(0f, 0f);
            nextPlayer.prepare();
            nextPlayer.start();

            final MediaPlayer oldPlayer = sActivePlayer;
            sActivePlayer = nextPlayer;

            // Crossfade over 1000ms in 20 steps (50ms interval)
            final int steps = 20;
            final float volTarget = sMasterVolume;
            for (int i = 1; i <= steps; i++) {
                final int step = i;
                getHandler().postDelayed(new Runnable() {
                    @Override
                    public void run() {
                        float progress = (float) step / steps;
                        if (sActivePlayer == nextPlayer) {
                            try {
                                nextPlayer.setVolume(volTarget * progress, volTarget * progress);
                            } catch (Exception ignored) {}
                        }
                        if (oldPlayer != null) {
                            try {
                                if (oldPlayer.isPlaying()) {
                                    float oldVol = volTarget * (1.0f - progress);
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

    public static synchronized void setVolume(final float volume) {
        sMasterVolume = Math.max(0.0f, Math.min(1.0f, volume));
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                if (sActivePlayer != null) {
                    try {
                        sActivePlayer.setVolume(sMasterVolume, sMasterVolume);
                    } catch (Exception ignored) {}
                }
            }
        });
    }

    public static synchronized void pauseMusic(final boolean pause) {
        sIsPaused = pause;
        getHandler().post(new Runnable() {
            @Override
            public void run() {
                if (sActivePlayer != null) {
                    try {
                        if (pause && sActivePlayer.isPlaying()) {
                            sActivePlayer.pause();
                        } else if (!pause && !sActivePlayer.isPlaying()) {
                            sActivePlayer.start();
                        }
                    } catch (Exception ignored) {}
                }
            }
        });
    }

    public static synchronized void stopMusic() {
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
