package com.jeremykenedy.reelatrium;

/** A parallel front view that drifts inside a small overscan margin. */
public final class FullscreenCamera {
  public final double height;
  public final double width;

  public FullscreenCamera(String game, double aspect) {
    height = ("garden".equals(game) ? .76 : "palace".equals(game) ? .63 : .70) * .97;
    width = height * aspect;
  }

  public double x(double seconds) {
    return Math.sin(seconds * Math.PI * 2 / 110) * width * .004;
  }

  public double y(double seconds) {
    return Math.cos(seconds * Math.PI * 2 / 137) * height * .004;
  }
}
