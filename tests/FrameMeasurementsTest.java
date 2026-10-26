package com.jeremykenedy.reelatrium;

import static org.junit.Assert.assertEquals;

import org.junit.Test;

public final class FrameMeasurementsTest {
  @Test
  public void unsupportedDurationsAreUnavailableInsteadOfZeroCost() {
    FrameMeasurements values = new FrameMeasurements();
    values.add(-1);
    values.add(-2);
    assertEquals(0, values.count());
    assertEquals(-1, values.meanNanos());
  }

  @Test
  public void recentFramesReplaceOldWarmupAndPreserveZeroDurations() {
    FrameMeasurements values = new FrameMeasurements();
    values.add(1000000);
    for (int i = 0; i < 64; i++) values.add(i % 2 == 0 ? 0 : 200);
    assertEquals(64, values.count());
    assertEquals(100, values.meanNanos());
    values.add(128);
    assertEquals(102, values.meanNanos());
    values.clear();
    assertEquals(0, values.count());
    assertEquals(-1, values.meanNanos());
    values.add(400);
    assertEquals(400, values.meanNanos());
  }
}
