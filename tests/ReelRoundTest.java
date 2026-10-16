package com.jeremykenedy.reelatrium;

import static org.junit.Assert.*;

import org.junit.Test;

public final class ReelRoundTest {
  @Test
  public void paysOnlyMatchingRowsFromTheFirstReelAndScalesLongerWins() {
    assertEquals(0, ReelRound.payout(new int[] {0, 1, 2}, 3));
    assertEquals(0, ReelRound.payout(new int[] {1, 0, 0, 0, 0}, 3));
    assertEquals(64, ReelRound.payout(new int[] {1, 0, 7, 0, 1}, 3));
    assertEquals(64, ReelRound.payout(new int[] {-1, 0, 1, 0, -1}, 3));
    assertEquals(115, ReelRound.payout(new int[] {0, 0, 0, 1, 2}, 5));
    int three = ReelRound.payout(new int[] {0, 0, 0}, 3);
    assertEquals(8, three);
    assertEquals(80 * 3, ReelRound.payout(new int[] {0, 0, 0, 0}, 3));
    assertEquals(80 * 8, ReelRound.payout(new int[] {0, 0, 0, 0, 0}, 3));
    assertEquals(three, ReelRound.payout(new int[] {8, 0, 8}, 3));
    assertEquals(60, ReelRound.payout(new int[] {-1, 7, 15}, 3));
    assertTrue(ReelRound.payout(new int[] {0, 0, 0, 0, 0}, 5) > three * 8);
  }

  @Test
  public void everyWinHasCoinsAndLargerPayoutsHaveLargerBoundedBursts() {
    ReelRound jackpot = new ReelRound(1, 0, 3, 3);
    assertTrue(jackpot.jackpot());
    assertTrue(new ReelRound(1, 0, 3, 3).payout > 0);
    assertEquals(100, ReelRound.payout(jackpot.stops, 3));
    assertEquals(0, ReelRound.coinCount(0));
    assertEquals(0, ReelRound.coinCount(-1));
    assertTrue(ReelRound.coinCount(1) > 0);
    assertTrue(ReelRound.coinCount(8) > ReelRound.coinCount(1));
    assertEquals(64, ReelRound.coinCount(100000));
  }

  @Test
  public void spinsSettleExactlyOnTheSymbolsUsedToCalculateThePayout() {
    for (int columns : new int[] {3, 5})
      for (int rows : new int[] {3, 5}) {
        int wins = 0;
        for (int round = 0; round < 80; round++) {
          ReelRound previous = new ReelRound(22, round - 1, columns, rows);
          ReelRound current = new ReelRound(22, round, columns, rows);
          assertEquals(rows == 5 ? 16 : 8, current.sectors);
          assertEquals(ReelRound.payout(current.stops, rows), current.payout);
          boolean allSeven = true;
          for (int stop : current.stops) allSeven &= stop % 8 == 5;
          assertEquals(allSeven, current.jackpot());
          if (current.payout > 0) wins++;
          for (int reel = 0; reel < columns; reel++) {
            assertEquals(previous.stops[reel], current.position(previous, 0, reel), 0);
            assertEquals(
                current.stops[reel],
                current.position(previous, ReelRound.settledAt(columns), reel) % current.sectors,
                .000001);
            assertEquals(
                current.position(previous, 7, reel), current.position(previous, 11, reel), 0);
            assertTrue(current.position(previous, 1, reel) > current.position(previous, .5, reel));
          }
        }
        assertTrue(wins > 10);
      }
  }
}
