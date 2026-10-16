package com.jeremykenedy.reelatrium;

import java.util.Random;

/** A decorative spin with visible row wins, without wagers or stored currency. */
public final class ReelRound {
  private static final int[] VALUES = {8, 12, 15, 25, 40, 100, 20, 60};
  public final int[] stops;
  public final int payout;
  public final int sectors;

  public ReelRound(long seed, long round, int columns, int rows) {
    sectors = rows == 5 ? 16 : 8;
    Random random = new Random(seed + round * 7919L);
    stops = new int[columns];
    for (int i = 0; i < columns; i++) stops[i] = random.nextInt(sectors);
    if (round % 3 == 0 || random.nextInt(3) == 0) {
      int symbol = random.nextInt(8);
      int offset = random.nextInt(rows) - rows / 2;
      int matched = 3 + random.nextInt(columns - 2);
      for (int i = 0; i < matched; i++) stops[i] = wrap(symbol - offset, 8);
    }
    if (round % 12 == 0) java.util.Arrays.fill(stops, 5);
    payout = payout(stops, rows);
  }

  public static int payout(int[] stops, int rows) {
    int total = 0;
    int first = stops.length == 3 ? 0 : -rows / 2;
    int last = stops.length == 3 ? 0 : rows / 2;
    for (int row = first; row <= last; row++) {
      int[] offsets = new int[stops.length];
      java.util.Arrays.fill(offsets, row);
      total += linePayout(stops, offsets);
    }
    if (stops.length == 5 && rows == 3) {
      total += linePayout(stops, new int[] {-1, 0, 1, 0, -1});
      total += linePayout(stops, new int[] {1, 0, -1, 0, 1});
    }
    return total;
  }

  private static int linePayout(int[] stops, int[] offsets) {
    int symbol = wrap(stops[0] + offsets[0], 8);
    int matched = 1;
    while (matched < stops.length && wrap(stops[matched] + offsets[matched], 8) == symbol)
      matched++;
    return matched < 3 ? 0 : VALUES[symbol] * (matched == 5 ? 8 : matched == 4 ? 3 : 1);
  }

  public boolean jackpot() {
    for (int stop : stops) if (wrap(stop, 8) != 5) return false;
    return true;
  }

  public static int coinCount(int payout) {
    return payout <= 0 ? 0 : Math.min(64, 4 + (int) Math.ceil(Math.sqrt(payout) * 3));
  }

  public double celebrationDuration() {
    return payout <= 0 ? 0 : jackpot() ? 10 : Math.min(6, 1.5 + Math.sqrt(payout) * .12);
  }

  public static double roundDuration(int columns, float speed) {
    return settledAt(columns) / speed + 11;
  }

  private static int wrap(int value, int sectors) {
    return (value % sectors + sectors) % sectors;
  }

  public static double settledAt(int columns) {
    return 4 + (columns - 1) * .35;
  }

  public double position(ReelRound previous, double phase, int reel) {
    double progress = Math.min(phase / (4 + reel * .35), 1);
    double eased = progress * progress * (3 - 2 * progress);
    int travel = sectors * 3 + wrap(stops[reel] - previous.stops[reel], sectors);
    return previous.stops[reel] + travel * eased;
  }
}
