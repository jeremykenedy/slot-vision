package com.jeremykenedy.reelatrium;

import static org.junit.Assert.*;

import org.junit.Test;

public final class FullscreenCameraTest {
  @Test
  public void everyLayoutKeepsItsAspectAndEnoughOverscanForTheWholeDrift() {
    for (String game : new String[] {"classic", "palace", "garden"}) {
      FullscreenCamera camera = new FullscreenCamera(game, 16.0 / 9);
      assertEquals(16.0 / 9, camera.width / camera.height, 1e-12);
      assertTrue(camera.height > .5 && camera.height < .8);
      for (int seconds = 0; seconds <= 18000; seconds++) {
        assertTrue(Math.abs(camera.x(seconds)) <= camera.width * .004001);
        assertTrue(Math.abs(camera.y(seconds)) <= camera.height * .004001);
        assertTrue(camera.width / 2 + Math.abs(camera.x(seconds)) < camera.width / .97 / 2);
        assertTrue(camera.height / 2 + Math.abs(camera.y(seconds)) < camera.height / .97 / 2);
        assertTrue(Math.abs(camera.x(seconds + 1) - camera.x(seconds)) < camera.width * .00023);
        assertTrue(Math.abs(camera.y(seconds + 1) - camera.y(seconds)) < camera.height * .00019);
      }
    }
  }

  @Test
  public void timedSamplesMoveBothAxesWithoutHardResets() {
    FullscreenCamera camera = new FullscreenCamera("classic", 16.0 / 9);
    assertTrue(Math.abs(camera.x(15) - camera.x(0)) > camera.width * .0025);
    assertTrue(Math.abs(camera.y(30) - camera.y(0)) > camera.height * .0025);
    assertEquals(camera.x(0), camera.x(110), 1e-12);
    assertEquals(camera.y(0), camera.y(137), 1e-12);
  }
}
