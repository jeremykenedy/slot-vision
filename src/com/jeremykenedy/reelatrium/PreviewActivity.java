package com.jeremykenedy.reelatrium;

import android.app.Activity;
import android.os.Bundle;
import android.view.View;
import java.io.FileDescriptor;
import java.io.PrintWriter;

public final class PreviewActivity extends Activity {
  private ReelSceneView scene;

  @Override
  public void onCreate(Bundle state) {
    super.onCreate(state);
    getWindow().addFlags(android.view.WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    getWindow()
        .getDecorView()
        .setSystemUiVisibility(
            View.SYSTEM_UI_FLAG_FULLSCREEN
                | View.SYSTEM_UI_FLAG_HIDE_NAVIGATION
                | View.SYSTEM_UI_FLAG_IMMERSIVE_STICKY
                | View.SYSTEM_UI_FLAG_LAYOUT_STABLE);
    scene = new ReelSceneView(this);
    setContentView(scene);
  }

  @Override
  protected void onResume() {
    super.onResume();
    if (scene != null) scene.start();
  }

  @Override
  protected void onDestroy() {
    if (scene != null) scene.destroy();
    super.onDestroy();
  }

  @Override
  public void dump(String prefix, FileDescriptor fd, PrintWriter out, String[] args) {
    super.dump(prefix, fd, out, args);
    if (scene != null) scene.dump(out, prefix);
  }

  @Override
  protected void onPause() {
    if (scene != null) scene.stop();
    super.onPause();
  }
}
