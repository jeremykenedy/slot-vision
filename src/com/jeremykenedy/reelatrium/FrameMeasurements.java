package com.jeremykenedy.reelatrium;

/** Bounded recent durations for local, user-requested renderer diagnostics. */
final class FrameMeasurements {
  private final long[] durations = new long[64];
  private int next;
  private int count;

  void add(long nanos) {
    if (nanos < 0) return;
    durations[next] = nanos;
    next = (next + 1) % durations.length;
    count = Math.min(count + 1, durations.length);
  }

  void clear() {
    next = 0;
    count = 0;
  }

  int count() {
    return count;
  }

  long meanNanos() {
    if (count == 0) return -1;
    double total = 0;
    for (int i = 0; i < count; i++) total += durations[i];
    return Math.round(total / count);
  }
}
