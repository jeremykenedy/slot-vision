package com.jeremykenedy.reelatrium;

import android.service.dreams.DreamService;

public final class ReelAtriumDreamService extends DreamService {
  private ReelSceneView scene;

  @Override
  public void onAttachedToWindow() {
    super.onAttachedToWindow();
    setInteractive(false);
    setFullscreen(true);
    scene = new ReelSceneView(this);
    setContentView(scene);
  }

  @Override
  public void onDreamingStarted() {
    super.onDreamingStarted();
    if (scene != null) scene.start();
  }

  @Override
  public void onDreamingStopped() {
    if (scene != null) scene.stop();
    super.onDreamingStopped();
  }

  @Override
  public void onDetachedFromWindow() {
    if (scene != null) scene.stop();
    if (scene != null) scene.destroy();
    scene = null;
    super.onDetachedFromWindow();
  }
}
