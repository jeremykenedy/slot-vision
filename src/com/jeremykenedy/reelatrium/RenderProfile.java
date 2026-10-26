package com.jeremykenedy.reelatrium;

/** Temporary local GPU comparisons; never stored as screensaver preferences. */
enum RenderProfile {
  BASELINE("baseline"),
  NO_FLOOR("no-floor"),
  UNLIT_FLOOR("unlit-floor"),
  NO_SURROUND("no-surround"),
  NO_POST("no-post"),
  NO_IBL("no-ibl");

  final String id;

  RenderProfile(String id) {
    this.id = id;
  }

  static RenderProfile requested(String[] args, RenderProfile current) {
    if (args == null) return current;
    for (String arg : args) {
      if (!arg.startsWith("--render-profile=")) continue;
      String value = arg.substring("--render-profile=".length());
      for (RenderProfile profile : values()) if (profile.id.equals(value)) return profile;
      throw new IllegalArgumentException("Unknown render profile");
    }
    return current;
  }
}
