package com.jeremykenedy.reelatrium;

import java.util.Random;

/** The public settings contract; unknown persisted values resolve to documented defaults. */
public final class ReelOptions {
  public static final String[] KEYS = {
    "game", "season", "speed", "brightness", "camera", "background", "view"
  };
  public static final String[] TITLES = {
    "Machine game",
    "Season and theme",
    "Reel speed",
    "Lighting",
    "Camera movement",
    "Background",
    "View mode"
  };
  public static final String[][] VALUES = {
    {"classic", "palace", "garden", "random"},
    {"atrium", "spring", "summer", "autumn", "winter", "random"},
    {"relaxed", "natural", "lively", "random"},
    {"dim", "cinematic", "bright", "random"},
    {"gentle", "wide", "random"},
    {"lounge", "casino", "random"},
    {"cabinet", "fullscreen", "random"}
  };
  public static final String[][] LABELS = {
    {"Classic three reels", "Palace five reels", "Garden twenty-five tiles", "Random"},
    {"Midnight atrium", "Spring blossom", "Summer sun", "Autumn harvest", "Winter frost", "Random"},
    {"Relaxed", "Natural", "Lively", "Random"},
    {"Dim", "Cinematic", "Bright", "Random"},
    {"Slow front orbit", "Slow wide front orbit", "Random"},
    {"Private lounge", "Casino floor", "Random"},
    {"Slot machine", "Fullscreen reels", "Random"}
  };
  public static final String[] DEFAULTS = {
    "classic", "atrium", "natural", "cinematic", "gentle", "lounge", "cabinet"
  };

  private ReelOptions() {}

  public static int settingIndex(String key) {
    for (int i = 0; i < KEYS.length; i++) if (KEYS[i].equals(key)) return i;
    return -1;
  }

  public static boolean valid(String key, String value) {
    int i = settingIndex(key);
    if (i < 0) return false;
    for (String option : VALUES[i]) if (option.equals(value)) return true;
    return false;
  }

  public static String resolve(int setting, String value, Random random) {
    if (!valid(KEYS[setting], value)) value = DEFAULTS[setting];
    if ("random".equals(value)) return VALUES[setting][random.nextInt(VALUES[setting].length - 1)];
    return value;
  }

  public static int columns(String game) {
    return "classic".equals(game) ? 3 : 5;
  }

  public static int rows(String game) {
    return "garden".equals(game) ? 5 : 3;
  }

  public static float speed(String value) {
    if ("relaxed".equals(value)) return 0.65f;
    if ("lively".equals(value)) return 1.35f;
    return 1f;
  }

  public static float light(String value) {
    if ("dim".equals(value)) return 0.65f;
    if ("bright".equals(value)) return 1.2f;
    return 0.9f;
  }
}
