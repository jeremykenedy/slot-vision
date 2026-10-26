package com.jeremykenedy.reelatrium;

import static org.junit.Assert.*;

import org.junit.Test;

public final class LeverMotionTest {
  @Test
  public void leverPullsThenReturnsToItsRestPosition() {
    assertEquals(0, LeverMotion.angle(-1), 0);
    assertEquals(0, LeverMotion.angle(0), 0);
    assertEquals(-1.5, LeverMotion.angle(.06), .0001);
    assertEquals(-3, LeverMotion.angle(.12), .0001);
    assertEquals(33.5, LeverMotion.angle(.47), .0001);
    assertEquals(70, LeverMotion.angle(.82), .0001);
    assertEquals(70, LeverMotion.angle(.9), .0001);
    assertEquals(70, LeverMotion.angle(.94), .0001);
    assertEquals(35, LeverMotion.angle(1.33), .0001);
    assertEquals(0, LeverMotion.angle(1.72), 0);
    assertEquals(0, LeverMotion.angle(20), 0);
    for (double boundary : new double[] {0, .12, .82, .94, 1.72}) {
      assertEquals(
          LeverMotion.angle(boundary - .00001), LeverMotion.angle(boundary + .00001), .0001);
    }
  }

  @Test
  public void reelsWaitForThePullWithoutChangingTheWinOrCelebration() {
    for (float speed : new float[] {.65f, 1, 1.35f}) {
      for (int columns : new int[] {3, 5}) {
        ReelRound previous = new ReelRound(42, -1, columns, 3);
        ReelRound round = new ReelRound(42, 0, columns, 3);
        assertTrue(round.jackpot());
        assertEquals(192, round.celebrationCoinCount());
        assertEquals(10, round.celebrationDuration(), 0);
        for (double time : new double[] {0, .2, .6, .819}) {
          for (int reel = 0; reel < columns; reel++) {
            assertEquals(
                previous.stops[reel],
                round.position(previous, LeverMotion.reelPhase(time, speed, false), reel),
                0);
          }
        }
        assertTrue(
            round.position(previous, LeverMotion.reelPhase(.9, speed, false), 0)
                > previous.stops[0]);
        double settled = LeverMotion.spinDelay(false) + ReelRound.settledAt(columns) / speed;
        for (int reel = 0; reel < columns; reel++) {
          assertEquals(
              round.position(previous, ReelRound.settledAt(columns), reel),
              round.position(previous, LeverMotion.reelPhase(settled, speed, false), reel),
              .00001);
        }
        assertEquals(
            ReelRound.roundDuration(columns, speed) + .82,
            LeverMotion.roundDuration(columns, speed, false),
            .00001);
        assertEquals(
            ReelRound.roundDuration(columns, speed),
            LeverMotion.roundDuration(columns, speed, true),
            0);
        assertEquals(.4 * speed, LeverMotion.reelPhase(.4, speed, true), .00001);
      }
    }
  }
}
