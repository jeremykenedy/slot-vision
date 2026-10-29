package com.jeremykenedy.reelatrium;

import static org.junit.Assert.*;

import org.junit.Test;

public final class FrameChangesTest {
  @Test
  public void submitsInitialRestAndResubmitsItForEveryNewCabinet() {
    FrameChanges changes = new FrameChanges();
    for (int model = 0; model < 3; model++) {
      assertTrue(changes.lever(0));
      assertTrue(changes.beacon(0));
      for (int reel = 0; reel < 5; reel++) assertTrue(changes.reel(reel, 0));
      assertFalse(changes.lever(0));
      assertFalse(changes.beacon(0));
      for (int reel = 0; reel < 5; reel++) assertFalse(changes.reel(reel, 0));
      changes.reset();
    }
  }

  @Test
  public void movingValuesAreNeverQuantizedAndReturningToRestIsSubmitted() {
    FrameChanges changes = new FrameChanges();
    for (float value : new float[] {0, Float.MIN_VALUE, .5f, Math.nextUp(.5f), 70, 0}) {
      assertTrue(changes.lever(value));
      assertTrue(changes.beacon(value));
      assertTrue(changes.reel(4, value));
      assertFalse(changes.lever(value));
      assertFalse(changes.beacon(value));
      assertFalse(changes.reel(4, value));
    }
  }

  @Test
  public void everyPresentedPoseMatchesTheOriginalMotionAcrossRoundsAndSkippedTimes() {
    for (String game : new String[] {"classic", "palace", "garden"}) {
      int columns = ReelOptions.columns(game);
      int rows = ReelOptions.rows(game);
      int sectors = rows == 5 ? 16 : 8;
      for (float speed : new float[] {.65f, 1, 1.35f}) {
        for (boolean fullscreen : new boolean[] {false, true}) {
          FrameChanges changes = new FrameChanges();
          float[] submitted = new float[columns + 2];
          java.util.Arrays.fill(submitted, Float.NaN);
          double duration = LeverMotion.roundDuration(columns, speed, fullscreen);
          int count = 0;
          for (double time = 0; time < duration * 14; time += count++ % 7 == 0 ? .71 : 1.0 / 30) {
            long number = (long) Math.floor(time / duration);
            double elapsed = time - number * duration;
            double phase = LeverMotion.reelPhase(elapsed, speed, fullscreen);
            ReelRound previous = new ReelRound(42, number - 1, columns, rows);
            ReelRound round = new ReelRound(42, number, columns, rows);
            float lever = LeverMotion.angle(elapsed);
            if (changes.lever(lever)) submitted[0] = lever;
            assertEquals(lever, submitted[0], 0);
            for (int reel = 0; reel < columns; reel++) {
              float angle =
                  (float) ((round.position(previous, phase, reel) % sectors) * (360.0 / sectors));
              if (changes.reel(reel, angle)) submitted[reel + 1] = angle;
              assertEquals(angle, submitted[reel + 1], 0);
            }
            double age = (phase - ReelRound.settledAt(columns)) / speed;
            float pulse =
                round.jackpot() && age >= 0 && age < 10
                    ? Math.max(0f, (float) Math.sin(age * 9))
                    : 0f;
            if (changes.beacon(pulse)) submitted[columns + 1] = pulse;
            assertEquals(pulse, submitted[columns + 1], 0);
          }
        }
      }
    }
  }

  @Test
  public void settledReelsAndQuietBeaconNeedNoMoreNativeWrites() {
    FrameChanges changes = new FrameChanges();
    ReelRound previous = new ReelRound(42, 6, 5, 3);
    ReelRound round = new ReelRound(42, 7, 5, 3);
    int submissions = 0;
    for (int frame = 0; frame < 300; frame++) {
      double seconds = 7 + frame / 30.0;
      if (changes.lever(LeverMotion.angle(seconds))) submissions++;
      if (changes.beacon(0)) submissions++;
      for (int reel = 0; reel < 5; reel++) {
        float angle = (float) ((round.position(previous, seconds, reel) % 8) * 45);
        if (changes.reel(reel, angle)) submissions++;
      }
    }
    assertEquals(7, submissions);
  }
}
