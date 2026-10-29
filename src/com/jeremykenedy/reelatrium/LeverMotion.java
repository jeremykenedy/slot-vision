package com.jeremykenedy.reelatrium;

/** Cabinet spins begin when the lever reaches the bottom of its stroke. */
public final class LeverMotion {
  private LeverMotion() {}

  public static double spinDelay(boolean fullscreen) {
    return fullscreen ? 0 : .82;
  }

  public static double roundDuration(int columns, float speed, boolean fullscreen) {
    return ReelRound.roundDuration(columns, speed) + spinDelay(fullscreen);
  }

  public static double reelPhase(double elapsed, float speed, boolean fullscreen) {
    return Math.max(0, elapsed - spinDelay(fullscreen)) * speed;
  }

  public static float angle(double elapsed) {
    if (elapsed <= 0) return 0;
    if (elapsed < .12) return (float) (-3 * ease(elapsed / .12));
    if (elapsed < .82) return (float) (-3 + 73 * ease((elapsed - .12) / .70));
    if (elapsed < .94) return 70;
    if (elapsed < 1.72) return (float) (70 * (1 - ease((elapsed - .94) / .78)));
    return 0;
  }

  private static double ease(double progress) {
    return progress * progress * progress * (progress * (progress * 6 - 15) + 10);
  }
}
