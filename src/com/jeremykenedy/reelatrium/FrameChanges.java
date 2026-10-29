package com.jeremykenedy.reelatrium;

import java.util.Arrays;

/** Tracks exact values already submitted to the current cabinet's native components. */
final class FrameChanges {
  private final float[] reels = new float[5];
  private float lever;
  private float beacon;

  FrameChanges() {
    reset();
  }

  void reset() {
    Arrays.fill(reels, Float.NaN);
    lever = Float.NaN;
    beacon = Float.NaN;
  }

  boolean lever(float value) {
    if (lever == value) return false;
    lever = value;
    return true;
  }

  boolean reel(int index, float value) {
    if (reels[index] == value) return false;
    reels[index] = value;
    return true;
  }

  boolean beacon(float value) {
    if (beacon == value) return false;
    beacon = value;
    return true;
  }
}
