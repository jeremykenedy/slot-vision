package com.jeremykenedy.reelatrium;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.fail;

import org.junit.Test;

public final class RenderProfileTest {
  @Test
  public void ordinaryDumpsKeepTheCurrentScene() {
    assertEquals(RenderProfile.BASELINE, RenderProfile.requested(null, RenderProfile.BASELINE));
    assertEquals(
        RenderProfile.NO_FLOOR,
        RenderProfile.requested(new String[] {"--unrelated"}, RenderProfile.NO_FLOOR));
  }

  @Test
  public void onlyTheSixReviewedProfilesCanChangeTheComparison() {
    for (RenderProfile profile : RenderProfile.values()) {
      assertEquals(
          profile,
          RenderProfile.requested(
              new String[] {"--render-profile=" + profile.id}, RenderProfile.BASELINE));
    }
    try {
      RenderProfile.requested(new String[] {"--render-profile=unknown"}, RenderProfile.BASELINE);
      fail("Unsupported profiles must not change the scene");
    } catch (IllegalArgumentException expected) {
      assertEquals("Unknown render profile", expected.getMessage());
    }
  }
}
