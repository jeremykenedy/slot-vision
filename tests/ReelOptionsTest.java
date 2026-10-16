package com.jeremykenedy.reelatrium;

import static org.junit.Assert.*;

import java.util.Random;
import org.junit.Test;

public final class ReelOptionsTest {
  @Test
  public void settingsRejectUnknownKeysAndValuesAndResolveEveryChoice() {
    assertEquals(-1, ReelOptions.settingIndex(null));
    assertFalse(ReelOptions.valid("absent", "classic"));
    for (int i = 0; i < ReelOptions.KEYS.length; i++) {
      assertEquals(ReelOptions.DEFAULTS[i], ReelOptions.resolve(i, "broken", new Random(1)));
      assertEquals(ReelOptions.DEFAULTS[i], ReelOptions.resolve(i, null, new Random(1)));
      for (String value : ReelOptions.VALUES[i]) {
        assertTrue(ReelOptions.valid(ReelOptions.KEYS[i], value));
        String selected = ReelOptions.resolve(i, value, new Random(2));
        assertTrue(ReelOptions.valid(ReelOptions.KEYS[i], selected));
        assertNotEquals("random", selected);
        if (!"random".equals(value)) assertEquals(value, selected);
      }
    }
  }

  @Test
  public void layoutsHaveThePromisedNumberOfVisiblePositions() {
    assertEquals(9, ReelOptions.columns("classic") * ReelOptions.rows("classic"));
    assertEquals(15, ReelOptions.columns("palace") * ReelOptions.rows("palace"));
    assertEquals(25, ReelOptions.columns("garden") * ReelOptions.rows("garden"));
  }

  @Test
  public void presetsUseOrderedBrightnessAndSpeed() {
    assertTrue(ReelOptions.speed("relaxed") < ReelOptions.speed("natural"));
    assertTrue(ReelOptions.speed("natural") < ReelOptions.speed("lively"));
    assertTrue(ReelOptions.light("dim") < ReelOptions.light("cinematic"));
    assertTrue(ReelOptions.light("cinematic") < ReelOptions.light("bright"));
  }
}
